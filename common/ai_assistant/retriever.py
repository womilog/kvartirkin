"""Tiny TF-IDF retriever over the apartment knowledge base.

Why roll our own:

* Zero new dependencies — pure stdlib (``math``, ``re``, ``collections``).
* The corpus is tiny (tens to low hundreds of docs), so any O(N·V) scan
  finishes in well under a millisecond.
* The data changes whenever an admin edits a listing; rebuilding the index
  is cheap, so we just invalidate by TTL.

If the catalogue grows to thousands of items, swap this file for a
pgvector-backed retriever — ``Assistant`` only depends on the
``search()`` signature.
"""

from __future__ import annotations

import math
import re
import threading
import time
from collections import Counter
from dataclasses import dataclass
from typing import List, Tuple

from .knowledge_base import Document, load_documents

# Match Cyrillic + Latin word characters and digits. ``\w`` in Python's
# ``re`` already matches Unicode letters, but being explicit documents intent.
_TOKEN_RE = re.compile(r"[\w\-]+", re.UNICODE)

# A short Russian/English stop-word list — keeps the index small and stops
# common words from dominating cosine scores.
_STOPWORDS = frozenset(
    """
    и в во не что он на я с со как а то все она так его но да ты к у же вы за
    бы по только ее мне было вот от меня еще нет о из ему теперь когда даже ну
    вдруг ли если уже или ни быть был него до вас нибудь опять уж вам ведь там
    потом себя ничего ей может они тут где есть надо ней для мы тебя их чем
    была сам чтоб без будто чего раз тоже себе под будет ж тогда кто этот того
    потому этого какой совсем ним здесь эту ней свою впрочем хорошо свое перед
    иногда лучше чуть том нельзя такой им более всегда конечно всю между
    the a an and or of to in is are was were be been being it this that these
    those for with on at by from as i you he she we they me him her us them
    """.split()
)


def _tokenize(text: str) -> list[str]:
    return [
        t.lower()
        for t in _TOKEN_RE.findall(text)
        if len(t) > 1 and t.lower() not in _STOPWORDS
    ]


@dataclass
class _IndexedDoc:
    doc: Document
    tf: Counter  # raw term frequencies
    norm: float  # pre-computed L2 norm of the tf-idf vector


class Retriever:
    """In-memory TF-IDF retriever with a thread-safe rebuild.

    Use ``get_retriever()`` to obtain the shared instance. The instance
    rebuilds its index lazily on the first query and whenever it is older
    than ``ttl_seconds``.
    """

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._built_at: float = 0.0
        self._docs: List[_IndexedDoc] = []
        self._idf: dict[str, float] = {}

    # -- index management ---------------------------------------------------
    def _needs_rebuild(self) -> bool:
        return (
            not self._docs
            or (time.monotonic() - self._built_at) > self._ttl
        )

    def _rebuild(self) -> None:
        documents = load_documents()
        df: Counter = Counter()
        indexed: list[_IndexedDoc] = []

        for d in documents:
            tokens = _tokenize(d.text + " " + d.title)
            if not tokens:
                continue
            tf = Counter(tokens)
            indexed.append(_IndexedDoc(doc=d, tf=tf, norm=0.0))
            for term in tf:
                df[term] += 1

        n_docs = max(len(indexed), 1)
        # Smoothed IDF (a la sklearn) avoids div-by-zero and dampens super-common terms.
        idf = {
            term: math.log((n_docs + 1) / (cnt + 1)) + 1.0
            for term, cnt in df.items()
        }

        # Pre-compute vector norms once.
        for ix in indexed:
            sq = 0.0
            for term, cnt in ix.tf.items():
                w = cnt * idf.get(term, 0.0)
                sq += w * w
            ix.norm = math.sqrt(sq) or 1.0

        self._docs = indexed
        self._idf = idf
        self._built_at = time.monotonic()

    def invalidate(self) -> None:
        """Force the next ``search()`` to rebuild the index."""
        with self._lock:
            self._built_at = 0.0
            self._docs = []

    # -- query --------------------------------------------------------------
    def search(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """Return the top-``k`` documents with their cosine scores (desc)."""
        with self._lock:
            if self._needs_rebuild():
                self._rebuild()
            docs = self._docs
            idf = self._idf

        q_tokens = _tokenize(query)
        if not q_tokens or not docs:
            return []

        q_tf = Counter(q_tokens)
        q_vec = {t: c * idf.get(t, 0.0) for t, c in q_tf.items()}
        q_norm = math.sqrt(sum(w * w for w in q_vec.values())) or 1.0

        scored: list[tuple[Document, float]] = []
        for ix in docs:
            # Cosine similarity: dot(q, d) / (|q| * |d|).
            # Iterate over the smaller of the two vectors for speed.
            if len(q_vec) <= len(ix.tf):
                dot = sum(
                    qw * ix.tf.get(term, 0) * idf.get(term, 0.0)
                    for term, qw in q_vec.items()
                )
            else:
                dot = sum(
                    q_vec.get(term, 0.0) * cnt * idf.get(term, 0.0)
                    for term, cnt in ix.tf.items()
                )
            if dot <= 0:
                continue
            score = dot / (q_norm * ix.norm)
            scored.append((ix.doc, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


_RETRIEVER: Retriever | None = None
_RETRIEVER_LOCK = threading.Lock()


def get_retriever() -> Retriever:
    """Process-wide retriever singleton."""
    global _RETRIEVER
    if _RETRIEVER is None:
        with _RETRIEVER_LOCK:
            if _RETRIEVER is None:
                _RETRIEVER = Retriever()
    return _RETRIEVER

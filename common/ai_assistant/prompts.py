"""Prompt templates for the assistant.

Kept in a dedicated module so prompt engineers can iterate without touching
any Python logic.
"""

from .knowledge_base import load_rules_text

BASE_SYSTEM_PROMPT = (
    "Ты — вежливый и точный нейро-консультант сервиса посуточной аренды\n"
    "квартир \"Квартиркинъ\" в городах Геленджик и Воркута. Ты помогаешь гостям подобрать\n"
    "апартаменты, разъясняешь правила бронирования и отвечаешь на общие\n"
    "вопросы о сайте.\n"
    "\n"
    "Правила:\n"
    "1. Отвечай кратко, по-русски, дружелюбно, на «вы».\n"
    "2. Опирайся ТОЛЬКО на сведения из блока «Контекст». Если данных в\n"
    "   контексте нет — честно скажи об этом и предложи связаться с\n"
    "   администратором или посмотреть страницу «Квартиры».\n"
    "3. Не выдумывай цены, адреса, удобства и даты. Не обещай скидок.\n"
    "4. Если гость спрашивает о бронировании — объясни, что заявка\n"
    "   оформляется на странице квартиры и подтверждается\n"
    "   администратором.\n"
    "5. Если вопрос не относится к аренде или сайту — мягко верни диалог\n"
    "   к теме.\n"
    "6. Когда уместно — упомяни конкретную квартиру по названию и дай\n"
    "   понять, что её можно открыть из каталога.\n"
    "7. По вопросам о правилах проживания опирайся на блок «Правила\n"
    "   проживания» ниже — это официальные правила сервиса. Излагай их\n"
    "   точно и не придумывай пунктов, которых там нет.\n"
    "8. Если вопрос спорный, неоднозначный или не описан в правилах —\n"
    "   не принимай решение самостоятельно. Вежливо сообщи, что вопрос\n"
    "   решается индивидуально, и перенаправь гостя к администратору\n"
    "   (контакты в подвале сайта).\n"
)


def _rules_block() -> str:
    """Embed the full living-rules text into the system prompt.

    Loaded fresh so edits to the .txt file take effect without a code change
    (the prompt is rebuilt via ``build_system_prompt()`` per assistant init).
    """
    rules = load_rules_text()
    if not rules:
        return ""
    return (
        "\n\nПравила проживания (официальные правила сервиса, "
        "используй их при ответах о проживании):\n\n" + rules
    )


def build_system_prompt() -> str:
    """Return the persona prompt with the living rules appended."""
    return BASE_SYSTEM_PROMPT + _rules_block()


# Backwards-compatible module-level constant (rules included).
SYSTEM_PROMPT = build_system_prompt()


def build_context_block(snippets: list[str]) -> str:
    """Wrap retrieved RAG snippets into a single context block."""
    if not snippets:
        return "Контекст: (база знаний не вернула релевантных записей)"
    body = "\n\n---\n\n".join(snippets)
    return f"Контекст из базы знаний (используй только его):\n\n{body}"

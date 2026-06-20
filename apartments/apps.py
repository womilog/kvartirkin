from django.apps import AppConfig


class ApartmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apartments'
    verbose_name = 'Апартаменты'

    def ready(self):
        # Workaround for Django 4.2 + Python 3.14 incompatibility.
        #
        # In Python 3.14, copy(super()) used inside
        # django.template.context.BaseContext.__copy__ returns a `super`
        # proxy object, and the subsequent `duplicate.dicts = ...`
        # assignment fails with:
        #   "'super' object has no attribute 'dicts' and no dict for
        #    setting new attributes"
        # This breaks the admin changelist (and any template that calls
        # Context.new / copy(context)).
        from copy import copy as _copy
        from django.template import context as _ctx

        def _basecontext_copy(self):
            duplicate = self.__class__.__new__(self.__class__)
            duplicate.__dict__.update(self.__dict__)
            duplicate.dicts = self.dicts[:]
            return duplicate

        def _context_copy(self):
            duplicate = _basecontext_copy(self)
            duplicate.render_context = _copy(self.render_context)
            return duplicate

        _ctx.BaseContext.__copy__ = _basecontext_copy
        _ctx.Context.__copy__ = _context_copy
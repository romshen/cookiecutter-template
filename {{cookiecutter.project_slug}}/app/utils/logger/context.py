"""Модуль в котором написана реализация контекста, например, для использования в логировании"""
from collections import ChainMap
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any


class _ContextManager:
    _context: ContextVar[ChainMap] = ContextVar("_context")

    @property
    def context(self) -> ChainMap:
        """Общий контекст"""
        if (context := self._context.get(None)) is not None:
            return context
        context = ChainMap()
        self._context.set(context)
        return context

    def get(self, key: str, default: Any = None) -> str:
        """Получаем значение из общего контекста(включая локальные)"""
        return self.context.get(key, default)

    def update(self, **kwargs):
        """Обновить глобальный контекст"""
        kwargs = {key: str(value) for key, value in kwargs.items()}
        self.context.maps[-1].update(kwargs)

    @contextmanager
    def tmp_context(self, **extra):
        """
        Создаем локальный контекст. Он не изменяет глобальный, но заменяет его значения
        Все изменения сделанные в него будут отменены после закрытия контекст менеджера
        """
        parent_context = self.context
        now_context = parent_context.new_child(
            {key: str(value) for key, value in extra.items()}
        )
        self._context.set(now_context)
        try:
            yield now_context
        finally:
            self._context.set(parent_context)

    def __getitem__(self, key: str) -> str:
        """Получаем значение из общего контекста(включая локальные)"""
        return self.context[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Изменяем глобальный контекст"""
        self.context.maps[-1][key] = str(value)


CONTEXT = _ContextManager()

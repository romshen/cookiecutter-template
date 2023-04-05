"""Ошибки http-сессии"""


class SessionError(Exception):
    """Базовый класс ошибок сессии"""


class ClientSessionError(SessionError):
    """Ошибка клиента"""


class UnknownSessionError(SessionError):
    """Неизвестная ошибка Http-соединения"""

"""Схемы для передачи системных ошибок на фронт"""
# pylint: disable = too-few-public-methods, no-name-in-module
# pylint: disable = no-self-argument, duplicate-code
from fastapi import status
from pydantic import BaseModel, PydanticValueError


class CustomValidationError(PydanticValueError):
    """Класс ошибки для изменения шаблона сообщения, создаваемого pydantic."""

    msg_template = '{message} "{wrong_value}"'


class Model(BaseModel):
    """Базоавя модель"""

    message: str
    detail: str = ""


class ErrorModel(Model):
    """Модель ошибки"""

    level: str = "error"


class WarningModel(Model):
    """Модель предупреждения"""

    level: str = "warning"


# pylint: disable=R6101
responses = {
    status.HTTP_403_FORBIDDEN: {"model": ErrorModel},
    status.HTTP_404_NOT_FOUND: {"model": ErrorModel},
}

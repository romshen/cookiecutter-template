"""Валидаторы для pydantic моделей, которые используются как тип к полю"""
# pylint: disable=unused-argument
import re
from collections import ChainMap
from collections.abc import Callable, Generator, Sequence
from datetime import date, datetime
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Protocol, TypeVar
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from pydantic.validators import (  # pylint: disable=no-name-in-module
    str_validator,
)

from app.config.settings import settings
from app.utils.logger.logs_adapter import logger
from app.utils.url_helper import get_domain

_IT = TypeVar("_IT")  # input type
_RT = TypeVar("_RT")  # return type

ValidatorsType = Generator[Callable[[_IT], _RT], None, None]


class _TypeWithValidators(Protocol):
    """Pydantic validator"""

    @classmethod
    def __get_validators__(cls) -> Generator[Callable, None, None]:
        ...


_T = TypeVar("_T", bound=_TypeWithValidators)


class And:
    """
    Для использования нескольких валидаторов

    Пример использования:
    class PydanticModel(BaseModel):
        some_field: And[OnlyDomain, DecodeIdna]

    В этом случае, сначала выполнятся все функции-валидаторы из OnlyDomain, а потом из DecodeIdna
    """

    @staticmethod
    def get_validators(
        classes: Sequence[type[_TypeWithValidators]],
    ) -> Callable:
        """Получаем последовательно декораторы из classes"""

        def wrapped() -> Generator[Callable, None, None]:
            for class_ in classes:
                yield from class_.__get_validators__()

        return wrapped

    def __class_getitem__(cls, classes: Sequence[type[_T]]) -> type[_T]:
        class_names = ", ".join(class_.__name__ for class_ in classes)
        new_cls = type(
            f"And[{class_names}]",
            (classes[-1],),
            {
                # для типов от pydantic, например, которые создаются через constr()
                **ChainMap(*(class_.__dict__ for class_ in classes)),
                "__get_validators__": cls.get_validators(classes),
            },
        )
        return new_cls


class DecodeIdna(str):
    """
    Перевод idna кодировки в человеко читаемый вид
    """

    @classmethod
    def __get_validators__(cls) -> ValidatorsType[str, str]:
        yield cls.decode_idna

    @staticmethod
    def decode_idna(value: str) -> str:
        """Декодируем из idna кодировки. Если не получилось отдаем то что пришло"""
        try:
            return value.encode("idna").decode("idna")
        except UnicodeError:
            return value


class StripDot(str):
    """
    Удаляет точки слева и справа строки
    """

    @classmethod
    def __get_validators__(cls) -> ValidatorsType[str, str]:
        yield cls.strip_dot

    @classmethod
    def strip_dot(cls, value: str) -> str:
        """Удаляем точки слева и справа"""
        return value.strip(".")


def split_comma_separated_row(value: str) -> list[str] | None:
    """Разбивает строку в список строк по запятым."""
    if not value:
        return None

    values = [
        part_cleaned
        for part in value.split(",")
        if (part_cleaned := part.strip())
    ]

    return values


def now_msk():
    """Текущее время по мск"""
    return datetime.now(ZoneInfo("Europe/Moscow"))

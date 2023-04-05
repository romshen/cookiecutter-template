"""Тестирование модуля pydantic_validators"""
# pylint: disable=no-name-in-module, too-few-public-methods, duplicate-code
from datetime import date, datetime

import pytest
from pydantic import BaseModel

from app.utils.pydantic_validators import DateValidator, TruncateSourceLink


@pytest.mark.parametrize(
    ("input_value", "expected_value"),
    (
        ("17.11.2022", date(2022, 11, 17)),
        (date(2022, 11, 17), date(2022, 11, 17)),
        (datetime(2022, 11, 17, 1, 1, 1), date(2022, 11, 17)),
    ),
)
def test_parse_date(input_value, expected_value):
    """Проверка валидатора DateValidator"""

    class Class(BaseModel):
        """Тестовый класс"""

        date: DateValidator | None

    assert Class(date=input_value).date == expected_value


@pytest.mark.parametrize(
    ("input_value", "expected_value"),
    (
        ("https://www.youtube.com/", "youtube.com"),
        ("http://www.youtube.com/", "youtube.com"),
        ("http://youtube.com/", "youtube.com"),
        ("http://youtube.com", "youtube.com"),
        ("http://youtube.com/123", "youtube.com/123"),
    ),
)
def test_truncate_source_link(input_value, expected_value):
    """Проверка валидатора TruncateSourceLink"""

    class Class(BaseModel):
        """Тестовый класс"""

        source: TruncateSourceLink

    assert Class(source=input_value).source == expected_value

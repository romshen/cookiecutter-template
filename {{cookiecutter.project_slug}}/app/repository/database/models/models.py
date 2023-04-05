"""Инициализация моделей."""
import re

from sqlalchemy import (
    JSON,
    TEXT,
    TIMESTAMP,
    BigInteger,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Index,
    Integer,
    MetaData,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import as_declarative, declared_attr, relationship

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# pylint: disable=locally-disabled, too-few-public-methods
@as_declarative(metadata=MetaData(naming_convention=convention))
class Base:
    """Базовый класс для моделей."""

    # pylint: disable=locally-disabled, no-member, no-self-argument
    @declared_attr
    def __tablename__(cls) -> str:
        """Конвертирует имя класса в название таблицы.

        :return: название таблицы строчными буквами со словами, разделенными
        нижним подчёркиванием.
        """
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)  # type: ignore
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()

    id = Column(
        BigInteger, Identity(always=True), primary_key=True, index=True
    )


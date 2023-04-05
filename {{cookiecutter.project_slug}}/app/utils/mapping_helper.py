"""
Содержит вспомогательные функции/классы для работы с маппингами
"""
# pylint: disable = too-few-public-methods, invalid-name
import json
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic.utils import GetterDict


class GetterSetterDict(GetterDict):
    """
    Дополняет Pydantic GetterDict методом для присваивания значений
    атрибутам валидируемого класса.
    pydantic GetterDict does not support item assignment
    """

    def __setitem__(self, key, value) -> Any:
        try:
            return setattr(self._obj, key, value)
        except AttributeError as e:
            raise KeyError(key) from e


class AliasDict(dict):
    """Маппинг с поддержкой alias по ключам"""

    def __init__(self, data: dict, aliases: dict | None = None):
        data = remove_none(data)
        super().__init__(data)
        self._aliases = aliases

    def by_alias(self) -> dict:
        """Возвращаем копию себя, заменяя ключи на их alias"""
        if self._aliases is None:
            return self.copy()

        new_data = self.copy()
        for key, alias in self._aliases.items():
            try:
                value = new_data.pop(key)
            except KeyError:
                continue
            new_data[alias] = value
        return new_data


def remove_none(data: Mapping) -> dict:
    """Возвращаем новый dict без None"""
    return {key: value for key, value in data.items() if value is not None}


# pylint: disable=R1710
def first(list_: Sequence | None) -> Any | None:
    """Возвращает первый элемент из списка"""
    if list_ is not None:
        for el in list_:
            return el


def prettify(data: Mapping | Sequence, indent: int = 2) -> str:
    """Отображает вложенные данные с отступами и отсортированные"""
    return json.dumps(data, sort_keys=True, indent=indent, ensure_ascii=False)

"""Модуль, реализует базовые SQL операции над объектами приложения"""
from typing import Generic, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.elements import BinaryExpression

from app.repository.database.models.models import Base
from app.utils.call_counter import CALL_COUNTER_IN_REQUEST

ModelType = TypeVar("ModelType", bound=Base)  # pylint: disable = invalid-name
CreateSchemaType = TypeVar(  # pylint: disable = invalid-name
    "CreateSchemaType", bound=BaseModel
)
UpdateSchemaType = TypeVar(  # pylint: disable = invalid-name
    "UpdateSchemaType", bound=BaseModel
)


def is_pydantic(obj: object):
    """Проверяет является ли obj экзэмпляром модели pydantic."""
    return type(obj).__class__.__module__ == "pydantic.main"


def create_nested_db_items(schema_instance: BaseModel) -> dict:
    """
    Итерируется по экзэмпляру pydantic модели и трансформирует вложенные
    модели в SQLAlchemy модели.
    Функция работает, если во вложенных pydantic моделях прописан
    Meta.orm_model.
    """
    model_attributes: dict = dict(schema_instance)
    for key, value in model_attributes.items():
        try:
            if isinstance(value, list) and len(value):
                if is_pydantic(value[0]):
                    model_attributes[key] = [
                        schema.Meta.orm_model(**schema.dict())
                        for schema in value
                    ]
            elif is_pydantic(value):  # pylint: disable=R5601
                model_attributes[key] = value.Meta.orm_model(**value.dict())
        except AttributeError as exc:
            raise AttributeError(
                "Найдена вложенная Pydantic модель, ноатрибут "
                "Meta.orm_model не определен."
            ) from exc
    return model_attributes


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый класс по созданию/чтению/обновлению/удалению сущностей из БД

    Управление сессией вынесено за пределы класса, поэтому для закрытия
    транзакций и ORM объектов необходимо использовать: db_session.close()
    """

    def __init__(self, model: type[ModelType]):
        self._model = model

    async def get(
        self,
        db_session: AsyncSession,
        filter_expr: BinaryExpression,
    ) -> ModelType | None:
        """Возвращает объект по переданным фильтрам"""
        res = await db_session.execute(
            select(self._model).where(filter_expr).limit(1)
        )
        return res.scalars().unique().one_or_none()

    async def get_or_404(
        self,
        db_session: AsyncSession,
        filter_expr: BinaryExpression,
        exception_args: tuple = (404, "Query group not found", None),
    ) -> ModelType | None:
        """Возвращает объект по переданным фильтрам или 404 ошибку в случае его отсутствия"""
        if (db_obj := await self.get(db_session, filter_expr)) is None:
            raise HTTPException(*exception_args)
        return db_obj

    async def get_multi(  # pylint: disable = too-many-arguments
        self,
        db_session: AsyncSession,
        filter_expr: BinaryExpression | None = None,
        offset: int = 0,
        limit: int = 100,
        order: str | None = None,
    ) -> list[ModelType]:
        """Возвращает список объектов по переданным фильтрам"""
        select_st = select(self._model)
        if filter_expr is not None:
            select_st = select_st.where(filter_expr)

        if order is not None:
            select_st = select_st.order_by(order)
        if limit:
            select_st = select_st.offset(offset).limit(limit)

        res = await db_session.execute(select_st.offset(offset))
        return res.scalars().unique().all()

    @CALL_COUNTER_IN_REQUEST
    async def create(
        self,
        db_session: AsyncSession,
        obj_in: CreateSchemaType,
    ) -> ModelType:
        """Делает запись объекта в БД"""

        db_obj = self._model(**create_nested_db_items(obj_in))
        db_session.add(db_obj)
        await db_session.commit()
        await db_session.refresh(db_obj)
        return db_obj

    @CALL_COUNTER_IN_REQUEST
    async def update(
        self,
        db_session: AsyncSession,
        filter_expr: BinaryExpression,
        obj_in: UpdateSchemaType,
        exception_args=(404, "Object of update's been not found", None),
    ) -> ModelType | None:
        """Обновляет объект в БД"""
        await self.get_or_404(
            db_session, filter_expr, exception_args=exception_args
        )
        update_st = (
            update(self._model)
            .where(filter_expr)
            .values(**create_nested_db_items(obj_in))
        )
        await db_session.execute(update_st)
        await db_session.commit()
        return await self.get(db_session, filter_expr)

    @CALL_COUNTER_IN_REQUEST
    async def update_got(
        self,
        db_session: AsyncSession,
        db_entity: ModelType,
        new_data: UpdateSchemaType,
    ) -> ModelType | None:
        """Обновляет объект в БД"""
        values = create_nested_db_items(new_data)
        for field, value in values.items():
            setattr(db_entity, field, value)
        await db_session.commit()
        return db_entity

    @CALL_COUNTER_IN_REQUEST
    async def remove(
        self,
        db_session: AsyncSession,
        filter_expr: BinaryExpression,
        exception_args=(404, "Object of delete's been not found", None),
    ) -> None:
        """Удаляет объект из бд"""
        await self.get_or_404(
            db_session, filter_expr, exception_args=exception_args
        )
        await db_session.execute(delete(self._model).where(filter_expr))
        await db_session.commit()
        return

    async def count(
        self,
        db_session: AsyncSession,
        filter_expr: BinaryExpression | None = None,
    ) -> int:
        """Выводит число объектов по переданным фильтрам"""
        select_st = select(func.count(self._model.id))

        if filter_expr is not None:
            select_st = select_st.where(filter_expr)

        res = await db_session.execute(select_st)
        return res.scalar_one()

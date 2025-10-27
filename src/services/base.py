from collections.abc import Sequence
from typing import Any

import sqlalchemy
from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    InternalError,
    ProgrammingError,
    NoResultFound,
    StatementError,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from typing_extensions import override

from src.database import Base, session_maker
from sqlalchemy import desc, asc, Select, insert, update, select, delete, func

from src.services.exceptions import SqlError, NotFoundError, UniqueRecordError


class BaseService:
    db_model: Base
    db_session: async_sessionmaker[AsyncSession]

    def __init__(self):
        # свой session_maker для каждого сервиса
        self.db_session = session_maker

    @override
    async def create(self, schema: dict) -> dict:
        stmt = insert(self.db_model).values(schema).returning(self.db_model)
        async with self.db_session() as session:
            async with session.begin():
                try:
                    result = (await session.execute(stmt)).scalar_one()
                    await session.commit()
                except (IntegrityError, OperationalError, InternalError, ProgrammingError, StatementError) as error:
                    if isinstance(error.orig.__cause__, UniqueViolationError):
                        raise UniqueRecordError(error)
                    raise SqlError(error)

            return result.to_dict()

    @override
    async def mass_create(self, schemas: list[dict]) -> list[dict]:
        stmt = insert(self.db_model).values(schemas).returning(self.db_model)
        async with self.db_session() as session:
            async with session.begin():
                try:
                    results = (await session.execute(stmt)).scalars().all()
                    await session.commit()
                except (IntegrityError, OperationalError, InternalError, ProgrammingError, StatementError) as error:
                    if isinstance(error.orig.__cause__, UniqueViolationError):
                        raise UniqueRecordError(error)
                    raise SqlError(error)

            return [r.to_dict() for r in results]

    @override
    async def update(self, id_: int, schema: dict) -> dict:
        stmt = (
            update(self.db_model)
            .where(self.db_model.id == id_)
            .values(**schema)
            .returning(self.db_model)
        )
        async with self.db_session() as session:
            async with session.begin():
                try:
                    result = (await session.execute(stmt)).scalar_one()
                    await session.commit()
                except NoResultFound as error:
                    raise NotFoundError(error)
                except (IntegrityError, OperationalError, InternalError, ProgrammingError, StatementError) as error:
                    if isinstance(error.orig.__cause__, UniqueViolationError):
                        raise UniqueRecordError(error)
                    raise SqlError(error)

            return result.to_dict()

    @override
    async def bulk_update(self, schemas: list[dict]) -> list[dict]:
        stmt = update(self.db_model)
        async with self.db_session() as session:
            async with session.begin():
                try:
                    await session.execute(stmt, schemas)
                    await session.commit()
                except NoResultFound as error:
                    raise NotFoundError(error)
                except (IntegrityError, OperationalError, InternalError, ProgrammingError, StatementError) as error:
                    if isinstance(error.orig.__cause__, UniqueViolationError):
                        raise UniqueRecordError(error)
                    raise SqlError(error)

    @override
    async def get(self, id_: int) -> dict:
        query_str = select(self.db_model).where(self.db_model.id == id_)
        async with self.db_session() as session:
            try:
                result = (await session.execute(query_str)).scalar_one()
            except NoResultFound as error:
                raise NotFoundError(error)
            except (IntegrityError, OperationalError, InternalError, ProgrammingError, StatementError) as error:
                raise SqlError(error)

            return result.to_dict()

    @override
    async def get_list(
        self,
        filter_: dict[str, Any] | None = None,
        range_: list[int] | None = None,
        sort: list[str] | None = None
    ) -> dict[str, int | list[dict]]:
        query_str = self._prepare_query_str(select(self.db_model), filter_, range_, sort)
        async with self.db_session() as session:
            try:
                count_query = select(func.count()).select_from(
                    query_str.order_by(None).limit(None).offset(None).options(sqlalchemy.orm.noload("*")).subquery()
                )
                count: int = await session.scalar(count_query)
                results: Sequence = (await session.execute(query_str)).scalars().all()
            except (IntegrityError, OperationalError, InternalError, ProgrammingError, StatementError) as error:
                raise SqlError(error)

            return {'total': count, 'data': [r.to_dict() for r in results]}

    @override
    async def delete(self, id_: int) -> bool:
        stmt = delete(self.db_model).where(self.db_model.id == id_).returning(self.db_model)
        async with self.db_session() as session:
            try:
                result = (await session.execute(stmt)).scalars().all()
                await session.commit()
                if result:
                    return True
            except (IntegrityError, OperationalError, InternalError, ProgrammingError, StatementError) as error:
                raise SqlError(error)

            return False

    def _prepare_query_str(self, query_str: Select, filter_: dict[str, Any] | None = None,
                           range_: list[int] | None = None, sort: list[str] | None = None) -> Select:
        if filter_:
            for field, val in filter_.items():
                match val:
                    case list():
                        if field.startswith("!"):
                            query_str = query_str.where(
                                self.db_model.__getattribute__(self.db_model, field[1:]).not_in(val))
                        else:
                            query_str = query_str.where(self.db_model.__getattribute__(self.db_model, field).in_(val))
                    case int() | float() | None:
                        if field.startswith("!"):
                            query_str = query_str.where(self.db_model.__getattribute__(self.db_model, field[1:]) != val)
                        else:
                            query_str = query_str.where(self.db_model.__getattribute__(self.db_model, field) == val)
                    case str():
                        if field.startswith("!"):
                            query_str = query_str.where(
                                self.db_model.__getattribute__(self.db_model, field[1:]).not_ilike(val))
                        else:
                            query_str = query_str.where(self.db_model.__getattribute__(self.db_model, field).ilike(val))
        if range_:
            if len(range_) == 1:
                query_str = query_str.limit(range_[0])
            elif len(range_) == 2:
                query_str = query_str.limit(range_[0]).offset(range_[1])
        if sort:
            if len(sort) == 1:
                query_str = query_str.order_by(self.db_model.__getattribute__(self.db_model, sort[0]))
            elif len(sort) == 2:
                if isinstance(sort[1], str) and sort[1].lower() == "desc":
                    query_str = query_str.order_by(desc(self.db_model.__getattribute__(self.db_model, sort[0])))
                else:
                    query_str = query_str.order_by(asc(self.db_model.__getattribute__(self.db_model, sort[0])))

        return query_str

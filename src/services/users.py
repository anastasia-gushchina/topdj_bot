import json
import logging
from typing import Any

from redis import Redis
from src.models.users import Users
from src.schemas.users import CreateUserSchema, UpdateUserSchema, MassUpdateUserSchema
from src.services.base import BaseService
from src.schemas.pages_schema import PagesSchema

logger = logging.getLogger()


class UsersService(BaseService):
    db_model = Users

    async def create(self, schema: CreateUserSchema) -> Users:
        logger.info('Creating new user.')

        result: dict[str, Any] = await super().create(schema.model_dump(exclude_none=True))
        logger.info(f"User was created with id: {result.get('id')}.")

        return Users(**result)

    async def check_and_create(self, schema: CreateUserSchema, redis: Redis | None):
        if redis:
            user_key = f"user_{schema.tg_id}"
            has_user = redis.get(user_key)
        else:
            has_user = False
        if has_user:
            logger.info("User already set to redis")
            return
        created_user = await self.get_list(filter_={"tg_id": schema.tg_id})
        if created_user.data:
            logger.info(f"User already created in DB: {created_user}")
            return
        created = await self.create(schema)
        dict_str = json.dumps(created.to_dict(), default=str)
        redis.set(user_key, dict_str)

    async def mass_create(self, schemas: list[CreateUserSchema]) -> list[Users]:
        logger.info(f'Creating new {self.db_model.__tablename__}.')
        results: list[dict[str, Any]] = await super().mass_create([s.model_dump(exclude_none=True) for s in schemas])

        return [Users(**r) for r in results]

    async def update(self, filter_: dict[str, Any], schema: UpdateUserSchema) -> Users:
        logger.info(f'Updating user: {filter_}.')
        result: dict[str, Any] = await super().update(filter_, schema.model_dump(exclude_none=True, exclude_unset=True))

        return Users(**result)

    async def mass_update(self, schema: list[MassUpdateUserSchema]) -> None:
        logger.info(f'Updating user: {[s.id for s in schema]}.')
        await super().mass_update([s.model_dump(exclude_none=True, exclude_unset=True) for s in schema])

    async def get(self, id_: str | int) -> Users:
        logger.info(f'Get user {id_}.')
        data: dict[str, Any] = await super().get(id_)

        return Users(**data)

    async def get_list(
        self,
        filter_: dict[str, Any] | None = None,
        range_: list[int] | None = None,
        sort: list[str] | None = None
    ) -> PagesSchema:
        logger.info(f'Get list {self.db_model.__tablename__}.')
        results: dict[str, int | list[dict[str, Any]]] = await super().get_list(filter_, range_, sort)
        return PagesSchema(**results, type=self.db_model)

    async def delete(self, id_: str | int) -> bool:
        logger.info(f'Deleting user {id_}')
        return await super().delete(id_)

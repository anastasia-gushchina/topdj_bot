import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, IntegrityError, OperationalError, InternalError, ProgrammingError, \
    StatementError

from src.schemas.payments import CreatePaymentsSchema, PaymentsSchema, UpdatePaymentsSchema
from src.models.payments import PaymentsModel

from src.services.base import BaseService
from src.services.exceptions import NotFoundError, SqlError

logger = logging.getLogger("category-cat:service")


class PaymentService(BaseService):
    db_model = PaymentsModel

    async def create(self, schema: CreatePaymentsSchema) -> PaymentsSchema:
        result: dict = await super().create(schema.model_dump(exclude_none=True))
        logger.info(f"Payment was created with id: {result.get('id')}.")
        return PaymentsSchema(**result)

    async def update(self, filter_: dict[str, Any], schema: UpdatePaymentsSchema) -> PaymentsSchema:
        logger.info("Update payment.")
        result: dict[str, Any] = await super().update(filter_, schema.model_dump(exclude_none=True, exclude_unset=True))

        return PaymentsSchema(**result)

    async def get(self, payment_id: int) -> PaymentsSchema:
        logger.info(f"Get payment by payment id {payment_id}.")
        return PaymentsSchema(**await super().get(payment_id))

    async def get_by_user_id(self, user_id: str) -> PaymentsSchema:
        query_str = select(self.db_model).where(PaymentsModel.user_id == user_id)
        async with self.db_session() as session:
            try:
                result = (await session.execute(query_str)).scalars()[-1]
            except NoResultFound as error:
                raise NotFoundError(error)
            except (IntegrityError, OperationalError, InternalError, ProgrammingError, StatementError) as error:
                raise SqlError(error)

            return PaymentsSchema(**result.to_dict())

    async def get_list(
        self,
        filter_: dict[str, Any] | None = None,
        range_: list[int] | None = None,
        sort: list[str] | None = None,
    ) -> PaymentsSchema:
        logger.info("Get payment list.")
        return PaymentsSchema(**await super().get_list(filter_, range_, sort))

    async def delete(self, category_id: int) -> bool:
        logger.info(f"Deleting category with id: {category_id}")
        return await super().delete(category_id)

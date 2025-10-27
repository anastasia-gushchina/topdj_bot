from pydantic import BaseModel
from enum import Enum


class PaymentStatus(Enum):
    payment_started = "started"
    transaction_created = "tr_created"
    transaction_completed = "tr_complet"


class CreatePaymentsSchema(BaseModel):
    user_id: str
    status: str = ""
    transaction_id: str | None = None
    pack_name: str


class UpdatePaymentsSchema(BaseModel):
    user_id: str | None = None
    status: str | None = None
    transaction_id: str | None = None
    pack_name: str | None = None


class PaymentsSchema(CreatePaymentsSchema):
    id: int

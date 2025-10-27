from datetime import datetime
from pydantic import BaseModel, Field


class CreateUserSchema(BaseModel):
    username: str = Field(max_length=32)
    name: str | None = Field(max_length=64, default=None)
    surname: str | None = Field(max_length=64, default=None)
    tg_id: int
    chat_id: int


class UpdateUserSchema(CreateUserSchema):
    username: str | None = Field(max_length=32, default=None)
    tg_id: int | None = None
    chat_id: int | None = None


class MassUpdateUserSchema(UpdateUserSchema):
    id: int


class UserSchema(CreateUserSchema):
    id: int
    created_at: datetime
    updated_at: datetime | None = None


class UserPagesSchema(BaseModel):
    total: int
    data: list[UserSchema]

from src.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, UniqueConstraint, inspect
from datetime import datetime
from sqlalchemy import TIMESTAMP, func


class PaymentsModel(Base):
    __tablename__ = "payments"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "transaction_id",
            name="chat_for_user",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(length=32), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(length=10), nullable=True)
    transaction_id: Mapped[str] = mapped_column(String(length=32), nullable=True)
    pack_name: Mapped[str] = mapped_column(String(length=100), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), onupdate=func.now(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=False, server_default=func.now())

    def to_dict(self) -> dict:
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

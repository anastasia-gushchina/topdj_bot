from src.database import Base
from sqlalchemy import BigInteger, String, inspect
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy import TIMESTAMP, func


class Users(Base):
    __tablename__ = "users"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=True)
    surname: Mapped[str] = mapped_column(String(64), nullable=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), onupdate=func.now(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=False, server_default=func.now())

    def to_dict(self) -> dict:
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

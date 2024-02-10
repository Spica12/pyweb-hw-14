import uuid
from datetime import date

from sqlalchemy import DateTime, ForeignKey, Integer, String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base


class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[date] = mapped_column("created_at", DateTime, default=func.now())
    updated_at: Mapped[date] = mapped_column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now()
    )
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)


class TokenModel(Base):
    __tablename__ = "tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.id"), nullable=True)
    user: Mapped[UserModel] = relationship("UserModel", backref="tokens")
    created_at: Mapped[date] = mapped_column(
        "created_at", DateTime, default=func.now(), nullable=True
    )
    updated_at: Mapped[date] = mapped_column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now(), nullable=True
    )

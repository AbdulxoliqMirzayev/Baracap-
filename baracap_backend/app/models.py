from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        return str(value if isinstance(value, uuid.UUID) else uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None or isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    language: Mapped[str] = mapped_column(String(2), nullable=False, default="uz", server_default="uz")

    financial_profile: Mapped[FinancialProfile | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    goals: Mapped[list[Goal]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    plans: Mapped[list[Plan]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    progress_updates: Mapped[list[ProgressUpdate]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class FinancialProfile(Base, TimestampMixin):
    __tablename__ = "financial_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    monthly_income: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    monthly_expenses: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    current_savings: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="UZS", server_default="UZS")
    has_extra_income: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    extra_income_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extra_income_amount: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False, default=0, server_default="0")
    available_money: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)

    user: Mapped[User] = relationship(back_populates="financial_profile")


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    goal_type: Mapped[str] = mapped_column(String(120), nullable=False)
    custom_goal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="UZS", server_default="UZS")
    target_duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    goal_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_percent: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default="active")

    user: Mapped[User] = relationship(back_populates="goals")
    plans: Mapped[list[Plan]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
    )
    progress_updates: Mapped[list[ProgressUpdate]] = relationship(
        back_populates="goal",
        cascade="all, delete-orphan",
    )


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    goal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("goals.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    monthly_investment: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    annual_return_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=0, server_default="0")
    total_invested: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    estimated_profit: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    final_capital: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    estimated_completion_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selected_money_sources: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")

    user: Mapped[User] = relationship(back_populates="plans")
    goal: Mapped[Goal] = relationship(back_populates="plans")


class ProgressUpdate(Base):
    __tablename__ = "progress_updates"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    goal_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("goals.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    added_amount: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    total_balance_after_update: Mapped[Decimal] = mapped_column(Numeric(24, 2), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="progress_updates")
    goal: Mapped[Goal] = relationship(back_populates="progress_updates")

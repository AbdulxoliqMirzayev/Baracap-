import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PlainSerializer, field_validator


class CurrencyEnum(str, Enum):
    UZS = "UZS"
    USD = "USD"


class LanguageEnum(str, Enum):
    uz = "uz"
    ru = "ru"
    en = "en"


class GoalStatusEnum(str, Enum):
    active = "active"
    archived = "archived"


NonNegativeDecimal = Annotated[Decimal, Field(ge=Decimal("0"))]
PositiveDecimal = Annotated[Decimal, Field(gt=Decimal("0"))]

# Decimal fields in response models are serialized as float in JSON (Pydantic v2 native approach)
SerializedDecimal = Annotated[
    Decimal,
    PlainSerializer(float, return_type=float, when_used="json"),
]


class APIModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class GoogleLoginRequest(APIModel):
    id_token: str = Field(min_length=1)


class DevLoginRequest(APIModel):
    email: EmailStr = "demo@baracap.uz"
    name: str = Field(default="BARACAP Demo User", min_length=1, max_length=255)


class UserOut(APIModel):
    id: uuid.UUID
    name: str | None = None
    email: EmailStr
    avatar_url: str | None = None
    language: LanguageEnum
    created_at: datetime
    updated_at: datetime


class TokenResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserLanguageUpdate(APIModel):
    language: LanguageEnum


class FinancialProfileCreate(APIModel):
    monthly_income: NonNegativeDecimal
    monthly_expenses: NonNegativeDecimal
    current_savings: NonNegativeDecimal
    currency: CurrencyEnum = CurrencyEnum.UZS
    has_extra_income: bool = False
    extra_income_source: str | None = Field(default=None, max_length=255)
    extra_income_amount: NonNegativeDecimal = Decimal("0")

    @field_validator("extra_income_source")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class FinancialProfileOut(APIModel):
    id: uuid.UUID
    user_id: uuid.UUID
    monthly_income: SerializedDecimal
    monthly_expenses: SerializedDecimal
    current_savings: SerializedDecimal
    currency: CurrencyEnum
    has_extra_income: bool
    extra_income_source: str | None = None
    extra_income_amount: SerializedDecimal
    available_money: SerializedDecimal
    created_at: datetime
    updated_at: datetime


class GoalCreate(APIModel):
    goal_type: str = Field(min_length=1, max_length=120)
    custom_goal: str | None = Field(default=None, max_length=255)
    target_amount: PositiveDecimal
    current_balance: NonNegativeDecimal = Decimal("0")
    currency: CurrencyEnum = CurrencyEnum.UZS
    target_duration_months: int = Field(gt=0)
    goal_note: str | None = None

    @field_validator("goal_type")
    @classmethod
    def clean_goal_type(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("goal_type must not be blank")
        return stripped

    @field_validator("custom_goal", "goal_note")
    @classmethod
    def clean_nullable_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class GoalUpdate(APIModel):
    goal_type: str | None = Field(default=None, min_length=1, max_length=120)
    custom_goal: str | None = Field(default=None, max_length=255)
    target_amount: PositiveDecimal | None = None
    current_balance: NonNegativeDecimal | None = None
    currency: CurrencyEnum | None = None
    target_duration_months: int | None = Field(default=None, gt=0)
    goal_note: str | None = None
    status: GoalStatusEnum | None = None

    @field_validator("goal_type", "custom_goal", "goal_note")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class GoalOut(APIModel):
    id: uuid.UUID
    user_id: uuid.UUID
    goal_type: str
    custom_goal: str | None = None
    target_amount: SerializedDecimal
    current_balance: SerializedDecimal
    currency: CurrencyEnum
    target_duration_months: int
    goal_note: str | None = None
    progress_percent: SerializedDecimal
    status: str
    created_at: datetime
    updated_at: datetime


class PlanCreate(APIModel):
    goal_id: uuid.UUID
    monthly_investment: NonNegativeDecimal
    annual_return_percent: NonNegativeDecimal = Decimal("0")
    target_duration_months: int = Field(gt=0)
    selected_money_sources: list[str] = Field(default_factory=list)

    @field_validator("selected_money_sources")
    @classmethod
    def clean_money_sources(cls, value: list[str]) -> list[str]:
        return [source.strip() for source in value if source and source.strip()]


class PlanOut(APIModel):
    id: uuid.UUID
    user_id: uuid.UUID
    goal_id: uuid.UUID
    monthly_investment: SerializedDecimal
    annual_return_percent: SerializedDecimal
    total_invested: SerializedDecimal
    estimated_profit: SerializedDecimal
    final_capital: SerializedDecimal
    estimated_completion_months: int | None = None
    selected_money_sources: list[str]
    created_at: datetime
    updated_at: datetime


class ProgressCreate(APIModel):
    goal_id: uuid.UUID
    added_amount: PositiveDecimal
    note: str | None = None

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ProgressOut(APIModel):
    id: uuid.UUID
    user_id: uuid.UUID
    goal_id: uuid.UUID
    added_amount: SerializedDecimal
    total_balance_after_update: SerializedDecimal
    note: str | None = None
    created_at: datetime


class ProgressWithGoalOut(APIModel):
    goal: GoalOut
    progress_update: ProgressOut


class SyncPlanPayload(APIModel):
    goal_id: uuid.UUID | None = None
    monthly_investment: NonNegativeDecimal
    annual_return_percent: NonNegativeDecimal = Decimal("0")
    target_duration_months: int | None = Field(default=None, gt=0)
    selected_money_sources: list[str] = Field(default_factory=list)

    @field_validator("selected_money_sources")
    @classmethod
    def clean_money_sources(cls, value: list[str]) -> list[str]:
        return [source.strip() for source in value if source and source.strip()]


class SyncProgressPayload(APIModel):
    goal_id: uuid.UUID | None = None
    added_amount: PositiveDecimal
    note: str | None = None

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class SyncLocalPlanRequest(APIModel):
    financial_profile: FinancialProfileCreate | None = None
    goal: GoalCreate | None = None
    plan: SyncPlanPayload | None = None
    progress_history: list[SyncProgressPayload] = Field(default_factory=list)


class SyncLocalPlanResponse(APIModel):
    financial_profile: FinancialProfileOut | None = None
    goal: GoalOut | None = None
    plan: PlanOut | None = None
    progress_history: list[ProgressOut] = Field(default_factory=list)

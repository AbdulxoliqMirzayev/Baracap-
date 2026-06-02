from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import FinancialProfile, User
from app.schemas import FinancialProfileCreate, FinancialProfileOut
from app.utils.calculations import calculate_available_money

router = APIRouter(prefix="/financial-profile", tags=["financial-profile"])


def _normalize_extra_income(payload: FinancialProfileCreate) -> tuple[Decimal, str | None]:
    if not payload.has_extra_income:
        return Decimal("0"), None
    return payload.extra_income_amount, payload.extra_income_source


@router.post("", response_model=FinancialProfileOut)
async def upsert_financial_profile(
    payload: FinancialProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FinancialProfile:
    extra_income_amount, extra_income_source = _normalize_extra_income(payload)
    try:
        available_money = calculate_available_money(
            payload.monthly_income,
            payload.monthly_expenses,
            extra_income_amount,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    values = {
        "monthly_income": payload.monthly_income,
        "monthly_expenses": payload.monthly_expenses,
        "current_savings": payload.current_savings,
        "currency": payload.currency.value,
        "has_extra_income": payload.has_extra_income,
        "extra_income_source": extra_income_source,
        "extra_income_amount": extra_income_amount,
        "available_money": available_money,
    }

    if profile is None:
        profile = FinancialProfile(user_id=current_user.id, **values)
        db.add(profile)
    else:
        for key, value in values.items():
            setattr(profile, key, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("", response_model=FinancialProfileOut)
async def get_financial_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FinancialProfile:
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial profile not found",
        )
    return profile


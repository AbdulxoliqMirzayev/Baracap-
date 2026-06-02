import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import FinancialProfile, Goal, Plan, ProgressUpdate, User
from app.schemas import (
    FinancialProfileCreate,
    FinancialProfileOut,
    GoalCreate,
    GoalOut,
    PlanCreate,
    PlanOut,
    SyncLocalPlanRequest,
    SyncLocalPlanResponse,
)
from app.utils.calculations import (
    calculate_available_money,
    calculate_compound_future_value,
    calculate_estimated_completion_months,
    calculate_progress_percent,
    calculate_total_invested,
    quantize_money,
)

router = APIRouter(tags=["sync"])


async def _get_goal_or_404(db: AsyncSession, user_id: uuid.UUID, goal_id: uuid.UUID) -> Goal:
    result = await db.execute(select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id))
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


def _extra_income_values(payload: FinancialProfileCreate) -> tuple[Decimal, str | None]:
    if not payload.has_extra_income:
        return Decimal("0"), None
    return payload.extra_income_amount, payload.extra_income_source


async def _upsert_financial_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    payload: FinancialProfileCreate,
) -> FinancialProfile:
    extra_income_amount, extra_income_source = _extra_income_values(payload)
    available_money = calculate_available_money(
        payload.monthly_income,
        payload.monthly_expenses,
        extra_income_amount,
    )
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

    result = await db.execute(select(FinancialProfile).where(FinancialProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = FinancialProfile(user_id=user_id, **values)
        db.add(profile)
    else:
        for key, value in values.items():
            setattr(profile, key, value)
    await db.flush()
    return profile


async def _create_goal(
    db: AsyncSession,
    user_id: uuid.UUID,
    payload: GoalCreate,
) -> Goal:
    progress_percent = calculate_progress_percent(payload.current_balance, payload.target_amount)
    await db.execute(
        update(Goal)
        .where(Goal.user_id == user_id, Goal.status == "active")
        .values(status="archived")
    )
    goal = Goal(
        user_id=user_id,
        goal_type=payload.goal_type,
        custom_goal=payload.custom_goal,
        target_amount=payload.target_amount,
        current_balance=payload.current_balance,
        currency=payload.currency.value,
        target_duration_months=payload.target_duration_months,
        goal_note=payload.goal_note,
        progress_percent=progress_percent,
        status="active",
    )
    db.add(goal)
    await db.flush()
    return goal


def _plan_values(goal: Goal, payload: PlanCreate) -> dict[str, Decimal | int | None | list[str]]:
    final_capital = calculate_compound_future_value(
        goal.current_balance,
        payload.monthly_investment,
        payload.annual_return_percent,
        payload.target_duration_months,
    )
    total_invested = calculate_total_invested(
        goal.current_balance,
        payload.monthly_investment,
        payload.target_duration_months,
    )
    return {
        "monthly_investment": payload.monthly_investment,
        "annual_return_percent": payload.annual_return_percent,
        "total_invested": total_invested,
        "estimated_profit": quantize_money(final_capital - total_invested),
        "final_capital": final_capital,
        "estimated_completion_months": calculate_estimated_completion_months(
            goal.current_balance,
            goal.target_amount,
            payload.monthly_investment,
            payload.annual_return_percent,
        ),
        "selected_money_sources": payload.selected_money_sources,
    }


async def _create_plan(
    db: AsyncSession,
    user_id: uuid.UUID,
    goal: Goal,
    payload: PlanCreate,
) -> Plan:
    plan = Plan(
        user_id=user_id,
        goal_id=goal.id,
        **_plan_values(goal, payload),
    )
    db.add(plan)
    await db.flush()
    return plan


async def _create_progress_update(
    db: AsyncSession,
    user_id: uuid.UUID,
    goal: Goal,
    added_amount: Decimal,
    note: str | None,
) -> ProgressUpdate:
    goal.current_balance = quantize_money(goal.current_balance + added_amount)
    goal.progress_percent = calculate_progress_percent(goal.current_balance, goal.target_amount)

    progress_update = ProgressUpdate(
        user_id=user_id,
        goal_id=goal.id,
        added_amount=added_amount,
        total_balance_after_update=goal.current_balance,
        note=note,
    )
    db.add(progress_update)
    await db.flush()
    return progress_update


@router.post("/sync-local-plan", response_model=SyncLocalPlanResponse)
async def sync_local_plan(
    payload: SyncLocalPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SyncLocalPlanResponse:
    saved_profile: FinancialProfile | None = None
    saved_goal: Goal | None = None
    saved_plan: Plan | None = None
    saved_progress: list[ProgressUpdate] = []

    try:
        if payload.financial_profile is not None:
            saved_profile = await _upsert_financial_profile(
                db,
                current_user.id,
                payload.financial_profile,
            )

        if payload.goal is not None:
            saved_goal = await _create_goal(db, current_user.id, payload.goal)

        if payload.plan is not None:
            goal_id = payload.plan.goal_id or (saved_goal.id if saved_goal else None)
            if goal_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Plan goal_id is required when no goal is provided",
                )
            plan_goal = saved_goal if saved_goal and saved_goal.id == goal_id else await _get_goal_or_404(
                db,
                current_user.id,
                goal_id,
            )
            months = payload.plan.target_duration_months or plan_goal.target_duration_months
            plan_payload = PlanCreate(
                goal_id=plan_goal.id,
                monthly_investment=payload.plan.monthly_investment,
                annual_return_percent=payload.plan.annual_return_percent,
                target_duration_months=months,
                selected_money_sources=payload.plan.selected_money_sources,
            )
            saved_plan = await _create_plan(db, current_user.id, plan_goal, plan_payload)
            saved_goal = saved_goal or plan_goal

        for progress_payload in payload.progress_history:
            goal_id = progress_payload.goal_id or (saved_goal.id if saved_goal else None)
            if goal_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Progress goal_id is required when no goal is provided",
                )
            progress_goal = saved_goal if saved_goal and saved_goal.id == goal_id else await _get_goal_or_404(
                db,
                current_user.id,
                goal_id,
            )
            saved_progress.append(
                await _create_progress_update(
                    db,
                    current_user.id,
                    progress_goal,
                    progress_payload.added_amount,
                    progress_payload.note,
                )
            )
            saved_goal = saved_goal or progress_goal

    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except HTTPException:
        await db.rollback()
        raise

    await db.commit()

    if saved_profile is not None:
        await db.refresh(saved_profile)
    if saved_goal is not None:
        await db.refresh(saved_goal)
    if saved_plan is not None:
        await db.refresh(saved_plan)
    for item in saved_progress:
        await db.refresh(item)

    return SyncLocalPlanResponse(
        financial_profile=(
            FinancialProfileOut.model_validate(saved_profile) if saved_profile is not None else None
        ),
        goal=GoalOut.model_validate(saved_goal) if saved_goal is not None else None,
        plan=PlanOut.model_validate(saved_plan) if saved_plan is not None else None,
        progress_history=saved_progress,
    )


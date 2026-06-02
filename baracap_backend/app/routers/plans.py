import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Goal, Plan, User
from app.schemas import PlanCreate, PlanOut
from app.utils.calculations import (
    calculate_compound_future_value,
    calculate_estimated_completion_months,
    calculate_total_invested,
    quantize_money,
)

router = APIRouter(prefix="/plans", tags=["plans"])


async def get_user_goal_or_404(
    db: AsyncSession,
    user_id: uuid.UUID,
    goal_id: uuid.UUID,
) -> Goal:
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


async def get_user_plan_or_404(
    db: AsyncSession,
    user_id: uuid.UUID,
    plan_id: uuid.UUID,
) -> Plan:
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.user_id == user_id)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


def build_plan_values(goal: Goal, payload: PlanCreate) -> dict[str, Decimal | int | None | list[str]]:
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
    estimated_profit = quantize_money(final_capital - total_invested)
    estimated_completion_months = calculate_estimated_completion_months(
        goal.current_balance,
        goal.target_amount,
        payload.monthly_investment,
        payload.annual_return_percent,
    )

    return {
        "monthly_investment": payload.monthly_investment,
        "annual_return_percent": payload.annual_return_percent,
        "total_invested": total_invested,
        "estimated_profit": estimated_profit,
        "final_capital": final_capital,
        "estimated_completion_months": estimated_completion_months,
        "selected_money_sources": payload.selected_money_sources,
    }


@router.post("", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Plan:
    goal = await get_user_goal_or_404(db, current_user.id, payload.goal_id)
    try:
        values = build_plan_values(goal, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    plan = Plan(
        user_id=current_user.id,
        goal_id=goal.id,
        **values,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("", response_model=list[PlanOut])
async def list_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Plan]:
    result = await db.execute(
        select(Plan)
        .where(Plan.user_id == current_user.id)
        .order_by(Plan.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/active", response_model=PlanOut)
async def get_active_plan(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Plan:
    goal_result = await db.execute(
        select(Goal)
        .where(Goal.user_id == current_user.id, Goal.status == "active")
        .order_by(Goal.created_at.desc())
        .limit(1)
    )
    active_goal = goal_result.scalar_one_or_none()
    if active_goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active goal not found")

    plan_result = await db.execute(
        select(Plan)
        .where(Plan.user_id == current_user.id, Plan.goal_id == active_goal.id)
        .order_by(Plan.created_at.desc())
        .limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active plan not found")
    return plan


@router.get("/{plan_id}", response_model=PlanOut)
async def get_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Plan:
    return await get_user_plan_or_404(db, current_user.id, plan_id)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    plan = await get_user_plan_or_404(db, current_user.id, plan_id)
    await db.delete(plan)
    await db.commit()


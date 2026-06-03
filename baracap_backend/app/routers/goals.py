import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Goal, User
from app.schemas import GoalCreate, GoalOut, GoalUpdate
from app.utils.calculations import calculate_progress_percent

router = APIRouter(prefix="/goals", tags=["goals"])


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


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: GoalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Goal:
    try:
        progress_percent = calculate_progress_percent(
            payload.current_balance,
            payload.target_amount,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await db.execute(
        update(Goal)
        .where(Goal.user_id == current_user.id, Goal.status == "active")
        .values(status="archived")
    )

    goal = Goal(
        user_id=current_user.id,
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
    await db.commit()
    await db.refresh(goal)
    return goal


@router.get("", response_model=list[GoalOut])
async def list_goals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Goal]:
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == current_user.id)
        .order_by(Goal.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/active", response_model=GoalOut)
async def get_active_goal(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Goal:
    result = await db.execute(
        select(Goal)
        .where(Goal.user_id == current_user.id, Goal.status == "active")
        .order_by(Goal.created_at.desc())
        .limit(1)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active goal not found")
    return goal


@router.get("/{goal_id}", response_model=GoalOut)
async def get_goal(
    goal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Goal:
    return await get_user_goal_or_404(db, current_user.id, goal_id)


@router.patch("/{goal_id}", response_model=GoalOut)
async def update_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Goal:
    goal = await get_user_goal_or_404(db, current_user.id, goal_id)
    values = payload.model_dump(exclude_unset=True)
    nullable_fields = {"custom_goal", "goal_note"}

    for key, value in values.items():
        if value is None and key not in nullable_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{key} cannot be null",
            )

    requested_status = values.get("status")
    if requested_status is not None and requested_status.value == "active":
        await db.execute(
            update(Goal)
            .where(
                Goal.user_id == current_user.id,
                Goal.id != goal.id,
                Goal.status == "active",
            )
            .values(status="archived")
        )

    for key, value in values.items():
        if key == "currency" and value is not None:
            value = value.value
        if key == "status" and value is not None:
            value = value.value
        setattr(goal, key, value)

    try:
        goal.progress_percent = calculate_progress_percent(
            goal.current_balance,
            goal.target_amount,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await db.commit()
    await db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    goal = await get_user_goal_or_404(db, current_user.id, goal_id)
    await db.delete(goal)
    await db.commit()

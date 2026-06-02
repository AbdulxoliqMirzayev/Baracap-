import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Goal, ProgressUpdate, User
from app.schemas import ProgressCreate, ProgressOut, ProgressWithGoalOut
from app.utils.calculations import calculate_progress_percent, quantize_money

router = APIRouter(prefix="/progress", tags=["progress"])


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


@router.post("", response_model=ProgressWithGoalOut, status_code=status.HTTP_201_CREATED)
async def create_progress_update(
    payload: ProgressCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProgressWithGoalOut:
    goal = await get_user_goal_or_404(db, current_user.id, payload.goal_id)

    try:
        goal.current_balance = quantize_money(goal.current_balance + payload.added_amount)
        goal.progress_percent = calculate_progress_percent(
            goal.current_balance,
            goal.target_amount,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    progress_update = ProgressUpdate(
        user_id=current_user.id,
        goal_id=goal.id,
        added_amount=payload.added_amount,
        total_balance_after_update=goal.current_balance,
        note=payload.note,
    )
    db.add(progress_update)
    await db.commit()
    await db.refresh(goal)
    await db.refresh(progress_update)

    return ProgressWithGoalOut(goal=goal, progress_update=progress_update)


@router.get("/{goal_id}", response_model=list[ProgressOut])
async def get_progress_history(
    goal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProgressUpdate]:
    await get_user_goal_or_404(db, current_user.id, goal_id)
    result = await db.execute(
        select(ProgressUpdate)
        .where(
            ProgressUpdate.user_id == current_user.id,
            ProgressUpdate.goal_id == goal_id,
        )
        .order_by(ProgressUpdate.created_at.desc())
    )
    return list(result.scalars().all())


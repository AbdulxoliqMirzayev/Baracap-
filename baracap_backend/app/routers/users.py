from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import UserLanguageUpdate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_my_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me/language", response_model=UserOut)
async def update_my_language(
    payload: UserLanguageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    current_user.language = payload.language.value
    await db.commit()
    await db.refresh(current_user)
    return current_user


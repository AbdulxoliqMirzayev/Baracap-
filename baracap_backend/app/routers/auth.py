from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.auth import create_access_token, get_current_user, verify_google_id_token
from app.config import settings
from app.database import get_db
from app.models import User
from app.schemas import DevLoginRequest, GoogleLoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/google", response_model=TokenResponse)
async def google_login(
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    google_payload = await run_in_threadpool(verify_google_id_token, payload.id_token)
    email = str(google_payload["email"]).lower()
    name = google_payload.get("name")
    picture = google_payload.get("picture")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=email, name=name, avatar_url=picture)
        db.add(user)
    else:
        user.name = name or user.name
        user.avatar_url = picture or user.avatar_url

    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.post("/dev", response_model=TokenResponse, include_in_schema=False)
async def dev_login(
    payload: DevLoginRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    if not settings.DEV_AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Development login is disabled",
        )

    data = payload or DevLoginRequest()
    email = str(data.email).lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(email=email, name=data.name)
        db.add(user)
    else:
        user.name = data.name or user.name

    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
async def auth_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user

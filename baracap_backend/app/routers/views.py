from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PageViewCounter


router = APIRouter(prefix="/views", tags=["views"])

HOME_PAGE_KEY = "home"


@router.get("")
async def get_page_views(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    return {"views": await current_view_count(db)}


@router.post("")
async def track_page_view(db: AsyncSession = Depends(get_db)) -> dict[str, int]:
    await get_or_create_counter(db)
    await db.execute(
        update(PageViewCounter)
        .where(PageViewCounter.key == HOME_PAGE_KEY)
        .values(count=PageViewCounter.count + 1)
    )
    await db.commit()
    return {"views": await current_view_count(db)}


async def current_view_count(db: AsyncSession) -> int:
    result = await db.execute(
        select(PageViewCounter.count).where(PageViewCounter.key == HOME_PAGE_KEY)
    )
    return int(result.scalar_one_or_none() or 0)


async def get_or_create_counter(db: AsyncSession) -> PageViewCounter:
    result = await db.execute(
        select(PageViewCounter).where(PageViewCounter.key == HOME_PAGE_KEY)
    )
    counter = result.scalar_one_or_none()
    if counter is not None:
        return counter

    counter = PageViewCounter(key=HOME_PAGE_KEY, count=0)
    db.add(counter)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        result = await db.execute(
            select(PageViewCounter).where(PageViewCounter.key == HOME_PAGE_KEY)
        )
        counter = result.scalar_one()
    return counter

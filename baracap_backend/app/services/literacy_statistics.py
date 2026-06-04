from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LiteracyAssessmentSubmission


PASSING_SCORE = 50


@dataclass(frozen=True)
class LiteracySubmissionSnapshot:
    id: UUID
    first_name: str
    last_name: str
    phone: str
    status: str
    score: int
    level: str
    guide_type: str
    language: str
    created_at: datetime


@dataclass(frozen=True)
class LiteracyStatistics:
    total_users: int
    high_score_users: int
    low_score_users: int
    average_score: float
    highest_score: int
    lowest_score: int
    recent_submissions: list[LiteracySubmissionSnapshot]


async def get_literacy_statistics(
    db: AsyncSession,
    *,
    recent_limit: int = 10,
) -> LiteracyStatistics:
    aggregate_result = await db.execute(
        select(
            func.count(LiteracyAssessmentSubmission.id),
            func.coalesce(
                func.sum(
                    case(
                        (LiteracyAssessmentSubmission.score >= PASSING_SCORE, 1),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    case(
                        (LiteracyAssessmentSubmission.score < PASSING_SCORE, 1),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(func.avg(LiteracyAssessmentSubmission.score), 0),
            func.coalesce(func.max(LiteracyAssessmentSubmission.score), 0),
            func.coalesce(func.min(LiteracyAssessmentSubmission.score), 0),
        )
    )
    total, high_score, low_score, average, highest, lowest = aggregate_result.one()

    recent_result = await db.execute(
        select(LiteracyAssessmentSubmission)
        .order_by(desc(LiteracyAssessmentSubmission.created_at))
        .limit(recent_limit)
    )
    recent_submissions = [
        LiteracySubmissionSnapshot(
            id=submission.id,
            first_name=submission.first_name,
            last_name=submission.last_name,
            phone=submission.phone,
            status=submission.status,
            score=submission.score,
            level=submission.level,
            guide_type=submission.guide_type,
            language=submission.language,
            created_at=submission.created_at,
        )
        for submission in recent_result.scalars()
    ]

    return LiteracyStatistics(
        total_users=int(total or 0),
        high_score_users=int(high_score or 0),
        low_score_users=int(low_score or 0),
        average_score=round(float(average or 0), 2),
        highest_score=int(highest or 0),
        lowest_score=int(lowest or 0),
        recent_submissions=recent_submissions,
    )

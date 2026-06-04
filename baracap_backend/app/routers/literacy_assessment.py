from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.database import get_db
from app.models import LiteracyAssessmentSubmission
from app.services.pdf_guides import build_guide_pdf, guide_filename
from app.services.literacy_assessment import (
    answer_breakdown,
    guide_type_for_score,
    level_for_score,
    normalize_language,
    public_questions,
    score_answers,
    validate_answer_payload,
)
from app.services.literacy_statistics import (
    LiteracyStatistics,
    get_literacy_statistics,
)
from app.services.telegram import TelegramNotConfiguredError, send_telegram_message

router = APIRouter(prefix="/literacy-assessment", tags=["literacy-assessment"])


class Participant(BaseModel):
    first_name: str = Field(min_length=2, max_length=80)
    last_name: str = Field(min_length=2, max_length=80)
    phone: str = Field(min_length=7, max_length=24)
    status: str = Field(min_length=2, max_length=40)

    @field_validator("first_name", "last_name", "phone", "status")
    @classmethod
    def clean_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Maydon bo'sh bo'lmasligi kerak")
        return value


class LiteracySubmission(BaseModel):
    participant: Participant
    answers: dict[str, str]
    language: str = "uz"

    @field_validator("language")
    @classmethod
    def clean_language(cls, value: str) -> str:
        return normalize_language(value)


class QuestionBreakdown(BaseModel):
    question_id: str
    question: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    earned_points: int
    max_points: int


class LiteracyResult(BaseModel):
    score: int
    level: str
    guide_type: str
    guide_url: str | None = None
    telegram_sent: bool
    telegram_configured: bool
    breakdown: list[QuestionBreakdown]


class LiteracySubmissionOut(BaseModel):
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


class LiteracyStatisticsOut(BaseModel):
    total_users: int
    high_score_users: int
    low_score_users: int
    average_score: float
    highest_score: int
    lowest_score: int
    recent_submissions: list[LiteracySubmissionOut]


@router.get("/questions")
async def get_questions(language: str = Query(default="uz", pattern="^(uz|ru)$")) -> dict[str, object]:
    return {"questions": public_questions(language)}


@router.post("", response_model=LiteracyResult)
async def submit_literacy_assessment(
    payload: LiteracySubmission,
    db: AsyncSession = Depends(get_db),
) -> LiteracyResult:
    try:
        validate_answer_payload(payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    score = score_answers(payload.answers)
    level = level_for_score(score, payload.language)
    guide_type = guide_type_for_score(score)
    guide_url = f"/api/literacy-assessment/guide/{guide_type}?language={payload.language}"

    submission = LiteracyAssessmentSubmission(
        first_name=payload.participant.first_name,
        last_name=payload.participant.last_name,
        phone=payload.participant.phone,
        status=payload.participant.status,
        score=score,
        level=level,
        guide_type=guide_type,
        language=payload.language,
        answers=dict(payload.answers),
    )
    db.add(submission)
    await db.commit()

    statistics = await get_literacy_statistics(db)
    telegram_sent = False
    telegram_configured = bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)
    if telegram_configured:
        text = build_telegram_text(
            payload.participant,
            score,
            level,
            guide_type,
            payload.language,
            statistics,
        )
        try:
            telegram_sent = await run_in_threadpool(send_telegram_message, text)
        except TelegramNotConfiguredError:
            telegram_configured = False
        except Exception:
            telegram_sent = False

    return LiteracyResult(
        score=score,
        level=level,
        guide_type=guide_type,
        guide_url=guide_url,
        telegram_sent=telegram_sent,
        telegram_configured=telegram_configured,
        breakdown=answer_breakdown(payload.answers, payload.language),
    )


@router.get("/statistics", response_model=LiteracyStatisticsOut)
async def get_statistics(
    token: str = Query(default="", description="Admin statistics token"),
    db: AsyncSession = Depends(get_db),
) -> LiteracyStatisticsOut:
    if not settings.ADMIN_STATS_TOKEN or token != settings.ADMIN_STATS_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    statistics = await get_literacy_statistics(db)
    return statistics_to_response(statistics)


@router.get("/guide/{guide_type}", include_in_schema=False)
async def download_guide(
    guide_type: Literal["simple", "professional"],
    language: str = Query(default="uz", pattern="^(uz|ru)$"),
) -> Response:
    pdf = build_guide_pdf(guide_type, normalize_language(language))
    filename = guide_filename(guide_type)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def build_telegram_text(
    participant: Participant,
    score: int,
    level: str,
    guide_type: str,
    language: str,
    statistics: LiteracyStatistics,
) -> str:
    is_ru = normalize_language(language) == "ru"
    guide_label = "Профессиональное руководство" if guide_type == "professional" and is_ru else (
        "Простое понятное руководство" if is_ru else (
            "Professional qo'llanma" if guide_type == "professional" else "Sodda tushunarli qo'llanma"
        )
    )
    labels = {
        "title": "Тест финансовой грамотности BARACAP" if is_ru else "BARACAP moliyaviy savodxonlik testi",
        "first_name": "Имя" if is_ru else "Ism",
        "last_name": "Фамилия" if is_ru else "Familiya",
        "phone": "Телефон" if is_ru else "Telefon",
        "status": "Статус" if is_ru else "Holati",
        "score": "Балл" if is_ru else "Ball",
        "level": "Уровень" if is_ru else "Daraja",
        "gift": "Подарок" if is_ru else "Sovg'a",
    }
    recent_lines = [
        f"{index}. {escape(item.first_name)} {escape(item.last_name)} - {item.score}/100"
        for index, item in enumerate(statistics.recent_submissions[:5], start=1)
    ]
    if not recent_lines:
        recent_lines = ["Hali natija yo'q"]

    return "\n".join(
        [
            f"<b>{labels['title']}</b>",
            "",
            f"{labels['first_name']}: {escape(participant.first_name)}",
            f"{labels['last_name']}: {escape(participant.last_name)}",
            f"{labels['phone']}: {escape(participant.phone)}",
            f"{labels['status']}: {escape(participant.status)}",
            "",
            f"{labels['score']}: <b>{score}/100</b>",
            f"{labels['level']}: <b>{escape(level)}</b>",
            f"{labels['gift']}: {escape(guide_label)}",
            "",
            "<b>Statistika</b>",
            f"Jami foydalanuvchilar: <b>{statistics.total_users}</b>",
            f"50 va undan yuqori ball: <b>{statistics.high_score_users}</b>",
            f"50 dan past ball: <b>{statistics.low_score_users}</b>",
            f"O'rtacha ball: <b>{statistics.average_score}/100</b>",
            f"Eng yuqori / eng past: <b>{statistics.highest_score}/{statistics.lowest_score}</b>",
            "",
            "<b>Oxirgi natijalar</b>",
            *recent_lines,
        ]
    )


def statistics_to_response(statistics: LiteracyStatistics) -> LiteracyStatisticsOut:
    return LiteracyStatisticsOut(
        total_users=statistics.total_users,
        high_score_users=statistics.high_score_users,
        low_score_users=statistics.low_score_users,
        average_score=statistics.average_score,
        highest_score=statistics.highest_score,
        lowest_score=statistics.lowest_score,
        recent_submissions=[
            LiteracySubmissionOut(
                id=item.id,
                first_name=item.first_name,
                last_name=item.last_name,
                phone=item.phone,
                status=item.status,
                score=item.score,
                level=item.level,
                guide_type=item.guide_type,
                language=item.language,
                created_at=item.created_at,
            )
            for item in statistics.recent_submissions
        ],
    )

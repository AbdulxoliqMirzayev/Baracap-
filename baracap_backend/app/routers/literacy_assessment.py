from __future__ import annotations

from html import escape
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from app.config import settings
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


@router.get("/questions")
async def get_questions(language: str = Query(default="uz", pattern="^(uz|ru)$")) -> dict[str, object]:
    return {"questions": public_questions(language)}


@router.post("", response_model=LiteracyResult)
async def submit_literacy_assessment(payload: LiteracySubmission) -> LiteracyResult:
    try:
        validate_answer_payload(payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    score = score_answers(payload.answers)
    level = level_for_score(score, payload.language)
    guide_type = guide_type_for_score(score)
    guide_url = f"/api/literacy-assessment/guide/{guide_type}?language={payload.language}"

    telegram_sent = False
    telegram_configured = bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)
    if telegram_configured:
        text = build_telegram_text(payload.participant, score, level, guide_type, payload.language)
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
        ]
    )

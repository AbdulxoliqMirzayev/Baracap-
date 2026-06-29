from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import engine
from app.frontend import register_frontend
from app.models import Base
from app.routers import literacy_assessment, views


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.AUTO_CREATE_TABLES:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="BARACAP Backend",
    description="Financial literacy assessment API for Uzbek users.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^(https?://(localhost|127\.0\.0\.1)(:\d+)?|null)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(part) for part in first_error.get("loc", []) if part != "body")
    message = first_error.get("msg", "Invalid request")
    detail = f"{location}: {message}" if location else message
    return JSONResponse(status_code=400, content={"detail": detail})


api_router = APIRouter(prefix="/api")


@api_router.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "BARACAP backend"}


@api_router.get("/config", tags=["frontend"])
async def frontend_config() -> dict[str, str | bool]:
    return {
        "telegram_configured": bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
        "simple_guide_ready": True,
        "professional_guide_ready": True,
        "frontend_url": settings.public_frontend_url,
    }


api_router.include_router(literacy_assessment.router)
api_router.include_router(views.router)

app.include_router(api_router)
register_frontend(app)

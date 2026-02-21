import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import router_api
from app.config import settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.schemas.query import QueryResponse
from app.telemetry.metrics import inc_counter

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("app.exceptions")

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.include_router(router_api)


@app.on_event("startup")
async def record_startup() -> None:
    inc_counter("server_start_total")


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_exception",
        extra={"error_type": type(exc).__name__, "error_message": str(exc)},
    )
    payload = QueryResponse(
        answer="حدث خطأ داخلي. حاول مرة أخرى.",
        steps=[],
        citations=[],
        confidence=0.2,
        category="unknown",
        risk_level="low",
        handoff=True,
        handoff_reason="خطأ داخلي",
        handoff_payload=None,
    )
    return JSONResponse(status_code=500, content=payload.model_dump())

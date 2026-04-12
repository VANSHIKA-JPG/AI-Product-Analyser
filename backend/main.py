"""
FastAPI Application Entry Point — AI Product Analyser Backend.

Run dev:  uvicorn main:app --reload --port 8000
Run prod: gunicorn main:app -c gunicorn.conf.py
Swagger:  http://localhost:8000/docs
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api import routes, auth
from app.api.routes import startup_ml_models
from config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger("main")


# ── Lifespan (startup / shutdown) ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting AI Product Analyser API...")
    await init_db()
    logger.info("✅ Database tables created/verified")
    startup_ml_models()          # Load fake review + sentiment .pkl models
    logger.info("✅ ML models loaded")
    yield
    logger.info("Shutting down...")



# ── FastAPI App ────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered Amazon product analyser: sentiment analysis, "
        "fake review detection, and Gemini AI summaries."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api")
app.include_router(routes.router, prefix="/api")


# ── Root / Health ──────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"message": "AI Product Analyser API", "docs": "/docs"}


@app.get("/api/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
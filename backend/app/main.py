from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy import select

from app.api.admin import admin_router
from app.api.cockpit import cockpit_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.user import User


async def init_db_and_seed() -> None:
    """Create tables (Phase 0 dev convenience — Phase 1+ migrate via Alembic) and seed admin user."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        exists = (
            await db.execute(select(User).where(User.username == settings.DEFAULT_ADMIN_USERNAME))
        ).scalar_one_or_none()
        if not exists:
            db.add(
                User(
                    username=settings.DEFAULT_ADMIN_USERNAME,
                    full_name="Team Lead",
                    role="lead",
                    hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                )
            )
            await db.commit()
            logger.info(f"Seeded default admin user: {settings.DEFAULT_ADMIN_USERNAME}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(f"{settings.APP_NAME} starting…")
    try:
        await init_db_and_seed()
    except Exception as e:
        logger.warning(f"DB init skipped (likely DB unavailable): {e}")
    yield
    logger.info(f"{settings.APP_NAME} stopping…")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(cockpit_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME}

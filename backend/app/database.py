"""Async database connection — supports SQLite (dev) and PostgreSQL (prod)."""

import ssl as ssl_lib
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from config import get_settings

settings = get_settings()

_url = settings.DATABASE_URL
_is_sqlite = _url.startswith("sqlite")
_is_neon = "neon.tech" in _url or "neondb" in _url

# Build engine kwargs based on DB type
if _is_sqlite:
    # SQLite: use NullPool (no connection pooling support)
    _engine_kwargs = {"poolclass": NullPool}
elif _is_neon:
    # Neon PostgreSQL: must pass SSL as connect_args (not as URL param)
    _ssl_ctx = ssl_lib.create_default_context()
    _engine_kwargs = {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
        "connect_args": {"ssl": _ssl_ctx},
    }
else:
    # Local PostgreSQL: no SSL needed
    _engine_kwargs = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
    }

engine = create_async_engine(_url, echo=settings.DEBUG, **_engine_kwargs)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """FastAPI dependency: provides a DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

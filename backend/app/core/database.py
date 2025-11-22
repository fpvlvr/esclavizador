"""
Database configuration and initialization for Tortoise ORM.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import RegisterTortoise

from app.core.config import settings


async def init_db() -> None:
    """
    Initialize database connection.
    Used for standalone scripts and testing.
    """
    await Tortoise.init(config=settings.tortoise_orm_config)
    await Tortoise.generate_schemas()


async def close_db() -> None:
    """Close database connections."""
    await Tortoise.close_connections()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager for database initialization and cleanup.
    This replaces the old startup/shutdown events in FastAPI.
    """
    # Startup: Initialize database
    async with RegisterTortoise(
        app=app,
        config=settings.tortoise_orm_config,
        generate_schemas=False,  # Use Aerich migrations instead
        add_exception_handlers=True,
    ):
        # Application is running
        yield
        # Shutdown: Tortoise will automatically close connections


# Tortoise ORM configuration for Aerich migrations
TORTOISE_ORM = settings.tortoise_orm_config

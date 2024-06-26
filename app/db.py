from contextlib import asynccontextmanager
import logging
from asyncio import sleep
from typing import AsyncGenerator, AsyncIterator

from fastapi import FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.engine.base import Connection
from sqlmodel.ext.asyncio.session import AsyncSession
from alembic import command
from alembic.config import Config

from .config import settings

# Enable pool pre-ping to avoid failing when database container scales to 0
# See https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
engine = create_async_engine(
    settings.DB_URL, connect_args=settings.DB_ARGUMENTS, pool_pre_ping=True, echo=settings.DEBUG
)


SessionLocal = async_sessionmaker(
    autoflush=False, bind=engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as db:
        try:
            yield db
        except Exception:
            logging.debug("Request returned an error: rolling back database changes")
            await db.rollback()
            raise

        try:
            await db.commit()
        except Exception as e:
            logging.error("Error committing database changes", exc_info=e)
            await db.rollback()
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to persist database changes"
            ) from e


@asynccontextmanager
async def run_migrations(_: FastAPI) -> AsyncIterator[None]:
    connection_attempt = 0
    while connection_attempt < 5:
        connection_attempt += 1
        logging.info(f"Attempting connection to database {connection_attempt}")
        try:

            def run(connection: Connection) -> None:
                alembic_cfg = Config("alembic.ini")
                alembic_cfg.attributes["connection"] = connection
                command.upgrade(alembic_cfg, "head")

            logging.info("Running migrations...")
            async with engine.begin() as conn:
                await conn.run_sync(run)
            logging.info("Migrations have been run")
            break
        except ConnectionRefusedError as exc:
            logging.info("Could not connect to database")
            if connection_attempt >= 5:
                logging.error("Max attempts reached, throwing error")
                raise exc
            await sleep(10)
    yield

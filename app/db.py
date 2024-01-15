from contextlib import asynccontextmanager
import logging
from asyncio import sleep
from typing import AsyncGenerator, AsyncIterator, Callable, Awaitable

from fastapi import FastAPI, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.base import Connection
from sqlmodel.ext.asyncio.session import AsyncSession
from alembic import command
from alembic.config import Config

from app.handlers.base_handlers import handle_http_exception
from .config import settings

# Enable pool pre-ping to avoid failing when database container scales to 0
# See https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
engine = create_async_engine(
    settings.DB_URL, connect_args=settings.DB_ARGUMENTS, pool_pre_ping=True
)


SessionLocal = sessionmaker(  # type: ignore
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db(req: Request) -> AsyncGenerator[AsyncSession, None]:
    db: AsyncSession = SessionLocal()
    try:
        req.state.db = db
        yield db
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()


async def commit_db(req: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    response = await call_next(req)
    db: AsyncSession | None = getattr(req.state, "db", None)
    if db is None:
        return response
    try:
        logging.debug("Committing database changes")
        await db.commit()
        return response
    except Exception as e:
        logging.error("Error committing database changes", exc_info=e)
        await db.rollback()
        return handle_http_exception(
            req,
            HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR, "Failed to persist database changes"
            ),
        )


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

import logging

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from .models.util import HealthCheck
from .validators.validator_schema import ValidatorSchema
from .routes.stores import router as stores_router
from .db import get_db

api_router = APIRouter(
    responses={"400": {"model": ValidatorSchema, "description": "Bad Request"}},
)
api_router.include_router(stores_router)


@api_router.get("/health", tags=["Healthcheck"])
async def healthcheck(db: AsyncSession = Depends(get_db)) -> HealthCheck:
    try:
        result = await db.exec(select(1))
        logging.debug("DB healthcheck result: %d", result.one())
        return HealthCheck(message="Alive")
    except Exception as e:
        return HealthCheck(message=f"Database connection error: {e}")

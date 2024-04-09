from decimal import Decimal
import logging

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from .config import settings
from .auth import authenticate
from .validators.error_schema import ErrorSchema
from .models.util import HealthCheck
from .validators.validator_schema import ValidatorSchema
from .routes.responses.auth import UNAUTHORIZED
from .routes.util import get_exception_docs
from .routes.stores import router as stores_router
from .routes.services import router as services_router
from .routes.payments import router as payments_router
from .db import get_db

api_router = APIRouter(
    responses={
        "400": {"model": ValidatorSchema, "description": "Bad Request"},
        "500": {"model": ErrorSchema, "description": "Internal Server Error"},
    },
)

auth_router = APIRouter(
    responses=get_exception_docs(UNAUTHORIZED), dependencies=[Depends(authenticate)]
)
auth_router.include_router(stores_router)
auth_router.include_router(services_router)


@api_router.get("/health", tags=["Healthcheck"])
async def healthcheck(db: AsyncSession = Depends(get_db)) -> HealthCheck:
    try:
        result = await db.exec(select(1))
        logging.debug("DB healthcheck result: %d", result.one())
        return HealthCheck(message="Alive")
    except Exception as e:
        return HealthCheck(message=f"Database connection error: {e}")


@auth_router.get("/fee", tags=["Fee"])
async def get_fee() -> Decimal:
    return settings.FEE_PERCENTAGE


api_router.include_router(auth_router)
api_router.include_router(payments_router)

import logging

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from .auth import authenticate, validate_payments_key
from .validators.error_schema import ErrorSchema
from .models.util import HealthCheck
from .validators.validator_schema import ValidatorSchema
from .routes.responses.auth import UNAUTHORIZED
from .routes.util import get_exception_docs
from .routes.stores import router as stores_router
from .routes.stores_image import router as stores_image_router
from .routes.products import router as products_router
from .routes.products_image import router as products_image_router
from .routes.purchases import (
    router as purchases_router,
    router_payments as purchases_router_payments,
)
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
auth_router.include_router(stores_image_router)
auth_router.include_router(products_router)
auth_router.include_router(products_image_router)
auth_router.include_router(purchases_router)

payments_router = APIRouter(
    responses=get_exception_docs(UNAUTHORIZED), dependencies=[Depends(validate_payments_key)]
)
payments_router.include_router(purchases_router_payments)

api_router.include_router(auth_router)
api_router.include_router(payments_router)


@api_router.get("/health", tags=["Healthcheck"])
async def healthcheck(db: AsyncSession = Depends(get_db)) -> HealthCheck:
    try:
        result = await db.exec(select(1))
        logging.debug("DB healthcheck result: %d", result.one())
        return HealthCheck(message="Alive")
    except Exception as e:
        return HealthCheck(message=f"Database connection error: {e}")

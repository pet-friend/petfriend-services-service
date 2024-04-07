from fastapi import APIRouter

from .services import router as services_router
from .services_image import router as services_image_router
from .appointments import router as appointments_router

router = APIRouter()
router.include_router(services_router)
router.include_router(services_image_router)
router.include_router(appointments_router)

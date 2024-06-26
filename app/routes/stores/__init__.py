from fastapi import APIRouter

from .stores import router as stores_router
from .stores_image import router as stores_image_router
from .products import router as products_router
from .products_image import router as products_image_router
from .purchases import router as purchases_router
from .product_reviews import router as product_reviews_router
from .store_reviews import router as store_reviews_router

router = APIRouter()
router.include_router(stores_router)
router.include_router(stores_image_router)
router.include_router(store_reviews_router)
router.include_router(products_router)
router.include_router(products_image_router)
router.include_router(product_reviews_router)
router.include_router(purchases_router)

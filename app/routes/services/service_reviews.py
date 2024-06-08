from fastapi import APIRouter, Depends, Query, status

from app.auth import get_caller_id
from app.models.services import ServiceReviewRead
from app.models.reviews import ReviewCreate
from app.models.util import Id, SortOrder
from app.routes.responses.reviews import (
    REVIEW_NOT_FOUND_ERROR,
    REVIEW_REQUIREMENTS_NOT_MET_ERROR,
    REVIEW_ALREADY_SUBMITTED_ERROR,
)
from app.serializers.reviews import ReviewList
from app.services.reviews import ReviewSortBy
from app.services.services import ServiceReviewsService
from ..util import get_exception_docs

router = APIRouter(prefix="/services/{service_id}/reviews", tags=["Service reviews"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=get_exception_docs(REVIEW_REQUIREMENTS_NOT_MET_ERROR, REVIEW_ALREADY_SUBMITTED_ERROR),
)
async def create_service_review(
    service_id: Id,
    review: ReviewCreate,
    reviews_service: ServiceReviewsService = Depends(),
    caller_id: Id = Depends(get_caller_id),
) -> ServiceReviewRead:
    return await reviews_service.create_review(review, service_id, caller_id)


@router.get("")
async def get_service_reviews(
    service_id: Id,
    sort_by: ReviewSortBy | None = Query(None),
    sort_order: SortOrder = Query(SortOrder.DESCENDING),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    reviews_service: ServiceReviewsService = Depends(),
) -> ReviewList[ServiceReviewRead]:
    reviews = await reviews_service.get_reviews(
        limit, offset, sort_by, sort_order, service_id=service_id
    )
    count, average = await reviews_service.count_and_average_reviews(service_id=service_id)
    return ReviewList(reviews=reviews, amount=count, average_rating=average)


@router.get("/me", responses=get_exception_docs(REVIEW_NOT_FOUND_ERROR))
async def get_my_service_review(
    service_id: Id,
    reviews_service: ServiceReviewsService = Depends(),
    caller_id: Id = Depends(get_caller_id),
) -> ServiceReviewRead:
    return await reviews_service.get_review_by_id(service_id, caller_id)


@router.get("/{user_id}", responses=get_exception_docs(REVIEW_NOT_FOUND_ERROR))
async def get_user_service_review(
    service_id: Id,
    user_id: Id,
    reviews_service: ServiceReviewsService = Depends(),
) -> ServiceReviewRead:
    return await reviews_service.get_review_by_id(service_id, user_id)


@router.put("/me", responses=get_exception_docs(REVIEW_NOT_FOUND_ERROR))
async def update_my_service_review(
    service_id: Id,
    review: ReviewCreate,
    reviews_service: ServiceReviewsService = Depends(),
    caller_id: Id = Depends(get_caller_id),
) -> ServiceReviewRead:
    return await reviews_service.update_review(review, service_id, caller_id)


@router.delete(
    "/me",
    responses=get_exception_docs(REVIEW_NOT_FOUND_ERROR),
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_my_service_review(
    service_id: Id,
    reviews_service: ServiceReviewsService = Depends(),
    caller_id: Id = Depends(get_caller_id),
) -> None:
    await reviews_service.delete_review(service_id, caller_id)

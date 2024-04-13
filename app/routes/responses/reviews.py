from fastapi import HTTPException, status

from app.exceptions.reviews import ReviewNotFound, ReviewRequirementsNotMet, AlreadyReviewed

REVIEW_NOT_FOUND_ERROR = (
    ReviewNotFound,
    HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Review not found",
    ),
)

REVIEW_REQUIREMENTS_NOT_MET_ERROR = (
    ReviewRequirementsNotMet,
    HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="The user does not meet the requirements to create this review",
    ),
)

REVIEW_ALREADY_SUBMITTED_ERROR = (
    AlreadyReviewed,
    HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="The user has already submitted a review",
    ),
)

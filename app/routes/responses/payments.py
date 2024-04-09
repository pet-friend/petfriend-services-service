from fastapi import HTTPException, status

from app.exceptions.payments import OutsideBusinessRange, CantBuyFromOwnBusiness, CollectorNotReady

OUTSIDE_BUSINESS_RANGE = (
    OutsideBusinessRange,
    HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="This address is too far away from the business",
    ),
)

CANT_BUY_FROM_OWN_BUSINESS = (
    CantBuyFromOwnBusiness,
    HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can't buy from your own business",
    ),
)

COLLECTOR_NOT_READY = (
    CollectorNotReady,
    HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="The business owner has not linked his payment account",
    ),
)

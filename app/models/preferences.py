from decimal import Decimal
from enum import StrEnum
from typing import Literal, Sequence, TypedDict, TypeVar, Generic

from .util import Id


M = TypeVar("M")


class PurchaseTypes(StrEnum):
    STORE_PURCHASE = "P"


class PreferenceItem(TypedDict):
    title: str
    currency_id: Literal["ARS"]
    picture_url: str | None
    description: str
    quantity: int
    unit_price: Decimal


class PreferenceShipment(TypedDict):
    cost: Decimal
    mode: Literal["not_specified"]


class PreferenceData(TypedDict, Generic[M]):
    items: Sequence[PreferenceItem]
    marketplace_fee: Decimal
    shipments: PreferenceShipment
    metadata: M


class BasePaymentData(TypedDict):
    service_reference: Id


# Store purchases


class StorePurchaseMetadata(TypedDict):
    store_id: Id
    purchase_id: Id
    type: Literal[PurchaseTypes.STORE_PURCHASE]


class StorePurchasePaymentData(BasePaymentData):
    preference_data: PreferenceData[StorePurchaseMetadata]
    type: Literal[PurchaseTypes.STORE_PURCHASE]


# ---


PaymentData = StorePurchasePaymentData  # | ... | ...

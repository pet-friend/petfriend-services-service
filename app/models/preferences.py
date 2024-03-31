from decimal import Decimal
from enum import StrEnum
from typing import Literal, Sequence, TypedDict

from .util import Id


class PurchaseTypes(StrEnum):
    STORE_PURCHASE = "S"


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


class PreferenceBase(TypedDict):
    external_reference: Id
    items: Sequence[PreferenceItem]
    marketplace_fee: Decimal
    shipments: PreferenceShipment


# Store purchases


class StorePurchaseMetadata(TypedDict):
    store_id: Id
    purchase_id: Id
    type: Literal[PurchaseTypes.STORE_PURCHASE]


class StorePurchasePreference(PreferenceBase):
    type: Literal[PurchaseTypes.STORE_PURCHASE]
    metadata: StorePurchaseMetadata


# ---

Preference = StorePurchasePreference  # | ... | ...


class PaymentData(TypedDict):
    payment_data: Preference

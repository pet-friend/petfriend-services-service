from decimal import Decimal
from enum import StrEnum
from typing import Literal, Sequence, TypedDict, TypeVar, Generic, NotRequired

from .util import Id


M = TypeVar("M")


class PaymentType(StrEnum):
    STORE_PURCHASE = "P"
    SERVICE_APPOINTMENT = "A"


class PreferenceItem(TypedDict):
    title: str
    currency_id: Literal["ARS"]
    picture_url: NotRequired[str | None]
    description: NotRequired[str]
    quantity: int
    unit_price: Decimal


class PreferenceShipment(TypedDict):
    cost: Decimal
    mode: Literal["not_specified"]


class PreferenceData(TypedDict, Generic[M]):
    items: Sequence[PreferenceItem]
    marketplace_fee: NotRequired[Decimal]
    shipments: NotRequired[PreferenceShipment]
    metadata: M


class BasePaymentData(TypedDict):
    service_reference: Id


# Store purchases


class StorePurchaseMetadata(TypedDict):
    store_id: Id
    purchase_id: Id
    type: Literal[PaymentType.STORE_PURCHASE]


class StorePurchasePaymentData(BasePaymentData):
    preference_data: PreferenceData[StorePurchaseMetadata]
    type: Literal[PaymentType.STORE_PURCHASE]


# Service appointments


class ServiceAppointmentMetadata(TypedDict):
    service_id: Id
    appointment_id: Id
    type: Literal[PaymentType.SERVICE_APPOINTMENT]


class ServiceAppointmentPaymentData(BasePaymentData):
    preference_data: PreferenceData[ServiceAppointmentMetadata]
    type: Literal[PaymentType.SERVICE_APPOINTMENT]


# ---


PaymentData = StorePurchasePaymentData | ServiceAppointmentPaymentData

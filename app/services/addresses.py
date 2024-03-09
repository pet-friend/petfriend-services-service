import httpx

from app.config import settings
from app.models.addresses import AddressCreate, Address
from app.models.util import Coordinates
from app.exceptions.addresses import NonExistentAddress


class AddressesService:
    @staticmethod
    def _get_text_address(address: AddressCreate) -> str:
        return (
            f"{address.street_number} {address.street}, "
            f"{address.city}, {address.region}, {address.country_code.short_name}"
        )

    @staticmethod
    async def get_address_coordinates(address: AddressCreate) -> Coordinates:
        async with httpx.AsyncClient() as client:
            url = httpx.URL(
                settings.GOOGLE_MAPS_URL,
                params={
                    "key": settings.GOOGLE_MAPS_API_KEY,
                    "address": AddressesService._get_text_address(address),
                },
            )
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()

        status = data["status"]
        if status == "ZERO_RESULTS":
            raise NonExistentAddress
        if status != "OK":
            raise RuntimeError(f"Failed to fetch address location ({status})")

        coords = data["results"][0]["geometry"]["location"]
        return Coordinates(latitude=coords["lat"], longitude=coords["lng"])

    @staticmethod
    async def get_address(address: AddressCreate | None) -> Address | None:
        if address is None:
            return None
        coords = await AddressesService.get_address_coordinates(address)
        return Address(**address.model_dump(), **coords.model_dump())

from fastapi import Depends

import httpx
from app.exceptions.services import ServiceNotFound

from app.config import settings
from app.models.util import Id
from app.models.addresses import AddressCreate, Address
from app.repositories.services import ServicesRepository
from app.repositories.addresses import AddressesRepository
from app.exceptions.repository import RecordNotFound
from app.exceptions.addresses import AddressNotFound, AddressAlreadyExists, NonExistentAddress


class AddressesService:
    def __init__(
        self,
        addresses_repo: AddressesRepository = Depends(AddressesRepository),
        services_repo: ServicesRepository = Depends(ServicesRepository),
    ):
        self.addresses_repo = addresses_repo
        self.services_repo = services_repo

    def _get_text_address(self, address: AddressCreate) -> str:
        return (
            f"{address.street_number} {address.street}, "
            f"{address.city}, {address.region}, {address.country_code.short_name}"
        )

    async def get_address_coordinates(self, address: AddressCreate) -> tuple[float, float]:
        async with httpx.AsyncClient() as client:
            url = httpx.URL(
                settings.GOOGLE_MAPS_URL,
                params={
                    "key": settings.GOOGLE_MAPS_API_KEY,
                    "address": self._get_text_address(address),
                },
            )
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()

            status = data["status"]
            if status == "ZERO_RESULTS":
                raise NonExistentAddress
            elif status != "OK":
                raise Exception(f"Failed to fetch address location ({status})")

            coords = data["results"][0]["geometry"]["location"]
            return (coords["lat"], coords["lng"])

    async def create_address(self, service_id: Id, data: AddressCreate) -> Address:
        if await self.services_repo.get_by_id(service_id) is None:
            raise ServiceNotFound
        if await self.addresses_repo.get_by_id(service_id) is not None:
            raise AddressAlreadyExists
        lat, long = await self.get_address_coordinates(data)
        address = Address(id=service_id, latitude=lat, longitude=long, **data.model_dump())
        return await self.addresses_repo.save(address)

    async def get_address(self, service_id: Id) -> Address:
        address = await self.addresses_repo.get_by_id(service_id)
        if address is None:
            raise AddressNotFound
        return address

    async def update_address(self, service_id: Id, data: AddressCreate) -> Address:
        lat, long = await self.get_address_coordinates(data)
        try:
            return await self.addresses_repo.update(
                service_id, {"latitude": lat, "longitude": long, **data.model_dump()}
            )
        except RecordNotFound as e:
            raise AddressNotFound from e

    async def delete_address(self, service_id: Id) -> None:
        try:
            await self.addresses_repo.delete(service_id)
        except RecordNotFound as e:
            raise AddressNotFound from e

from fastapi import Depends

from app.models.util import Id
from app.models.addresses import AddressCreate, Address
from app.repositories.addresses import AddressesRepository
from app.exceptions.addresses import AddressNotFound, AddressAlreadyExists


class AddressesService:
    def __init__(
        self,
        addresses_repo: AddressesRepository = Depends(AddressesRepository),
    ):
        self.addresses_repo = addresses_repo

    async def create_address(self, service_id: Id, data: AddressCreate) -> Address:
        # TODO: check if service_id exists
        if await self.addresses_repo.get_by_id(service_id) is not None:
            raise AddressAlreadyExists
        address = Address(id=service_id, **data.model_dump())
        return await self.addresses_repo.save(address)

    async def get_address(self, service_id: Id) -> Address:
        address = await self.addresses_repo.get_by_id(service_id)
        if address is None:
            raise AddressNotFound
        return address

from asyncio import gather
from typing import Sequence, Any

from fastapi import Depends

from app.exceptions.services import ServiceNotFound
from app.exceptions.users import Forbidden
from app.models.services import ServiceCreate, Service, ServiceRead, AppointmentSlots
from app.models.util import Id
from app.repositories.services import ServicesRepository
from ..users import UsersService
from ..addresses import AddressesService

# from ..files import FilesService, services_images_service


class ServicesService:
    def __init__(
        self,
        services_repo: ServicesRepository = Depends(ServicesRepository),
        # files_service: FilesService = Depends(services_images_service),
        users_service: UsersService = Depends(UsersService),
    ):
        self.services_repo = services_repo
        # self.files_service = files_service
        self.users_service = users_service

    async def create_service(self, data: ServiceCreate, owner_id: Id) -> Service:
        address = await AddressesService.get_address(data.address)
        service = Service(
            **data.model_dump(exclude={"address", "appointment_slots"}),
            owner_id=owner_id,
            address=address,
            appointment_slots=[
                AppointmentSlots(**slot.model_dump()) for slot in data.appointment_slots
            ],
        )
        return await self.services_repo.save(service)

    async def get_services(self, limit: int, skip: int, **filters: Any) -> Sequence[Service]:
        services = await self.services_repo.get_all(skip=skip, limit=limit, **filters)
        return services

    async def get_nearby_services(
        self, user_token: str, limit: int, skip: int, user_id: Id, user_address_id: Id
    ) -> tuple[Sequence[Service], int]:
        """
        Returns a tuple of services and the total amount of services nearby
        """
        c = await self.users_service.get_user_address_coordinates(
            user_id, user_address_id, user_token
        )
        services = await self.services_repo.get_nearby(
            c.latitude, c.longitude, skip=skip, limit=limit
        )
        amount = await self.services_repo.count_nearby(c.latitude, c.longitude)
        return services, amount

    async def count_services(self, **filters: Any) -> int:
        services_count = await self.services_repo.count_all(**filters)
        return services_count

    async def get_service_by_id(self, service_id: Id | str) -> Service:
        service = await self.services_repo.get_by_id(service_id)
        if service is None:
            raise ServiceNotFound
        return service

    async def get_services_read(self, services: Sequence[Service]) -> Sequence[ServiceRead]:
        # token = self.files_service.get_token()
        # return await gather(*(self.__readable(service, token) for service in services))
        return await gather(*(self.__readable(service) for service in services))

    async def update_service(self, service_id: Id, data: ServiceCreate, user_id: Id) -> Service:
        service = await self.get_service_by_id(service_id)
        if service.owner_id != user_id:
            raise Forbidden

        address = await AddressesService.get_address(data.address)
        return await self.services_repo.update(
            service_id, {**data.model_dump(), "address": address}
        )

    async def delete_service(self, service_id: Id, user_id: Id) -> None:
        service = await self.get_service_by_id(service_id)
        if service.owner_id != user_id:
            raise Forbidden

        # try:
        #     await self.files_service.delete_file(service_id)  # delete image if exists
        # except FileNotFoundError:
        #     pass
        await self.services_repo.delete(service_id)

    # async def create_service_image(self, service_id: Id, image: File, user_id: Id) -> str:
    #     service = await self.get_service_by_id(service_id)
    #     if service.owner_id != user_id:
    #         raise Forbidden

    #     return await self.files_service.create_file(service_id, image)

    # async def set_service_image(self, service_id: Id, image: File, user_id: Id) -> str:
    #     service = await self.get_service_by_id(service_id)
    #     if service.owner_id != user_id:
    #         raise Forbidden

    #     return await self.files_service.set_file(service_id, image)

    # async def delete_service_image(self, service_id: Id, user_id: Id) -> None:
    #     service = await self.get_service_by_id(service_id)
    #     if service.owner_id != user_id:
    #         raise Forbidden

    #     await self.files_service.delete_file(service_id)

    async def __readable(
        self,
        service: Service,
        # token: str
    ) -> ServiceRead:
        # image = await self.files_service.get_file_url(service.id, token)
        return ServiceRead(
            **service.model_dump(),
            address=service.address,
            appointment_slots=service.appointment_slots,
            # image_url=image
        )

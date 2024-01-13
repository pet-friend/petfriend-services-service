from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Self, Type
from azure.storage.blob.aio import ContainerClient
from azure.storage.blob import generate_container_sas
from azure.core.exceptions import ResourceExistsError

from app.models.util import Id, File
from app.config import settings

TOKEN_EXPIRY = timedelta(hours=24)


class FilesService:
    container: ContainerClient

    def __init__(self, container_client: ContainerClient) -> None:
        self.container = container_client

    @classmethod
    async def from_container_name(
        cls: Type[Self], container_name: str
    ) -> AsyncGenerator[Self, None]:
        async with ContainerClient.from_connection_string(
            settings.STORAGE_CONNECTION_STRING, container_name
        ) as container:
            yield cls(container)

    async def create_file(self, file_id: str | Id, file: File) -> None:
        try:
            await self.container.upload_blob(str(file_id), file.file, overwrite=False)
        except ResourceExistsError as e:
            raise FileExistsError() from e

    async def set_file(self, file_id: str | Id, file: File) -> None:
        await self.container.upload_blob(str(file_id), file.file, overwrite=True)

    async def delete_file(self, file_id: str | Id) -> None:
        async with self.container.get_blob_client(str(file_id)) as blob:
            if not await blob.exists():
                raise FileNotFoundError()
            await blob.delete_blob()

    async def file_exists(self, file_id: str | Id) -> bool:
        async with self.container.get_blob_client(str(file_id)) as blob:
            return await blob.exists()

    async def get_file_url(self, file_id: str | Id, token: str | None = None) -> str | None:
        async with self.container.get_blob_client(str(file_id)) as blob:
            if not await blob.exists():
                return None

            if not token:
                token = self.get_token()
            return f"{blob.url}?{token}"

    def get_token(self) -> str:
        start_time = datetime.now(timezone.utc)
        expiry_time = start_time + TOKEN_EXPIRY
        return generate_container_sas(
            self.container.account_name,
            self.container.container_name,
            self.container.credential.account_key,
            start=start_time,
            expiry=expiry_time,
            permission="r",
        )


async def products_images_service() -> AsyncGenerator[FilesService, None]:
    async with ContainerClient.from_connection_string(
        settings.STORAGE_CONNECTION_STRING, settings.PRODUCTS_IMAGES_CONTAINER
    ) as container:
        yield FilesService(container)


async def stores_images_service() -> AsyncGenerator["FilesService", None]:
    async with ContainerClient.from_connection_string(
        settings.STORAGE_CONNECTION_STRING, settings.STORES_IMAGES_CONTAINER
    ) as container:
        yield FilesService(container)

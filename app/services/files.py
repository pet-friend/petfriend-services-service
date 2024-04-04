from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Callable

from azure.storage.blob.aio import ContainerClient, BlobClient
from azure.storage.blob import generate_container_sas
from azure.core.exceptions import ResourceExistsError

from app.models.util import Id, File
from app.config import settings

TOKEN_EXPIRY = timedelta(hours=24)


class FilesService:
    container: ContainerClient

    def __init__(self, container_client: ContainerClient) -> None:
        self.container = container_client

    async def create_file(self, file_id: Id | str, file: File) -> str:
        return await self.__set_blob(file_id, file, overwrite=False)

    async def set_file(self, file_id: Id | str, file: File) -> str:
        return await self.__set_blob(file_id, file, overwrite=True)

    async def delete_file(self, file_id: Id | str) -> None:
        async with self.container.get_blob_client(str(file_id)) as blob:
            if not await blob.exists():
                raise FileNotFoundError()
            await blob.delete_blob()

    async def file_exists(self, file_id: Id | str) -> bool:
        async with self.container.get_blob_client(str(file_id)) as blob:
            return await blob.exists()

    async def get_file_url(self, file_id: Id | str, token: str | None = None) -> str | None:
        async with self.container.get_blob_client(str(file_id)) as blob:
            if not await blob.exists():
                return None
            return self.__full_url(blob, token)

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

    async def __set_blob(self, file_id: Id | str, file: File, overwrite: bool = False) -> str:
        try:
            async with await self.container.upload_blob(
                str(file_id), file.file, overwrite=overwrite
            ) as b:
                return self.__full_url(b)
        except ResourceExistsError as e:
            raise FileExistsError() from e

    def __full_url(self, blob: BlobClient, token: str | None = None) -> str:
        if not token:
            token = self.get_token()
        return f"{blob.url}?{token}"

    @staticmethod
    def generator(
        container_name: str,
    ) -> Callable[[], AsyncGenerator["FilesService", None]]:
        async def get_service() -> AsyncGenerator[FilesService, None]:
            async with ContainerClient.from_connection_string(
                settings.STORAGE_CONNECTION_STRING, container_name
            ) as container:
                yield FilesService(container)

        return get_service


products_images_service = FilesService.generator(settings.PRODUCTS_IMAGES_CONTAINER)
stores_images_service = FilesService.generator(settings.STORES_IMAGES_CONTAINER)
services_images_service = FilesService.generator(settings.SERVICES_IMAGES_CONTAINER)

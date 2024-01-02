# mypy: disable-error-code="method-assign"
from unittest.mock import AsyncMock
from unittest import IsolatedAsyncioTestCase
from uuid import uuid4

from azure.storage.blob.aio import ContainerClient, BlobClient
from azure.core.exceptions import ResourceExistsError
import pytest

from app.services.files import FilesService
from .util import File


class TestUsersService(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.blob_client = AsyncMock(spec=BlobClient)
        self.container = AsyncMock(spec=ContainerClient)
        self.service = FilesService(self.container)
        self.file = File(open("tests/assets/test_image.jpg", "rb"))

    def tearDown(self) -> None:
        self.file.file.close()

    @pytest.mark.asyncio
    async def test_create_file_calls_upload_blob(self) -> None:
        # Given
        file_id = uuid4()

        # When
        await self.service.create_file(file_id, self.file)

        # Then
        self.container.upload_blob.assert_called_once_with(
            str(file_id), self.file.file, overwrite=False
        )

    @pytest.mark.asyncio
    async def test_set_file_calls_upload_blob(self) -> None:
        # Given
        file_id = uuid4()

        # When
        await self.service.set_file(file_id, self.file)

        # Then
        self.container.upload_blob.assert_called_once_with(
            str(file_id), self.file.file, overwrite=True
        )

    @pytest.mark.asyncio
    async def test_delete_file_calls_delete_blob(self) -> None:
        # Given
        file_id = uuid4()
        blob = AsyncMock(spec=BlobClient)
        blob.exists.return_value = True
        self.container.get_blob_client.return_value.__aenter__.return_value = blob

        # When
        await self.service.delete_file(file_id)

        # Then
        self.container.get_blob_client.assert_called_once_with(str(file_id))
        blob.delete_blob.assert_called_once_with()
        blob.exists.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_delete_file_not_exists_raises_exception(self) -> None:
        # Given
        file_id = uuid4()
        blob = AsyncMock(spec=BlobClient)
        blob.exists.return_value = False
        self.container.get_blob_client.return_value.__aenter__.return_value = blob

        # When, Then
        with self.assertRaises(FileNotFoundError):
            await self.service.delete_file(file_id)

        # Then
        self.container.get_blob_client.assert_called_once_with(str(file_id))
        blob.exists.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_get_file_url_with_given_token(self) -> None:
        # Given
        file_id = uuid4()
        blob_url = "blob"
        token = "test_token"

        blob = AsyncMock(spec=BlobClient)
        blob.exists.return_value = True
        blob.url = blob_url
        self.container.get_blob_client.return_value.__aenter__.return_value = blob

        # When
        url = await self.service.get_file_url(file_id, token=token)

        # Then
        self.container.get_blob_client.assert_called_once_with(str(file_id))
        assert url == f"{blob_url}?{token}"
        blob.exists.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_get_file_url_blob_does_not_exist_is_none(self) -> None:
        # Given
        file_id = uuid4()

        blob = AsyncMock(spec=BlobClient)
        blob.exists.return_value = False
        self.container.get_blob_client.return_value.__aenter__.return_value = blob

        # When
        url = await self.service.get_file_url(file_id)

        # Then
        self.container.get_blob_client.assert_called_once_with(str(file_id))
        assert url is None
        blob.exists.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_create_file_already_exists_raises_exception(self) -> None:
        # Given
        file_id = uuid4()
        self.container.upload_blob.side_effect = ResourceExistsError("")

        # When, Then
        with self.assertRaises(FileExistsError):
            await self.service.create_file(file_id, self.file)

        # Then
        self.container.upload_blob.assert_called_once_with(
            str(file_id), self.file.file, overwrite=False
        )

    @pytest.mark.asyncio
    async def test_file_exists_calls_method(self) -> None:
        # Given
        file_id = uuid4()

        blob = AsyncMock(spec=BlobClient)
        blob.exists.return_value = False
        self.container.get_blob_client.return_value.__aenter__.return_value = blob

        # When
        exists = await self.service.file_exists(file_id)

        # Then
        self.container.get_blob_client.assert_called_once_with(str(file_id))
        assert not exists
        blob.exists.assert_called_once_with()

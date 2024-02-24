import os
from typing import Generator

import pytest
from testcontainers.azurite import AzuriteContainer  # type: ignore
from azure.storage.blob import BlobServiceClient

os.environ["ENVIRONMENT"] = "TESTING"

azurite = AzuriteContainer(ports_to_expose=[AzuriteContainer._BLOB_SERVICE_PORT])
azurite.with_command("azurite-blob --blobHost 0.0.0.0 --inMemoryPersistence")
azurite.start()
connection_string = azurite.get_connection_string()
os.environ["STORAGE_CONNECTION_STRING"] = connection_string
os.environ["STORES_IMAGES_CONTAINER"] = "stores"
os.environ["PRODUCTS_IMAGES_CONTAINER"] = "products"


@pytest.fixture(scope="session", autouse=True)
def blob_global_setup() -> Generator[None, None, None]:
    yield
    azurite.stop()


@pytest.fixture(scope="function", autouse=True)
def blob_setup() -> Generator[None, None, None]:
    client = BlobServiceClient.from_connection_string(connection_string)
    stores_client = client.create_container("stores")
    products_client = client.create_container("products")
    yield
    stores_client.delete_container()
    products_client.delete_container()


@pytest.fixture
def non_mocked_hosts() -> list[str]:
    return ["test", "localhost"]

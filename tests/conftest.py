import os
from typing import Generator

import pytest
from testcontainers.azurite import AzuriteContainer  # type: ignore
from azure.storage.blob import BlobServiceClient

os.environ["ENVIRONMENT"] = "TESTING"

IMAGES_CONTAINERS = ["stores", "products", "services"]

azurite = AzuriteContainer(ports_to_expose=[AzuriteContainer._BLOB_SERVICE_PORT])
azurite.with_command("azurite-blob --blobHost 0.0.0.0 --inMemoryPersistence")
azurite.start()
connection_string = azurite.get_connection_string()
os.environ["STORAGE_CONNECTION_STRING"] = connection_string
os.environ.update(
    {f"{container.upper()}_IMAGES_CONTAINER": container for container in IMAGES_CONTAINERS}
)


@pytest.fixture(scope="session", autouse=True)
def blob_global_setup() -> Generator[None, None, None]:
    yield
    azurite.stop()


@pytest.fixture(scope="function", autouse=True)
def blob_setup() -> Generator[None, None, None]:
    client = BlobServiceClient.from_connection_string(connection_string)
    containers = [client.create_container(container) for container in IMAGES_CONTAINERS]
    yield
    for container in containers:
        container.delete_container()


@pytest.fixture
def non_mocked_hosts() -> list[str]:
    return ["test", "localhost"]

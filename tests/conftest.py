import os
from typing import Generator, TYPE_CHECKING
import importlib

import pytest
from testcontainers.azurite import AzuriteContainer  # type: ignore
from azure.storage.blob import BlobServiceClient

if TYPE_CHECKING:
    from app.config import TestingSettings

IMAGES_CONTAINERS = ["stores", "products", "services"]

os.environ["ENVIRONMENT"] = "TESTING"
os.environ["STORAGE_CONNECTION_STRING"] = ""
for container in IMAGES_CONTAINERS:
    os.environ[f"{container.upper()}_IMAGES_CONTAINER"] = container


@pytest.fixture(scope="session", autouse=True)
def blob_global_setup() -> Generator[str, None, None]:
    azurite = AzuriteContainer(ports_to_expose=[AzuriteContainer._BLOB_SERVICE_PORT])
    # Make sure it uses in memory persistence:
    azurite.with_command("azurite-blob --blobHost 0.0.0.0 --inMemoryPersistence")
    azurite.start()
    connection_string = azurite.get_connection_string()

    # Import settings after setting the env vars above and add the connection string
    settings: "TestingSettings" = importlib.import_module("app.config").settings
    settings.STORAGE_CONNECTION_STRING = connection_string
    try:
        yield connection_string
    finally:
        azurite.stop(force=True)


@pytest.fixture(scope="function", autouse=True)
def blob_setup(blob_global_setup: str) -> Generator[None, None, None]:
    client = BlobServiceClient.from_connection_string(blob_global_setup)
    containers = [client.create_container(container) for container in IMAGES_CONTAINERS]
    try:
        yield
    finally:
        for container in containers:
            container.delete_container()
            container.close()


@pytest.fixture
def non_mocked_hosts() -> list[str]:
    return ["test", "localhost"]

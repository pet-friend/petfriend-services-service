import os
from typing import Type

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Services API"
    DB_URL: str = Field(validation_alias="DATABASE_URL")
    USERS_SERVICE_URL: str = Field(validation_alias="USERS_SERVICE_URL")
    DB_FORCE_ROLLBACK: bool = False
    DB_ARGUMENTS: dict[str, str | bool] = {}
    DEBUG: bool = False
    TESTING: bool = False

    # Images containers settings
    STORAGE_CONNECTION_STRING: str
    PRODUCTS_IMAGES_CONTAINER: str
    STORES_IMAGES_CONTAINER: str


class ProductionSettings(Settings):
    pass


class StagingSettings(Settings):
    DEVELOPMENT: bool = True
    DEBUG: bool = True


class DevelopmentSettings(Settings):
    DEVELOPMENT: bool = True
    DEBUG: bool = True


class TestingSettings(Settings):
    TESTING: bool = True
    DB_URL: str = "sqlite+aiosqlite:///:memory:"
    DB_FORCE_ROLLBACK: bool = True
    DB_ARGUMENTS: dict[str, str | bool] = {"check_same_thread": False}
    USERS_SERVICE_URL: str = "http://service_url"

    __test__ = False  # Prevent pytest from discovering this class as a test class


config_environments: dict[str, Type[Settings]] = {
    "PRODUCTION": ProductionSettings,
    "DEVELOPMENT": DevelopmentSettings,
    "TESTING": TestingSettings,
    "STAGING": StagingSettings,
}

settings = config_environments[os.environ["ENVIRONMENT"]]()

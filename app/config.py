from decimal import Decimal
import os
from typing import Type

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Services API"
    DB_URL: str = Field(validation_alias="DATABASE_URL")
    USERS_SERVICE_URL: str
    PAYMENTS_SERVICE_URL: str
    PAYMENTS_API_KEY: str
    FEE_PERCENTAGE: Decimal = Field(
        ge=0, le=100, default=Decimal(3), max_digits=5, decimal_places=3
    )

    GOOGLE_MAPS_URL: str = "https://maps.googleapis.com/maps/api/geocode/json"
    GOOGLE_MAPS_API_KEY: str

    DB_FORCE_ROLLBACK: bool = False
    DB_ARGUMENTS: dict[str, str | bool] = {}
    DEBUG: bool = False
    TESTING: bool = False

    # Images containers settings
    STORAGE_CONNECTION_STRING: str
    PRODUCTS_IMAGES_CONTAINER: str
    STORES_IMAGES_CONTAINER: str
    SERVICES_IMAGES_CONTAINER: str


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
    USERS_SERVICE_URL: str = "http://users_service_url"
    PAYMENTS_SERVICE_URL: str = "http://payments_service_url"
    PAYMENTS_API_KEY: str = "API_KEY"
    GOOGLE_MAPS_URL: str = "https://map_url"
    GOOGLE_MAPS_API_KEY: str = "API_KEY"

    __test__ = False  # Prevent pytest from discovering this class as a test class


config_environments: dict[str, Type[Settings]] = {
    "PRODUCTION": ProductionSettings,
    "DEVELOPMENT": DevelopmentSettings,
    "TESTING": TestingSettings,
    "STAGING": StagingSettings,
}

settings = config_environments[os.environ["ENVIRONMENT"]]()

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Services API"
    DB_URL: str = os.environ["DATABASE_URL"]
    DB_FORCE_ROLLBACK: bool = False
    DB_ARGUMENTS: dict[str, str | bool] = {}
    DEBUG: bool = False
    TESTING: bool = False


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

    __test__ = False  # Prevent pytest from discovering this class as a test class


config_environments = {
    "PRODUCTION": ProductionSettings,
    "DEVELOPMENT": DevelopmentSettings,
    "TESTING": TestingSettings,
    "STAGING": StagingSettings,
}


@lru_cache()
def get_settings() -> Settings:
    return config_environments[os.environ["ENVIRONMENT"]]()


settings = get_settings()

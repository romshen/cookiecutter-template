"""
Подтягивает и валидирует с переменные окружения.

"""
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import (
    BaseSettings,
    FilePath,
    PostgresDsn,
    RedisDsn,
    constr,
    validator,
)

# pylint: disable=no-self-argument, consider-using-f-string

APP_DIR = Path(__file__).resolve(strict=True).parent.parent


class Environment(Enum):
    """Где запущен сервис"""

    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


class EnvironmentSettings(BaseSettings):
    """
    Настройки в части окружения и локации файла с переменными окружения.

    Для безопасности по умолчанию используются настройки для prod.
    """

    environment: Environment = Environment.PROD

    class Config:
        """Класс-конфигуратор модели. Подтягивает переменные из файла,
        указанного в поле env_file.
        """

        env_file = f"{APP_DIR}/config/.env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


# pylint: disable=locally-disabled, too-few-public-methods, no-self-argument
class CommonSettings(EnvironmentSettings):
    """Настройки, общие для всех окружений."""

    # DEBUG
    debug: bool = False

    # SESSION
    proxy: str | None = None
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/96.0.4664.45 Safari/537.36"
    )

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_reload: bool = False
    title: str = "name"
    openapi_url: str = "/api/openapi.json"
    version: str = "1"

    # Database engine
    DB_DIALECT: str = ""
    DB_API: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_PORT: str = "5432"
    DB_NAME: str = "test"
    db_future: bool = True
    db_pool_recycle: int = 30 * 60
    db_echo: bool = True

   session_settings: dict[str, Any] = {}

    @validator("session_settings", pre=True)
    def pass_session_settings(  # pylint: disable = no-self-argument
        cls, value: str | None, values: dict[str, Any]
    ) -> dict[str, Any]:
        """Прокидывает настройки сессии"""
        if value and isinstance(value, dict):
            return value

        return {
            "proxy": values["proxy"] or None,
            "user_agent": values["user_agent"],
            "throttler_rate_limit": values["throttler_rate_limit"],
            "throttler_period": values["throttler_period"],
        }

    engine_config: dict[str, Any] = {}

    @validator("engine_config", always=True)
    def generate_engine_arguments(
        cls, value: dict[str, Any], values: dict[str, Any]
    ) -> dict[str, Any]:
        """Проверяет наличие переменной "engine_config" с параметрами движка
        БД.

        При отсутствии, генерирует с использованием имеющихся переменных с
        элементами URL.
        """
        if value:
            return value
        return {
            "url": PostgresDsn.build(
                scheme=f"{values['DB_DIALECT']}+{values['DB_API']}",
                user=values["DB_USER"],
                password=values["DB_PASSWORD"],
                host=values["DB_HOST"],
                port=values["DB_PORT"],
                path=f"/{values['DB_NAME']}",
            ),
            "future": values["db_future"],
            "pool_recycle": values["db_pool_recycle"],
            "echo": values["db_echo"],
        }

    @validator("engine_config")
    def check_url_specified(cls, value: dict[str, Any]) -> dict[str, Any]:
        """Проверяет наличие URL БД в параметрах движка."""
        if "url" not in value:
            raise ValueError("DB URL should be in engine parameters.")
        return value

    @validator("engine_config")
    def check_sources_url_specified(
        cls, value: dict[str, Any]
    ) -> dict[str, Any]:
        """Проверяет наличие URL БД в параметрах движка."""
        if "url" not in value:
            raise ValueError("DB URL should be in engine parameters.")
        return value

    # авторизация
    allow_unauthorized: bool = False

    # Logging
    log_level: str = "INFO"
    logging: dict[str, Any] = {}

    @validator("logging", pre=True)
    def pass_logging_settings(
        cls, value: str | None, values: dict[str, Any]
    ) -> dict[str, Any]:
        """Прокидывает настройки логгера"""
        if value and isinstance(value, dict):
            return value

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "format": (
                        "%(name)-12s %(asctime)s %(levelname)-8s "
                        "%(filename)s:%(funcName)s %(message)s"
                    ),
                    "datefmt": "%d.%m.%y %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "root": {"level": "DEBUG", "handlers": ["console"]},
                "register-manager": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                },
            },
        }

    date_format: str = "%d.%m.%Y"

    # pagination
    min_page: int = 1
    max_page: int = 1_000
    default_start_page: int = min_page
    min_per_page: int = 1
    max_per_page: int = 30
    default_per_page: int = 10

    context_headers_prefix: constr(to_lower=True) = "x-context-"  # type: ignore[valid-type]


class LocalSettings(CommonSettings):
    """Загрузка и валидация настроек приложения для local окружения."""

    # DEBUG
    debug: bool = True

    # Server
    server_reload: bool = True
    root_path: str = ""

    # Logging
    logging: dict[str, Any] = {}

    @validator("logging", pre=True)
    def pass_logging_settings(
        cls, value: str | None, values: dict[str, Any]
    ) -> dict[str, Any]:
        """Прокидывает настройки логгера"""
        if value and isinstance(value, dict):
            return value

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "format": (
                        "%(name)-12s %(asctime)s %(levelname)-8s "
                        "%(filename)s:%(funcName)s %(message)s"
                    ),
                    "datefmt": "%d.%m.%y %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "root": {"level": "DEBUG", "handlers": ["console"]},
                "register-manager": {
                    "level": "DEBUG",
                    "handlers": ["console"],
                },
            },
        }


class DevSettings(CommonSettings):
    """Загрузка и валидация настроек приложения для dev окружения."""


class ProdSettings(CommonSettings):
    """Загрузка и валидация настроек приложения для prod окружения."""


@lru_cache
def get_settings(environment: str) -> CommonSettings:
    """
    Инициализирует класс с настройками приложения.

    Поскольку вызовы кэшируются, добавлен параметр environment для удобства
    тестирования.
    """
    settings_index = dict(
        local=LocalSettings,
        dev=DevSettings,
        prod=ProdSettings,
    )
    return settings_index.get(environment, ProdSettings)()


settings = get_settings(EnvironmentSettings().environment.value)

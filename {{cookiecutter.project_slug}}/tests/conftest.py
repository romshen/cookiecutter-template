"""Содержит фикстуры для тестов"""
# pylint: disable=unused-argument, redefined-outer-name, duplicate-code
import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import pytest
from sqlalchemy import delete
from starlette.datastructures import URL

from app.repository.database.database import async_engine, async_session
from app.repository.database.models import models
from app.services.create.create_service import CreateService
from app.services.read.read_service import ReadItemService, ReadService
from app.services.update.reader import Reader
from app.tests import parameters
from app.utils.logger.logs_adapter import logger

TEST_DATA_FOLDER = "data"


@pytest.fixture(scope="session", autouse=True)
def event_loop(request):
    """Создаёт экземпляр default event loop для каждой тестовой сессии.
    Добавлен в связи с появлением ошибки:
    RuntimeError: Task ... attached to a different loop
    """
    policy = asyncio.get_event_loop_policy()
    res = policy.new_event_loop()
    asyncio.set_event_loop(res)
    res.close_ = res.close
    res.close = lambda: None

    yield res

    res.close_()


@pytest.fixture(scope="session", autouse=True)
async def create_tables(event_loop):
    """Перед стартом тестовой сессии проверяет наличие таблиц в БД и создаёт
    отсутствующие.
    """
    await async_engine.create_tables()
    yield
    await async_engine.close_connections()


@pytest.fixture
async def get_test_session(event_loop):
    """Генератор сессии для тестов."""
    async with async_session() as session:
        yield session


class CleanUpDB:
    """Класс-помощник для очистки БД после каждого теста."""

    def __init__(self, *models):
        """Принимает модели, с которыми работают тесты, для дальнейшей
        очистки созданных записей.
        """
        self.models = models

    async def delete_db_rows(self, session):
        """Удаляет все записи, связанные с моделью."""
        for model in self.models:
            await session.execute(delete(model))
            await session.commit()


@pytest.fixture(autouse=True)
async def clean_up_db(get_test_session):
    """Очищает таблицы БД после тестов.
    Вовлечённые модели передаются при инициализации CleanUpDB.
    """
    clean_up_db = CleanUpDB(
        models.NetworkAccount,
        models.MediaForeignAgent,
        models.UpdateHistory,
        models.SignificantResource,
        models.OppositionalSmk,
        models.RichItResource,
        models.InternationalBroadcaster,
        models.LabThreshold,
        models.ImportantResource,
        models.BankResource,
        models.RuDomainZone,
        models.GovernmentWebsite,
        models.ProRussianMediaProhibitedInfo,
        models.OnlineStoresWebsites,
        models.SocialOrganization,
        models.StateAndLargeMedia,
        models.InternationalNewsAgenciesWithWikiPage,
        models.CountrySpecificInfoResource,
        models.GlobalWebResource,
    )
    yield
    await clean_up_db.delete_db_rows(get_test_session)


class Request:
    """Mock Request class."""

    def __init__(
        self,
        route_url: str = "http://test.ru/frontend-api/media-foreign-agents",
        query_params=None,
    ):
        self.url = URL(url=route_url)
        self.query_params: dict = query_params if query_params else {}


@dataclass
class JwtUser:
    """Mock JwtUser для тестов"""

    username: str = "test_user"
    full_name: str = "Фамилия Имя"


@pytest.fixture(params=parameters.route_url_entity_pairs)
def get_create_service(request):
    route_url, entity = request.param
    mock_request = Request(route_url)

    return CreateService(
        entity_data=entity, user=JwtUser(), request=mock_request
    )


@pytest.fixture(params=parameters.route_urls)
def get_mock_request(request):
    route_url = request.param
    return Request(route_url)


@pytest.fixture
def get_read_service(get_test_session, get_create_service):
    """
    Переиспользуем параметризованную get_create_service фикстуру для создания
    экзэмпляров ReadService.
    """
    create_service = get_create_service
    mock_request = Request(str(create_service._request.url))

    return ReadService(request=mock_request, query_params={})


@pytest.fixture
def get_read_item_service(get_test_session, get_create_service):
    """
    Переиспользуем параметризованную get_create_service фикстуру для создания
    экзэмпляров ReadItemService.
    """
    create_service = get_create_service
    mock_request = Request(str(create_service._request.url))

    return ReadItemService(request=mock_request)


def get_data_folder_path():
    return f"{Path(__file__).parent}/{TEST_DATA_FOLDER}"


@pytest.fixture(name="get_data_folder_path")
def get_data_folder_path_fixture():
    return get_data_folder_path()


@dataclass
class UploadFile:
    """Mock UploadFile для тестов"""

    filename: str = "test.xlsx"
    file: BinaryIO | None = None


def get_file_object(file_name):
    """Генерирует файл как объект."""
    file_path = f"{get_data_folder_path()}/{file_name}"
    return open(file_path, "rb")
    # with open(file_path, "rb") as file_object:
    #     yield file_object


def get_upload_file(file_name):
    """Создаёт экземпляр UploadFile."""
    file_object = get_file_object(file_name)
    # file_iterator = get_file_object(file_name)
    # file_object = next(file_iterator)
    logger.debug(f"{file_object.name=}")

    return UploadFile(filename=file_object.name, file=file_object)


@pytest.fixture(params=parameters.route_url_filename_pairs)
def get_reader(request):
    route_url, file_name = request.param
    logger.debug(f"{route_url=}")
    logger.debug(f"{file_name=}")

    return Reader(Request(route_url), get_upload_file(file_name))

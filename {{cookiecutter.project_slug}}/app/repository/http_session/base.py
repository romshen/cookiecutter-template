"""
Модуль выносит работу с сессиями в отдельный слой абстракции.

При обращении к соцсетям важно соблюдать ограничения апи
на число запросов в секунду.
Для этого реализуем класс-throttler,
ограничивающий число единовременных запросов в рамках одной сессии.
"""

import asyncio
import functools
import json
import time
from asyncio import TimeoutError as AsyncTimeoutError
from collections import deque
from collections.abc import Callable
from typing import Any

from aiohttp import (
    ClientConnectionError,
    ClientOSError,
    ClientPayloadError,
    ClientSession,
    ContentTypeError,
)
from yarl import URL

from app.repository.http_session.exception import (
    ClientSessionError,
    UnknownSessionError,
)


class Throttler:
    """
    При обращении к соцсетям важно соблюдать ограничения апи
    на число запросов в секунду.
    Для этого реализуем класс-throttler,
    ограничивающий число единовременных запросов в рамках одной сессии.

    rate_limit/period = число запросов/n секунд
    """

    def __init__(self, rate_limit: int, period: int | float = 1.0):
        self._period = float(period)
        self._times = deque(0.0 for _ in range(rate_limit))

    async def __aenter__(self):
        while True:
            curr_ts = time.monotonic()
            if (diff := curr_ts - (self._times[0] + self._period)) > 0.0:
                self._times.popleft()
                break
            await asyncio.sleep(-diff)

        self._times.append(curr_ts)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class ApiResponse:  # pylint: disable=too-few-public-methods
    """
    Переопределяем класс респонса
    """

    def __init__(
        self, status_code: int, response_url: URL, response_body: str
    ):
        self.status = status_code
        self.url = response_url
        self.body = response_body

    def __repr__(self):
        return (
            f"<Response with "
            f"status: {self.status}; "
            f"url: {self.url}; "
            f"body: {self.body}>"
        )

    def deserialize_json(self) -> Any:
        """
        Функция десереализует JSON тела ответа и возвращает Python объект.
        """
        return json.loads(self.body.strip())

    def text(self):
        """
        Функция возвращает текст тела ответа
        """
        return self.body.strip()


def retry_api_request(
    times: int = 5,
    backoff_sleep: float = 0.5,
    session_exceptions: tuple = (
        ClientOSError,
        ClientPayloadError,
        ClientConnectionError,
        ContentTypeError,
        AsyncTimeoutError,
    ),
) -> Callable:
    """
    Повторяем попытку обращения к соцсети
    в случае клиентских ошибок
    в течении times раз.
    Каждый новый запрос будем делать с задержкой в backoff_factor секунд
    """

    def retry_decorator(session_func: Callable) -> Callable:
        @functools.wraps(session_func)
        async def request_wrapper(*args, **kwargs) -> ApiResponse:
            attempt = 0
            sleep_time = min(1, backoff_sleep)
            session_error = "Session Error"

            while attempt < times:
                try:
                    response = await session_func(*args, **kwargs)
                except session_exceptions as error:
                    session_error = error
                    await asyncio.sleep(sleep_time)
                    continue
                except Exception as error:
                    raise UnknownSessionError(
                        f"Unknown error: {error}. Params: {args, kwargs}."
                    ) from error
                else:
                    return response
                finally:
                    attempt += 1
                    sleep_time += backoff_sleep

            raise ClientSessionError(session_error)

        return request_wrapper

    return retry_decorator


class ApiSession:
    """
    Класс реализует интерфейс http запросов через aiohttp
    """

    def __init__(
        self,
        proxy: str | None,
        user_agent: str,
        throttler_rate_limit: int,
        throttler_period: int | float,
    ):
        self._proxy = proxy
        self._headers = {
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "User-Agent": user_agent,
        }
        self._throttler = Throttler(throttler_rate_limit, throttler_period)
        self._session = ClientSession(trust_env=True)
        self._closed = False

    @property
    def closed(self) -> bool:
        """Показывает, закрыта ли http-сессия"""
        return self._closed

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @retry_api_request()
    async def get(
        self,
        url: str,
        params: None | str | list[tuple[str, str]] = None,
        headers: dict[str, Any] | None = None,
    ) -> ApiResponse:
        """
        Функция посылает GET запрос
        """
        headers = self._headers | (headers or {})

        async with self._throttler:
            async with self._session.get(
                url, params=params, proxy=self._proxy, headers=headers
            ) as response:
                return ApiResponse(
                    response.status, response.url, await response.text()
                )

    @retry_api_request()
    async def post(
        self,
        url: str,
        data: dict | bytes | Any = None,
        json_data: dict | Any = None,
        headers: dict[str, Any] | None = None,
        ssl: bool = False,
    ) -> ApiResponse:
        """
        Функция посылает POST запрос
        """
        headers = self._headers | (headers or {})
        post_params: dict[str, Any] = {
            "proxy": self._proxy,
            "headers": headers,
            "ssl": ssl,
        }
        if json_data is not None:
            post_params["json"] = json_data
        elif data is not None:
            post_params["data"] = data

        async with self._throttler:
            async with self._session.post(url, **post_params) as response:
                return ApiResponse(
                    response.status, response.url, await response.text()
                )

    async def close(self):
        """
        Функция закрывает сессию
        """
        await self._session.close()
        self._closed = True

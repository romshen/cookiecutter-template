# pylint: disable=missing-module-docstring
import asyncio
from asyncio import ensure_future
from collections.abc import Callable
from functools import wraps

from starlette.concurrency import run_in_threadpool

from app.utils.logger.logs_adapter import logger


def repeat(interval_seconds: float) -> Callable:
    """
    This function returns a decorator that modifies a function so it is
    periodically re-executed
    """

    def decorator(func: Callable) -> Callable:
        """
        Converts the decorated function into a repeated, periodically-called
        version of itself.
        """
        is_coroutine = asyncio.iscoroutinefunction(func)

        @wraps(func)
        async def wrapped() -> None:
            async def loop() -> None:
                while True:
                    try:
                        if is_coroutine:
                            await func()  # type: ignore
                        else:
                            await run_in_threadpool(func)
                    except Exception as exc:  # pylint: disable=broad-except
                        logger.error(exc)

                    await asyncio.sleep(interval_seconds)

            ensure_future(loop())

        return wrapped

    return decorator

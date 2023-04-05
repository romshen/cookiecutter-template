"""Описывает пути к концевым точкам для фронта"""

from fastapi import APIRouter

from app.api.frontend.endpoints import (
    module_name
)

router = APIRouter(prefix="/frontend-api")
router.include_router(
    module_name.router, tags=["frontend-api, module_name"]
)


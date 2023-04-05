"""Описывает пути к концевым точкам проверки здоровья контейнера."""
from fastapi import APIRouter

router = APIRouter(prefix="/check", tags=["health check"])


@router.get("/health", status_code=200)
async def get_health_check():
    """Api health check"""
    return {}

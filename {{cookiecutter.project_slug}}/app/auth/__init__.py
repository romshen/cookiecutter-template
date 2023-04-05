"""Модуль авторизации"""

from .jwt import JWTIdentityFastAPI, make_user

__all__ = ["JWTIdentityFastAPI", "make_user"]

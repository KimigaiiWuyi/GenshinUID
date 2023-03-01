"""Enka Network 包装
参考：https://api.enka.network
"""
from .models import EnkaData as EnkaData  # noqa: F401
from .request import get_enka_info as get_enka_info  # noqa: F401

__all__ = ["request", "models"]

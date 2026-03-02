"""
RAG模块 - 原神数据RAG解析系统
"""

from .register import rag_register, char_register, weapon_register  # noqa: F401

__all__ = ["rag_register", "char_register", "weapon_register"]

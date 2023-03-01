from typing import Any

from ..types import AnyDict


class MiniggNotFoundError(Exception):
    """MiniGG API 未找到报错"""

    def __init__(self, **raw: Any) -> None:
        self.raw: AnyDict = raw

    def __repr__(self) -> str:
        raw = self.raw
        return f"<MiniggNotFoundError {raw=}>"

    def __str__(self) -> str:
        return repr(self)

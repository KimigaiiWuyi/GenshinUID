from typing import Set

from nonebot import get_driver
from pydantic import Field, BaseModel


class Config(BaseModel):
    disabled_plugins: Set[str] = Field(
        default_factory=set, alias="genshinuid_disabled_plugins"
    )
    priority: int = Field(2, alias="genshinuid_priority")


config = Config.parse_obj(get_driver().config)
priority = config.priority

from __future__ import annotations

from enum import IntEnum
from typing import List, Optional, NamedTuple

from pydantic import HttpUrl, BaseModel, validator


class MapID(IntEnum):
    """地图 ID"""

    teyvat = 2
    """提瓦特"""
    enkanomiya = 7
    """渊下宫"""
    chasm = 9
    """层岩巨渊·地下矿区"""
    # golden_apple_archipelago = 12
    """金苹果群岛"""


class Label(BaseModel):
    id: int
    name: str
    icon: HttpUrl
    parent_id: int
    depth: int
    node_type: int
    jump_type: int
    jump_target_id: int
    display_priority: int
    children: list
    activity_page_label: int
    area_page_label: List[int]
    is_all_area: bool


class Tree(BaseModel):
    id: int
    name: str
    icon: str
    parent_id: int
    depth: int
    node_type: int
    jump_type: int
    jump_target_id: int
    display_priority: int
    children: List[Label]
    activity_page_label: int
    area_page_label: List
    is_all_area: bool


class Point(BaseModel):
    id: int
    label_id: int
    x_pos: float
    y_pos: float
    author_name: str
    ctime: str
    display_state: int


class Slice(BaseModel):
    url: HttpUrl


class Maps(BaseModel):
    slices: List[List[HttpUrl]]
    origin: List[int]
    total_size: List[int]
    padding: List[int]

    @validator("slices", pre=True)
    def slices_to_list(cls, v):
        return [[i["url"] for i in y] for y in v]


class MapInfo(BaseModel):
    id: int
    name: str
    parent_id: int
    depth: int
    detail: Maps
    node_type: int
    children: list
    icon: Optional[HttpUrl]
    ch_ext: Optional[str]

    @validator("detail", pre=True)
    def detail_str_to_maps(cls, v):
        return Maps.parse_raw(v)


class XYPoint(NamedTuple):
    x: float
    y: float


class Kind(BaseModel):
    id: int
    name: str
    icon_id: int
    icon_url: HttpUrl
    is_game: int


class SpotKinds(BaseModel):
    list: List[Kind]
    is_sync: bool
    already_share: bool


class Spot(BaseModel):
    id: int
    name: str
    content: str
    kind_id: int
    spot_icon: str
    x_pos: float
    y_pos: float
    nick_name: str
    avatar_url: HttpUrl
    status: int

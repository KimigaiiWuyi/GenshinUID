from typing import Dict, List, Union

import msgspec


class GsConfig(msgspec.Struct, tag=True):
    title: str
    desc: str


class GsStrConfig(GsConfig, tag=True):
    data: str


class GsBoolConfig(GsConfig, tag=True):
    data: bool


class GsDictConfig(GsConfig, tag=True):
    data: Dict[str, List]


class GsListStrConfig(GsConfig, tag=True):
    data: List[str]


class GsListConfig(GsConfig, tag=True):
    data: List[int]


GSC = Union[
    GsDictConfig, GsBoolConfig, GsListConfig, GsListStrConfig, GsStrConfig
]

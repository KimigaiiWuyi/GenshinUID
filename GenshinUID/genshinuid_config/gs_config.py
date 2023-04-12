from typing import Dict, List, Union, Literal, overload

from msgspec import json as msgjson

from .config_default import CONIFG_DEFAULT
from ..utils.resource.RESOURCE_PATH import CONFIG_PATH
from .models import (
    GSC,
    GsStrConfig,
    GsBoolConfig,
    GsDictConfig,
    GsListConfig,
    GsListStrConfig,
)

STR_CONFIG = Literal['proxy', '_pass_API', 'random_pic_API', 'restart_command']
LIST_INT_CONFIG = Literal['Ann_Ids']
LIST_STR_CONFIG = Literal['SignTime', 'BBSTaskTime']
DICT_CONFIG = Literal['Ann_Groups']


class StringConfig:
    def __init__(self) -> None:
        if not CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'wb') as file:
                file.write(msgjson.encode(CONIFG_DEFAULT))

        self.config: Dict[str, GSC] = {}
        self.update_config()

    def __len__(self):
        return len(self.config)

    def __iter__(self):
        return iter(self.config)

    def __getitem__(self, key) -> GSC:
        return self.config[key]

    def write_config(self):
        with open(CONFIG_PATH, 'wb') as file:
            file.write(msgjson.format(msgjson.encode(self.config), indent=4))

    def update_config(self):
        # 打开config.json
        with open(CONFIG_PATH, 'r', encoding='UTF-8') as f:
            self.config: Dict[str, GSC] = msgjson.decode(
                f.read(),
                type=Dict[str, GSC],
            )
        # 对没有的值，添加默认值
        for key in CONIFG_DEFAULT:
            if key not in self.config:
                self.config[key] = CONIFG_DEFAULT[key]

        # 对默认值没有的值，直接删除
        delete_keys = []
        for key in self.config:
            if key not in CONIFG_DEFAULT:
                delete_keys.append(key)
        for key in delete_keys:
            self.config.pop(key)

        # 重新写回
        self.write_config()

    @overload
    def get_config(self, key: STR_CONFIG) -> GsStrConfig:
        ...

    @overload
    def get_config(self, key: LIST_INT_CONFIG) -> GsListConfig:
        ...

    @overload
    def get_config(self, key: LIST_STR_CONFIG) -> GsListStrConfig:
        ...

    @overload
    def get_config(self, key: DICT_CONFIG) -> GsDictConfig:
        ...

    @overload
    def get_config(self, key: str) -> GsBoolConfig:
        ...

    def get_config(self, key: str) -> GSC:
        if key in self.config:
            return self.config[key]
        elif key in CONIFG_DEFAULT:
            self.update_config()
            return self.config[key]
        else:
            return GsBoolConfig('缺省值', '获取错误的配置项', False)

    @overload
    def set_config(self, key: STR_CONFIG, value: str) -> bool:
        ...

    @overload
    def set_config(self, key: LIST_INT_CONFIG, value: List[int]) -> bool:
        ...

    @overload
    def set_config(self, key: LIST_STR_CONFIG, value: List[str]) -> bool:
        ...

    @overload
    def set_config(self, key: DICT_CONFIG, value: Dict) -> bool:
        ...

    @overload
    def set_config(self, key: str, value: bool) -> bool:
        ...

    def set_config(
        self, key: str, value: Union[str, List, bool, Dict]
    ) -> bool:
        if key in CONIFG_DEFAULT:
            temp = self.config[key]
            temp.data = value  # type:ignore
            # 设置值
            self.config[key] = temp
            # 重新写回
            self.write_config()
            return True
        else:
            return False


gsconfig = StringConfig()

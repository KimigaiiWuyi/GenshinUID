import json
from typing import List, Union, Literal, overload

from ..utils.download_resource.RESOURCE_PATH import CONFIG_PATH

CONIFG_DEFAULT = {
    'LU_TOKEN': '',
    'proxy': '',
    '_pass_API': '',
    'Ann_Groups': [],
    'Ann_Ids': [],
}

STR_CONFIG = Literal['LU_TOKEN', 'proxy', '_pass_API']
LIST_CONFIG = Literal['Ann_Groups', 'Ann_Ids']


class StringConfig:
    def __init__(self) -> None:
        if not CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'w', encoding='UTF-8') as file:
                json.dump(CONIFG_DEFAULT, file, ensure_ascii=False)

        self.update_config()

    def write_config(self):
        with open(CONFIG_PATH, 'w', encoding='UTF-8') as file:
            json.dump(self.config, file, ensure_ascii=False)

    def update_config(self):
        # 打开config.json
        with open(CONFIG_PATH, 'r', encoding='UTF-8') as f:
            self.config = json.load(f)
        # 对没有的值，添加默认值
        for key in CONIFG_DEFAULT:
            if key not in self.config:
                self.config[key] = CONIFG_DEFAULT[key]

        # 重新写回
        self.write_config()

    @overload
    def get_config(self, key: STR_CONFIG) -> str:
        ...

    @overload
    def get_config(self, key: LIST_CONFIG) -> List:
        ...

    def get_config(self, key: str) -> Union[str, List]:
        if key in self.config:
            return self.config[key]
        elif key in CONIFG_DEFAULT:
            self.update_config()
            return self.config[key]
        else:
            return []

    @overload
    def set_config(self, key: STR_CONFIG, value: str) -> bool:
        ...

    @overload
    def set_config(self, key: LIST_CONFIG, value: List) -> bool:
        ...

    def set_config(self, key: str, value: Union[str, List]) -> bool:
        if key in CONIFG_DEFAULT:
            # 设置值
            self.config[key] = value
            # 重新写回
            self.write_config()
            return True
        else:
            return False


string_config = StringConfig()

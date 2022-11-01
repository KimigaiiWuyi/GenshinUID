from typing import Dict
from enum import IntEnum


class Element(IntEnum):
    Physical = 0
    Anemo = 1
    Cryo = 2
    Dendro = 3
    Electro = 4
    Geo = 5
    Hydro = 6
    Pyro = 7


# 消耗后面元素量,抵消前面1单位元素量
reactable_elements_dict: Dict[Element, Dict[Element, Dict[str, str]]] = {
    # 风反应,被所有元素克制
    Element.Anemo: {
        Element.Cryo: {
            'value': '2',
            'reaction': '扩散',
            'dmg': '0',
        },
        Element.Dendro: {
            'value': '2',
            'reaction': '扩散',
            'dmg': '0',
        },
        Element.Electro: {
            'value': '2',
            'reaction': '扩散',
            'dmg': '0',
        },
        Element.Hydro: {
            'value': '2',
            'reaction': '扩散',
            'dmg': '0',
        },
        Element.Pyro: {
            'value': '2',
            'reaction': '扩散',
            'dmg': '0',
        },
    },
    # 冰反应,被火克制,与雷水反应
    Element.Cryo: {
        Element.Pyro: {
            'value': '2',
            'reaction': '融化',
            'dmg': '2',
        },
        Element.Electro: {
            'value': '2',
            'reaction': '超导',
            'dmg': '0',
        },
        Element.Hydro: {
            'value': '1',
            'reaction': '冻结',
            'dmg': '0',
        },
    },
    # 草反应, 火,水,雷
    Element.Dendro: {
        Element.Hydro: {
            'value': '1',
            'reaction': '燃烧',
            'dmg': '0',
        },
        Element.Pyro: {
            'value': '2',
            'reaction': '绽放',
            'dmg': '0',
        },
        Element.Electro: {
            'value': '2',
            'reaction': '激化',
            'dmg': '0',
        },
    },
    # 雷反应, 水,火,冰,草
    Element.Electro: {
        Element.Hydro: {
            'value': '1',
            'reaction': '感电',
            'dmg': '0',
        },
        Element.Pyro: {
            'value': '1',
            'reaction': '超载',
            'dmg': '0',
        },
        Element.Cryo: {
            'value': '1',
            'reaction': '超导',
            'dmg': '0',
        },
        Element.Dendro: {
            'value': '1',
            'reaction': '激化',
            'dmg': '0',
        },
    },
    # 岩反应,被所有元素克制
    Element.Geo: {
        Element.Cryo: {
            'value': '2',
            'reaction': '结晶',
            'dmg': '0',
        },
        Element.Dendro: {
            'value': '2',
            'reaction': '结晶',
            'dmg': '0',
        },
        Element.Electro: {
            'value': '2',
            'reaction': '结晶',
            'dmg': '0',
        },
        Element.Hydro: {
            'value': '2',
            'reaction': '结晶',
            'dmg': '0',
        },
        Element.Pyro: {
            'value': '2',
            'reaction': '结晶',
            'dmg': '0',
        },
    },
    # 水反应,草,火,冰,雷
    Element.Hydro: {
        Element.Dendro: {
            'value': '1',
            'reaction': '绽放',
            'dmg': '0',
        },
        Element.Pyro: {
            'value': '0.5',
            'reaction': '蒸发',
            'dmg': '1.5',
        },
        Element.Cryo: {
            'value': '1',
            'reaction': '冻结',
            'dmg': '0',
        },
        Element.Electro: {
            'value': '1',
            'reaction': '感电',
            'dmg': '0',
        },
    },
    # 火反应, 雷,水,冰,草
    Element.Pyro: {
        Element.Dendro: {
            'value': '1',
            'reaction': '燃烧',
            'dmg': '0',
        },
        Element.Hydro: {
            'value': '2',
            'reaction': '蒸发',
            'dmg': '2',
        },
        Element.Cryo: {
            'value': '0.5',
            'reaction': '融化',
            'dmg': '1.5',
        },
        Element.Electro: {
            'value': '1',
            'reaction': '超载',
            'dmg': '0',
        },
    },
}

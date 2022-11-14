from typing import Dict, List

from .Element import Element, reactable_elements_dict


class Enemy:
    def __init__(self, char_level: int, enemy_level: int):
        self.char_level = char_level
        self.level: int = enemy_level
        self.hp: int = 10000000

        self.time: float = 0

        self.defense_resist: float = 0
        self.ignore_defense: float = 0
        self.element: Dict[Element, float] = {}

        self.physical_resist: float = 0.1
        self.anemo_resist: float = 0.1
        self.cryo_resist: float = 0.1
        self.dendro_resist: float = 0.1
        self.electro_resist: float = 0.1
        self.geo_resist: float = 0.1
        self.hydro_resist: float = 0.1
        self.pyro_resist: float = 0.1

        self.total_dmg: float = 0
        self.debuff: List = []

    async def update(self, time):
        self.time += time
        # TODO 遍历debuff列表, 超过时间的移除

    async def get_dmg_reaction(self, dmg_type: Element) -> float:
        reaction: float = 1
        # 如果是物理伤害,则不反应
        if dmg_type == Element.Physical:
            return 1

        # 如果怪物头上没元素,给定此次伤害类型元素量1
        if self.element == {}:
            self.element[dmg_type] = 1
        # 如果怪物头上元素相同,则刷新元素量
        elif dmg_type in self.element:
            self.element[dmg_type] = 1
        else:
            # 遍历怪物头上的元素
            new_element_list = self.element
            for element in self.element:
                # 如果本次伤害类型,在这个元素的可反应列表里
                if dmg_type in reactable_elements_dict[element]:
                    # 元素列表里的这个元素 就要减去反应量
                    new_element_list[element] -= float(
                        reactable_elements_dict[element][dmg_type]['value']
                    )
                    # 如果是增幅反应,给出相对应的倍率
                    reaction_name = reactable_elements_dict[element][dmg_type][
                        'reaction'
                    ]
                    if reaction_name in [
                        '蒸发',
                        '融化',
                    ]:
                        reaction *= float(
                            reactable_elements_dict[element][dmg_type]['dmg']
                        )
                    else:
                        self.debuff.append(reaction_name)

            # 结算怪物的元素
            result_element: Dict[Element, float] = {}
            for element in new_element_list:
                if new_element_list[element] > 0:
                    result_element[element] = new_element_list[element]
            self.element = result_element

        return reaction

    async def get_dmg_proof(self, dmg_type: Element) -> float:
        proof: float = 0

        # 计算抗性
        r = getattr(self, f'{dmg_type}_resist')
        if r > 0.75:
            r = 1 / (1 + 4 * r)
        elif r > 0:
            r = 1 - r
        else:
            r = 1 - r / 2

        # 计算防御
        d = (self.char_level + 100) / (
            (self.char_level + 100)
            + (1 - self.defense_resist)
            * (1 - self.ignore_defense)
            * (self.level + 100)
        )
        proof = r * d

        # 返回减伤百分比
        return proof

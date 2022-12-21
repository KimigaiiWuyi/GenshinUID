<<<<<<< HEAD
from typing import Dict, List, Optional
=======
from typing import Dict, List
>>>>>>> 57bd1814ee1479e2c9d421865531fd2ecc9522da

from .Character import Character
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

        self.PhysicalResist: float = 0.1
        self.AnemoResist: float = 0.1
        self.CryoResist: float = 0.1
        self.DendroResist: float = 0.1
        self.ElectroResist: float = 0.1
        self.GeoResist: float = 0.1
        self.HydroResist: float = 0.1
        self.PyroResist: float = 0.1

        self.total_dmg: float = 0
        self.debuff: List = []

    async def update(self, time):
        self.time += time
        # TODO 遍历debuff列表, 超过时间的移除

    async def update_resist(self, effect: str):
        name, val = effect.split('+')
        val = float(val) / 100
        if name != 'Resist':
            r = getattr(self, name)
            setattr(self, name, r + val)
        else:
            for element in self.element:
                r = getattr(self, f'{element.name}Resist')
                setattr(self, name, r + val)

    async def get_dmg_reaction(
        self,
        dmg_type: Optional[Element] = None,
        char: Optional[Character] = None,
    ) -> float:
        if char:
            for react in ['蒸发', '融化']:
                if react in char.power_name:
                    em = char.real_prop[f'{char.attack_type}_elementalMastery']
                    k = 0
                    if react == '蒸发':
                        if char.char_element == 'Pyro':
                            k = 1.5
                        else:
                            k = 2
                    elif react == '融化':
                        if char.char_element == 'Pyro':
                            k = 2
                        else:
                            k = 1.5
                    reaction_add_dmg = k * (
                        1 + (2.78 * em) / (em + 1400) + char.real_prop['a']
                    )
                    break
            else:
                reaction_add_dmg = 1
            return reaction_add_dmg
        else:
            if dmg_type:
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
                                reactable_elements_dict[element][dmg_type][
                                    'value'
                                ]
                            )
                            # 如果是增幅反应,给出相对应的倍率
                            reaction_name = reactable_elements_dict[element][
                                dmg_type
                            ]['reaction']
                            if reaction_name in [
                                '蒸发',
                                '融化',
                            ]:
                                reaction *= float(
                                    reactable_elements_dict[element][dmg_type][
                                        'dmg'
                                    ]
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
        return 0

    async def get_resist(self, dmg_type: Element):
        # 计算抗性
        r = getattr(self, f'{dmg_type.name}Resist')
        if r > 0.75:
            r = 1 / (1 + 4 * r)
        elif r > 0:
            r = 1 - r
        else:
            r = 1 - r / 2

        return r

    async def get_dmg_proof(
        self,
        dmg_type: Element,
        extra_d: float = 0,
        extra_ignoreD: float = 0,
    ) -> float:
        proof: float = 0

        # 计算抗性
        r = await self.get_resist(dmg_type)

        # 计算防御
        d_up = self.char_level + 100
        d_down = (
            self.char_level
            + 100
            + (1 - self.defense_resist - extra_d)
            * (1 - self.ignore_defense - extra_ignoreD)
            * (self.level + 100)
        )
        d = d_up / d_down
        proof = r * d

        # 返回减伤百分比
        return proof

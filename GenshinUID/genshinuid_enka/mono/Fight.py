from typing import List, Tuple

from .Enemy import Enemy
from .Element import Element
from .Character import Character


class Fight:
    def __init__(self, Character_list: dict[str, Character], Enemy: Enemy, SEQ: List):
        self.time = 0
        self.total_crit_dmg: float = 0
        self.total_normal_dmg: float = 0
        self.total_avg_dmg: float = 0

        self.SEQ: List = SEQ
        self.seq_history: dict = {}
        self.char_list: dict[str, Character] = Character_list
        self.enemy = Enemy

    async def update_dmg(self):
        for seq in self.SEQ:
            # 获取本次攻击的信息
            char_name = seq['char']
            self.char_list[char_name].power_name = seq['action']
            self.time += 0.4

            # 更新角色和怪物
            for char in self.char_list:
                await self.char_list[char].update(self.time)
            await self.enemy.update(self.time)

            # 获取本次攻击的类型
            attack_type = await self.get_attack_type(char_name)
            # 获取本次攻击的元素
            dmg_type = await self.get_dmg_type(char_name, attack_type, seq)

            # 更新self.seq_history
            self.seq_history = seq

            # 进行攻击
            normal_dmg, avg_dmg, crit_dmg = await self.get_dmg(
                char_name, dmg_type, attack_type
            )

    async def get_dmg_type(
        self, char_name: str, attack_type: str, seq: dict
    ) -> Element:
        # TODO 获取本次攻击的元素
        dmg_type: Element = Element.Physical
        char_element_dmg_type = getattr(Element, self.char_list[char_name].char_element)

        # 对重复的计数
        if seq['action'] == self.seq_history:
            return dmg_type

        # 计算角色伤害加成应该使用什么
        if self.char_list[char_name].weapon_type == '法器' or char_name in [
            '荒泷一斗',
            '刻晴',
            '诺艾尔',
            '胡桃',
            '宵宫',
            '魈',
            '神里绫华',
        ]:
            dmg_type = char_element_dmg_type
        elif self.char_list[char_name].weapon_type == '弓':
            if attack_type in ['B', 'E', 'Q']:
                dmg_type = char_element_dmg_type
        else:
            if attack_type in ['E', 'Q']:
                dmg_type = char_element_dmg_type

        return dmg_type

    async def get_attack_type(self, char_name: str) -> str:
        # 攻击类型ABCEQ应为label首位
        attack_type = self.char_list[char_name].power_name[0]
        # 如果是雷电将军, 则就按首位,因为Q的几段伤害均视为元素爆发
        if char_name == '雷电将军':
            pass
        else:
            # 重击或瞄准射击在label内,则视为B重击伤害,例如公子E内的重击伤害,不视为E伤害,而是B伤害
            if (
                '重击' in self.char_list[char_name].power_name
                or '瞄准射击' in self.char_list[char_name].power_name
            ):
                attack_type = 'B'
            # 特殊重击类型,例如甘雨和夜兰
            elif (
                '破局矢' in self.char_list[char_name].power_name
                or '霜华矢' in self.char_list[char_name].power_name
            ):
                attack_type = 'B'
            # 下落伤害类型,例如魈
            elif '高空下落' in self.char_list[char_name].power_name:
                attack_type = 'C'
            # 一段伤害, 二段伤害等等 应视为A伤害
            elif (
                '段' in self.char_list[char_name].power_name
                and '伤害' in self.char_list[char_name].power_name
            ):
                attack_type = 'A'

        self.char_list[char_name].attack_type = attack_type
        return attack_type

    async def get_power(self, char_name: str, attack_type: str) -> Tuple[float, float]:
        power: str = ''
        power_plus: int = 0

        # 按照ABCEQ等级查找倍率
        power = self.char_list[char_name].power_list[
            self.char_list[char_name].power_name
        ]['value'][
            self.char_list[char_name].fight_prop['{}_skill_level'.format(attack_type)]
            - 1
        ]
        # 计算是否多次伤害
        power_plus = self.char_list[char_name].power_list[
            self.char_list[char_name].power_name
        ]['plus']

        # 拿到百分比和固定值,百分比为float,形如2.2 也就是202%
        power_percent, power_value = await power_to_value(power, power_plus)

        return power_percent, power_value

    async def get_effect_prop(self, char_name: str, attack_type: str):
        # 根据type计算有效属性
        if (
            '攻击'
            in self.char_list[char_name].power_list[
                self.char_list[char_name].power_name
            ]['type']
        ):
            effect_prop = self.char_list[char_name].fight_prop[f'{attack_type}_attack']
        elif (
            '生命值'
            in self.char_list[char_name].power_list[
                self.char_list[char_name].power_name
            ]['type']
        ):
            effect_prop = self.char_list[char_name].fight_prop[f'{attack_type}_hp']
        elif (
            '防御'
            in self.char_list[char_name].power_list[
                self.char_list[char_name].power_name
            ]['type']
        ):
            effect_prop = self.char_list[char_name].fight_prop[f'{attack_type}_defense']
        else:
            effect_prop = self.char_list[char_name].fight_prop[f'{attack_type}_attack']

        return effect_prop

    async def get_dmg(
        self, char_name: str, dmg_type: Element, attack_type: str
    ) -> Tuple[float, float, float]:
        effect_prop = await self.get_effect_prop(char_name, attack_type)
        power_percent, power_value = await self.get_power(char_name, attack_type)
        proof = await self.enemy.get_dmg_proof(dmg_type)
        reactio = await self.enemy.get_dmg_reaction(dmg_type)

        critrate_cal = self.char_list[char_name].fight_prop[f'{attack_type}_critrate']
        critdmg_cal = self.char_list[char_name].fight_prop[f'{attack_type}_critdmg']
        dmgBonus_cal = self.char_list[char_name].fight_prop[f'{attack_type}_dmgBonus']

        normal_dmg = (
            (effect_prop * power_percent + power_value)
            * (1 + dmgBonus_cal)
            * proof
            * reactio
        )
        # 暴击伤害
        crit_dmg = normal_dmg * (1 + critdmg_cal)
        # 平均伤害
        avg_dmg = crit_dmg * critrate_cal + (1 - critrate_cal) * normal_dmg

        self.total_normal_dmg += normal_dmg
        self.total_avg_dmg += avg_dmg
        self.total_crit_dmg += crit_dmg

        return normal_dmg, avg_dmg, crit_dmg


async def power_to_value(power: str, power_plus: int) -> Tuple[float, float]:
    """
    将power转换为value
    """
    if '+' in power:
        power_percent = (float(power.split('+')[0].replace('%', '')) / 100) * power_plus
        power_value = power.split('+')[1]
        if '%' in power_value:
            power_percent += float(power_value.replace('%', '')) / 100 * power_plus
            power_value = 0
        else:
            power_value = float(power_value)
    elif '%' in power:
        power_percent = float(power.replace('%', '')) / 100 * power_plus
        power_value = 0
    else:
        power_percent = 0
        power_value = float(power)

    return power_percent, power_value

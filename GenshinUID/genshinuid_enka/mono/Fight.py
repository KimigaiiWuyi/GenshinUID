from copy import deepcopy
from typing import Dict, List, Tuple, Optional

from nonebot.log import logger

from .Enemy import Enemy
from .Power import Power
from .Element import Element
from .Character import Character
from ..dmg_calc.base_value import base_value_list


class Fight:
    def __init__(
        self,
        Character_list: Dict[str, Character],
        Enemy: Enemy,
        SEQ: List = [],
    ):
        self.time = 0
        self.total_crit_dmg: float = 0
        self.total_normal_dmg: float = 0
        self.total_avg_dmg: float = 0

        self.SEQ: List = SEQ
        self.seq_history: Dict = {}
        self.char_list: Dict[str, Character] = Character_list
        self.enemy = Enemy

        self.dmg_data: Dict[str, Dict[str, float]] = {}

    # 进行队伍伤害计算
    async def update_dmg(self) -> Dict:
        result = {}
        for seq in self.SEQ:
            # 获取本次攻击的信息
            char_name = seq['char']
            char = self.char_list[char_name]
            char.power_name = seq['action']
            self.time += 0.4

            # 更新角色和怪物
            for _char in self.char_list:
                await self.char_list[_char].update(self.time)
            await self.enemy.update(self.time)

            # 获取本次攻击的类型
            await char.get_sp_fight_prop(char.power_name)
            await char.get_attack_type(char.power_name)
            # 获取本次攻击的元素
            dmg_type = await self.get_dmg_type(char, seq)
            # 更新角色的属性
            await self.get_new_fight_prop(char)

            # 更新self.seq_history
            self.seq_history = seq

            # 聚变反应
            for i in ['扩散', '绽放)', '感电', '超载']:
                if i in char.power_name:
                    dmg = await self.get_transform_dmg(char)
                    break
            else:
                # 进行攻击
                dmg = await self.get_dmg(char, dmg_type)
            normal_dmg, avg_dmg, crit_dmg = dmg[0], dmg[1], dmg[2]

            result[self.time] = {
                'char': char_name,
                'action': seq['action'],
                'normal_dmg': normal_dmg,
                'avg_dmg': avg_dmg,
                'crit_dmg': crit_dmg,
                'enemy_element': self.enemy.element,
            }
        logger.debug(result)
        return result

    # 进行单人伤害计算
    async def get_dmg_dict(
        self, char_name: str, without_talent: bool = False
    ) -> Dict:
        result = {}
        char = self.char_list[char_name]
        # 获取本次攻击的类型
        if without_talent:
            if char.rarity == '4' and char_name != '香菱':
                return self.dmg_data
            char.fight_prop = char.without_talent_fight

        for power_name in char.power_list:
            # 更新powername
            char.power_name = power_name
            await char.get_sp_fight_prop(char.power_name)
            await char.get_attack_type(char.power_name)
            # 更新角色的属性
            await self.get_new_fight_prop(char)
            # 聚变反应
            for i in ['扩散', '绽放)', '感电', '超载']:
                if i in power_name:
                    dmg = await self.get_transform_dmg(char)
                    break
            else:
                dmg = []

            # 正常伤害
            if not dmg:
                if '治疗' in power_name or '回复' in power_name:
                    dmg = await self.get_heal(char)
                elif '护盾' in power_name:
                    dmg = await self.get_shield(char)
                else:
                    # 获取本次攻击的元素
                    dmg_type = await self.get_dmg_type(char)
                    dmg = await self.get_dmg(char, dmg_type, True)

            # 得到结果
            result[power_name] = {
                'normal': dmg[0],
                'avg': dmg[1],
                'crit': dmg[2],
            }
        self.dmg_data = result
        logger.debug(result)
        return result

    # 伤害类型
    async def get_dmg_type(
        self, char: Character, seq: Optional[Dict] = None
    ) -> Element:
        # TODO 获取本次攻击的元素
        dmg_type: Element = Element.Physical
        char_element_dmg_type = getattr(Element, char.char_element)

        # 对重复的计数
        if seq:
            if seq['action'] == self.seq_history:
                return dmg_type

        # 计算角色伤害加成应该使用什么
        if char.weapon_type == '法器' or char.char_name in [
            '荒泷一斗',
            '刻晴',
            '诺艾尔',
            '胡桃',
            '宵宫',
            '魈',
            '神里绫华',
        ]:
            dmg_type = char_element_dmg_type
        elif char.weapon_type == '弓':
            if char.attack_type in ['B', 'E', 'Q']:
                dmg_type = char_element_dmg_type
        else:
            if char.attack_type in ['E', 'Q']:
                dmg_type = char_element_dmg_type

        if char.power_name in [
            'Q光降之剑基础伤害',
            'Q光降之剑基础伤害(13层)',
            'Q每层能量伤害',
            'Q光降之剑基础伤害(24层)',
        ]:
            dmg_type = Element.Physical

        if '段' in char.power_name and 'A' not in char.power_name:
            dmg_type = char_element_dmg_type

        if char.char_name == '辛焱' and char.power_name == 'Q伤害':
            dmg_type = Element.Physical

        return dmg_type

    # 计算倍率
    async def get_power(self, char: Character) -> Power:
        # 按照ABCEQ等级查找倍率
        power_name = char.power_name
        real_prop = char.real_prop
        power_list = char.power_list
        power_level = int(real_prop[f'{power_name[0]}_skill_level'])

        # 拿到倍率
        power = power_list[power_name]['value'][power_level - 1]
        # 计算是否多次伤害
        power_plus = power_list[power_name]['plus']

        if char.char_name == '宵宫' and power_name == 'A一段伤害':
            power_plus = 1

        # 拿到百分比和固定值,百分比为float,形如2.2 也就是202%
        power_percent, power_value = await p2v(power, power_plus)

        # 额外加成,目前有雷神和优菈
        if char.extra_effect and power_name in char.extra_effect:
            power_percent += char.extra_effect[power_name]

        return Power(
            name=power_name,
            level=power_level,
            percent=power_percent,
            value=power_value,
            plus=power_plus,
            raw=power,
        )

    # 额外加成和抗性计算
    async def get_new_fight_prop(self, char: Character) -> Dict:
        # 抗性传达
        if char.enemy_debuff:
            for effect in char.enemy_debuff:
                await self.enemy.update_resist(effect)
            char.enemy_debuff = []

        # 特殊buff计算
        effect_list = []
        if '前台' in char.power_list[char.power_name]['name']:
            if char.char_name == '纳西妲':
                em = char.fight_prop[f'{char.attack_type}_elementalMastery']
                effect = f'''elementalMastery+
                {0.25 * em if 0.25 * em <= 250 else 250}
                '''.strip()
                effect_list.append(effect)

        if '丰穰之核' in char.power_name and char.fight_prop['hp'] >= 30000:
            ex_add = ((char.fight_prop['hp'] - 30000) / 1000) * 9
            if ex_add >= 400:
                ex_add = 400
            effect = f'a+{ex_add}'
            effect_list.append(effect)

        if effect_list:
            char.real_prop = await char.get_effect_prop(
                deepcopy(char.fight_prop), effect_list, char.char_name
            )
            return char.real_prop
        else:
            char.real_prop = char.fight_prop

        return char.real_prop

    # 治疗值加成
    async def get_add_heal(self, char: Character) -> float:
        add_heal: float = char.real_prop[f'{char.attack_type}_addHeal']
        return add_heal

    # 增幅反应
    async def get_amplify_dmg(self, char: Character) -> float:
        # 计算元素反应 增幅
        em_cal = char.real_prop[f'{char.attack_type}_elementalMastery']
        for reaction in ['蒸发', '融化']:
            if reaction in char.power_list[char.power_name]['name']:
                if reaction == '蒸发':
                    if char.char_element == 'Pyro':
                        k = 1.5
                    else:
                        k = 2
                else:
                    if char.char_element == 'Pyro':
                        k = 2
                    else:
                        k = 1.5
                reaction_add_dmg = k * (
                    1 + (2.78 * em_cal) / (em_cal + 1400) + char.real_prop['a']
                )
                break
        else:
            reaction_add_dmg = 1
        return reaction_add_dmg

    # 激化反应
    async def get_quicken_dmg(self, char: Character) -> float:
        quicken_dmg = 0
        char_level = char.char_level
        power_name = char.power_list[char.power_name]['name']
        em_cal = char.real_prop[f'{char.attack_type}_elementalMastery']
        for reaction in ['超激化', '蔓激化']:
            if reaction in power_name:
                if reaction == '超激化':
                    k = 2.3
                else:
                    k = 2.5
                power_times = 1
                if '*' in power_name:
                    power_times = float(
                        (power_name.split('*')[-1].replace(')', ''))
                    )
                quicken_dmg = (
                    k
                    * base_value_list[char_level - 1]
                    * (1 + (5 * em_cal) / (em_cal + 1200))
                ) * power_times
                break
        return quicken_dmg

    # 有效数值
    async def get_effect_prop(self, char: Character):
        # 根据type计算有效属性
        _type = char.power_list[char.power_name]['type']
        if '攻击' in _type:
            effect_prop = char.real_prop[f'{char.attack_type}_atk']
        elif '生命值' in _type:
            effect_prop = char.real_prop[f'{char.attack_type}_hp']
        elif '防御' in _type:
            effect_prop = char.real_prop[f'{char.attack_type}_def']
        else:
            effect_prop = char.real_prop[f'{char.attack_type}_atk']

        return effect_prop

    # 伤害值加成
    async def get_add_dmg(self, char: Character) -> float:
        # 计算直接增加的伤害
        add_dmg: float = char.real_prop[f'{char.attack_type}_addDmg']
        return add_dmg

    # 防御值加成
    async def get_extra_d(self, char: Character) -> float:
        # 计算直接增加的伤害
        extra_d: float = char.real_prop[f'{char.attack_type}_d']
        return extra_d

    # 防御值加成
    async def get_base_area_plus(self, char: Character) -> float:
        # 计算直接增加的伤害
        base_area_plus: float = char.real_prop[f'{char.attack_type}_baseArea']
        return base_area_plus

    # 防御值加成
    async def get_extra_ignoreD(self, char: Character) -> float:
        # 计算直接增加的伤害
        extra_ignoreD: float = char.real_prop[f'{char.attack_type}_ignoreDef']
        return extra_ignoreD

    async def get_sp_base(self, power: Power, char: Character) -> float:
        power_sp = power.raw.replace('%', '').split('+')
        power_sp = [float(x) / 100 for x in power_sp]
        real_prop = char.real_prop
        atk = real_prop['E_atk'] + char.sp.attack
        em = real_prop[f'{char.attack_type}_elementalMastery']
        base = (power_sp[0] * atk + power_sp[1] * em) * power.plus
        return base

    # 基础乘区
    async def get_base_area(self, char: Character) -> float:
        # 获得该次伤害的倍率信息
        power = await self.get_power(char)
        # 获得激化乘区的信息
        reaction_power = await self.get_quicken_dmg(char)
        # 获得该次伤害的有效属性
        effect_prop = await self.get_effect_prop(char)
        # 获得伤害提高值的信息
        add_dmg = await self.get_add_dmg(char)

        base_area_plus = await self.get_base_area_plus(char)

        # 对草神进行特殊计算
        if '灭净三业' in power.name or '业障除' in power.name:
            base = await self.get_sp_base(power, char)
        elif char.char_name == '艾尔海森' and power.name.startswith('E'):
            base = await self.get_sp_base(power, char)
        else:
            base = effect_prop * power.percent + power.value

        if char.char_name == '珊瑚宫心海':
            hp = char.real_prop['hp']
            hb = char.real_prop['healBonus']
            add_dmg += 0.15 * hp * hb

        # 基本乘区 = 有效数值(例如攻击力) * 倍率 + 固定值 + 激化区 + 额外加成值 + 特殊加成值
        base_area = base + reaction_power + add_dmg + char.sp.addDmg
        if base_area_plus != 1:
            base_area_plus -= 1
            base_area = base_area_plus * base_area
        return base_area

    # 聚变反应
    async def get_transform_dmg(
        self, char: Character
    ) -> Tuple[float, float, float]:
        em = char.real_prop[f'{char.attack_type}_elementalMastery']
        is_crit = False
        if '绽放)' in char.power_name:
            # 获取激变反应基数
            if '烈绽放' in char.power_name:
                dmg_type = Element.Pyro
                base_time = 6
            elif '超绽放' in char.power_name:
                dmg_type = Element.Dendro
                base_time = 6
            else:
                dmg_type = Element.Dendro
                base_time = 4
            base_area = (
                base_value_list[char.char_level - 1]
                * base_time
                * (1 + (16.0 * em) / (em + 2000) + char.real_prop['a'])
            )
            is_crit = True
        elif '扩散伤害' in char.power_name:
            dmg_type = Element.Anemo
            base_area = (
                base_value_list[char.char_level - 1]
                * 1.2
                * (1 + (16.0 * em) / (em + 2000) + char.real_prop['a'])
                * (1 + char.real_prop['g'] / 100)
            )
        else:
            dmg_type = Element.Physical
            base_area = 0

        # 获得这次攻击的减伤乘区(抗性区+防御区)
        logger.debug(self.enemy.__dict__)
        proof = await self.enemy.get_resist(dmg_type)

        normal_dmg = base_area * proof
        if is_crit:
            crit_dmg = normal_dmg * 2
            avg_dmg = normal_dmg * 1.2
        else:
            crit_dmg = avg_dmg = 0
        return normal_dmg, avg_dmg, crit_dmg

    async def get_heal(self, char: Character) -> Tuple[float, float, float]:
        # 获得治疗增加值
        add_heal = await self.get_add_heal(char)
        # 获得治疗倍率
        power = await self.get_power(char)
        # 获得该次治疗的有效属性
        effect_prop = await self.get_effect_prop(char)
        heal_bonus = 1 + char.real_prop['healBonus']
        base_area = effect_prop * power.percent + power.value + add_heal
        normal_value = base_area * heal_bonus
        return normal_value, normal_value, 0

    async def get_shield(self, char: Character) -> Tuple[float, float, float]:
        # 获得护盾倍率
        power = await self.get_power(char)
        # 获得该次护盾的有效属性
        effect_prop = await self.get_effect_prop(char)
        shield_bonus = 1 + char.real_prop['shieldBonus']
        base_area = effect_prop * power.percent + power.value
        normal_value = base_area * shield_bonus
        return normal_value, 0, 0

    async def get_dmg(
        self,
        char: Character,
        dmg_type: Element,
        is_single: bool = False,
    ) -> Tuple[float, float, float]:
        # 获得基础乘区(攻击区+倍率区+激化区)
        base_area = await self.get_base_area(char)
        # 获得这次攻击的减伤乘区(抗性区+防御区)
        d = await self.get_extra_d(char)
        i_d = await self.get_extra_ignoreD(char)
        # logger.debug(self.enemy.__dict__)
        proof = await self.enemy.get_dmg_proof(dmg_type, d, i_d)
        # 获得这次攻击的增幅乘区
        _char = char if is_single else None
        reactio = await self.enemy.get_dmg_reaction(dmg_type, _char)

        if dmg_type == Element.Physical:
            _dmgBonus = char.real_prop[f'{char.attack_type}_physicalDmgBonus']
        else:
            _dmgBonus = char.real_prop[f'{char.attack_type}_dmgBonus']
        critrate = char.real_prop[f'{char.attack_type}_critRate']
        critdmg = char.real_prop[f'{char.attack_type}_critDmg']
        dmgBonus = _dmgBonus + char.sp.dmgBonus

        # 基础乘区 = 攻击*倍率+激化
        # 普通伤害 = 基础 * 增伤区 * 增幅区 * 抗性区
        normal_dmg = base_area * (1 + dmgBonus) * reactio * proof
        # 暴击伤害 = 普通伤害 * 暴击区
        crit_dmg = normal_dmg * (1 + critdmg)
        # 平均伤害
        avg_dmg = (
            normal_dmg
            if critrate < 0
            else crit_dmg
            if critrate > 1
            else crit_dmg * critrate + (1 - critrate) * normal_dmg
        )

        self.total_normal_dmg += normal_dmg
        self.total_avg_dmg += avg_dmg
        self.total_crit_dmg += crit_dmg

        return normal_dmg, avg_dmg, crit_dmg


async def p2v(power: str, power_plus: float) -> Tuple[float, float]:
    """
    将power转换为value
    """
    if '+' in power:
        power_percent = (
            float(power.split('+')[0].replace('%', '')) / 100
        ) * power_plus
        power_value = power.split('+')[1]
        if '%' in power_value:
            power_percent += (
                float(power_value.replace('%', '')) / 100 * power_plus
            )
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

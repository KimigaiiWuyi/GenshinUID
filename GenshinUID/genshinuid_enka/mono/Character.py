from copy import deepcopy
from typing import Dict, List, Tuple, Optional

from httpx import ConnectTimeout
from gsuid_core.logger import logger
from gsuid_core.utils.api.minigg.request import (
    get_weapon_info,
    get_weapon_stats,
    get_character_info,
    get_character_stats,
)

from .Power import sp_prop
from ..etc.beta_weapon import beta_weapons
from ..etc.get_buff_list import get_buff_list
from ...genshinuid_config.gs_config import gsconfig
from ..etc.status_change import EXTRA_CHAR_LIST, STATUS_CHAR_LIST
from ..etc.MAP_PATH import ActionMAP, char_action, avatarName2SkillAdd
from ...utils.map.GS_MAP_PATH import avatarName2Weapon, avatarName2Element
from ...utils.map.name_covert import name_to_avatar_id, avatar_id_to_char_star
from ...utils.ambr_to_minigg import (
    convert_ambr_to_minigg,
    convert_ambr_to_weapon,
)
from ..etc.base_info import (
    ATTR_MAP,
    ELEMENT_MAP,
    ICON_ELEMENT,
    PERCENT_ATTR,
    baseFightProp,
    baseWeaponInfo,
)

CHANGE_LIST = [
    '荒泷一斗',
    '刻晴',
    '诺艾尔',
    '胡桃',
    '宵宫',
    '魈',
    '神里绫华',
    '阿蕾奇诺',
]


class Character:
    def __init__(self, card_prop: Dict):
        # 面板数据
        self.card_prop: Dict = card_prop
        # 无命座效果
        self.without_talent_card = card_prop
        # 战斗数据
        self.fight_prop: Dict[str, float] = {}
        # 战斗数据
        self.without_talent_fight: Dict[str, float] = {}
        # 实时数据
        self.real_prop: Dict[str, float] = {}

        # 角色等级,名称,元素,武器类型
        self.char_level: int = int(card_prop['avatarLevel'])
        self.char_id: str = '10000029'
        self.char_name: str = card_prop['avatarName']
        self.char_element = self.card_prop['avatarElement']
        self.char_fetter = self.card_prop['avatarFetter']
        self.char_talent: int = len(self.card_prop['talentList'])
        self.weapon_type = self.card_prop['weaponInfo']['weaponType']
        self.char_bytes: Optional[bytes] = None
        self.rarity: str = '4'

        self.power_name: str = ''
        self.attack_type: str = ''

        # 角色的圣遗物总分
        self.artifacts_all_score: float = 0
        self.percent: str = '0.0'
        self.dmg_data: Dict = {}
        self.seq_str: str = '无匹配'

        # 特殊
        self.sp_list: List = []
        self.sp: sp_prop = sp_prop()
        self.extra_effect: Dict = {}

        self.time: float = 0
        self.buff: List = []
        self.enemy_debuff: List = []
        self.power_list: Dict[str, ActionMAP] = {}

        # 处理旅行者
        self.s_char_name = self.char_name
        if self.char_name == '旅行者':
            for element in ELEMENT_MAP:
                if self.char_element == ELEMENT_MAP[element]:
                    self.s_char_name += f'({element})'
                    break

    async def new(
        self,
        weapon: Optional[str] = None,
        weapon_affix: Optional[int] = None,
        talent_num: Optional[int] = None,
    ):
        '''
        <初始化角色 - 1>

        <新生成角色的基础属性>
          如果要替换武器也在这边进行处理

        参数：
            weapon: `Optional[str]`
                武器名称(fake)
            weapon_affix: `Optional[int]`
                武器精炼次数(fake)
            talent_num: `Optional[int]`
                命座数量(fake)
        '''
        if not gsconfig.get_config('OldPanle').data:
            self.card_prop = await self.get_card_prop(
                weapon, weapon_affix, talent_num
            )
        if self.card_prop == {}:
            return '要替换的武器不正确或发生了未知错误~'
        self.baseHp = self.card_prop['avatarFightProp']['baseHp']
        self.baseAtk = self.card_prop['avatarFightProp']['baseAtk']
        self.baseDef = self.card_prop['avatarFightProp']['baseDef']
        self.rarity = await avatar_id_to_char_star(
            str(self.card_prop['avatarId'])
        )
        self.char_id = await name_to_avatar_id(self.char_name)

    async def get_card_prop(
        self,
        weapon: Optional[str] = None,
        weapon_affix: Optional[int] = None,
        talent_num: Optional[int] = None,
    ) -> dict:
        # 创造一个假武器
        if weapon:
            weapon_info = deepcopy(baseWeaponInfo)
            try:
                weapon_raw_data = await get_weapon_info(weapon)
            except ConnectTimeout:
                weapon_raw_data = -1
            if isinstance(weapon_raw_data, int) or isinstance(
                weapon_raw_data, List
            ):
                if weapon in beta_weapons:
                    weapon_id = beta_weapons[weapon]
                else:
                    return {}
                weapon_raw_data = await convert_ambr_to_weapon(weapon_id)
                if not weapon_raw_data:
                    return {}
                else:
                    weapon_info['weaponStar'] = int(weapon_raw_data['rarity'])
                    weapon_level_data = weapon_raw_data
                    weapon_info['weaponLevel'] = 90
                    weapon_info['promoteLevel'] = 6
            else:
                weapon_info['weaponStar'] = int(weapon_raw_data['rarity'])
                if weapon_info['weaponStar'] >= 3:
                    weapon_level_data = await get_weapon_stats(weapon, 90)
                    weapon_info['weaponLevel'] = 90
                    weapon_info['promoteLevel'] = 6
                else:
                    weapon_level_data = await get_weapon_stats(weapon, 70)
                    weapon_info['weaponLevel'] = 70
                    weapon_info['promoteLevel'] = 4
                if isinstance(weapon_level_data, int) or isinstance(
                    weapon_level_data, List
                ):
                    return {}
            weapon_info['weaponName'] = weapon_raw_data['name']
            if weapon_affix is None:
                if weapon_info['weaponStar'] >= 5:
                    weapon_info['weaponAffix'] = 1
                else:
                    weapon_info['weaponAffix'] = 5
            else:
                weapon_info['weaponAffix'] = weapon_affix
            weapon_info['weaponStats'][0]['statValue'] = round(
                weapon_level_data['attack']
            )
            if weapon_raw_data['mainStatText'] != '':
                weapon_info['weaponStats'][1]['statName'] = weapon_raw_data[
                    'mainStatText'
                ]
                if weapon_raw_data['mainStatText'] == '元素精通':
                    fake_value = round(weapon_level_data['specialized'])
                else:
                    fake_value = float(
                        '{:.2f}'.format(weapon_level_data['specialized'] * 100)
                    )
                weapon_info['weaponStats'][1]['statValue'] = fake_value

            if 'effect' in weapon_raw_data:
                weapon_info['weaponEffect'] = weapon_raw_data['effect'].format(
                    *weapon_raw_data[
                        'r{}'.format(str(weapon_info['weaponAffix']))
                    ]
                )
            else:
                weapon_info['weaponEffect'] = '无特效。'
            weapon_info['weaponType'] = weapon_raw_data['weaponText']
            self.card_prop['weaponInfo'] = weapon_info

        # 修改假命座:

        if self.s_char_name.startswith('旅行者'):
            icon_name = f'Player{ICON_ELEMENT[self.s_char_name[-2]]}'
        else:
            icon_name = self.card_prop['avatarEnName']

        if talent_num is None:
            talent_num = len(self.card_prop['talentList'])

        if talent_num or talent_num == 0:
            talent_list = []
            for i in range(1, talent_num + 1):
                talent_list.append(
                    {
                        'talentId': 300 + i,
                        'talentName': f'FakeTalent{i}',
                        'talentIcon': f'UI_Talent_S_{icon_name}_0{i}',
                    }
                )
            self.card_prop['talentList'] = talent_list

        fight_prop = await self.get_base_prop(self.char_name, self.char_level)
        self.card_prop['avatarFightProp'] = fight_prop

        self.without_talent_card = self.card_prop
        # 计算圣遗物效果
        all_effects = await get_artifacts_value(self.card_prop)
        part_effects = deepcopy(all_effects)

        all_effects.extend(await get_buff_list(self.card_prop, 'normal'))
        part_effects.extend(
            await get_buff_list(self.card_prop, 'normal', False)
        )

        fight_prop_part = await self.get_effect_prop(
            deepcopy(fight_prop), part_effects, self.char_name
        )
        fight_prop_all = await self.get_effect_prop(
            deepcopy(fight_prop), all_effects, self.char_name
        )

        self.card_prop['avatarFightProp'] = fight_prop_all
        self.without_talent_card['avatarFightProp'] = fight_prop_part
        return self.card_prop

    async def get_base_prop(self, char_name: str, char_level: int) -> Dict:
        # 武器基本属
        weapon_atk = self.card_prop['weaponInfo']['weaponStats'][0][
            'statValue'
        ]
        if len(self.card_prop['weaponInfo']['weaponStats']) > 1:
            weapon_sub = self.card_prop['weaponInfo']['weaponStats'][1][
                'statName'
            ]
            weapon_sub_val = self.card_prop['weaponInfo']['weaponStats'][1][
                'statValue'
            ]
        else:
            weapon_sub = ''
            weapon_sub_val = 0

        fight_prop = deepcopy(baseFightProp)
        if '珊瑚宫心海' == char_name:
            fight_prop['critRate'] -= 1.0
            fight_prop['healBonus'] += 0.25

        char_name_covert = char_name
        if char_name == '旅行者':
            char_name_covert = '荧'

        self.char_id = await name_to_avatar_id(char_name_covert)
        try:
            char_raw = await get_character_info(name=char_name_covert)
        except:  # noqa: E722
            char_raw = -1

        if not self.char_id and char_name != '旅行者':
            return {}
        if isinstance(char_raw, int) or isinstance(char_raw, List):
            char_raw = char_data = await convert_ambr_to_minigg(self.char_id)
        else:
            char_data = await get_character_stats(char_name_covert, char_level)

        if (
            isinstance(char_data, List)
            or isinstance(char_data, int)
            or char_data is None
        ):
            return {}

        fight_prop['baseHp'] = char_data['hp']
        fight_prop['baseAtk'] = char_data['attack'] + weapon_atk
        fight_prop['baseDef'] = char_data['defense']
        fight_prop['exHp'] = 0
        fight_prop['exAtk'] = 0
        fight_prop['exDef'] = 0

        # 计算突破加成
        if isinstance(char_raw, dict):
            for attr in ATTR_MAP:
                if attr in char_raw['substatText']:
                    sp = char_data['specialized']
                    if attr == '暴击伤害':
                        sp -= 0.5
                    elif attr == '暴击率':
                        sp -= 0.05
                    fight_prop[ATTR_MAP[attr]] += sp
                if attr in weapon_sub:
                    if attr == '元素精通':
                        weapon_sub_val *= 100
                    fight_prop[ATTR_MAP[attr]] += weapon_sub_val / 100
        else:
            return {}

        return fight_prop

    async def init_prop(self):
        '''
        <初始化角色 - 2>

        生成角色的战斗属性和毕业度
        '''
        await self.get_fight_prop()

    async def get_effect_prop(
        self,
        prop: dict,
        effect_list: List[str],
        char_name: str,
    ) -> dict:
        logger.debug(effect_list)
        if 'A_d' not in prop:
            for attr in [
                'shieldBonus',
                'addDmg',
                'addHeal',
                'ignoreDef',
                'd',
                'g',
                'a',
            ]:
                prop[attr] = 0
            prop['k'] = 1
            prop['sp'] = []
            prop['baseArea'] = 1
            prop['powerPlus'] = 1
            if prop['baseHp'] + prop['addHp'] == prop['hp']:
                prop['exHp'] = prop['addHp']
                prop['exAtk'] = prop['addAtk']
                prop['exDef'] = prop['addDef']
                prop['addHp'] = 0
                prop['addAtk'] = 0
                prop['addDef'] = 0

            # 给每个技能 分别添加上属性
            for prop_attr in deepcopy(prop):
                for prop_limit in ['A', 'B', 'C', 'E', 'Q']:
                    prop[f'{prop_limit}_{prop_attr}'] = prop[prop_attr]

            weapon_type = avatarName2Weapon[char_name]

            # 计算角色伤害加成应该使用什么
            for prop_limit in ['A', 'B', 'C', 'E', 'Q']:
                if weapon_type == '法器' or char_name in CHANGE_LIST:
                    prop['{}_dmgBonus'.format(prop_limit)] = prop['dmgBonus']
                elif weapon_type == '弓':
                    if prop_limit in ['A', 'C']:
                        prop['{}_dmgBonus'.format(prop_limit)] = prop[
                            'physicalDmgBonus'
                        ]
                    elif prop_limit in ['B', 'E', 'Q']:
                        prop['{}_dmgBonus'.format(prop_limit)] = prop[
                            'dmgBonus'
                        ]
                else:
                    if prop_limit in ['A', 'B', 'C']:
                        prop['{}_dmgBonus'.format(prop_limit)] = prop[
                            'physicalDmgBonus'
                        ]
                    elif prop_limit in ['E', 'Q']:
                        prop['{}_dmgBonus'.format(prop_limit)] = prop[
                            'dmgBonus'
                        ]

        # 防止复数效果
        with_trans_effect: List[str] = []
        without_trans_effect: List[str] = []
        for effect in effect_list:
            if ';' in effect:
                effect = effect.split(';')
            else:
                effect = [effect]

            for _effect in effect:
                if _effect == '':
                    continue
                else:
                    if '%' in _effect:
                        with_trans_effect.append(_effect)
                    else:
                        without_trans_effect.append(_effect)

        new_effect_list: List[str] = without_trans_effect + with_trans_effect

        # 建立一份基于基础属性的effect_list, 确保hp,atk,def有正确的值
        base_effect_list: List[List] = []
        # 正式开始计算
        for effect in new_effect_list:
            if 'Resist' in effect:
                self.enemy_debuff.append(effect)
                continue
            else:
                self.buff.append(effect)
            # 分割效果
            # 例如:Q:dmgBonus+96%27%em
            # 分割后:
            # effect_limit = Q
            effect_limit = ''
            if ':' in effect:
                effect_limit = effect.split(':')[0]
                effect = effect.split(':')[1]

            effect_attr, effect_value = effect.split('+')
            effect_max = 9999999
            effect_base: str = ''

            # 判断effect_value中有几个百分号
            p_count = effect_value.count('%')
            # 如果有%,则认为是基于值的提升
            base_check = True
            if p_count >= 2:
                effect_max, effect_value, effect_base = effect_value.split('%')
            elif p_count == 1:
                effect_value, effect_base = effect_value.split('%')
            else:
                base_check = False

            # effect_attr, effect_value, effect_base, effect_max
            # dmgBonus, 27, em, 96

            # 暂时不处理extraDmg
            if effect_attr == 'extraDmg':
                continue

            effect_max = float(effect_max) / 100
            # 如果要增加的属性不是em元素精通,那么都要除于100
            if effect_attr not in [
                'exHp',
                'exAtk',
                'exDef',
                'elementalMastery',
            ]:
                # 正常除100
                effect_value = float(effect_value) / 100
            # 元素精通则为正常值
            else:
                if effect_base in ['hp', 'elementalMastery', 'def']:
                    effect_value = float(effect_value) / 100
                else:
                    effect_value = float(effect_value)

            # 如果属性是血量,攻击,防御值,并且是按照%增加的,那么增加值应为百分比乘上基础值
            if base_check:
                if effect_base in ['hp', 'atk', 'def']:
                    base_effect_list.append(
                        [effect_limit, effect_attr, effect_value, effect_base]
                    )
                    continue

                if effect_base == 'energyRecharge':
                    if effect_attr in PERCENT_ATTR:
                        effect_base_value = prop[effect_base] - 1
                    else:
                        effect_base_value = (prop[effect_base] - 1) / 100

                elif effect_base == 'energyrecharge':
                    effect_base = 'energyRecharge'
                    if effect_attr in PERCENT_ATTR:
                        effect_base_value = prop[effect_base]
                    else:
                        effect_base_value = prop[effect_base] / 100

                elif effect_base == 'elementalMastery':
                    # 针对草神的
                    if char_name == '纳西妲' and effect_attr == 'dmgBonus':
                        effect_base_value = (prop[effect_base] - 200) / 100
                    else:
                        effect_base_value = prop[effect_base]
                else:
                    effect_base_value = prop[effect_base]
                effect_value = effect_value * effect_base_value

            # 判断是否超过上限,超过则使用上限值
            if effect_value >= effect_max:
                effect_value = effect_max

            if char_name == '旅行者':
                char_element = 'Hydro'
            else:
                char_element = avatarName2Element[char_name]

            # 判断是否是自己属性的叠加
            if 'DmgBonus' in effect_attr:
                if effect_attr.replace('DmgBonus', '') == char_element:
                    effect_attr = 'dmgBonus'
                elif effect_attr == 'physicalDmgBonus':
                    effect_attr = 'physicalDmgBonus'
                else:
                    continue

            # 如果效果有限制条件
            prop = await self.get_buff_value(
                prop,
                effect_limit,
                effect_attr,
                effect_value,
                effect_base,
                False,
            )

        prop = await self.get_base_value(prop)

        # 重新计算加成值
        # base_effect_list = [
        #   [limit_list, effect_attr, effect_value,effect_base]
        # ]
        for effect in base_effect_list:
            prop = await self.get_buff_value(prop, *effect)

        prop = await self.get_base_value(prop)
        logger.debug(prop)
        return prop

    async def get_base_value(self, prop: Dict) -> Dict:
        prop['hp'] = (prop['addHp'] + 1) * prop['baseHp'] + prop['exHp']
        prop['atk'] = (prop['addAtk'] + 1) * prop['baseAtk'] + prop['exAtk']
        prop['def'] = (prop['addDef'] + 1) * prop['baseDef'] + prop['exDef']
        for prop_limit in ['A', 'B', 'C', 'E', 'Q']:
            for attr in ['hp', 'atk', 'def']:
                attr_up = attr[0].upper() + attr[1:]
                prop[f'{prop_limit}_{attr}'] = (
                    prop[f'{prop_limit}_add{attr_up}'] + 1
                ) * prop[f'base{attr_up}'] + prop[f'ex{attr_up}']
        return prop

    async def get_buff_value(
        self,
        prop: Dict,
        effect_limit: Optional[str],
        effect_attr: str,
        effect_value: float,
        effect_base: Optional[str] = None,
        is_calc_base: Optional[bool] = True,
    ) -> Dict:
        if effect_base and is_calc_base:
            effect_value = prop[effect_base] * effect_value
        if effect_limit:
            # 如果限制条件为中文,则为特殊label才生效
            if '\u4e00' <= effect_limit[-1] <= '\u9fff':
                prop['sp'].append(
                    {
                        'effect_name': effect_limit,
                        'effect_attr': effect_attr,
                        'effect_value': effect_value,
                    }
                )
            # 如果限制条件为英文,例如Q,则为Q才生效
            else:
                # 形如ABC:dmgBonus+75,则遍历ABC,增加值
                for limit in effect_limit:
                    prop['{}_{}'.format(limit, effect_attr)] += effect_value
        else:
            if effect_attr in ['a', 'addDmg']:
                pass
            else:
                for attr in ['A', 'B', 'C', 'E', 'Q']:
                    prop[f'{attr}_{effect_attr}'] += effect_value
            prop[f'{effect_attr}'] += effect_value

        logger.debug(f'{effect_attr} + {effect_value} 基于[{effect_base}]')

        return prop

    async def get_fight_prop(self) -> Dict:
        '''
        生成角色的倍率表

        返回:
            self.fight_prop
        '''
        # 拿到倍率表
        if self.s_char_name not in char_action:
            self.power_list = {}
        else:
            self.power_list = char_action[self.s_char_name]
            # 额外增加钟离倍率
            if self.char_name == '钟离':
                self.power_list['E总护盾量'] = {
                    'name': 'E总护盾量',
                    'type': '生命值',
                    'plus': 1.5,
                    'value': [
                        f'{self.power_list["E护盾附加吸收量"]["value"][index]}+{i}'
                        for index, i in enumerate(
                            self.power_list['E护盾基础吸收量']['value']
                        )
                    ],
                }
            elif self.char_name == '赛诺':
                for power_name in ['E渡荒之雷', 'E渡荒之雷(超激化)']:
                    self.power_list[power_name] = {
                        'name': power_name,
                        'type': '攻击力',
                        'plus': 1,
                        'value': ['100%'] * 15,
                    }
            elif self.char_name == '纳西妲':
                for power_name in [
                    'E业障除(前台)',
                    'E业障除(蔓激化·前台)',
                ]:
                    self.power_list[power_name] = {
                        'name': power_name,
                        'type': '攻击力',
                        'plus': 1,
                        'value': ['200%+400%'] * 15,
                    }
            elif self.char_name == '甘雨':
                for power_name in [
                    'A霜华矢两段伤害',
                    'A霜华矢两段伤害(融化)',
                ]:
                    val = []

                    for index, i in enumerate(
                        self.power_list['A霜华矢命中伤害']['value']
                    ):
                        zf = self.power_list['A霜华矢·霜华绽发伤害']
                        v2 = int(zf['value'][index][:-1])
                        v1 = int(i[:-1])
                        val.append(f'{v1 + v2}%')

                    self.power_list[power_name] = {
                        'name': power_name,
                        'type': '攻击力',
                        'plus': 1,
                        'value': val,
                    }

        # 获取值
        skillList = self.card_prop['avatarSkill']
        prop = deepcopy(self.card_prop['avatarFightProp'])
        prop['A_skill_level'] = skillList[0]['skillLevel']
        prop['E_skill_level'] = skillList[1]['skillLevel']
        prop['Q_skill_level'] = skillList[-1]['skillLevel']

        if self.char_name in avatarName2SkillAdd:
            skill_add = avatarName2SkillAdd[self.char_name]
        else:
            skill_add = ['E', 'Q']
        for skillAdd_index in range(0, 2):
            if len(self.card_prop['talentList']) >= 3 + skillAdd_index * 2:
                if skill_add[skillAdd_index] == 'E':
                    prop['E_skill_level'] += 3
                elif skill_add[skillAdd_index] == 'Q':
                    prop['Q_skill_level'] += 3

        prop = await self.get_effect_prop(prop, [], self.char_name)
        all_effect = await get_buff_list(self.card_prop, 'fight')
        part_effect = await get_buff_list(self.card_prop, 'fight', False)

        ex_effect = []
        # 开启效果
        if self.char_name in STATUS_CHAR_LIST:
            for skill_effect in STATUS_CHAR_LIST[self.char_name]:
                skill_level = (
                    prop[f'{skill_effect["name"][0]}_skill_level'] - 1
                )
                skill_value = skill_effect['value'][skill_level]
                plus = skill_effect['plus']
                if isinstance(skill_value, float):
                    skill_value = '{:.4f}%'.format(skill_value * 100 * plus)
                skill: str = skill_effect['effect'].format(skill_value)
                if skill.endswith('%'):
                    skill = skill[:-1]
                ex_effect.append(skill)

        # 特殊效果,目前有雷神满愿力
        if self.char_name in EXTRA_CHAR_LIST:
            if self.char_name == '雷电将军':
                skill1 = EXTRA_CHAR_LIST[self.char_name]['Q愿力加成']['value']
                skill2 = EXTRA_CHAR_LIST[self.char_name]['Q伤害提升']['value']
                attack_type = 'Q'
                skill_level = prop[f'{attack_type}_skill_level'] - 1

                value_1 = float(skill1[skill_level].split('+')[0])
                value_1 *= 0.6
                value_2 = float(skill1[skill_level].split('+')[1])
                value_2 *= 0.6
                value_3 = skill2[skill_level] * 90
                ex_effect.append((f'Q梦想一刀基础伤害:dmgBonus+{value_3}'))
                self.extra_effect = {
                    'Q梦想一刀基础伤害(满愿力)': value_1,
                    'Q一段伤害(满愿力)': value_2,
                    'Q重击伤害(满愿力)': value_2,
                    'Q高空下落伤害(满愿力)': value_2,
                }
                if self.card_prop['weaponInfo']['weaponName'] == '薙草之稻光':
                    weaponAffix = self.card_prop['weaponInfo']['weaponAffix']
                    _ex = 10 + weaponAffix * 2
                    ex_effect.append(f'Q:dmgBonus+{_ex}')
            elif self.char_name == '优菈':
                skill_effect = EXTRA_CHAR_LIST[self.char_name][
                    'Q每层能量伤害'
                ]['value']
                attack_type = 'Q'
                skill_level = prop[f'{attack_type}_skill_level'] - 1
                value = float(skill_effect[skill_level])
                self.extra_effect = {
                    'Q光降之剑基础伤害(13层)': value * 13,
                    'Q光降之剑基础伤害(24层)': value * 24,
                }
            elif self.char_name == '纳西妲':
                self.char_talent = len(self.card_prop['talentList'])
                if self.char_talent >= 1:
                    char_talent = 1
                else:
                    char_talent = 0
                skill_effect = EXTRA_CHAR_LIST[self.char_name][
                    f'E灭净三业伤害提升{char_talent}'
                ]['value']
                attack_type = 'E'
                skill_level = prop[f'{attack_type}_skill_level'] - 1
                value = float(skill_effect[skill_level])
                ex_effect.append((f'前台:dmgBonus+{value*100}'))

        # 在计算buff前, 引入特殊效果
        if self.char_name == '雷电将军':
            ex_effect.append('Q:dmgBonus+27')
        elif self.char_name == '钟离':
            ex_effect.append('AnemoResist+-20;PhysicalResist+-20')
            ex_effect.append('CryoResist+-20;DendroResist+-20')
            ex_effect.append('ElectroResist+-20;HydroResist+-20')
            ex_effect.append('PyroResist+-20;GeoResist+-20')
        elif self.char_name == '妮露':
            ex_effect.append('addHp+25')
            ex_effect.append('elementalMastery+80')

        all_effect.extend(ex_effect)
        part_effect.extend(ex_effect)

        # 计算全部的buff，添加入属性
        self.fight_prop = await self.get_effect_prop(
            deepcopy(prop), all_effect, self.char_name
        )

        if self.rarity != '5' and self.char_name != '香菱':
            self.without_talent_fight = self.fight_prop
        else:
            if self.char_name == '香菱':
                part_effect.append('exAtk+1202')
            self.without_talent_fight = await self.get_effect_prop(
                deepcopy(prop), part_effect, self.char_name
            )
        return self.fight_prop

    async def get_sp_fight_prop(self, power_name: str) -> sp_prop:
        '''
        获得角色的特殊状态战斗加成

        返回:
            self.sp: `sp_prop`
        '''
        self.sp = sp_prop()
        for sp_single in self.fight_prop['sp']:  # type:ignore
            if sp_single['effect_name'] in power_name:
                if sp_single['effect_attr'] == 'dmgBonus':
                    self.sp.dmgBonus += sp_single['effect_value']
                elif sp_single['effect_attr'] == 'addDmg':
                    self.sp.addDmg += sp_single['effect_value']
                elif sp_single['effect_attr'] == 'atk':
                    self.sp.attack += sp_single['effect_value']
                else:
                    self.sp.attack += sp_single['effect_value']
        return self.sp

    async def get_attack_type(self, power_name: str) -> str:
        '''
        获得角色的当前攻击类型

        参数:
            power_name: `str`
        返回:
            self.attack_type: `Literal['A','B','C','E','Q']`
        '''
        # 攻击类型ABCEQ应为label首位
        self.attack_type = power_name[0]
        # 如果是雷电将军, 则就按首位,因为Q的几段伤害均视为元素爆发
        if self.char_name == '雷电将军':
            pass
        else:
            # 重击或瞄准射击在label内,则视为B重击伤害,例如公子E内的重击伤害,不视为E伤害,而是B伤害
            if '重击' in power_name or '瞄准射击' in power_name:
                self.attack_type = 'B'
            # 特殊重击类型,例如甘雨和夜兰
            elif (
                '破局矢' in power_name
                or '霜华矢' in power_name
                or '藏蕴花矢' in power_name
                or '花筥箭' in power_name
                or '刀风界' in power_name
            ):
                self.attack_type = 'B'
            # 下落伤害类型,例如魈
            elif '高空下落' in power_name:
                self.attack_type = 'C'
            # 一段伤害, 二段伤害等等 应视为A伤害
            elif '段' in power_name and '伤害' in power_name:
                self.attack_type = 'A'
            elif '不生断' in power_name:
                self.attack_type = 'A'
        return self.attack_type

    async def update(self, time):
        self.time += time
        # TODO 遍历buff列表, 超过时间的移除


async def p2v(power: str, power_plus: int) -> Tuple[float, float]:
    """
    将power转换为value
    """
    # 如果存在123%+123%形式的
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


async def get_artifacts_value(raw_data: Dict) -> List[str]:
    # 计算圣遗物效果
    all_effects = []
    for equip in raw_data['equipList']:
        statNmae = equip['reliquaryMainstat']['statName']
        statValue = equip['reliquaryMainstat']['statValue']
        all_effects.append(await text_to_effect(statNmae, statValue))
        for sub in equip['reliquarySubstats']:
            sub_name = sub['statName']
            sub_value = sub['statValue']
            all_effects.append(await text_to_effect(sub_name, sub_value))
    return all_effects


async def text_to_effect(name: str, value: float) -> str:
    str = ''
    if name == '血量':
        str = f'exHp+{value}'
    elif name == '百分比血量':
        str = f'addHp+{value}'
    elif name == '攻击力':
        str = f'exAtk+{value}'
    elif name == '百分比攻击力':
        str = f'addAtk+{value}'
    elif name == '防御力':
        str = f'exDef+{value}'
    elif name == '百分比防御力':
        str = f'addDef+{value}'
    elif name == '暴击率':
        str = f'critRate+{value}'
    elif name == '暴击伤害':
        str = f'critDmg+{value}'
    elif name == '元素精通':
        str = f'elementalMastery+{value}'
    elif name == '元素充能效率':
        str = f'energyRecharge+{value}'
    elif name == '物理伤害加成':
        str = f'physicalDmgBonus+{value}'
    elif '元素伤害加成' in name:
        str = f'{ELEMENT_MAP[name[0]]}DmgBonus+{value}'
    elif '治疗加成' in name:
        str = f'healBonus+{value}'
    return str


async def get_char(
    raw_data: dict,
    weapon: Optional[str] = None,
    weapon_affix: Optional[int] = None,
    talent_num: Optional[int] = None,
):
    char = Character(card_prop=raw_data)
    err = await char.new(
        weapon=weapon,
        weapon_affix=weapon_affix,
        talent_num=talent_num,
    )
    if isinstance(err, str):
        return err

    await char.init_prop()
    return char

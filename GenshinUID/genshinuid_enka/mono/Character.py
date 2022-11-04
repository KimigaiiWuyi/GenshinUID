from typing import Dict, List, Tuple, Union, Optional

from ..etc.etc import get_char_percent
from ..etc.prop_calc import get_card_prop
from ..dmg_calc.dmg_calc import get_fight_prop
from ...utils.db_operation.db_operation import config_check
from ..etc.MAP_PATH import char_action, avatarName2SkillAdd


class Character:
    def __init__(self, card_prop: Dict):
        # 面板数据
        self.card_prop: Dict = card_prop
        # 战斗数据
        self.fight_prop: Dict = {}

        # 角色等级,名称,元素,武器类型
        self.char_level: int = card_prop['avatarLevel']
        self.char_name: str = card_prop['avatarName']
        self.char_element = self.card_prop['avatarElement']
        self.char_fetter = self.card_prop['avatarFetter']
        self.weapon_type = self.card_prop['weaponInfo']['weaponType']
        self.char_bytes: Optional[bytes] = None

        self.power_name: str = ''
        self.attack_type: str = ''

        # 角色的圣遗物总分
        self.artifacts_all_score: float = 0
        self.percent: str = '0.0'
        self.seq_str: str = '无匹配'

        self.time: float = 0
        self.buff: List = []
        self.power_list: Dict = {}

    async def new(
        self,
        weapon: Optional[str] = None,
        weapon_affix: Optional[int] = None,
        talent_num: Optional[int] = None,
    ):
        if not await config_check('OldPanle'):
            self.card_prop = await get_card_prop(
                self.card_prop, weapon, weapon_affix, talent_num
            )
        if self.card_prop == {}:
            return '要替换的武器不正确或发生了未知错误~'
        self.baseHp = self.card_prop['avatarFightProp']['baseHp']
        self.baseAtk = self.card_prop['avatarFightProp']['baseAtk']
        self.baseDef = self.card_prop['avatarFightProp']['baseDef']

    async def init_prop(self):
        await self.get_fight_prop()
        await self.get_percent()

    async def get_percent(self):
        self.percent, seq = await get_char_percent(
            self.card_prop, self.fight_prop, self.char_name
        )
        seq_str = '·'.join([s[:2] for s in seq.split('|')]) + seq[-1:]
        if seq_str:
            self.seq_str = seq_str

    async def get_fight_prop(self):
        # 拿到倍率表
        if self.char_name not in char_action:
            self.power_list = {}
        else:
            self.power_list = char_action[self.char_name]
            # 额外增加钟离倍率
            if self.char_name == '钟离':
                self.power_list['E总护盾量'] = {
                    'name': 'E总护盾量',
                    'type': '生命值',
                    'plus': 1,
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
                for power_name in ['E灭净三业·业障除', 'E灭净三业·业障除(蔓激化)']:
                    self.power_list[power_name] = {
                        'name': power_name,
                        'type': '攻击力',
                        'plus': 1,
                        'value': ['200%+400%'] * 15,
                    }
        self.fight_prop = await get_fight_prop(self.card_prop)

    async def update(self, time):
        self.time += time
        # TODO 遍历buff列表, 超过时间的移除

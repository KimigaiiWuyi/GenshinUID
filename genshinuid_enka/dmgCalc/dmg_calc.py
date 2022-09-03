import json
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw

from ...version import Genshin_version

# 元素百分比
# 超导：扩散：感电：碎冰：超载：绽放：超绽放/烈绽放：超激化：蔓激化=1 : 1.2 : 2.4 : 3 : 4 : 4 : 6 : 2.3 : 2.5
from .base_value import base_value_list
from ...utils.genshin_fonts.genshin_fonts import genshin_font_origin

DMG_PATH = Path(__file__).parents[0]
DMG_TEXT_PATH = DMG_PATH / 'texture2d'

version = Genshin_version
avatarName2SkillAdd_fileName = f'avatarName2SkillAdd_mapping_{version}.json'

with open(DMG_PATH / avatarName2SkillAdd_fileName, "r", encoding='UTF-8') as f:
    avatarName2SkillAdd = json.load(f)

with open(DMG_PATH / 'artifacts_effect.json', "r", encoding='UTF-8') as f:
    artifacts_effect_map = json.load(f)

with open(DMG_PATH / 'weapons_effect.json', "r", encoding='UTF-8') as f:
    weapons_effect_map = json.load(f)

with open(DMG_PATH / 'char_talent_effect.json', "r", encoding='UTF-8') as f:
    char_talent_effect_map = json.load(f)

with open(DMG_PATH / 'char_skill_effect.json', "r", encoding='UTF-8') as f:
    char_skill_effect_map = json.load(f)

with open(DMG_PATH / 'dmgMap.json', "r", encoding='UTF-8') as f:
    dmgMap = json.load(f)

dmgBar_1 = Image.open(DMG_TEXT_PATH / 'dmgBar_1.png')
dmgBar_2 = Image.open(DMG_TEXT_PATH / 'dmgBar_2.png')


async def get_first_main(mainName: str) -> str:
    if '伤害加成' in mainName:
        equipMain = mainName[0]
    elif '元素' in mainName:
        equipMain = mainName[2]
    elif '百分比' in mainName:
        if '血量' in mainName:
            equipMain = '生'
        else:
            equipMain = mainName[3]
    else:
        equipMain = mainName[0]
    return equipMain


async def get_char_percent(raw_data: dict, prop: dict, char_name: str) -> str:
    # print(prop)
    percent = '0.0%'
    weaponName = raw_data['weaponInfo']['weaponName']

    equipMain = ''
    for aritifact in raw_data['equipList']:
        mainName = aritifact['reliquaryMainstat']['statName']
        artifactsPos = aritifact['aritifactPieceName']
        if artifactsPos == '时之沙':
            equipMain += await get_first_main(mainName)
        elif artifactsPos == '空之杯':
            equipMain += await get_first_main(mainName)
        elif artifactsPos == '理之冠':
            equipMain += await get_first_main(mainName)

    if 'equipSets' in raw_data:
        equipSets = raw_data['equipSets']
    else:
        artifact_set_list = []
        for i in raw_data['equipList']:
            artifact_set_list.append(i['aritifactSetsName'])
        equipSetList = set(artifact_set_list)
        equipSets = {'type': '', 'set': ''}
        for equip in equipSetList:
            if artifact_set_list.count(equip) >= 4:
                equipSets['type'] = '4'
                equipSets['set'] = equip
                break
            elif artifact_set_list.count(equip) == 1:
                pass
            elif artifact_set_list.count(equip) >= 2:
                equipSets['type'] += '2'
                equipSets['set'] += equip

    if equipSets['type'] in ['2', '']:
        seq = ''
    else:
        seq = '{}|{}|{}'.format(
            weaponName.replace('「', '').replace('」', ''),
            equipSets['set'],
            equipMain,
        )
    print(seq)
    std_prop = dmgMap[char_name]
    for std_seq in std_prop:
        if std_seq['seq'] == seq:
            std = std_seq
            break
    else:
        std = dmgMap[char_name][0]
    print(std)
    f = []
    c = 0.83
    if std['critRate'] != 'any':
        crate = (prop['critrate'] - std['critRate']) / 2
        c = c * (crate + 1)
    if char_name == '珊瑚宫心海':
        c = 0.83
    else:
        if std['critDmg'] != 'any':
            f.append(float(prop['critdmg'] / std['critDmg']))
    if std['atk'] != 'any':
        f.append(float(prop['attack'] / std['atk']))
    for i in std['other']:
        if '生命' in i:
            f.append(float(prop['hp'] / std['other'][i]))
        elif '充能' in i:
            f.append(float(prop['ce'] / std['other'][i]))
        elif '精通' in i:
            f.append(float(prop['em'] / std['other'][i]))
        elif '防御' in i:
            f.append(float(prop['defense'] / std['other'][i]))
        else:
            f.append(1)
    print(f)
    percent = '{:.2f}'.format(c * (float(sum(f) / len(f)) * 100))
    return percent


async def calc_prop(raw_data: dict, power_list: dict) -> dict:
    # 获取值
    char_name = raw_data['avatarName']
    char_level = int(raw_data['avatarLevel'])
    weaponName = raw_data['weaponInfo']['weaponName']
    weaponType = raw_data['weaponInfo']['weaponType']
    weaponAffix = raw_data['weaponInfo']['weaponAffix']

    skillList = raw_data['avatarSkill']
    prop = {}
    prop['A_skill_level'] = skillList[0]['skillLevel']
    prop['E_skill_level'] = skillList[1]['skillLevel']
    prop['Q_skill_level'] = skillList[-1]['skillLevel']

    skill_add = avatarName2SkillAdd[char_name]
    for skillAdd_index in range(0, 2):
        if len(raw_data['talentList']) >= 3 + skillAdd_index * 2:
            if skill_add[skillAdd_index] == 'E':
                prop['E_skill_level'] += 3
            elif skill_add[skillAdd_index] == 'Q':
                prop['Q_skill_level'] += 3

    fight_prop = raw_data['avatarFightProp']
    prop['basehp'] = fight_prop['baseHp']
    prop['baseattack'] = fight_prop['baseAtk']
    prop['basedefense'] = fight_prop['baseDef']

    prop['hp'] = fight_prop['hp']
    prop['attack'] = fight_prop['atk']
    prop['defense'] = fight_prop['def']
    prop['em'] = fight_prop['elementalMastery']
    prop['critrate'] = fight_prop['critRate']
    prop['critdmg'] = fight_prop['critDmg']
    prop['ce'] = fight_prop['energyRecharge']
    prop['physicalDmgBonus'] = physicalDmgBonus = fight_prop[
        'physicalDmgBonus'
    ]
    prop['dmgBonus'] = dmgBonus = fight_prop['dmgBonus']
    prop['healBouns'] = fight_prop['healBonus']
    prop['shieldBouns'] = 0

    # 给每个技能 分别添加上属性
    for prop_attr in [
        'attack',
        'defense',
        'em',
        'ce',
        'hp',
        'dmgBonus',
        'critrate',
        'critdmg',
        'addDmg',
        'd',
        'g',
        'r',
        'ignoreDef',
        'shieldBouns',
        'physicalDmgBonus',
        'healBouns',
    ]:
        if prop_attr in ['addDmg', 'd', 'r', 'ignoreDef']:
            prop['{}'.format(prop_attr)] = 0
        for prop_limit in ['A', 'B', 'C', 'E', 'Q']:
            if prop_attr in [
                'attack',
                'defense',
                'em',
                'critrate',
                'critdmg',
                'ce',
                'hp',
                'physicalDmgBonus',
                'healBouns',
            ]:
                prop[f'{prop_limit}_{prop_attr}'] = prop[prop_attr]
            else:
                prop[f'{prop_limit}_{prop_attr}'] = 0

    # 计算角色伤害加成应该使用什么
    for prop_limit in ['A', 'B', 'C', 'E', 'Q']:
        if weaponType == '法器' or char_name in [
            '荒泷一斗',
            '刻晴',
            '诺艾尔',
            '胡桃',
            '宵宫',
            '魈',
            '神里绫华',
        ]:
            prop['{}_dmgBonus'.format(prop_limit)] = dmgBonus
        elif '万叶' in char_name and len(raw_data['talentList']) >= 6:
            prop['{}_dmgBonus'.format(prop_limit)] = dmgBonus
        elif weaponType == '弓':
            if prop_limit in ['A', 'C']:
                prop['{}_dmgBonus'.format(prop_limit)] = physicalDmgBonus
            elif prop_limit in ['B', 'E', 'Q']:
                prop['{}_dmgBonus'.format(prop_limit)] = dmgBonus
        else:
            if prop_limit in ['A', 'B', 'C']:
                prop['{}_dmgBonus'.format(prop_limit)] = physicalDmgBonus
            elif prop_limit in ['E', 'Q']:
                prop['{}_dmgBonus'.format(prop_limit)] = dmgBonus

    # 初始化各种值
    prop['hp_green'] = fight_prop['addHp']
    prop['attack_green'] = fight_prop['addAtk']
    prop['defense_green'] = fight_prop['addDef']

    prop['r'] = 0.1
    prop['a'] = 0
    prop['g'] = 0
    prop['k'] = 1

    all_effect = []

    # 计算武器buff
    weapon_effet = weapons_effect_map[weaponName][str(weaponAffix)]
    all_effect.append(weapon_effet)

    # 计算圣遗物套装
    if 'equipSets' in raw_data:
        equipSets = raw_data['equipSets']
    else:
        artifact_set_list = []
        for i in raw_data['equipList']:
            artifact_set_list.append(i['aritifactSetsName'])
        equipSetList = set(artifact_set_list)
        equipSets = {'type': '', 'set': ''}
        for equip in equipSetList:
            if artifact_set_list.count(equip) >= 4:
                equipSets['type'] = '4'
                equipSets['set'] = equip
                break
            elif artifact_set_list.count(equip) == 1:
                pass
            elif artifact_set_list.count(equip) >= 2:
                equipSets['type'] += '2'
                equipSets['set'] += '|' + equip

    if equipSets['set'].startswith('|'):
        equipSets['set'] = equipSets['set'][1:]

    # 计算圣遗物buff
    if equipSets['type'] == '4':
        all_effect.append(artifacts_effect_map[equipSets['set']]['4'])
    elif equipSets['type'] == '2':
        all_effect.append(artifacts_effect_map[equipSets['set']]['2'])
    elif equipSets['type'] == '22':
        if equipSets['set'][-2] == '之':
            first_artifact = equipSets['set'][-3:]
        else:
            first_artifact = equipSets['set'][-2:]
        # second_artifact = equipSets['set'][:2]
        temp = []
        temp_number = 0
        for artifacts_single_effect in artifacts_effect_map:
            if first_artifact in artifacts_single_effect:
                temp_number += 1
                temp.append(artifacts_effect_map[artifacts_single_effect]['2'])
                if temp_number >= 2:
                    break
        all_effect.extend(temp)

    # 计算技能buff
    for talent in char_talent_effect_map[char_name]:
        if int(talent) <= len(raw_data['talentList']):
            all_effect.append(char_talent_effect_map[char_name][talent])
        else:
            break

    # 计算角色buff
    for skill in char_skill_effect_map[char_name]:
        if int(skill) <= char_level:
            all_effect.append(char_skill_effect_map[char_name][skill])
        else:
            break

    # 开启效果
    power_effect = ''
    if 'effect' in power_list:
        for skill_effect_single in power_list['effect']:
            skill_effect_name = skill_effect_single['name']
            skill_effect_value = skill_effect_single['value']
            skill_effect = skill_effect_single['effect']
            skill_effect_level = (
                prop['{}_skill_level'.format(skill_effect_name[0])] - 1
            )
            skill_effect_value_detail = skill_effect_value[skill_effect_level]
            if skill_effect[-1] == '}':
                skill_effect_value_detail = skill_effect_value_detail.replace(
                    '%', ''
                )
            add_limit = skill_effect.split(':')
            if len(add_limit) == 1:
                for i in power_list:
                    if i == 'effect':
                        pass
                    else:
                        power_list[i]['name'] = (
                            '开{}后 '.format(skill_effect_name[0])
                            + power_list[i]['name']
                        )
            else:
                for i in power_list:
                    if i == 'effect':
                        pass
                    else:
                        add_type = i[0]
                        if '重击' in i or '蓄力' in i:
                            add_type = 'B'
                        elif '冲击伤害' in i:
                            add_type = 'C'
                        if add_type in add_limit[0]:
                            power_list[i]['name'] = (
                                '开{}后 '.format(skill_effect_name[0])
                                + power_list[i]['name']
                            )
            power_effect = skill_effect.format(skill_effect_value_detail)
            all_effect.append(power_effect)
        del power_list['effect']

    # 特殊效果,目前有雷神满愿力
    prop['extra_effect'] = {}
    if 'extra' in power_list:
        if char_name == '雷电将军':
            extra_value = (
                float(
                    power_list["extra"]["value"][prop["Q_skill_level"] - 1]
                    .replace("%", "")
                    .split('+')[0]
                )
                * 0.6
            )
            extra_value2 = float(
                power_list["extra"]["value"][prop["Q_skill_level"] - 1]
                .replace("%", "")
                .split('+')[1]
            )
            all_effect.append(
                (
                    f'Q一段伤害:attack+{60*extra_value2};'
                    f'Q重击伤害:attack+{60*extra_value2};'
                    f'Q高空下落伤害:attack+{60*extra_value2}'
                )
            )
            prop['extra_effect'] = {'Q梦想一刀基础伤害(满愿力)': extra_value}
        del power_list['extra']

    # 在计算buff前, 引入特殊效果
    if char_name == '雷电将军':
        all_effect.append('Q:dmgBonus+27')
    elif char_name == '钟离':
        all_effect.append('r+-20')

    prop['sp'] = []
    # 计算全部的buff，添加入属性
    print(all_effect)
    if all_effect:
        # 把所有的效果都用;链接
        all_effect = ';'.join(all_effect)
        # 然后再分隔成list
        all_effect_list = all_effect.split(';')
        # 遍历每个效果
        for effect in all_effect_list:
            # 空效果跳过
            if effect == '':
                continue

            # 如果效果没有限制条件,即dmgBonus+27这种,往前面增加:,方便后续分割
            effect_limit = ''
            if ':' in effect:
                pass
            else:
                effect = ':' + effect

            # 分割效果
            # 例如:Q:dmgBonus+27
            # 分割后:
            # effect_limit = Q
            effect_limit = effect.split(':')[0]
            # effect_name = dmgBonus
            effect_attr = effect.split(':')[1].split('+')[0]
            # effect_value = 27
            effect_value = effect.split(':')[1].split('+')[-1]

            base_check = True
            # 寻找effect_value是否存在%,形如: 27%ce,即 增加值是由自身ce值确定的
            if '%' in effect_value:
                # 如果存在%, 进行分割
                # 拿到基于的属性,例如ce
                effect_value_base_on_attr = effect_value.split('%')[-1]
                # 查找是否有多个%,例如一开始的"Q:dmgBonus+75%25%ce"意思是按照25%的元素充能增加伤害,上限为75%
                # 则这里会分割成['75', '25'] 然后 按%链接 即去掉最后一项,变为75%25
                effect_value_base_on_value = '%'.join(
                    effect_value.split('%')[:-1]
                )
                # 如果还有%存在,即形如75%25的情况
                if '%' in effect_value_base_on_value:
                    # 最大值 effect_value_base_on_max_value = 75
                    effect_value_base_on_max_value = (
                        effect_value_base_on_value.split('%')[0]
                    )
                    # 根据百分比的值 effect_value_base_on_max_value = 25
                    effect_value_base_on_value = (
                        effect_value_base_on_value.split('%')[-1]
                    )
                    # 按照百分比计算增加值
                    effect_now_value = (
                        float(effect_value_base_on_value)
                        * prop[effect_value_base_on_attr]
                    )
                    # 比大小, 上限不能超过75
                    effect_value = (
                        float(effect_value_base_on_max_value)
                        if effect_now_value
                        >= float(effect_value_base_on_max_value)
                        else effect_now_value
                    )
                # 如果不存在最大值,即形如25%ce的情况
                else:
                    # 直接计算增加值
                    effect_value = (
                        float(effect_value_base_on_value)
                        * prop[effect_value_base_on_attr]
                    )
                    if effect_attr in ['dmgBonus', 'critDmg', 'critrate']:
                        effect_value = float(effect_value / 100)
                base_check = False

            # 如果要增加的属性不是em元素精通,那么都要除于100
            if effect_attr != 'em':
                # 正常除100
                effect_value = float(effect_value) / 100
                # 如果属性是血量,攻击,防御值,并且是按照%增加的,那么增加值应为百分比乘上基础值
                if effect_attr in ['hp', 'attack', 'defense'] and base_check:
                    effect_value += (
                        effect_value * prop['base{}'.format(effect_attr)]
                    )
            # 元素精通则为正常值
            else:
                effect_value = float(effect_value)
            # 如果效果有限制条件
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
                    # 形如ABC:dmgBouns+75,则遍历ABC,增加值
                    for limit in effect_limit:
                        prop[
                            '{}_{}'.format(limit, effect_attr)
                        ] += effect_value
            # 如果没有限制条件,直接增加
            else:
                if effect_attr in ['a', 'd', 'r', 'addDmg', 'ignoreDef']:
                    pass
                else:
                    for attr in ['A', 'B', 'C', 'E', 'Q']:
                        prop[f'{attr}_{effect_attr}'] += effect_value
                prop[f'{effect_attr}'] += effect_value
    return prop


async def draw_dmgCacl_img(
    raw_data: dict, power_list: dict, prop: dict
) -> Tuple[Image.Image, int]:
    # 获取值
    char_name = raw_data['avatarName']
    char_level = int(raw_data['avatarLevel'])
    enemy_level = char_level

    extra_effect = prop['extra_effect']
    sp = prop['sp']

    # 计算伤害计算部分图片长宽值
    w = 950
    h = 40 * (len(power_list) + 1)
    result_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    # 反复贴上不同颜色的长条
    for i in range(0, len(power_list) + 1):
        if i % 2 == 0:
            result_img.paste(dmgBar_1, (0, i * 40))
        else:
            result_img.paste(dmgBar_2, (0, i * 40))

    result_draw = ImageDraw.Draw(result_img)

    text_color = (255, 255, 255)
    title_color = (255, 255, 100)
    text_size = genshin_font_origin(28)
    result_draw.text((45, 22), '角色动作', title_color, text_size, anchor='lm')
    result_draw.text((460, 22), '暴击伤害', title_color, text_size, anchor='lm')
    result_draw.text((695, 22), '期望伤害', title_color, text_size, anchor='lm')

    for index, power_name in enumerate(power_list):
        # 攻击类型ABCEQ应为label首位
        attack_type = power_name[0]
        # 如果是雷电将军, 则就按首位,因为Q的几段伤害均视为元素爆发
        if char_name == '雷电将军':
            pass
        else:
            # 重击或瞄准射击在label内,则视为B重击伤害,例如公子E内的重击伤害,不视为E伤害,而是B伤害
            if '重击' in power_name or '瞄准射击' in power_name:
                attack_type = 'B'
            # 特殊重击类型,例如甘雨和夜兰
            elif '破局矢' in power_name or '霜华矢' in power_name:
                attack_type = 'B'
            # 下落伤害类型,例如魈
            elif '高空下落' in power_name:
                attack_type = 'C'
            # 一段伤害, 二段伤害等等 应视为A伤害
            elif '段' in power_name and '伤害' in power_name:
                attack_type = 'A'

        # 额外的伤害增益,基于之前的特殊label
        sp_dmgBonus = 0
        sp_addDmg = 0
        sp_attack = 0

        if sp:
            for sp_single in sp:
                if sp_single['effect_name'] in power_name:
                    if sp_single['effect_attr'] == 'dmgBouns':
                        sp_dmgBonus += sp_single['effect_value']
                    elif sp_single['effect_attr'] == 'addDmg':
                        sp_addDmg += sp_single['effect_value']
                    elif sp_single['effect_attr'] == 'attack':
                        sp_attack += sp_single['effect_value']

        # 根据type计算有效属性
        if '攻击' in power_list[power_name]['type']:
            effect_prop = prop[f'{power_name[0]}_attack'] + sp_attack
        elif '生命值' in power_list[power_name]['type']:
            effect_prop = prop[f'{power_name[0]}_hp']
        elif '防御' in power_list[power_name]['type']:
            effect_prop = prop[f'{power_name[0]}_defense']
        else:
            effect_prop = prop[f'{power_name[0]}_attack']

        # 按照ABCEQ等级查找倍率
        power = power_list[power_name]['value'][
            prop['{}_skill_level'.format(power_name[0])] - 1
        ]
        # 计算是否多次伤害
        power_plus = power_list[power_name]['plus']

        # 拿到百分比和固定值,百分比为float,形如2.2 也就是202%
        power_percent, power_value = await power_to_value(power, power_plus)

        # 额外加成,目前只有雷神
        if extra_effect and power_name in extra_effect:
            power_percent += extra_effect[power_name]

        # 计算这个label的伤害加成为多少
        # 这个label是否为物理伤害
        if power_name in ['Q光降之剑基础伤害', 'Q光降之剑基础伤害(13层)', 'Q每层能量伤害']:
            dmgBonus_cal = (
                prop['{}_dmgBonus'.format(attack_type)]
                + sp_dmgBonus
                + prop['physicalDmgBonus']
            )
        # 常规元素伤害
        else:
            dmgBonus_cal = (
                prop['{}_dmgBonus'.format(attack_type)] + sp_dmgBonus
            )
        # 计算暴击伤害
        critdmg_cal = prop['{}_critdmg'.format(attack_type)]
        # 计算暴击率
        critrate_cal = prop['{}_critrate'.format(attack_type)]
        em_cal = prop['{}_em'.format(attack_type)]
        # 计算防御区
        d_cal = (char_level + 100) / (
            (char_level + 100)
            + (1 - prop['{}_d'.format(attack_type)])
            * (1 - prop['{}_ignoreDef'.format(attack_type)])
            * (enemy_level + 100)
        )
        # 计算抗性区
        if prop['r'] > 0.75:
            r = 1 / (1 + 4 * prop['r'])
        elif prop['r'] > 0:
            r = 1 - prop['r']
        else:
            r = 1 - prop['r'] / 2

        # 计算元素反应 增幅
        for reaction in ['蒸发', '融化']:
            if reaction in power_list[power_name]['name']:
                k = 0
                if reaction == '蒸发':
                    if raw_data['avatarElement'] == 'Pyro':
                        k = 1.5
                    else:
                        k = 2
                elif reaction == '融化':
                    if raw_data['avatarElement'] == 'Pyro':
                        k = 2
                    else:
                        k = 1.5
                reaction_add_dmg = k * (
                    1 + (2.78 * em_cal) / (em_cal + 1400) + prop['a']
                )
                break
        else:
            reaction_add_dmg = 1

        # 计算草系相关反应
        reaction_power = 0
        for reaction in ['超激化', '蔓激化']:
            if reaction in power_list[power_name]['name']:
                if reaction == '超激化':
                    k = 2.3
                else:
                    k = 2.5
                reaction_power = (
                    k
                    * base_value_list[char_level - 1]
                    * (1 + (5 * em_cal) / (em_cal + 1200))
                )
                break

        # 草系反应增加到倍率区
        power_value += reaction_power

        # 计算直接增加的伤害
        add_dmg = prop['{}_addDmg'.format(attack_type)] + sp_addDmg

        # 特殊伤害提高
        sp_power_percent = 0
        if '13层' in power_name:
            sp_power_percent = (
                float(
                    power_list['Q每层能量伤害']['value'][
                        prop['{}_skill_level'.format(power_name[0])] - 1
                    ].replace('%', '')
                )
                / 100
            ) * 13

        # 根据label_name 计算数值
        if '治疗' in power_name:
            crit_dmg = avg_dmg = (
                effect_prop * power_percent + power_value
            ) * (1 + prop['healBouns'])
        elif '扩散伤害' in power_name:
            crit_dmg = avg_dmg = (
                base_value_list[char_level - 1]
                * 1.2
                * (1 + (16.0 * em_cal) / (em_cal + 2000) + prop['a'])
                * (1 + prop['g'] / 100)
                * r
            )
            power_list[power_name]['name'] = power_list[power_name]['name'][1:]
        elif '伤害值提升' in power_name:
            crit_dmg = avg_dmg = effect_prop * power_percent + power_value
        elif '护盾' in power_name:
            crit_dmg = avg_dmg = (
                effect_prop * power_percent + power_value
            ) * (1 + prop['shieldBouns'])
        elif '提升' in power_name or '提高' in power_name:
            continue
        else:
            crit_dmg = (
                effect_prop * (power_percent + sp_power_percent) + power_value
            ) * (1 + critdmg_cal) * (
                1 + dmgBonus_cal
            ) * d_cal * r * reaction_add_dmg + add_dmg
            avg_dmg = (
                (crit_dmg - add_dmg) * critrate_cal
                + (1 - critrate_cal)
                * (
                    effect_prop * (power_percent + sp_power_percent)
                    + power_value
                )
                * (1 + dmgBonus_cal)
                * d_cal
                * r
                * reaction_add_dmg
                + add_dmg
            )

        result_draw.text(
            (45, 22 + (index + 1) * 40),
            power_list[power_name]['name'],
            text_color,
            text_size,
            anchor='lm',
        )
        result_draw.text(
            (460, 22 + (index + 1) * 40),
            str(round(crit_dmg)),
            text_color,
            text_size,
            anchor='lm',
        )
        result_draw.text(
            (695, 22 + (index + 1) * 40),
            str(round(avg_dmg)),
            text_color,
            text_size,
            anchor='lm',
        )

    return result_img, len(power_list) + 2


async def power_to_value(power: str, power_plus: int) -> Tuple[float, float]:
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

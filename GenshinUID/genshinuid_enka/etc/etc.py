from pathlib import Path
from typing import Tuple

from PIL import Image

from .MAP_PATH import ATTR_MAP, dmgMap

R_PATH = Path(__file__).parents[1]
TEXT_PATH = R_PATH / 'texture2D'

SCORE_MAP = {
    '暴击率': 2,
    '暴击伤害': 1,
    '元素精通': 0.25,
    '元素充能效率': 0.65,
    '百分比血量': 0.86,
    '百分比攻击力': 1,
    '百分比防御力': 0.7,
    '血量': 0.014,
    '攻击力': 0.12,
    '防御力': 0.18,
}

VALUE_MAP = {
    '攻击力': 4.975,
    '血量': 4.975,
    '防御力': 6.2,
    '元素精通': 19.75,
    '元素充能效率': 5.5,
    '暴击率': 3.3,
    '暴击伤害': 6.6,
}


def get_star_png(star: int) -> Image.Image:
    png = Image.open(TEXT_PATH / 's-{}.png'.format(str(star)))
    return png


def strLenth(r: str, size: int, limit: int = 540) -> str:
    result = ''
    temp = 0
    for i in r:
        if temp >= limit:
            result += '\n' + i
            temp = 0
        else:
            result += i

        if i.isdigit():
            temp += round(size / 10 * 6)
        elif i == '/':
            temp += round(size / 10 * 2.2)
        elif i == '.':
            temp += round(size / 10 * 3)
        elif i == '%':
            temp += round(size / 10 * 9.4)
        else:
            temp += size
    return result


async def get_artifacts_score(subName: str, subValue: int) -> int:
    score = subValue * SCORE_MAP[subName]
    return score


async def get_artifacts_value(
    subName: str,
    subValue: int,
    baseAtk: int,
    baseHp: int,
    baseDef: int,
    charName: str,
) -> float:
    if charName not in ATTR_MAP:
        ATTR_MAP[charName] = ['攻击力', '暴击率', '暴击伤害']
    if subName in ATTR_MAP[charName] and subName in ['血量', '防御力', '攻击力']:
        if subName == '血量':
            base = (subValue / baseHp) * 100
        elif subName == '防御力':
            base = (subValue / baseDef) * 100
        elif subName == '攻击力':
            base = (subValue / baseAtk) * 100
        else:
            base = 1.0
        value = float('{:.2f}'.format(base / VALUE_MAP[subName]))
    elif subName in ['百分比血量', '百分比防御力', '百分比攻击力']:
        subName = subName.replace('百分比', '')
        if subName in ATTR_MAP[charName]:
            value = float('{:.2f}'.format(subValue / VALUE_MAP[subName]))
        else:
            return 0
    else:
        if subName in ATTR_MAP[charName]:
            value = float('{:.2f}'.format(subValue / VALUE_MAP[subName]))
        else:
            value = 0

    if charName == '胡桃' and subName == '攻击力':
        value = value * 0.4
    return value


async def get_all_artifacts_value(
    raw_data: dict, baseHp: int, baseAtk: int, baseDef: int, char_name: str
) -> float:
    artifactsValue = 0
    raw_data = raw_data['equipList']
    for aritifact in raw_data:
        for i in aritifact['reliquarySubstats']:
            subName = i['statName']
            subValue = i['statValue']
            value_temp = await get_artifacts_value(
                subName, subValue, baseAtk, baseHp, baseDef, char_name
            )
            artifactsValue += value_temp
    return artifactsValue


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


async def get_char_percent(
    raw_data: dict, prop: dict, char_name: str
) -> Tuple[str, str]:
    percent = '0.0'
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

    if char_name not in dmgMap:
        return percent, ''
    std_prop = dmgMap[char_name]
    seq_temp_a = ''
    seq_temp_w = ''
    for std_seq in std_prop:
        # 如果序列完全相同, 则直接使用这个序列
        if std_seq['seq'] == seq:
            std = std_seq
            break
        # 如果不完全相同, 但是杯子的主词条相同, 也可以使用这个
        if len(seq) >= 2 and len(std_seq['seq']) >= 2:
            if std_seq['seq'][:2] == seq[:2] and seq_temp_w == '':
                seq_temp_w = std_seq
            if std_seq['seq'][-2] == seq[-2] and seq_temp_a == '':
                seq_temp_a = std_seq
    else:
        # 如果存在备选那就用备选
        if seq_temp_w:
            std = seq_temp_w
        elif seq_temp_a:
            std = seq_temp_a
        # 不存在则使用第一个
        else:
            std = dmgMap[char_name][0]

    f = []
    c = 0.83
    if std['critRate'] != 'any':
        crate = (prop['critRate'] - std['critRate']) / 2
        c = c * (crate + 1)
    if char_name == '珊瑚宫心海':
        c = 0.83
    else:
        if std['critDmg'] != 'any':
            if char_name == '香菱':
                prop['atk'] += 0.25 * prop['baseAtk']
            f.append(float(prop['critDmg'] / std['critDmg']))

    atk_val = 1
    if std['atk'] != 'any':
        atk_val = float(prop['atk'] / std['atk'])
        if '防御力' in std['other']:
            atk_val = (atk_val - 0.9) * 0.2 + 0.9
        f.append(atk_val)

    for i in std['other']:
        if '生命' in i:
            f.append(float(prop['hp'] / std['other'][i]))
        elif '充能' in i:
            f.append(float(prop['energyRecharge'] / std['other'][i]))
        elif '精通' in i:
            em_val = float(prop['elementalMastery'] / std['other'][i])
            if atk_val <= 0.7:
                em_val = 0.35 * em_val
            elif atk_val <= 0.8:
                em_val = 0.52 * em_val
            elif atk_val <= 0.95:
                em_val = 0.68 * em_val
            elif atk_val <= 1.05:
                em_val = 0.95 * em_val
            elif atk_val <= 1.15:
                em_val = 1.0 * em_val
            elif atk_val <= 1.3:
                em_val = 1.08 * em_val
            else:
                em_val = 1.15 * em_val
            f.append(em_val)
        elif '防御' in i:
            f.append(float(prop['def'] / std['other'][i]))
        else:
            f.append(1)

    percent = '{:.2f}'.format(c * (float(sum(f) / len(f)) * 100))
    return percent, std['seq']

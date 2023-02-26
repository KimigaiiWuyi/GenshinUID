import re
import sys
import json
import asyncio
from typing import List
from pathlib import Path
from copy import deepcopy

import httpx

sys.path.append(str(Path(__file__).parents[1]))
from version import Genshin_version  # noqa: E402
from utils.ambr_api.convert_ambr_data import (  # noqa: E402
    convert_ambr_to_talent,
)

path = (
    Path(__file__).parents[1]
    / 'utils'
    / 'enka_api'
    / 'map'
    / f'avatarId2Name_mapping_{Genshin_version}.json'
)
element_path = (
    Path(__file__).parents[1]
    / 'utils'
    / 'enka_api'
    / 'map'
    / f'avatarName2Element_mapping_{Genshin_version}.json'
)
with open(path, 'r', encoding='utf-8') as f:
    char_id_list = json.load(f)

with open(element_path, 'r', encoding='utf-8') as f:
    char_element_list = json.load(f)

char_list: List[str] = []
char_action = {}
INDEX_MAP = ['', 'A', 'E', 'Q']
attack_type_list = {'普通攻击': 'A', '重击': 'B', '下落攻击': 'C', '战技': 'E', '爆发': 'Q'}
label_type_list = {
    '普通攻击': 'A',
    '重击': 'B',
    '下落攻击': 'C',
    '攻击': 'attack',
    '充能效率': 'ce',
    '生命值': 'hp',
    '防御': 'defense',
    '暴击率': 'critrate',
    '暴击伤害': 'critDmg',
    '元素精通': 'em',
}
extra = {
    '烟绯': {'A重击伤害': '蒸发'},
    '胡桃': {'A重击伤害': '蒸发', 'Q低血量时技能伤害': '蒸发'},
    '安柏': {'A满蓄力瞄准射击': ['融化', '蒸发']},
    '香菱': {'E喷火伤害': '蒸发', 'Q旋火轮伤害': '蒸发'},
    '达达利亚': {'A满蓄力瞄准射击': '蒸发', 'Q技能伤害·近战': '蒸发', 'Q技能伤害·远程': '蒸发'},
    '重云': {'Q技能伤害': '融化'},
    '雷电将军': {
        'E协同攻击伤害': '超激化',
        'Q梦想一刀基础伤害': '满愿力',
        'Q一段伤害': '满愿力',
        'Q重击伤害': '满愿力',
    },
    '班尼特': {'Q技能伤害': '蒸发'},
    '甘雨': {'A霜华矢命中伤害': '融化', 'A霜华矢·霜华绽发伤害': '融化'},
    '可莉': {'A重击伤害': '蒸发'},
    '优菈': {'Q光降之剑基础伤害': ['13层', '24层']},
    '行秋': {'E技能伤害': '蒸发'},
    '莫娜': {'A重击伤害': '蒸发', 'Q泡影破裂伤害': '蒸发'},
    '迪卢克': {'Q斩击伤害': '蒸发'},
    '芭芭拉': {'A重击伤害': '蒸发'},
    '七七': {'Q技能伤害': '融化'},
    '八重神子': {
        'Q伤害': '超激化',
        'Q天狐霆雷伤害': '超激化',
        'E杀生樱伤害·叁阶': '超激化',
        'E杀生樱伤害·肆阶': '超激化',
    },
    '菲谢尔': {'E奥兹攻击伤害': '超激化'},
    '久岐忍': {'Q单次伤害': '超激化'},
    '柯莱': {'Q跃动伤害': '蔓激化', 'E技能伤害': '蔓激化'},
    '提纳里': {
        'A藏蕴花矢伤害': '蔓激化',
        'E技能伤害': '蔓激化',
        'Q缠藤箭伤害': '蔓激化',
        'Q次级缠藤箭伤害': '蔓激化',
    },
    '刻晴': {
        'A重击伤害': '超激化',
        'E雷楔伤害': '超激化',
        'E斩击伤害': '超激化',
        'Q技能伤害': '超激化',
        'Q连斩伤害': '超激化*2',
        'Q最后一击伤害': '超激化',
    },
    '北斗': {'Q闪雷伤害': '超激化'},
    '赛诺': {'E冥祭伤害': '超激化', 'Q一段伤害': '超激化', 'Q重击伤害': '超激化'},
    '纳西妲': {'E长按伤害': '蔓激化', 'E灭净三业伤害': ['蔓激化', '蔓激化·前台']},
    '旅行者(草)': {'Q草灯莲攻击伤害': '蔓激化'},
    '夜兰': {'E伤害': '蒸发'},
    '艾尔海森': {'Q单次伤害': '蔓激化', 'E突进攻击伤害': '蔓激化', 'E1枚光幕攻击伤害': '蔓激化'},
    '迪希雅': {
        'E净焰昂藏伤害': '蒸发',
        'E剑域炽焰伤害': '蒸发',
        'E领域伤害': '蒸发',
        'Q炽鬃拳伤害': '蒸发',
        'Q焚落踢伤害': '蒸发',
    },
}
template = {'A重击伤害': {'name': 'A重击伤害', 'type': '', 'plus': 1, 'value': []}}


def fill_label(label_name: str, index: int) -> str:
    label_name = INDEX_MAP[index] + label_name
    return label_name


def from_type_to_value(value_type: str, para):
    value = ''
    if value_type == 'F1P':
        value = '%.1f%%' % (para * 100)
    elif value_type == 'F2P':
        value = '%.2f%%' % (para * 100)
    elif value_type == 'F1':
        value = '%.1f' % (para)
    elif value_type == 'F2':
        value = '%.2f' % (para)
    elif value_type == 'P':
        value = str(round(para * 100)) + '%'
    elif value_type == 'I':
        value = '%.2f' % para
    return value


def find_tag(labels: List, index: int, char: str, parameters: dict) -> dict:
    result = {}
    for label in labels:
        if '旅行者' not in char:
            if char_element_list[char] == 'Anemo':
                if 'A扩散伤害' not in result:
                    result['A扩散伤害'] = {
                        'name': 'A扩散伤害',
                        'type': '扩散',
                        'plus': 0,
                        'value': [str(i) for i in range(1, 11)],
                    }
        if char == '妮露':
            if 'A丰穰之核(绽放)' not in result:
                result['A丰穰之核(绽放)'] = {
                    'name': 'A丰穰之核(绽放)',
                    'type': '绽放',
                    'plus': 0,
                    'value': [str(i) for i in range(1, 11)],
                }
        if char == '久岐忍':
            if 'A元素反应(超绽放)' not in result:
                result['A元素反应(超绽放)'] = {
                    'name': 'A元素反应(超绽放)',
                    'type': '扩散',
                    'plus': 0,
                    'value': [str(i) for i in range(1, 11)],
                }
        if char == '托马':
            if 'A元素反应(烈绽放)' not in result:
                result['A元素反应(烈绽放)'] = {
                    'name': 'A元素反应(烈绽放)',
                    'type': '扩散',
                    'plus': 0,
                    'value': [str(i) for i in range(1, 11)],
                }
        # 拿到形如{param1:F1P}的字典
        label_split = label.split('|')[-1]
        # 拿到单个标签的名称，形如一段伤害
        label_name = label.split('|')[0]
        # 寻找label中带*的倍数倍率,比如 攻击力*3
        label_plus = 1
        if '*' in label_split:
            label_plus = label_split.split('*')[-1]
            label_plus = int(re.findall(r'[0-9]+', label_plus)[0])
        # 如果在label_split内拿到了形如每秒{param2:F2P}生命值上限+{param3:I}，获取汉字转换类型
        laber_kanji_list = re.findall(r'[\u4e00-\u9fa5]+', label_split)
        # 如果label_split中有汉字，则获取汉字的类型
        laber_kanji_list_str = ''.join(laber_kanji_list).replace('每秒', '')
        for type in label_type_list:
            if type in laber_kanji_list_str:
                label_kanji = type
                break
        else:
            label_kanji = '攻击力'
        # 找到标签{param1:F1P}的List
        label_attr = re.findall(r'{[a-zA-Z0-9]+:[a-zA-Z0-9]+}', label_split)
        # 例如"持续治疗|每秒{param2:F2P}生命值上限+{param3:I}",
        # 对单个标签内多个param进行处理，处理成形如['{param2:F2P}', '{param3:I}']
        value_type = ''
        temp_value = []
        temp_temp = []
        for indexA, k in enumerate(label_attr):
            # 去除多多余字符 变成 param2:F2P
            k_deal = k.replace('{', '').replace('}', '')
            value_type = k_deal.split(':')[-1]  # F2P
            value_index = k_deal.split(':')[0]  # param2
            temp = [
                from_type_to_value(value_type, parameter)
                for parameter in parameters[value_index]
            ]
            if indexA == 0:
                temp_value = temp
            # 只采用高空坠地的倍率
            elif indexA == 1 and '低空/高空坠地' in label:
                temp_value = temp
            # 阿忍仅计算50%血量以下伤害
            elif indexA == 1 and char == '久岐忍' and label_name == '总伤害':
                temp_value = temp
            # 埃洛伊特殊值
            elif indexA == 2 and char == '埃洛伊':
                temp_value = temp
            # 烟绯满层丹火印
            elif indexA == 4 and char == '烟绯':
                temp_value = temp
            # 无例外情况倍率全部相加
            else:
                temp_value = [f'{i}+{j}' for i, j in zip(temp_temp, temp)]
            # 读入缓存
            temp_temp = temp
        # 制作倍率单元素
        parameter_list = {
            'name': '',
            'type': label_kanji,
            'plus': label_plus,
            'value': temp_value,
        }

        # 特殊化处理
        if '心海' in char:
            label_name = label_name.replace('提升', '提高')
        label_name = label_name.replace('低空/高空坠地冲击伤害', '高空下落伤害')
        label_name = label_name.replace('技能', '')

        # 提升指提升百分比 例如  E:dmgBouns+50%
        # 提高指提高固定值 例如  Q:addDmg+40%defense

        label_keyword_hurt_list = ['一段', '壹阶', '贰阶', '叁阶', '肆阶']

        if '炽焰箭' in label_name:
            continue
        elif char == '珊瑚宫心海' and '提高' in label_name:
            continue
        elif '元素爆发伤害提高' in label_name and char == '雷电将军':
            continue
        elif '持续时间' in label_name:
            continue
        elif '提升' in label_name:
            # 云瑾和申鹤
            if '伤害值提升' in label_name:
                parameter_list['name'] = fill_label(label_name, index)
                result[fill_label(label_name, index)] = parameter_list
            else:
                continue
        elif '伤害' in label_name:
            if '段' in label_name or '阶' in label_name:
                for label_keyword in label_keyword_hurt_list:
                    if label_keyword in label_name:
                        parameter_list['name'] = fill_label(label_name, index)
                        result[fill_label(label_name, index)] = parameter_list
            elif '低空/高空坠地冲击伤害' in label_name and char not in ['魈']:
                continue
            elif '下坠期间伤害' in label_name:
                continue
            else:
                parameter_list['name'] = fill_label(label_name, index)
                result[fill_label(label_name, index)] = parameter_list
        elif '治疗' in label_name or '回复' in label_name:
            parameter_list['name'] = fill_label(label_name, index)
            result[fill_label(label_name, index)] = parameter_list
        elif '护盾' in label_name:
            parameter_list['name'] = fill_label(label_name, index)
            result[fill_label(label_name, index)] = parameter_list
        elif '满蓄力瞄准射击' in label_name:
            parameter_list['name'] = fill_label(label_name, index)
            result[fill_label(label_name, index)] = parameter_list

        if char in extra:
            for extra_name in extra[char]:
                temp_name = extra_name.replace('技能', '')
                if fill_label(label_name, index) == temp_name:
                    if isinstance(extra[char][extra_name], List):
                        for extra_tag in extra[char][extra_name]:
                            new_parameter_list = deepcopy(parameter_list)
                            new_parameter_list['name'] = (
                                fill_label(label_name, index)
                                + f'({extra_tag})'
                            )
                            result[
                                fill_label(label_name, index)
                                + f'({extra_tag})'
                            ] = new_parameter_list
                    else:
                        new_parameter_list = deepcopy(parameter_list)
                        new_parameter_list['name'] = (
                            fill_label(label_name, index)
                            + f'({extra[char][extra_name]})'
                        )
                        result[
                            fill_label(label_name, index)
                            + f'({extra[char][extra_name]})'
                        ] = new_parameter_list

    return result


async def main():
    for char_id in char_id_list:
        char_list.append(char_id_list[char_id])
    char_list.extend(['旅行者(风)', '旅行者(雷)', '旅行者(岩)', '旅行者(草)'])
    for char in char_list:
        print(char)
        talent_data = httpx.get(
            f'https://info.minigg.cn/talents?query={char}'
        ).json()
        if 'errcode' in talent_data:
            for _id in char_id_list:
                if char_id_list[_id] == char:
                    char_id = _id
                    break
            else:
                continue
            if int(char_id) >= 11000000:
                continue
            talent_data = await convert_ambr_to_talent(char_id)
            if talent_data is None:
                continue
        result = {}
        for i in range(1, 4):
            skill = talent_data['combat{}'.format(str(i))]
            labels = skill['attributes']['labels']
            parameters = skill['attributes']['parameters']
            result = dict(result, **find_tag(labels, i, char, parameters))
        char_action[char] = result

    with open(
        str(
            Path(__file__).parents[1]
            / 'genshinuid_enka'
            / 'effect'
            / 'char_action.json'
        ),
        'w',
        encoding='UTF-8',
    ) as file:
        json.dump(char_action, file, ensure_ascii=False)


asyncio.run(main())

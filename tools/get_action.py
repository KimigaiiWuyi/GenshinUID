import re
import json
from typing import List
from pathlib import Path
from copy import deepcopy

import httpx

Genshin_version = '3.0.0'

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

char_list = []
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
    '胡桃': {'A重击伤害': '蒸发', 'Q低血量时技能伤害': '蒸发'},
    '香菱': {'E喷火伤害': '蒸发', 'Q旋火轮伤害': '蒸发'},
    '达达利亚': {'Q技能伤害·近战': '蒸发', 'Q技能伤害·远程': '蒸发'},
    '雷电将军': {'Q梦想一刀基础伤害': '满愿力', 'Q一段伤害': '超激化', 'Q重击伤害': '超激化'},
    '甘雨': {'A霜华矢命中伤害': '融化', 'A霜华矢·霜华绽发伤害': '融化'},
    '可莉': {'A重击伤害': '蒸发'},
    '优菈': {'Q光降之剑基础伤害': '13层'},
    '行秋': {'E技能伤害': '蒸发'},
    '八重神子': {'Q天狐霆雷伤害': '超激化', 'E杀生樱伤害·叁阶': '超激化'},
    '菲谢尔': {'E奥兹攻击伤害': '超激化'},
    '久岐忍': {'Q单次伤害': '超激化'},
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
        if char != '旅行者':
            if char_element_list[char] == 'Anemo':
                if 'A扩散伤害' not in result:
                    result['A扩散伤害'] = {
                        'name': 'A扩散伤害',
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
            elif indexA == 1 and char == '久岐忍':
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
        label_keyword_up_list = {
            '普通攻击': 'A:addDmg',
            '重击': 'B:addDmg',
            '攻击': 'attack',
            '生命值': 'hp',
            '防御': 'defense',
            '暴击率': 'critrate',
            '充能效率': 'ce',
            '元素精通': 'em',
        }

        if '持续时间' in label_name:
            continue
        elif '提升' in label_name:
            # 云瑾和申鹤
            if '伤害值提升' in label_name:
                parameter_list['name'] = fill_label(label_name, index)
                result[fill_label(label_name, index)] = parameter_list
            elif '伤害提升' in label_name:
                add_type = ''
                # 寻找有没有合适的加成eg
                target = 0
                for attack_type in attack_type_list:
                    if attack_type in label_name:
                        add_type += attack_type_list[attack_type]
                        target += 1
                # 没有就对E进行加成
                else:
                    if target > 0:
                        if '变格' in label_name:
                            parameter_list['plus'] = 4
                    else:
                        add_type += 'E'
                # 格式化加:
                if add_type:
                    add_type = add_type + ':'
                    add_attr = '{}dmgBonus+'.format(add_type) + '{' + '}'
                    parameter_list['effect'] = add_attr
                parameter_list['name'] = fill_label(label_name, index)
                if 'effect' not in result:
                    result['effect'] = []
                result['effect'].append(parameter_list)
            else:
                continue
        elif '提高' in label_name:
            # 阻止雷电将军E
            if '元素爆发伤害提高' in label_name:
                continue
            if '攻击速度' in label_name:
                continue
            for attack_type in label_type_list:
                if attack_type in label_name:
                    add_prop = label_keyword_up_list[attack_type]
                    break
            else:
                add_prop = 'E:addDmg'

            for attack_type in label_type_list:
                if attack_type in label_kanji:
                    base_prop = label_keyword_up_list[attack_type]
                    break
            else:
                base_prop = 'attack'
            add_attr = add_prop + '+{' + '}' + base_prop
            parameter_list['effect'] = add_attr
            parameter_list['name'] = fill_label(label_name, index)
            if 'effect' not in result:
                result['effect'] = []
            result['effect'].append(parameter_list)
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
        elif '治疗' in label_name:
            parameter_list['name'] = fill_label(label_name, index)
            result[fill_label(label_name, index)] = parameter_list
        elif '护盾' in label_name:
            parameter_list['name'] = fill_label(label_name, index)
            result[fill_label(label_name, index)] = parameter_list
        elif '满蓄力瞄准射击' in label_name:
            parameter_list['name'] = fill_label(label_name, index)
            result[fill_label(label_name, index)] = parameter_list
        elif '愿力加成' in label_name:
            parameter_list['name'] = fill_label(label_name, index)
            result['extra'] = parameter_list

        if char in extra:
            for extra_name in extra[char]:
                temp_name = extra_name.replace('技能', '')
                if label_name == temp_name[1:]:
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


for char_id in char_id_list:
    char_list.append(char_id_list[char_id])

for char in char_list:
    talent_data = json.loads(
        httpx.get('https://info.minigg.cn/talents?query={}'.format(char)).text
    )
    if 'errcode' in talent_data:
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
        / 'dmgCalc'
        / 'char_action.json'
    ),
    'w',
    encoding='UTF-8',
) as file:
    json.dump(char_action, file, ensure_ascii=False)

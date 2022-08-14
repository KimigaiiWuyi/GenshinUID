import re
import json
from typing import List
from pathlib import Path

import httpx

path = Path(__file__).parents[1] / 'utils' / 'alias' / 'avatarId2Name.json'
with open(path, 'r', encoding='utf-8') as f:
    char_id_list = json.load(f)

char_list = []
char_action = {}
INDEX_MAP = ['', 'A', 'E', 'Q']


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
        label_split = label.split('|')[-1]
        label_name = label.split('|')[0]
        laber_kanji_list = re.findall(r'[\u4e00-\u9fa5]+', label_split)
        label_plus = 1
        # 寻找label中带*的倍数倍率,比如 攻击力*3
        if '*' in label_split:
            label_plus = label_split.split('*')[-1]
            label_plus = int(re.findall(r'[0-9]+', label_plus)[0])
        if len(laber_kanji_list) == 0:
            label_kanji = '攻击力'
        else:
            label_kanji = laber_kanji_list[0]
        label_attr = re.findall(r'{[a-zA-Z0-9]+:[a-zA-Z0-9]+}', label_split)
        temp = []
        parameter_list = {}
        for k in label_attr:
            value_type = k.replace('{', '').replace('}', '').split(':')[-1]
            value_index = k.replace('{', '').replace('}', '').split(':')[0]
            parameter_list = {
                'type': label_kanji,
                'plus': label_plus,
                'value': parameters[value_index],
            }
            parameter_list['value'] = [
                from_type_to_value(value_type, parameter)
                for parameter in parameter_list['value']
            ]
            print(parameter_list)
            for indexA, j in enumerate(parameter_list['value']):
                try:
                    if '低空/高空坠地' in label:
                        temp = parameter_list['value']
                    else:
                        parameter_list['value'][indexA] = (
                            temp[indexA]
                            + '+'
                            + parameter_list['value'][indexA]
                        )
                except:
                    temp = parameter_list['value']
                    break

        if '心海' in char:
            label_name = label_name.replace('提升', '提高')

        if '段' in label_name:
            if '一段' in label_name and '伤害' in label_name:
                parameter_list['power_name'] = fill_label(label_name, index)
                result[fill_label(label_name, index)] = parameter_list
                # result.append(fill_label(label_name, index))
        elif '阶' in label_name:
            if '肆阶' in label_name:
                parameter_list['power_name'] = fill_label(label_name, index)
                result[fill_label(label_name, index)] = parameter_list
        elif '提高' in label_name or '提升' in label_name:
            if '充能效率' in label_name:
                continue
            elif '抗性' in label_name:
                continue
            elif '攻击速度' in label_name:
                continue

            if '伤害提升' in label_name:
                add_type = ''
                if '普通攻击' in label_name:
                    add_type += 'A'
                if '重击' in label_name:
                    add_type += 'B'
                if '下落攻击' in label_name:
                    add_type += 'C'
                if '战技' in label_name:
                    add_type += 'E'
                if '爆发' in label_name:
                    add_type += 'Q'
                if label_name in ['变格伤害提升', '正论伤害提升']:
                    add_type += 'E'
                if add_type:
                    add_type = add_type + ':'
                add_attr = '{}dmgBonus+'.format(add_type) + '{' + '}'
                parameter_list['effect'] = add_attr
                parameter_list['name'] = INDEX_MAP[index]
                parameter_list['power_name'] = fill_label(label_name, index)
                if 'effect' not in result:
                    result['effect'] = []
                result['effect'].append(parameter_list)
            elif '提高' in label_name:
                if '元素爆发伤害提高' in label_name:
                    continue

                if '普通攻击' in label_name:
                    add_prop = 'A:addDmg'
                elif '重击' in label_name:
                    add_prop = 'B:addDmg'
                elif '攻击' in label_name:
                    add_prop = 'attack'
                elif '生命值' in label_name:
                    add_prop = 'hp'
                elif '防御' in label_name:
                    add_prop = 'defense'
                elif '暴击率' in label_name:
                    add_prop = 'critrate'
                elif '充能效率' in label_name:
                    add_prop = 'ce'
                elif '元素精通' in label_name:
                    add_prop = 'em'
                else:
                    add_prop = 'E:addDmg'

                if '攻击' in label_kanji:
                    base_prop = 'attack'
                elif '生命值' in label_kanji:
                    base_prop = 'hp'
                elif '防御' in label_kanji:
                    base_prop = 'defense'
                elif '暴击率' in label_kanji:
                    base_prop = 'critrate'
                elif '充能效率' in label_kanji:
                    base_prop = 'ce'
                elif '元素精通' in label_kanji:
                    base_prop = 'em'
                else:
                    base_prop = 'attack'

                add_attr = add_prop + '+{' + '}' + base_prop
                parameter_list['effect'] = add_attr
                parameter_list['name'] = INDEX_MAP[index]
                parameter_list['power_name'] = fill_label(label_name, index)
                if 'effect' not in result:
                    result['effect'] = []
                result['effect'].append(parameter_list)
        elif '伤害' in label_name:
            if '下坠期间伤害' in label_name:
                continue
            if '低空/高空坠地冲击伤害' in label_name:
                if char in ['魈']:
                    label_name = label_name.replace('低空/高空坠地', '下落')
                else:
                    continue
            parameter_list['power_name'] = fill_label(label_name, index)
            result[fill_label(label_name, index)] = parameter_list
        elif '治疗' in label_name:
            parameter_list['power_name'] = fill_label(label_name, index)
            result[fill_label(label_name, index)] = parameter_list
        elif '护盾' in label_name:
            parameter_list['power_name'] = fill_label(label_name, index)
            result[fill_label(label_name, index)] = parameter_list
        elif '满蓄力瞄准射击' in label_name:
            parameter_list['power_name'] = fill_label(label_name, index)
            result[fill_label(label_name, index)] = parameter_list

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

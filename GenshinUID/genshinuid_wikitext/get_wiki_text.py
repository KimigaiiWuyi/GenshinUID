import re
import math
from typing import List, Union

from gsuid_core.models import Message
from gsuid_core.segment import MessageSegment
from gsuid_core.utils.api.minigg.request import (
    get_others_info,
    get_talent_info,
    get_weapon_info,
    get_weapon_costs,
    get_weapon_stats,
    get_character_info,
    get_character_costs,
    get_character_stats,
    get_constellation_info,
)

from .get_wiki_template import food_im, weapon_im, artifacts_im, char_info_im


async def artifacts_wiki(name: str) -> str:
    data = await get_others_info('artifacts', name)
    if isinstance(data, int):
        im = '该圣遗物不存在。'
    else:
        star = ''
        for i in data['rarity']:
            star = star + i + '星、'
        star = star[:-1]
        im = artifacts_im.format(
            data['name'],
            star,
            data['2pc'],
            data['4pc'],
            data['flower']['name'],
            data['flower']['description'],
            data['plume']['name'],
            data['plume']['description'],
            data['sands']['name'],
            data['sands']['description'],
            data['goblet']['name'],
            data['goblet']['description'],
            data['circlet']['name'],
            data['circlet']['description'],
        )
    return im


async def foods_wiki(name: str) -> str:
    data = await get_others_info('foods', name)
    if isinstance(data, int):
        im = '该食物不存在。'
    else:
        ingredients = ''
        food_temp = {}
        for i in data['ingredients']:
            if i['name'] not in food_temp:
                food_temp[i['name']] = i['count']
            else:
                food_temp[i['name']] = food_temp[i['name']] + i['count']
        for i in food_temp:
            ingredients += i + ':' + str(food_temp[i]) + '\n'
        ingredients = ingredients[:-1]
        im = food_im.format(
            data['name'],
            data['rarity'],
            data['foodtype'],
            data['foodfilter'],
            data['effect'],
            data['description'],
            ingredients,
        )
    return im


async def enemies_wiki(name: str) -> str:
    data = await get_others_info('enemies', name)
    if isinstance(data, int):
        im = '该原魔不存在。'
    else:
        reward = ''
        for i in data['rewardpreview']:
            reward += (
                f'{i["name"]}:{i["count"] if "count" in i else "未知"}'
                if 'count' in i.keys()
                else i['name'] + ': ' + '可能'
            )
            reward += '\n'
        im = '【{}】\n——{}——\n类型: {}\n信息: {}\n掉落物: \n{}'.format(
            data['name'],
            data['specialname'],
            data['category'],
            data['description'],
            reward,
        )
    return im


async def weapon_wiki(name: str) -> str:
    data = await get_weapon_info(name)
    if isinstance(data, int):
        im = '该武器不存在。'
    elif isinstance(data, List):
        im = ', '.join(data)
    else:
        name = data['name']
        _type = data['weapontype']
        star = data['rarity'] + '星'
        info = data['description']
        atk = str(data['baseatk'])
        sub_name = data['substat']
        if data['subvalue'] != '':
            sub_val = (
                (data['subvalue'] + '%')
                if sub_name != '元素精通'
                else data['subvalue']
            )
            sub = '\n' + '【' + sub_name + '】' + sub_val
        else:
            sub = ''

        if data['effectname'] != '':
            raw_effect = data['effect']
            rw_ef = []
            for i in range(len(data['r1'])):
                now = ''
                for j in range(1, 6):
                    now = now + data['r{}'.format(j)][i] + '/'
                now = now[:-1]
                rw_ef.append(now)
            raw_effect = raw_effect.format(*rw_ef)
            effect = '\n' + '【' + data['effectname'] + '】' + ': ' + raw_effect
        else:
            effect = ''
        im = weapon_im.format(name, _type, star, info, atk, sub, effect)
    return im


async def weapon_stats_wiki(name: str, stats: int):
    data = await get_weapon_info(name)
    data2 = await get_weapon_stats(name, stats)
    if isinstance(data, int) or isinstance(data2, int):
        im = '该武器不存在。'
    elif isinstance(data, List) or isinstance(data2, List):
        im = '请输入具体的武器名称...'
    else:
        if data['substat'] != '':
            sp = (
                data['substat']
                + ': '
                + '%.1f%%' % (data2['specialized'] * 100)
                if data['substat'] != '元素精通'
                else data['substat']
                + ': '
                + str(math.floor(data2['specialized']))
            )
        else:
            sp = ''
        im = (
            data['name']
            + '\n等级: '
            + str(data2['level'])
            + '（突破'
            + str(data2['ascension'])
            + '）'
            + '\n攻击力: '
            + str(round(data2['attack']))
            + '\n'
            + sp
        )
    return im


async def weapon_costs_wiki(name: str) -> str:
    data = await get_weapon_costs(name)
    if isinstance(data, int):
        im = '不存在该武器或类型。'
    elif isinstance(data, List):
        im = ', '.join(data)
    else:
        im = ''
        temp = {}
        data = data['costs']
        for i in data.values():
            for j in i:  # type:ignore
                if j['name'] not in temp:
                    temp[j['name']] = j['count']
                else:
                    temp[j['name']] = temp[j['name']] + j['count']
        for k in temp:
            im += k + ':' + str(temp[k]) + '\n'
    return im


async def char_wiki(name: str) -> str:
    data = await get_character_info(name)
    if isinstance(data, int):
        im = '不存在该角色或类型。'
    elif isinstance(data, List):
        im = ', '.join(data)
    else:
        name = data['title'] + ' — ' + data['name']
        star = data['rarity']
        _type = data['weapontype']
        element = data['element']
        up_val = data['substat']
        bdday = data['birthday']
        polar = data['constellation']
        cv = data['cv']['chinese']
        info = data['description']
        im = char_info_im.format(
            name, star, _type, element, up_val, bdday, polar, cv, info
        )
    return im


async def char_stats_wiki(name: str, stats: int):
    data2 = await get_character_info(name)
    data = await get_character_stats(name, stats)
    if isinstance(data, int) or isinstance(data2, int):
        im = '该角色不存在。'
    elif isinstance(data, List) or isinstance(data2, List):
        im = '请输入具体的角色名称...'
    else:
        sp = (
            data2['substat'] + ': ' + '%.1f%%' % (data['specialized'] * 100)
            if data2['substat'] != '元素精通'
            else data2['substat'] + ': ' + str(math.floor(data['specialized']))
        )
        im = (
            data2['name']
            + '\n等级: '
            + str(data['level'])
            + '\n血量: '
            + str(math.floor(data['hp']))
            + '\n攻击力: '
            + str(math.floor(data['attack']))
            + '\n防御力: '
            + str(math.floor(data['defense']))
            + '\n'
            + sp
        )
    return im


async def char_costs_wiki(name: str) -> str:
    data = await get_character_costs(name)
    data2 = await get_talent_info(name)
    if isinstance(data, int) or isinstance(data2, int):
        im = '该角色不存在。'
    elif isinstance(data, List) or isinstance(data2, List):
        im = '请输入具体的角色名称...'
    else:
        im = '【天赋材料(一份)】\n{}\n【突破材料】\n{}'
        im1 = ''
        im2 = ''

        talent_temp = {}
        talent_cost = data2['costs']
        for i in talent_cost.values():
            for j in i:  # type:ignore
                if j['name'] not in talent_temp:
                    talent_temp[j['name']] = j['count']
                else:
                    talent_temp[j['name']] = (
                        talent_temp[j['name']] + j['count']
                    )
        for k in talent_temp:
            im1 = im1 + k + ':' + str(talent_temp[k]) + '\n'

        temp = {}
        for i in range(1, 7):
            for j in data['ascend{}'.format(i)]:
                if j['name'] not in temp:
                    temp[j['name']] = j['count']
                else:
                    temp[j['name']] = temp[j['name']] + j['count']

        for k in temp:
            im2 = im2 + k + ':' + str(temp[k]) + '\n'

        im = im.format(im1, im2)
    return im


async def constellation_wiki(name: str, c: int) -> str:
    data = await get_constellation_info(name)
    if isinstance(data, int):
        im = '该角色不存在。'
    else:
        im = (
            '【'
            + data['c{}'.format(c)]['name']
            + '】'
            + ': '
            + '\n'
            + data['c{}'.format(c)]['effect'].replace('*', '')
        )
    return im


async def talent_wiki(name: str, level: int) -> Union[List[Message], str]:
    data = await get_talent_info(name)
    if isinstance(data, int):
        im = '该角色不存在。'
    else:
        if int(level) <= 3:
            if level == 1:
                data = data['combat1']
            elif level == 2:
                data = data['combat2']
            else:
                data = data['combat3']
            skill_name = data['name']
            skill_info = data['info']
            skill_detail = ''

            mes_list: List[Message] = []
            parameters = []
            add_switch = True

            labels = ''.join(data['attributes']['labels'])
            parameters_label = re.findall(
                r'{[a-zA-Z0-9]+:[a-zA-Z0-9]+}', labels
            )

            labels = {}
            for i in parameters_label:
                value_type = i.replace('{', '').replace('}', '').split(':')[-1]
                value_index = i.replace('{', '').replace('}', '').split(':')[0]
                labels[value_index] = value_type

            for para in data['attributes']['parameters']:
                if para in labels:
                    label_str = labels[para]
                    for index, j in enumerate(
                        data['attributes']['parameters'][para]
                    ):
                        if add_switch:
                            parameters.append({})

                        if label_str == 'F1P':
                            parameters[index].update(
                                {para: '%.1f%%' % (j * 100)}
                            )
                        if label_str == 'F2P':
                            parameters[index].update(
                                {para: '%.2f%%' % (j * 100)}
                            )
                        elif label_str == 'F1':
                            parameters[index].update({para: '%.1f' % j})
                        elif label_str == 'F2':
                            parameters[index].update({para: '%.2f' % j})
                        elif label_str == 'P':
                            parameters[index].update(
                                {para: str(round(j * 100)) + '%'}
                            )
                        elif label_str == 'I':
                            parameters[index].update({para: '%.2f' % j})
                    add_switch = False

            for k in data['attributes']['labels']:
                k = re.sub(r':[a-zA-Z0-9]+}', '}', k)
                skill_detail += k + '\n'

            skill_detail = skill_detail[:-1].replace('|', ' | ')

            for i in range(1, 10):
                if i % 2 != 0:
                    skill_info = skill_info.replace('**', '「', 1)
                else:
                    skill_info = skill_info.replace('**', '」', 1)

            mes_list.append(
                MessageSegment.text(f'【{skill_name}】\n{skill_info}')
            )
            for index, i in enumerate(parameters):
                mes = skill_detail.format(**i)
                mes_list.append(MessageSegment.text(f'lv.{index + 1}\n{mes}'))
            im = mes_list
        else:
            if level == 4:
                data = data['passive1']
            elif level == 5:
                data = data['passive2']
            elif level == 6:
                data = data['passive3']
            else:
                if 'passive4' in data:
                    data = data['passive4']
                else:
                    return '该角色未有第四个被动天赋...'
            skill_name = data['name']
            skill_info = data['info']
            im = '【{}】\n{}'.format(skill_name, skill_info)
    return im

import re
import math
import random
from io import BytesIO
from pathlib import Path

from httpx import AsyncClient

from .get_wiki_template import *  # noqa
from ..utils.minigg_api.get_minigg_data import (
    get_char_info,
    get_misc_info,
    get_audio_info,
    get_weapon_info,
)


async def audio_wiki(name, message):
    async def get(_audioid):
        for _ in range(3):  # 重试3次
            if _audioid in audio_json:
                if not audio_json[_audioid]:
                    return
                audioid1 = random.choice(audio_json[_audioid])
            else:
                audioid1 = _audioid
            url = await get_audio_info(name, audioid1)
            async with AsyncClient() as client:
                req = await client.get(url)
            if req.status_code == 200:
                return BytesIO(req.content)
            else:
                if _audioid in audio_json:
                    audio_json[_audioid].remove(audioid1)

    if name == '列表':
        with open(Path(__file__).parent / '语音列表.png', 'rb') as f:
            imgmes = f.read()
        return imgmes
    elif name == '':
        return '请输入角色名。'
    else:
        audioid = re.findall(r'\d+', message)
        try:
            audio = await get(audioid[0])
        except IndexError:
            return '请输入语音ID。'
        except:
            return '语音获取失败'
        if audio:
            return audio.getvalue()
        else:
            return '没有找到语音，请检查语音ID与角色名是否正确，如无误则可能未收录该语音'


async def artifacts_wiki(name):
    data = await get_misc_info('artifacts', name)
    if 'errcode' in data:
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


async def foods_wiki(name):
    data = await get_misc_info('foods', name)
    if 'errcode' in data:
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


async def enemies_wiki(name):
    raw_data = await get_misc_info('enemies', name)
    if 'errcode' in raw_data:
        im = '该原魔不存在。'
    else:
        reward = ''
        for i in raw_data['rewardpreview']:
            reward += (
                i['name'] + '：' + str(i['count'])
                if 'count' in i.keys()
                else i['name'] + '：' + '可能'
            )
            reward += '\n'
        im = '【{}】\n——{}——\n类型：{}\n信息：{}\n掉落物：\n{}'.format(
            raw_data['name'],
            raw_data['specialname'],
            raw_data['category'],
            raw_data['description'],
            reward,
        )
    return im


async def weapon_wiki(name, level=None):
    data = await get_weapon_info(name)
    if 'errcode' in data:
        im = '该武器不存在。'
    elif level:
        data2 = await get_weapon_info(name, level)
        if data['substat'] != '':
            sp = (
                data['substat'] + '：' + '%.1f%%' % (data2['specialized'] * 100)
                if data['substat'] != '元素精通'
                else data['substat']
                + '：'
                + str(math.floor(data2['specialized']))
            )
        else:
            sp = ''
        im = (
            data['name']
            + '\n等级：'
            + str(data2['level'])
            + '（突破'
            + str(data2['ascension'])
            + '）'
            + '\n攻击力：'
            + str(round(data2['attack']))
            + '\n'
            + sp
        )
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
            effect = '\n' + '【' + data['effectname'] + '】' + '：' + raw_effect
        else:
            effect = ''
        im = weapon_im.format(name, _type, star, info, atk, sub, effect)
    return im


async def char_wiki(name, mode='char', level=None):
    im = ''
    data = await get_char_info(name, mode, level if mode == 'char' else None)
    if mode == 'char':
        if isinstance(data, list):
            im = ','.join(data)
        elif 'errcode' in data:
            im = '不存在该角色或类型。'
        elif level:
            data2 = await get_char_info(name, mode)
            sp = (
                data2['substat'] + '：' + '%.1f%%' % (data['specialized'] * 100)
                if data2['substat'] != '元素精通'
                else data2['substat']
                + '：'
                + str(math.floor(data['specialized']))
            )
            im = (
                data2['name']
                + '\n等级：'
                + str(data['level'])
                + '\n血量：'
                + str(math.floor(data['hp']))
                + '\n攻击力：'
                + str(math.floor(data['attack']))
                + '\n防御力：'
                + str(math.floor(data['defense']))
                + '\n'
                + sp
            )
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
    elif mode == 'costs':
        if isinstance(data[1], list):
            im = ','.join(data[1])
        elif 'errcode' in data[1]:
            im = '不存在该角色或类型。'
        else:
            im = '【天赋材料(一份)】\n{}\n【突破材料】\n{}'
            im1 = ''
            im2 = ''

            talent_temp = {}
            talent_cost = data[1]
            for i in talent_cost.values():
                for j in i:
                    if j['name'] not in talent_temp:
                        talent_temp[j['name']] = j['count']
                    else:
                        talent_temp[j['name']] = (
                            talent_temp[j['name']] + j['count']
                        )
            for k in talent_temp:
                im1 = im1 + k + ':' + str(talent_temp[k]) + '\n'

            temp = {}
            cost = data[0]
            for i in range(1, 7):
                for j in cost['ascend{}'.format(i)]:
                    if j['name'] not in temp:
                        temp[j['name']] = j['count']
                    else:
                        temp[j['name']] = temp[j['name']] + j['count']

            for k in temp:
                im2 = im2 + k + ':' + str(temp[k]) + '\n'

            im = im.format(im1, im2)
    elif mode == 'constellations':
        if 'errcode' in data:
            im = '不存在该角色或命座数量。'
        else:
            im = (
                '【'
                + data['c{}'.format(level)]['name']
                + '】'
                + '：'
                + '\n'
                + data['c{}'.format(level)]['effect'].replace('*', '')
            )
    elif mode == 'talents':
        if 'errcode' in data:
            im = '不存在该角色。'
        else:
            if level:
                if 7 >= int(level) > 0:
                    if int(level) <= 3:
                        if level == '1':
                            data = data['combat1']
                        elif level == '2':
                            data = data['combat2']
                        elif level == '3':
                            data = data['combat3']
                        skill_name = data['name']
                        skill_info = data['info']
                        skill_detail = ''

                        mes_list = []
                        parameters = []
                        add_switch = True

                        labels = ''.join(data['attributes']['labels'])
                        parameters_label = re.findall(
                            r'{[a-zA-Z0-9]+:[a-zA-Z0-9]+}', labels
                        )

                        labels = {}
                        for i in parameters_label:
                            value_type = (
                                i.replace('{', '')
                                .replace('}', '')
                                .split(':')[-1]
                            )
                            value_index = (
                                i.replace('{', '')
                                .replace('}', '')
                                .split(':')[0]
                            )
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
                                        parameters[index].update(
                                            {para: '%.1f' % j}
                                        )
                                    elif label_str == 'F2':
                                        parameters[index].update(
                                            {para: '%.2f' % j}
                                        )
                                    elif label_str == 'P':
                                        parameters[index].update(
                                            {para: str(round(j * 100)) + '%'}
                                        )
                                    elif label_str == 'I':
                                        parameters[index].update(
                                            {para: '%.2f' % j}
                                        )
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
                            {
                                'type': 'node',
                                'data': {
                                    'name': '小仙',
                                    'uin': '3399214199',
                                    'content': '【'
                                    + skill_name
                                    + '】'
                                    + '\n'
                                    + skill_info,
                                },
                            }
                        )

                        for index, i in enumerate(parameters):
                            mes = skill_detail.format(**i)
                            node_data = {
                                'type': 'node',
                                'data': {
                                    'name': '小仙',
                                    'uin': '3399214199',
                                    'content': 'lv.'
                                    + str(index + 1)
                                    + '\n'
                                    + mes,
                                },
                            }
                            mes_list.append(node_data)
                        im = mes_list

                    else:
                        if level == '4':
                            data = data['passive1']
                        elif level == '5':
                            data = data['passive2']
                        elif level == '6':
                            data = data['passive3']
                        elif level == '7':
                            data = data['passive4']
                        skill_name = data['name']
                        skill_info = data['info']
                        im = '【{}】\n{}'.format(skill_name, skill_info)
                else:
                    im = '不存在该天赋。'
    return im

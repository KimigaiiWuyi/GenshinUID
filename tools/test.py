import asyncio
import json
import os

import aiofiles

FILE_PATH = r'../genshin_uid'


async def weapon_adv(name):
    async with aiofiles.open(os.path.join(FILE_PATH, 'mihoyo_libs/char_adv_list.json'), encoding='utf-8') as f:
        adv_li: dict = json.loads(await f.read())
    weapons = {}
    for char, info in adv_li.items():
        char_weapons = []
        for i in info['weapon'].values():  # 3 stars, 4 stars, 5 stars
            char_weapons.extend(i)

        for weapon_name in char_weapons:
            if name in weapon_name:  # fuzzy search
                char_weapon = weapons.get(weapon_name, [])
                char_weapon.append(char)
                weapons[weapon_name] = char_weapon

    if weapons:
        im = []
        for k, v in weapons.items():
            im.append(f'{"、".join(v)} 可能会用到【{k}】')
        im = '\n'.join(im)
    else:
        im = '没有角色能使用【{}】'.format(name)
    # print(im)
    return im


async def char_adv(name):
    async with aiofiles.open(os.path.join(FILE_PATH, 'mihoyo_libs/char_adv_list.json'), encoding='utf-8') as f:
        adv_li = json.loads(await f.read())
    for char, info in adv_li.items():
        if name in char:
            im = [f'「{char}」', '-=-=-=-=-=-=-=-=-=-']
            if weapon_5 := info['weapon']['5']:
                im.append(f'推荐5★武器：{"、".join(weapon_5)}')
            if weapon_4 := info['weapon']['4']:
                im.append(f'推荐4★武器：{"、".join(weapon_4)}')
            if weapon_3 := info['weapon']['3']:
                im.append(f'推荐3★武器：{"、".join(weapon_3)}')
            if artifacts := info['artifact']:
                im.append('推荐圣遗物搭配：')
                for arti in artifacts:
                    if len(arti) > 1:
                        im.append(f'[{arti[0]}]两件套 + [{arti[1]}]两件套')
                    else:
                        im.append(f'[{arti[0]}]四件套')
            return '\n'.join(im)

    return '没有找到角色信息'


async def main():
    # print(await weapon_adv('剑'))
    print()
    print(await char_adv('无疑'))


asyncio.run(main())

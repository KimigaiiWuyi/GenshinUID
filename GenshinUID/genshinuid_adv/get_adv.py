import json
from pathlib import Path

from ..utils.map.name_covert import alias_to_char_name

with open(
    Path(__file__).parent / 'char_adv_list.json', "r", encoding='UTF-8'
) as f:
    adv_lst = json.load(f)


async def weapon_adv(name):
    weapons = {}
    artifacts = {}
    for char, info in adv_lst.items():
        char_weapons = []
        char_artifacts = []

        for i in info['weapon'].values():  # 3 stars, 4 stars, 5 stars
            char_weapons.extend(i)
        for i in info['artifact']:
            char_artifacts.extend(i)
        # char_artifacts = list(set(char_artifacts))

        for weapon_name in char_weapons:
            if name in weapon_name:  # fuzzy search
                char_weapon = weapons.get(weapon_name, [])
                char_weapon.append(char)
                weapons[weapon_name] = char_weapon
        for artifact_name in char_artifacts:
            if name in artifact_name:  # fuzzy search
                char_artifact = artifacts.get(artifact_name, [])
                char_artifact.append(char)
                char_artifact = list(set(char_artifact))
                artifacts[artifact_name] = char_artifact

    im = []
    if weapons:
        im.append('✨武器：')
        for k, v in weapons.items():
            im.append(f'{"、".join(v)} 可能会用到【{k}】')
    if artifacts:
        im.append('✨圣遗物：')
        for k, v in artifacts.items():
            im.append(f'{"、".join(v)} 可能会用到【{k}】')
    if im == []:
        im = '没有角色能使用【{}】'.format(name)
    else:
        im = '\n'.join(im)
    return im


async def char_adv(name: str):
    name = await alias_to_char_name(name)
    for char, info in adv_lst.items():
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
            if remark := info['remark']:
                im.append('-=-=-=-=-=-=-=-=-=-')
                im.append('备注：')
                mark = "\n".join(remark)
                im.append(f'{mark}')
            return '\n'.join(im)

    return '没有找到角色信息'

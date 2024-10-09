import sys
import json
import asyncio
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).parents[5]))
sys.path.append(str(Path(__file__).parents[2]))

__package__ = 'GenshinUID.tools'
from gsuid_core.utils.api.ambr.request import (  # noqa: E402
    get_ambr_monster_data,
    get_ambr_monster_list,
)
from gsuid_core.utils.api.hakush.request import (  # noqa: E402
    get_hakush_char_list,
    get_hakush_weapon_list,
)

from GenshinUID.utils.map.GS_MAP_PATH import (  # noqa: E402
    mysData_fileName,
    charList_fileName,
    enName2Id_fileName,
    icon2Name_fileName,
    name2Icon_fileName,
    weaponList_fileName,
    skillId2Name_fileName,
    artifact2attr_fileName,
    avatarId2Name_fileName,
    avatarId2Star_fileName,
    monster2entry_fileName,
    talentId2Name_fileName,
    weaponId2Name_fileName,
    weaponHash2Name_fileName,
    weaponHash2Type_fileName,
    avatarName2Weapon_fileName,
    avatarName2Element_fileName,
)

from ..version import Genshin_version  # noqa: E402
from ..utils.ambr_to_minigg import convert_ambr_to_minigg  # noqa: E402

R_PATH = Path(__file__).parents[0]
MAP_PATH = Path(__file__).parents[1] / 'utils' / 'map' / 'data'
DATA_PATH = R_PATH / 'gs_data'
WEAPON_TYPE = {
    'WEAPON_POLE': '长柄武器',
    'WEAPON_BOW': '弓',
    'WEAPON_SWORD_ONE_HAND': '单手剑',
    'WEAPON_CLAYMORE': '双手剑',
    'WEAPON_CATALYST': '法器',
}

version = Genshin_version
raw_data = {}


BETA_CHAR = {
    '10000100': '卡齐娜',
    '10000101': '基尼奇',
    '10000102': '玛拉妮',
}


async def weaponId2Name():
    result = {}
    print('正在执行weaponId2Name')
    with open(
        DATA_PATH / 'WeaponExcelConfigData.json',
        'r',
        encoding='UTF-8',
    ) as f:
        weapon_data = json.load(f)

    for weapon in weapon_data:
        if str(weapon['nameTextMapHash']) in raw_data:
            result[weapon['id']] = raw_data[str(weapon['nameTextMapHash'])]

    with open(
        MAP_PATH / weaponId2Name_fileName,
        'w',
        encoding='UTF-8',
    ) as f:
        json.dump(result, f, ensure_ascii=False, indent=4)


async def avatarId2SkillGroupList():
    result = {}
    print('正在执行avatarId2SkillList')
    with open(
        MAP_PATH / f'enName2AvatarID_mapping_{version}.json',
        'r',
        encoding='UTF-8',
    ) as f:
        en_name = json.load(f)

    with open(
        DATA_PATH / 'AvatarSkillExcelConfigData.json',
        'r',
        encoding='UTF-8',
    ) as f:
        skill_data = json.load(f)

        for skill in skill_data:
            if 'proudSkillGroupId' in skill:
                if skill['abilityName']:
                    _name = skill['skillIcon'].split('_')[2]
                    count = skill['abilityName'].count('_')

                    if 'Diluc' in skill['abilityName']:
                        name = 'Diluc'
                    elif count <= 1:
                        name = skill['abilityName'].split('_')[0]
                    elif count >= 3:
                        if skill['abilityName'].split('_')[1] == _name:
                            name = skill['abilityName'].split('_')[1]
                        else:
                            continue
                    else:
                        name = skill['abilityName'].split('_')[1]

                    if (
                        _name != name
                        and skill['skillIcon'].count('_') > 2
                        and 'Catalyst' not in skill['skillIcon']
                    ):
                        print(_name)
                        print(name)
                        continue

                else:
                    name = skill['skillIcon'].split('_')[2]

                if not skill['skillIcon'].startswith(
                    ('Skill_A', 'Skill_S', 'Skill_E')
                ):
                    continue

                if name not in en_name:
                    name = name.split(' ')[-1]
                    for _en in en_name:
                        en = _en.split(' ')[-1]
                        if en == 'Jean':
                            en = 'Qin'
                        elif en == 'Baizhu':
                            en = 'Baizhuer'
                        elif en == 'Alhaitham':
                            en = 'Alhatham'
                        elif en == 'Jin':
                            en = 'Yunjin'
                        elif en == 'Miko':
                            en = 'Yae'
                        elif en == 'Heizou':
                            en = 'Heizo'
                        elif en == 'Amber':
                            en = 'Ambor'
                        elif en == 'Noelle':
                            en = 'Noel'
                        elif en == 'Yanfei':
                            en = 'Feiyan'
                        elif en == 'Shogun':
                            en = 'Shougun'
                        elif en == 'Lynette':
                            en = 'Linette'
                        elif en == 'Lyney':
                            en = 'Liney'
                        elif en == 'Tao':
                            en = 'Hutao'
                        elif en == 'Thoma':
                            en = 'Tohma'
                        elif en == 'Kirara':
                            en = 'Momoka'
                        elif en == 'Xianyun':
                            en = 'Liuyun'
                        if name == en:
                            avatar_id = en_name[_en]
                            break
                    else:
                        if not name.startswith('Player'):
                            print(name)
                        continue
                else:
                    avatar_id = en_name[name]

                if str(skill["nameTextMapHash"]) in raw_data:
                    skill_name = raw_data[str(skill["nameTextMapHash"])]
                else:
                    skill_name = ''

                if avatar_id not in result:
                    result[avatar_id] = {}

                result[avatar_id][skill['proudSkillGroupId']] = skill_name

    result['10000036'] = {
        "3631": "普通攻击·灭邪四式",
        "3632": "灵刃·重华叠霜",
        "3639": "灵刃·云开星落",
    }
    with open(
        MAP_PATH / f'avatarId2SkillList_mapping_{version}.json',
        'w',
        encoding='UTF-8',
    ) as f:
        json.dump(result, f, indent=4, ensure_ascii=False)


async def monster2map():
    print('正在执行monster2map')
    monster_list = await get_ambr_monster_list()
    result = {}
    if monster_list:
        for monster_main_id in monster_list['items']:
            if not monster_main_id.startswith('28'):
                data = await get_ambr_monster_data(monster_main_id)
                if data:
                    for entry_id in data['entries']:
                        entry: dict = data['entries'][entry_id]  # type: ignore
                        entry['name'] = data['name']
                        entry['route'] = data['route']
                        entry['icon'] = data['icon']
                        result[entry_id] = entry
    with open(MAP_PATH / monster2entry_fileName, 'w', encoding='UTF-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)


async def download_new_file():
    print('正在执行download_new_file')
    base_url = 'https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master'
    url_list = [
        f'{base_url}/ExcelBinOutput/AvatarExcelConfigData.json',
        f'{base_url}/ExcelBinOutput/WeaponExcelConfigData.json',
        f'{base_url}/ExcelBinOutput/AvatarSkillExcelConfigData.json',
        f'{base_url}/ExcelBinOutput/AvatarTalentExcelConfigData.json',
        f'{base_url}/ExcelBinOutput/ReliquaryExcelConfigData.json',
        f'{base_url}/ExcelBinOutput/DisplayItemExcelConfigData.json',
        f'{base_url}/TextMap/TextMapCHS.json',
    ]

    async with httpx.AsyncClient() as client:
        for url in url_list:
            file_name = url.split('/')[-1]
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                with open(DATA_PATH / file_name, 'w') as f:
                    json.dump(data, f, indent=4)
                print(f'文件已成功下载并保存为{DATA_PATH / file_name}')
            else:
                print(f'下载失败，状态码为{response.status_code}')


async def avatarId2NameJson() -> None:
    print('正在执行avatarId2NameJson')
    with open(
        DATA_PATH / 'AvatarExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        avatar_data = json.load(f)

    temp = {}
    for i in avatar_data:
        temp[str(i['id'])] = raw_data[str(i['nameTextMapHash'])]

    for _id in BETA_CHAR:
        temp[_id] = BETA_CHAR[_id]

    result = {}
    for _id in temp:
        if int(_id) >= 11000000:
            continue
        else:
            result[_id] = temp[_id]

    with open(
        MAP_PATH / avatarId2Name_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(result, file, ensure_ascii=False)


async def avatarName2ElementJson() -> None:
    print('正在执行avatarName2ElementJson')
    with open(MAP_PATH / avatarId2Name_fileName, 'r', encoding='UTF-8') as f:
        avatarId2Name = json.load(f)

    temp = {}
    enName2Id_result = {}
    avatarId2Star_result = {}
    avatarName2Weapon_result = {}
    elementMap = {
        '风': 'Anemo',
        '岩': 'Geo',
        '草': 'Dendro',
        '火': 'Pyro',
        '水': 'Hydro',
        '冰': 'Cryo',
        '雷': 'Electro',
    }
    for _id in avatarId2Name:
        print(_id)
        if _id in ['10000005', '10000007'] or int(_id) >= 11000000:
            continue
        name = avatarId2Name[_id]
        data = httpx.get(
            f'https://info.minigg.cn/characters?query={name}'
        ).json()
        if 'retcode' in data:
            data = await convert_ambr_to_minigg(_id)
        if data is not None and 'code' not in data:
            temp[name] = elementMap[data['elementText']]
            try:
                nameicon = data['images']['namesideicon']  # type: ignore
                enName = nameicon.split('_')[-1]
                enName2Id_result[enName] = _id
                avatarId2Star_result[int(_id)] = str(data['rarity'])
                avatarName2Weapon_result[data['name']] = data['weaponText']
            except:  # noqa: E722
                while True:
                    try:
                        adata = httpx.get(
                            f'https://gi.yatta.moe/api/v2/chs/avatar/{_id}'
                        ).json()
                        break
                    except:  # noqa: E722
                        pass
                adata = adata['data']
                enName = adata['route']
                enName2Id_result[enName] = _id
                avatarId2Star_result[int(_id)] = str(adata['rank'])
                avatarName2Weapon_result[data['name']] = WEAPON_TYPE[
                    adata['weaponType']
                ]

    avatarId2Star_result['10000005'] = '5'
    avatarId2Star_result['10000007'] = '5'
    avatarName2Weapon_result['旅行者'] = '单手剑'

    with open(MAP_PATH / enName2Id_fileName, 'w', encoding='UTF-8') as file:
        json.dump(enName2Id_result, file, ensure_ascii=False)

    with open(
        MAP_PATH / avatarId2Star_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(avatarId2Star_result, file, ensure_ascii=False)

    with open(
        MAP_PATH / avatarName2Element_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(temp, file, ensure_ascii=False)

    with open(
        MAP_PATH / avatarName2Weapon_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(avatarName2Weapon_result, file, ensure_ascii=False)


async def weaponHash2NameJson() -> None:
    print('正在执行weaponHash2NameJson')
    with open(
        DATA_PATH / 'WeaponExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        weapon_data = json.load(f)
    temp = {
        str(i['nameTextMapHash']): raw_data[str(i['nameTextMapHash'])]
        for i in weapon_data
        if str(i['nameTextMapHash']) in raw_data
    }

    with open(
        MAP_PATH / weaponHash2Name_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(temp, file, ensure_ascii=False)


async def weaponHash2TypeJson() -> None:
    print('正在执行weaponHash2TypeJson')
    with open(
        DATA_PATH / 'WeaponExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        weapon_data = json.load(f)
    temp = {
        str(i['nameTextMapHash']): WEAPON_TYPE.get(i['weaponType'], '')
        for i in weapon_data
    }

    with open(
        MAP_PATH / weaponHash2Type_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(temp, file, ensure_ascii=False)


async def skillId2NameJson() -> None:
    print('正在执行skillId2NameJson')
    with open(
        DATA_PATH / 'AvatarSkillExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        skill_data = json.load(f)

    temp = {'Name': {}, 'Icon': {}}
    for i in skill_data:
        if str(i['nameTextMapHash']) in raw_data:
            temp['Name'][str(i['id'])] = raw_data[str(i['nameTextMapHash'])]
            temp['Icon'][str(i['id'])] = i['skillIcon']

    with open(MAP_PATH / skillId2Name_fileName, 'w', encoding='UTF-8') as file:
        json.dump(temp, file, ensure_ascii=False)


async def talentId2NameJson() -> None:
    print('正在执行talentId2NameJson')
    with open(
        DATA_PATH / 'AvatarTalentExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        talent_data = json.load(f)

    temp = {'Name': {}, 'Icon': {}}
    for i in talent_data:
        temp['Name'][str(i['talentId'])] = raw_data[str(i['nameTextMapHash'])]
        temp['Icon'][str(i['talentId'])] = i['icon']

    with open(
        MAP_PATH / talentId2Name_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(temp, file, ensure_ascii=False)


async def artifact2attrJson() -> None:
    print('正在执行artifact2attrJson')
    with open(
        DATA_PATH / 'ReliquaryExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        reliquary_data = json.load(f)

    with open(
        DATA_PATH / 'DisplayItemExcelConfigData.json', 'r', encoding='UTF-8'
    ) as f:
        Display_data = json.load(f)

    temp = {}
    for i in reliquary_data:
        temp[str(i['icon'])] = raw_data[str(i['nameTextMapHash'])]

    temp['UI_RelicIcon_10001_1'] = '异国之盏'
    temp['UI_RelicIcon_10001_2'] = '归乡之羽'
    temp['UI_RelicIcon_10001_3'] = '感别之冠'
    temp['UI_RelicIcon_10001_4'] = '故人之心'
    temp['UI_RelicIcon_10001_5'] = '逐光之石'
    with open(MAP_PATH / icon2Name_fileName, 'w', encoding='UTF-8') as file:
        json.dump(temp, file, ensure_ascii=False)

    temp_reverse = {}
    for i in temp:
        temp_reverse[temp[i]] = i
    with open(MAP_PATH / name2Icon_fileName, 'w', encoding='UTF-8') as file:
        json.dump(temp_reverse, file, ensure_ascii=False)

    temp2 = {}
    for i in Display_data:
        if i['icon'].startswith('UI_RelicIcon'):
            temp2[raw_data[str(i['nameTextMapHash'])]] = '_'.join(
                i['icon'].split('_')[:-1]
            )

    temp3 = {}
    for i in temp:
        for k in temp2:
            if i.startswith(temp2[k]):
                temp3[temp[i]] = k

    temp3['异国之盏'] = '行者之心'
    temp3['归乡之羽'] = '行者之心'
    temp3['感别之冠'] = '行者之心'
    temp3['故人之心'] = '行者之心'
    temp3['逐光之石'] = '行者之心'

    with open(
        MAP_PATH / artifact2attr_fileName, 'w', encoding='UTF-8'
    ) as file:
        json.dump(temp3, file, ensure_ascii=False)


async def restore_hakush_data():
    data = await get_hakush_char_list()
    data2 = await get_hakush_weapon_list()

    with open(MAP_PATH / charList_fileName, 'w', encoding='UTF-8') as f:
        json.dump(data, f, ensure_ascii=False)

    with open(MAP_PATH / weaponList_fileName, 'w', encoding='UTF-8') as f:
        json.dump(data2, f, ensure_ascii=False)


async def restore_mysData():
    base_url = 'https://api-takumi.mihoyo.com'
    resp = httpx.get(f'{base_url}/event/platsimulator/config?gids=2&game=hk4e')
    with open(MAP_PATH / mysData_fileName, 'w', encoding='UTF-8') as f:
        json.dump(resp.json(), f, ensure_ascii=False)


async def main():
    await download_new_file()
    await restore_mysData()
    await restore_hakush_data()
    global raw_data
    try:
        with open(DATA_PATH / 'TextMapCHS.json', 'r', encoding='UTF-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        pass
    # await monster2map()
    await avatarId2NameJson()
    await avatarName2ElementJson()
    await weaponHash2NameJson()
    await skillId2NameJson()
    await talentId2NameJson()
    await weaponHash2TypeJson()
    await artifact2attrJson()
    await weaponId2Name()
    await avatarId2SkillGroupList()


asyncio.run(main())

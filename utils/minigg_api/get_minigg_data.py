import json

from httpx import AsyncClient

from .minigg_api import *  # noqa: F401, F403


async def get_minigg_enka_info(uid: str):
    """
    :说明:
      返回角色信息。
    :参数:
      * uid (str): 玩家uid。
    :返回:
      * dict: 角色信息。
    """
    url = MINIGG_ENKA_URL.format(uid)
    async with AsyncClient() as client:
        req = await client.get(url=url)
    data = json.loads(req.text)
    return data


async def get_audio_info(name: str, audioid: str, language: str = 'cn') -> str:
    """
    :说明:
      访问miniggAPI获得原神角色音频信息。
    :参数:
      * name (str): 原神角色名称。
      * audioid (str): 语音id。
      * language (str): 默认为cn。
    :返回:
      * req.text (str): url。
    """
    async with AsyncClient() as client:
        req = await client.get(
            url=MINIGG_AUDIO_URL,
            params={
                'characters': name,
                'audioid': audioid,
                'language': language,
            },
        )
    return req.text


async def get_weapon_info(name, level=None) -> dict:
    """
    :说明:
      访问miniggAPI获得原神武器信息。
      https://info.minigg.cn/weapons?query=飞雷
    :参数:
      * name (str): 武器名称。
      * level (str): 武器等级。
    :返回:
      * data (dict): 武器信息。
    :Template:
      * data['name'] (str): 武器名称。
      * data['description'] (str): 武器描述。
      * data['weapontype'] (str): 武器类型。
    """
    if level:
        params = {'query': name, 'stats': level}
    else:
        params = {'query': name}
    async with AsyncClient() as client:
        req = await client.get(url=MINIGG_WEAPON_URL, params=params)
    data = json.loads(req.text)
    return data


async def get_misc_info(mode: str, name: str):
    """
    :说明:
      一些杂项信息。
    :参数:
      * name (str): 'enemies', 'foods', 'artifacts'。
      * name (str): 参数。
    :返回:
      * data (str): 获取数据信息。
    """
    url = MINIGG_MISC_URL.format(mode)
    async with AsyncClient() as client:
        req = await client.get(url=url, params={'query': name})
    data = json.loads(req.text)
    return data


async def get_char_info(name, mode='char', level=None):
    """
    :说明:
      返回角色信息。
    :参数:
      * name (str): 角色名称。
      * mode (str): 'char', 'talents', 'costs'。
      * level (str): 角色等级。
    :返回:
      * data (str): 获取数据信息。
    """
    url2 = None
    url3 = ''
    data2 = None
    baseurl = 'https://info.minigg.cn/characters?query='
    if mode == 'talents':
        url = 'https://info.minigg.cn/talents?query=' + name
    elif mode == 'constellations':
        url = 'https://info.minigg.cn/constellations?query=' + name
    elif mode == 'costs':
        url = baseurl + name + '&costs=1'
        url2 = 'https://info.minigg.cn/talents?query=' + name + '&costs=1'
        url3 = (
            'https://info.minigg.cn/talents?query='
            + name
            + '&matchCategories=true'
        )
    elif level:
        url = baseurl + name + '&stats=' + level
    else:
        url = baseurl + name

    if url2:
        async with AsyncClient() as client:
            req = await client.get(url=url2)
            data2 = json.loads(req.text)
            if 'errcode' in data2:
                async with AsyncClient() as client_:
                    req = await client_.get(url=url3)
                    data2 = json.loads(req.text)

    async with AsyncClient() as client:
        req = await client.get(url=url)
        try:
            data = json.loads(req.text)
            if 'errcode' in data:
                async with AsyncClient() as client_:
                    req = await client_.get(url=url + '&matchCategories=true')
                    data = json.loads(req.text)
        except:
            data = None
    return data if data2 is None else [data, data2]

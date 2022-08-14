import copy
from typing import Optional

from nonebot.log import logger
from aiohttp import ClientSession

from .mhy_api import *
from ..db_operation.db_operation import cache_db, owner_cookies
from .mhy_api_tools import (  # noqa: F401,F403
    random_hex,
    get_ds_token,
    old_version_get_ds_token,
)

mhyVersion = '2.11.1'

_HEADER = {
    'x-rpc-app_version': mhyVersion,
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 ('
    'KHTML, like Gecko) miHoYoBBS/2.11.1',
    'x-rpc-client_type': '5',
    'Referer': 'https://webstatic.mihoyo.com/',
    'Origin': 'https://webstatic.mihoyo.com',
}


async def _mhy_request(
    url: str,
    method: str = 'get',
    header: dict = _HEADER,
    params: dict = {},
    data: dict = {},
    sess: Optional[ClientSession] = None,
) -> dict:
    """
    :说明:
      访问URL并进行json解析返回。
    :参数:
      * url (str): MihoyoAPI。
      * method (str): `post` or `get`。
      * header (str): 默认为_HEADER。
      * params (dict): 参数。
      * data (dict): 参数(`post`方法需要传)。
      * client (ClientSession): 可选, 指定client。
    :返回:
      * result (dict): json.loads()解析字段。
    """
    try:
        if sess is None:
            async with ClientSession() as sess:
                if method == 'get':
                    async with sess.get(
                        url=url, headers=header, params=params
                    ) as res:
                        result = await res.json()
                else:
                    async with sess.post(
                        url=url, headers=header, json=data
                    ) as res:
                        result = await res.json()
            return result
        else:
            if method == 'get':
                async with sess.get(
                    url=url, headers=header, params=params
                ) as res:
                    result = await res.json()
            else:
                async with sess.post(
                    url=url, headers=header, json=data
                ) as res:
                    result = await res.json()
            return result
    except:
        logger.exception('访问{}失败！'.format(url))
        return {}


async def get_stoken_by_login_ticket(loginticket: str, mys_id: str) -> dict:
    data = await _mhy_request(
        url=GET_STOKEN_URL,
        method='get',
        header=_HEADER,
        params={
            'login_ticket': loginticket,
            'token_types': '3',
            'uid': mys_id,
        },
    )
    return data


async def get_cookie_token_by_stoken(stoken: str, mys_id: str) -> dict:
    HEADER = copy.deepcopy(_HEADER)
    HEADER['Cookie'] = f'stuid={mys_id};stoken={stoken}'
    data = await _mhy_request(
        url=GET_COOKIE_TOKEN_URL,
        method='get',
        header=HEADER,
        params={
            'stoken': stoken,
            'uid': mys_id,
        },
    )
    return data


async def get_daily_data(uid: str, server_id: str = 'cn_gf01') -> dict:
    if uid[0] == '5':
        server_id = 'cn_qd01'
    HEADER = copy.deepcopy(_HEADER)
    HEADER['Cookie'] = await owner_cookies(uid)
    HEADER['DS'] = get_ds_token('role_id=' + uid + '&server=' + server_id)
    data = await _mhy_request(
        url=DAILY_NOTE_URL,
        method='get',
        header=HEADER,
        params={'server': server_id, 'role_id': uid},
    )
    return data


async def get_sign_list() -> dict:
    data = await _mhy_request(
        url=SIGN_LIST_URL,
        method='get',
        header=_HEADER,
        params={'act_id': 'e202009291139501'},
    )
    return data


async def get_sign_info(uid, server_id='cn_gf01') -> dict:
    if uid[0] == '5':
        server_id = 'cn_qd01'
    HEADER = copy.deepcopy(_HEADER)
    HEADER['Cookie'] = await owner_cookies(uid)
    data = await _mhy_request(
        url=SIGN_INFO_URL,
        method='get',
        header=HEADER,
        params={'act_id': 'e202009291139501', 'region': server_id, 'uid': uid},
    )
    return data


async def mihoyo_bbs_sign(uid, server_id='cn_gf01') -> dict:
    if uid[0] == '5':
        server_id = 'cn_qd01'
    HEADER = copy.deepcopy(_HEADER)
    HEADER['User_Agent'] = (
        'Mozilla/5.0 (Linux; Android 10; MIX 2 Build/QKQ1.190825.002; wv) AppleWebKit/537.36 ('
        'KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.101 Mobile Safari/537.36 '
        'miHoYoBBS/2.3.0'
    )
    HEADER['Cookie'] = await owner_cookies(uid)
    HEADER['x-rpc-device_id'] = random_hex(32)
    HEADER['x-rpc-app_version'] = '2.28.1'
    HEADER['x-rpc-client_type'] = '2'
    HEADER['X_Requested_With'] = 'com.mihoyo.hyperion'
    HEADER['DS'] = old_version_get_ds_token(True)
    HEADER['Referer'] = (
        'https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html?bbs_auth_required=true&act_id'
        '=e202009291139501&utm_source=bbs&utm_medium=mys&utm_campaign=icon'
    )
    data = await _mhy_request(
        url=SIGN_URL,
        method='post',
        header=HEADER,
        data={'act_id': 'e202009291139501', 'uid': uid, 'region': server_id},
    )
    return data


async def get_award(uid, server_id='cn_gf01') -> dict:
    if uid[0] == '5':
        server_id = 'cn_qd01'
    HEADER = copy.deepcopy(_HEADER)
    HEADER['Cookie'] = await owner_cookies(uid)
    HEADER['DS'] = old_version_get_ds_token()
    HEADER['x-rpc-device_id'] = random_hex(32)
    data = await _mhy_request(
        url=MONTHLY_AWARD_URL,
        method='get',
        header=HEADER,
        params={
            'act_id': 'e202009291139501',
            'bind_region': server_id,
            'bind_uid': uid,
            'month': '0',
            'bbs_presentation_style': 'fullscreen',
            'bbs_auth_required': 'true',
            'utm_source': 'bbs',
            'utm_medium': 'mys',
            'utm_campaign': 'icon',
        },
    )
    return data


async def get_info(uid, ck, server_id='cn_gf01') -> dict:
    if uid[0] == '5':
        server_id = 'cn_qd01'
    HEADER = copy.deepcopy(_HEADER)
    HEADER['Cookie'] = ck
    HEADER['DS'] = get_ds_token('role_id=' + uid + '&server=' + server_id)
    data = await _mhy_request(
        url=PLAYER_INFO_URL,
        method='get',
        header=HEADER,
        params={'server': server_id, 'role_id': uid},
    )
    return data


async def get_spiral_abyss_info(
    uid, ck, schedule_type='1', server_id='cn_gf01'
) -> dict:
    if uid[0] == '5':
        server_id = 'cn_qd01'
    HEADER = copy.deepcopy(_HEADER)
    HEADER['Cookie'] = ck
    HEADER['DS'] = get_ds_token(
        'role_id='
        + uid
        + '&schedule_type='
        + schedule_type
        + '&server='
        + server_id
    )
    data = await _mhy_request(
        url=PLAYER_ABYSS_INFO_URL,
        method='get',
        header=HEADER,
        params={
            'server': server_id,
            'role_id': uid,
            'schedule_type': schedule_type,
        },
    )
    return data


async def get_character(uid, character_ids, ck, server_id='cn_gf01') -> dict:
    if uid[0] == '5':
        server_id = 'cn_qd01'
    HEADER = copy.deepcopy(_HEADER)
    HEADER['Cookie'] = ck
    HEADER['DS'] = get_ds_token(
        '',
        {'character_ids': character_ids, 'role_id': uid, 'server': server_id},
    )
    data = await _mhy_request(
        url=PLAYER_DETAIL_INFO_URL,
        method='post',
        header=HEADER,
        data={
            'character_ids': character_ids,
            'role_id': uid,
            'server': server_id,
        },
    )
    return data


async def get_calculate_info(
    client: ClientSession, uid, char_id, ck, name, server_id='cn_gf01'
):
    if uid[0] == '5':
        server_id = 'cn_qd01'
    HEADER = copy.deepcopy(_HEADER)
    HEADER['Cookie'] = ck
    HEADER['DS'] = get_ds_token(
        'uid={}&avatar_id={}&region={}'.format(uid, char_id, server_id)
    )
    req = await client.get(
        url=CALCULATE_INFO_URL,
        headers=HEADER,
        params={'avatar_id': char_id, 'uid': uid, 'region': server_id},
    )
    data = await req.json()
    data.update({'name': name})
    return data


async def get_mihoyo_bbs_info(mysid: str, ck: Optional[str] = None) -> dict:
    """
    :说明:
      返回米游社账号对应的游戏角色信息。
      包括原神, 崩坏3 等等。
      mys_data['data']['list']是一个列表，
      每个元素是一个字典, 对应每一个游戏
      ```原神的'game_id' = 2```
    :参数:
      * mysid (str): 米游社通行证。
      * ck (str): 米游社Cookie。
    :返回:
      * mys_data (dict): 米游社账号的游戏角色信息。
    """
    if ck is None:
        ck = str(await cache_db(mysid))
    HEADER = copy.deepcopy(_HEADER)
    HEADER['Cookie'] = ck
    HEADER['DS'] = get_ds_token('uid=' + mysid)
    data = await _mhy_request(
        url=MIHOYO_BBS_PLAYER_INFO_URL,
        method='get',
        header=HEADER,
        params={'uid': mysid},
    )
    return data

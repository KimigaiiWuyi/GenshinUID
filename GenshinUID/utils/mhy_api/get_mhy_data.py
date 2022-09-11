import copy
import time
import random
import asyncio
from typing import Any, Dict, Literal, Optional

from nonebot.log import logger
from aiohttp import ClientSession

from ..db_operation.db_operation import cache_db, get_stoken, owner_cookies
from ..mhy_api.mhy_api_tools import (
    random_hex,
    random_text,
    get_ds_token,
    old_version_get_ds_token,
)
from ..mhy_api.mhy_api import (
    SIGN_URL,
    SIGN_INFO_URL,
    SIGN_LIST_URL,
    DAILY_NOTE_URL,
    GET_STOKEN_URL,
    GET_AUTHKEY_URL,
    PLAYER_INFO_URL,
    GET_GACHA_LOG_URL,
    MONTHLY_AWARD_URL,
    CALCULATE_INFO_URL,
    GET_COOKIE_TOKEN_URL,
    PLAYER_ABYSS_INFO_URL,
    PLAYER_DETAIL_INFO_URL,
    MIHOYO_BBS_PLAYER_INFO_URL,
)

gacha_type_meta_data = {
    '新手祈愿': ['100'],
    '常驻祈愿': ['200'],
    '角色祈愿': ['301', '400'],
    '武器祈愿': ['302'],
}

mhyVersion = '2.11.1'

_HEADER = {
    'x-rpc-app_version': mhyVersion,
    'User-Agent': (
        'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) '
        'AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1'
    ),
    'x-rpc-client_type': '5',
    'Referer': 'https://webstatic.mihoyo.com/',
    'Origin': 'https://webstatic.mihoyo.com',
}


async def get_gacha_log_by_authkey(
    uid: str, old_data: Optional[dict] = None
) -> Optional[dict]:
    server_id = 'cn_qd01' if uid[0] == '5' else 'cn_gf01'
    authkey_rawdata = await get_authkey_by_cookie(uid)
    if authkey_rawdata == {} or authkey_rawdata is None:
        return None
    if 'data' in authkey_rawdata and 'authkey' in authkey_rawdata['data']:
        authkey = authkey_rawdata['data']['authkey']
    else:
        return None
    full_data = old_data or {'新手祈愿': [], '常驻祈愿': [], '角色祈愿': [], '武器祈愿': []}
    temp = []
    for gacha_name in gacha_type_meta_data:
        for gacha_type in gacha_type_meta_data[gacha_name]:
            end_id = 0
            for page in range(1, 999):
                raw_data = await _mhy_request(
                    url=GET_GACHA_LOG_URL,
                    method='GET',
                    header=_HEADER,
                    params={
                        'authkey_ver': '1',
                        'sign_type': '2',
                        'auth_appid': 'webview_gacha',
                        'init_type': '200',
                        'gacha_id': 'fecafa7b6560db5f3182222395d88aaa6aaac1bc',
                        'timestamp': str(int(time.time())),
                        'lang': 'zh-cn',
                        'device_type': 'mobile',
                        'plat_type': 'ios',
                        'region': server_id,
                        'authkey': authkey,
                        'game_biz': 'hk4e_cn',
                        'gacha_type': gacha_type,
                        'page': page,
                        'size': '20',
                        'end_id': end_id,
                    },
                )

                if 'data' in raw_data and 'list' in raw_data['data']:
                    data = raw_data['data']['list']
                else:
                    logger.warning(raw_data)
                    return {}
                if data == []:
                    break
                end_id = data[-1]["id"]
                if data[-1] in full_data[gacha_name]:
                    for item in data:
                        if item not in full_data[gacha_name]:
                            temp.append(item)
                    full_data[gacha_name][0:0] = temp
                    temp = []
                    break
                if len(full_data[gacha_name]) >= 1:
                    if int(data[-1]['id']) <= int(
                        full_data[gacha_name][0]['id']
                    ):
                        full_data[gacha_name].extend(data)
                    else:
                        full_data[gacha_name][0:0] = data
                else:
                    full_data[gacha_name].extend(data)
                await asyncio.sleep(0.7)
    return full_data


async def get_authkey_by_cookie(uid: str) -> dict:
    server_id = 'cn_qd01' if uid[0] == '5' else 'cn_gf01'
    HEADER = copy.deepcopy(_HEADER)
    stoken = await get_stoken(uid)
    if stoken == '该用户没有绑定过Stoken噢~' or stoken == '':
        return {}
    HEADER['Cookie'] = stoken
    HEADER['DS'] = old_version_get_ds_token(True)
    HEADER['User-Agent'] = 'okhttp/4.8.0'
    HEADER['x-rpc-app_version'] = '2.35.2'
    HEADER['x-rpc-sys_version'] = '12'
    HEADER['x-rpc-client_type'] = '5'
    HEADER['x-rpc-channel'] = 'mihoyo'
    HEADER['x-rpc-device_id'] = random_hex(32)
    HEADER['x-rpc-device_name'] = random_text(random.randint(1, 10))
    HEADER['x-rpc-device_model'] = 'Mi 10'
    HEADER['Referer'] = 'https://app.mihoyo.com'
    HEADER['Host'] = 'api-takumi.mihoyo.com'
    authkey = await _mhy_request(
        url=GET_AUTHKEY_URL,
        method='POST',
        header=HEADER,
        data={
            'auth_appid': 'webview_gacha',
            'game_biz': 'hk4e_cn',
            'game_uid': uid,
            'region': server_id,
        },
    )

    return authkey


async def get_stoken_by_login_ticket(loginticket: str, mys_id: str) -> dict:
    data = await _mhy_request(
        url=GET_STOKEN_URL,
        method='GET',
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
        method='GET',
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
    HEADER['DS'] = get_ds_token(f'role_id={uid}&server={server_id}')
    data = await _mhy_request(
        url=DAILY_NOTE_URL,
        method='GET',
        header=HEADER,
        params={'server': server_id, 'role_id': uid},
    )

    return data


async def get_sign_list() -> dict:
    data = await _mhy_request(
        url=SIGN_LIST_URL,
        method='GET',
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
        method='GET',
        header=HEADER,
        params={'act_id': 'e202009291139501', 'region': server_id, 'uid': uid},
    )
    return data


async def mihoyo_bbs_sign(uid, ua=None, server_id='cn_gf01') -> dict:
    if uid[0] == '5':
        server_id = 'cn_qd01'
    HEADER = copy.deepcopy(_HEADER)
    if ua == 'iphone':
        HEADER['User-Agent'] = (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
            'AppleWebKit/605.1.15 (KHTML, like Gecko) '
            'miHoYoBBS/miHoYoBBS/2.35.2'
        )
    else:
        HEADER['User_Agent'] = (
            'Mozilla/5.0 (Linux; Android 10; MIX 2 Build/QKQ1.190825.002; wv) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
            'Chrome/83.0.4103.101 Mobile Safari/537.36 miHoYoBBS/2.35.2'
        )
    HEADER['Cookie'] = await owner_cookies(uid)
    HEADER['x-rpc-device_id'] = random_hex(32)
    HEADER['x-rpc-app_version'] = '2.35.2'
    HEADER['x-rpc-client_type'] = '5'
    HEADER['X_Requested_With'] = 'com.mihoyo.hyperion'
    HEADER['DS'] = old_version_get_ds_token(True)
    HEADER['Referer'] = (
        'https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html'
        '?bbs_auth_required=true&act_id=e202009291139501&utm_source=bbs'
        '&utm_medium=mys&utm_campaign=icon'
    )
    data = await _mhy_request(
        url=SIGN_URL,
        method='POST',
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
        method='GET',
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
    HEADER['DS'] = get_ds_token(f'role_id={uid}&server={server_id}')
    data = await _mhy_request(
        url=PLAYER_INFO_URL,
        method='GET',
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
        f'role_id={uid}&schedule_type={schedule_type}&server={server_id}'
    )
    data = await _mhy_request(
        url=PLAYER_ABYSS_INFO_URL,
        method='GET',
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
        method='POST',
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
        f'uid={uid}&avatar_id={char_id}&region={server_id}'
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
    '''
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
    '''
    if ck is None:
        ck = str(await cache_db(mysid))
    HEADER = copy.deepcopy(_HEADER)
    HEADER['Cookie'] = ck
    HEADER['DS'] = get_ds_token(f'uid={mysid}')
    data = await _mhy_request(
        url=MIHOYO_BBS_PLAYER_INFO_URL,
        method='GET',
        header=HEADER,
        params={'uid': mysid},
    )
    return data


async def _mhy_request(
    url: str,
    method: Literal['GET', 'POST'] = 'GET',
    header: Dict[str, Any] = _HEADER,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    sess: Optional[ClientSession] = None,
) -> dict:
    '''
    :说明:
      访问URL并进行json解析返回。
    :参数:
      * url (str): MihoyoAPI。
      * method (Literal["GET", "POST"]): `POST` or `GET`。
      * header (Dict[str, Any]): 默认为_HEADER。
      * params (Dict[str, Any]): 参数。
      * data (Dict[str, Any]): 参数(`post`方法需要传)。
      * sess (ClientSession): 可选, 指定client。
    :返回:
      * result (dict): json.loads()解析字段。
    '''
    is_temp_sess = False
    if sess is None:
        sess = ClientSession()
        is_temp_sess = True
    try:
        req = await sess.request(
            method, url=url, headers=header, params=params, json=data
        )
        return await req.json()
    except Exception:
        logger.exception(f'访问{url}失败！')
        return {}
    finally:
        if is_temp_sess:
            await sess.close()

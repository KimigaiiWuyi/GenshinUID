import copy
import json
import time
import uuid
import random
import asyncio
from string import digits, ascii_letters
from typing import Any, Dict, Literal, Optional

from nonebot.log import logger
from aiohttp import ClientSession

from .mhy_api import VERIFY_URL, VERIFICATION_URL
from ...genshinuid_config.default_config import string_config
from ..db_operation.db_operation import cache_db, get_stoken, owner_cookies
from ..mhy_api.mhy_api_tools import (
    random_hex,
    random_text,
    get_ds_token,
    gen_payment_sign,
    generate_passport_ds,
    generate_dynamic_secret,
    old_version_get_ds_token,
)
from ..mhy_api.mhy_api import (  # noqa
    GCG_INFO,
    SIGN_URL,
    GET_STOKEN,
    GCG_INFO_OS,
    REG_TIME_CN,
    REG_TIME_OS,
    SIGN_URL_OS,
    CHECK_QRCODE,
    CREATE_QRCODE,
    SIGN_INFO_URL,
    SIGN_LIST_URL,
    DAILY_NOTE_URL,
    GET_STOKEN_URL,
    HK4E_LOGIN_URL,
    GET_AUTHKEY_URL,
    PLAYER_INFO_URL,
    SIGN_INFO_URL_OS,
    SIGN_LIST_URL_OS,
    DAILY_NOTE_URL_OS,
    GET_GACHA_LOG_URL,
    HK4E_LOGIN_URL_OS,
    MONTHLY_AWARD_URL,
    CALCULATE_INFO_URL,
    PLAYER_INFO_URL_OS,
    GET_COOKIE_TOKEN_URL,
    MONTHLY_AWARD_URL_OS,
    CALCULATE_INFO_URL_OS,
    PLAYER_ABYSS_INFO_URL,
    PLAYER_DETAIL_INFO_URL,
    PLAYER_ABYSS_INFO_URL_OS,
    PLAYER_DETAIL_INFO_URL_OS,
    MIHOYO_BBS_PLAYER_INFO_URL,
    MIHOYO_BBS_PLAYER_INFO_URL_OS,
    GET_COOKIE_TOKEN_BY_GAME_TOKEN,
    CheckOrderurl,
    CreateOrderurl,
    fetchGoodsurl,
)

PROXY_URL = string_config.get_config('proxy')

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

_HEADER_OS = {
    'x-rpc-app_version': '1.5.0',
    'x-rpc-client_type': '4',
    'x-rpc-language': 'zh-cn',
}

RECOGNIZE_SERVER = {
    '1': 'cn_gf01',
    '2': 'cn_gf01',
    '5': 'cn_qd01',
    '6': 'os_usa',
    '7': 'os_euro',
    '8': 'os_asia',
    '9': 'os_cht',
}

ATTR = vars()


async def get_gacha_log_by_authkey(
    uid: str, old_data: Optional[dict] = None, is_force: bool = False
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
                await asyncio.sleep(0.9)
                if 'data' in raw_data and 'list' in raw_data['data']:
                    data = raw_data['data']['list']
                else:
                    logger.warning(raw_data)
                    return {}
                if data == []:
                    break
                end_id = data[-1]['id']
                if data[-1] in full_data[gacha_name] and not is_force:
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
                await asyncio.sleep(0.5)
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


async def get_cookie_token_by_stoken(
    stoken: str, mys_id: str, full_sk: Optional[str] = None
) -> dict:
    HEADER = copy.deepcopy(_HEADER)
    if full_sk:
        HEADER['Cookie'] = full_sk
    else:
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


async def get_daily_data(uid: str) -> dict:
    return await basic_mhy_req('DAILY_NOTE_URL', uid)


async def get_sign_list(uid) -> dict:
    # server_id = RECOGNIZE_SERVER.get(str(uid)[0])
    if int(str(uid)[0]) < 6:
        data = await _mhy_request(
            url=SIGN_LIST_URL,
            method='GET',
            header=_HEADER,
            params={'act_id': 'e202009291139501'},
        )
    else:
        data = await _mhy_request(
            url=SIGN_LIST_URL_OS,
            method='GET',
            header=_HEADER_OS,
            params={
                'act_id': 'e202102251931481',
                'lang': 'zh-cn',
            },
            use_proxy=True,
        )
    return data


async def get_sign_info(uid) -> dict:
    server_id = RECOGNIZE_SERVER.get(str(uid)[0])
    if int(str(uid)[0]) < 6:
        HEADER = copy.deepcopy(_HEADER)
        HEADER['Cookie'] = await owner_cookies(uid)
        data = await _mhy_request(
            url=SIGN_INFO_URL,
            method='GET',
            header=HEADER,
            params={
                'act_id': 'e202009291139501',
                'region': server_id,
                'uid': uid,
            },
        )
    else:
        HEADER = copy.deepcopy(_HEADER_OS)
        HEADER['Cookie'] = await owner_cookies(uid)
        HEADER['DS'] = generate_dynamic_secret()
        data = await _mhy_request(
            url=SIGN_INFO_URL_OS,
            method='GET',
            header=HEADER,
            params={
                'act_id': 'e202102251931481',
                'lang': 'zh-cn',
                'region': server_id,
                'uid': uid,
            },
            use_proxy=True,
        )
    return data


async def mihoyo_bbs_sign(uid, Header={}, server_id='cn_gf01') -> dict:
    server_id = RECOGNIZE_SERVER.get(str(uid)[0])
    if int(str(uid)[0]) < 6:
        HEADER = copy.deepcopy(_HEADER)
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
        HEADER.update(Header)
        data = await _mhy_request(
            url=SIGN_URL,
            method='POST',
            header=HEADER,
            data={
                'act_id': 'e202009291139501',
                'uid': uid,
                'region': server_id,
            },
        )
    else:
        HEADER = copy.deepcopy(_HEADER_OS)
        HEADER['Cookie'] = await owner_cookies(uid)
        HEADER['DS'] = generate_dynamic_secret()
        HEADER.update(Header)
        data = await _mhy_request(
            url=SIGN_URL_OS,
            method='POST',
            header=HEADER,
            data={
                'act_id': 'e202102251931481',
                'lang': 'zh-cn',
                'uid': uid,
                'region': server_id,
            },
            use_proxy=True,
        )
    return data


async def get_award(uid) -> dict:
    server_id = RECOGNIZE_SERVER.get(str(uid)[0])
    if int(str(uid)[0]) < 6:
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
    else:
        HEADER = copy.deepcopy(_HEADER_OS)
        HEADER['Cookie'] = await owner_cookies(uid)
        HEADER['x-rpc-device_id'] = random_hex(32)
        HEADER['DS'] = generate_dynamic_secret()
        data = await _mhy_request(
            url=MONTHLY_AWARD_URL_OS,
            method='GET',
            header=HEADER,
            params={
                'act_id': 'e202009291139501',
                'region': server_id,
                'uid': uid,
                'month': '0',
            },
            use_proxy=True,
        )
    return data


async def get_info(uid, ck) -> dict:
    return await basic_mhy_req('PLAYER_INFO_URL', uid, ck)


async def get_spiral_abyss_info(uid, ck, schedule_type='1') -> dict:
    server_id = RECOGNIZE_SERVER.get(str(uid)[0])
    if int(str(uid)[0]) < 6:
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
    else:
        HEADER = copy.deepcopy(_HEADER_OS)
        HEADER['Cookie'] = ck
        HEADER['DS'] = generate_dynamic_secret()
        data = await _mhy_request(
            url=PLAYER_ABYSS_INFO_URL_OS,
            method='GET',
            header=HEADER,
            params={
                'server': server_id,
                'role_id': uid,
                'schedule_type': schedule_type,
            },
            use_proxy=True,
        )
    return data


async def get_character(uid, character_ids, ck) -> dict:
    server_id = RECOGNIZE_SERVER.get(str(uid)[0])
    if int(str(uid)[0]) < 6:
        HEADER = copy.deepcopy(_HEADER)
        HEADER['Cookie'] = ck
        HEADER['DS'] = get_ds_token(
            '',
            {
                'character_ids': character_ids,
                'role_id': uid,
                'server': server_id,
            },
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
    else:
        HEADER = copy.deepcopy(_HEADER_OS)
        HEADER['Cookie'] = ck
        HEADER['DS'] = generate_dynamic_secret()
        data = await _mhy_request(
            url=PLAYER_DETAIL_INFO_URL_OS,
            method='POST',
            header=HEADER,
            data={
                'character_ids': character_ids,
                'role_id': uid,
                'server': server_id,
            },
            use_proxy=True,
        )
    return data


async def get_calculate_info(client: ClientSession, uid, char_id, ck, name):
    server_id = RECOGNIZE_SERVER.get(str(uid)[0])
    if int(str(uid)[0]) < 6:
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
    else:
        HEADER = copy.deepcopy(_HEADER_OS)
        HEADER['Cookie'] = ck
        HEADER['DS'] = generate_dynamic_secret()
        req = await client.get(
            url=CALCULATE_INFO_URL_OS,
            headers=HEADER,
            params={'avatar_id': char_id, 'uid': uid, 'region': server_id},
            proxy=PROXY_URL,
        )
        data = await req.json()
        data.update({'name': name})
    return data


async def get_mihoyo_bbs_info(
    mysid: str, ck: Optional[str] = None, is_os: Optional[bool] = False
) -> dict:
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
    if is_os:
        HEADER['DS'] = generate_dynamic_secret()
        URL = MIHOYO_BBS_PLAYER_INFO_URL_OS
    else:
        HEADER['DS'] = get_ds_token(f'uid={mysid}')
        URL = MIHOYO_BBS_PLAYER_INFO_URL
    data = await _mhy_request(
        url=URL,
        method='GET',
        header=HEADER,
        params={'uid': mysid},
        use_proxy=is_os,
    )
    return data


async def get_gcg_info(uid: str):
    return await basic_mhy_req('GCG_INFO', uid)


async def create_qrcode_url():
    device_id: str = ''.join(random.choices(ascii_letters + digits, k=64))
    app_id: str = '8'
    data = await _mhy_request(
        CREATE_QRCODE,
        'POST',
        header={},
        data={'app_id': app_id, 'device': device_id},
    )
    url = data['data']['url']
    ticket = url.split('ticket=')[1]
    return {
        'app_id': app_id,
        'ticket': ticket,
        'device': device_id,
        'url': url,
    }


async def check_qrcode(app_id: str, ticket: str, device: str):
    return await _mhy_request(
        CHECK_QRCODE,
        'POST',
        data={
            'app_id': app_id,
            'ticket': ticket,
            'device': device,
        },
    )


async def get_cookie_token(token: str, uid: str):
    return await _mhy_request(
        GET_COOKIE_TOKEN_BY_GAME_TOKEN,
        'GET',
        params={
            'game_token': token,
            'account_id': uid,
        },
    )


async def basic_mhy_req(URL: str, uid: str, ck: Optional[str] = None) -> Dict:
    if ck is None:
        ck = await owner_cookies(uid)
        if '该用户没有绑定过Cookies' in ck:
            CK = await cache_db(uid)
            if isinstance(CK, str):
                return {}
            ck = CK.CK

    server_id = RECOGNIZE_SERVER.get(str(uid)[0])
    _URL = ATTR[URL]
    _URL_OS = ATTR[f'{URL}_OS']
    if int(str(uid)[0]) < 6:
        HEADER = copy.deepcopy(_HEADER)
        HEADER['Cookie'] = ck
        HEADER['DS'] = get_ds_token(f'role_id={uid}&server={server_id}')
        data = await _mhy_request(
            url=_URL,
            method='GET',
            header=HEADER,
            params={'server': server_id, 'role_id': uid},
        )
    else:
        HEADER = copy.deepcopy(_HEADER_OS)
        HEADER['Cookie'] = ck
        HEADER['DS'] = generate_dynamic_secret()
        data = await _mhy_request(
            url=_URL_OS,
            method='GET',
            header=HEADER,
            params={'server': server_id, 'role_id': uid},
            use_proxy=True,
        )
    return data


async def get_stoken_by_game_token(account_id: int, game_token: str):
    data = {
        'account_id': account_id,
        'game_token': game_token,
    }
    return await _mhy_request(
        GET_STOKEN,
        'POST',
        {
            'x-rpc-app_version': '2.41.0',
            'DS': generate_passport_ds(b=data),
            'x-rpc-aigis': '',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-rpc-game_biz': 'bbs_cn',
            'x-rpc-sys_version': '11',
            'x-rpc-device_id': uuid.uuid4().hex,
            'x-rpc-device_fp': ''.join(
                random.choices(ascii_letters + digits, k=13)
            ),
            'x-rpc-device_name': 'GenshinUid_login_device_lulu',
            'x-rpc-device_model': 'GenshinUid_login_device_lulu',
            'x-rpc-app_id': 'bll8iq97cem8',
            'x-rpc-client_type': '2',
            'User-Agent': 'okhttp/4.8.0',
        },
        data=data,
    )


async def _pass(gt: str, ch: str, header: Dict):
    # 警告：使用该服务（例如某RR等）需要注意风险问题
    # 本项目不以任何形式提供相关接口
    # 代码来源：GITHUB项目MIT开源
    _pass_api = string_config.get_config('_pass_API')
    if _pass_api:
        logger.info('正在进行加强跳过验证...')
        data = await _mhy_request(
            url=f'{_pass_api}&gt={gt}&challenge={ch}',
            method='GET',
            header=header,
        )
        if 'data' in data and 'validate' in data['data']:
            validate = data['data']['validate']
            ch = data['data']['challenge']
        else:
            return None, None
    else:
        validate = None
        '''
        logger.warning('开始普通无感验证...')
        header['DS'] = get_ds_token(f'gt={gt}')
        _ = await _mhy_request(
            url=GT_TPYE_URL.format(gt),
            method='GET',
            header=header,
        )
        header['DS'] = get_ds_token(f'gt={gt}&challenge={ch}')
        data = await _mhy_request(
            url=GT_TEST_URL_V6.format(gt, ch),
            method='GET',
            header=header,
        )
        validate = data['data']['validate']
        '''

    return validate, ch


async def _upass(header: Dict):
    # 警告：使用该服务（例如某RR等）需要注意风险问题
    # 本项目不以任何形式提供相关接口
    # 代码来源：GITHUB项目MIT开源
    header['DS'] = get_ds_token('is_high=false')
    raw_data = await _mhy_request(
        url=VERIFICATION_URL,
        method='GET',
        header=header,
    )
    gt = raw_data['data']['gt']
    ch = raw_data['data']['challenge']

    vl, ch = await _pass(gt, ch, header)

    if vl:
        header['DS'] = get_ds_token(
            '',
            {
                'geetest_challenge': ch,
                'geetest_validate': vl,
                'geetest_seccode': f'{vl}|jordan',
            },
        )
        _ = await _mhy_request(
            url=VERIFY_URL,
            method='POST',
            header=header,
            data={
                'geetest_challenge': ch,
                'geetest_validate': vl,
                'geetest_seccode': f'{vl}|jordan',
            },
        )
    else:
        return True


async def _mhy_request(
    url: str,
    method: Literal['GET', 'POST'] = 'GET',
    header: Dict[str, Any] = _HEADER,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    sess: Optional[ClientSession] = None,
    use_proxy: Optional[bool] = False,
) -> dict:
    '''
    :说明:
      访问URL并进行json解析返回。
    :参数:
      * url (str): MihoyoAPI。
      * method (Literal['GET', 'POST']): `POST` or `GET`。
      * header (Dict[str, Any]): 默认为_HEADER。
      * params (Dict[str, Any]): 参数。
      * data (Dict[str, Any]): 参数(`post`方法需要传)。
      * sess (ClientSession): 可选, 指定client。
      * use_proxy (bool): 是否使用proxy
    :返回:
      * result (dict): json.loads()解析字段。
    '''
    is_temp_sess = False
    if sess is None:
        sess = ClientSession()
        is_temp_sess = True
    try:
        req = await sess.request(
            method,
            url=url,
            headers=header,
            params=params,
            json=data,
            proxy=PROXY_URL if use_proxy else None,
            timeout=300,
        )
        text_data = await req.text()
        # DEBUG 日志
        logger.debug(f'【mhy_request】请求如下:\n{text_data}')
        if text_data.startswith('('):
            text_data = json.loads(text_data.replace('(', '').replace(')', ''))
            return text_data
        raw_data = await req.json()
        if 'retcode' in raw_data and raw_data['retcode'] == 1034:
            await _upass(header)
        return raw_data
    except Exception:
        logger.exception(f'访问{url}失败！')
        return {'retcode': -1}
    finally:
        if is_temp_sess:
            await sess.close()


async def get_hk4e_token(uid: str):
    # 获取e_hk4e_token
    server_id = RECOGNIZE_SERVER.get(uid[0])
    header = {
        'Cookie': await owner_cookies(uid),
        'Content-Type': 'application/json;charset=UTF-8',
        'Referer': 'https://webstatic.mihoyo.com/',
        'Origin': 'https://webstatic.mihoyo.com',
    }
    use_proxy = False
    data = {
        'game_biz': 'hk4e_cn',
        'lang': 'zh-cn',
        'uid': f'{uid}',
        'region': f'{server_id}',
    }
    if int(str(uid)[0]) < 6:
        url = HK4E_LOGIN_URL
    else:
        url = HK4E_LOGIN_URL_OS
        data['game_biz'] = 'hk4e_global'
        use_proxy = True

    async with ClientSession() as client:
        async with client.request(
            method='POST',
            url=url,
            headers=header,
            json=data,
            proxy=PROXY_URL if use_proxy else None,
            timeout=300,
        ) as resp:
            raw_data = await resp.json()
            if 'retcode' in raw_data and raw_data['retcode'] == 0:
                _k = resp.cookies['e_hk4e_token'].key
                _v = resp.cookies['e_hk4e_token'].value
                ck = f'{_k}={_v}'
                return ck
            if 'retcode' in raw_data and raw_data['retcode'] == 1034:
                await _upass(header)


async def get_regtime_data(uid: str) -> Any:
    server_id = RECOGNIZE_SERVER.get(uid[0])
    hk4e_token = await get_hk4e_token(uid)
    ck_token = await owner_cookies(uid)
    params = {
        'game_biz': 'hk4e_cn',
        'lang': 'zh-cn',
        'badge_uid': uid,
        'badge_region': server_id,
    }
    if int(str(uid)[0]) < 6:
        HEADER = copy.deepcopy(_HEADER)
        HEADER['Cookie'] = f'{hk4e_token};{ck_token}'
        data = await _mhy_request(
            url=REG_TIME_CN, method='GET', header=HEADER, params=params
        )
    else:
        HEADER = copy.deepcopy(_HEADER_OS)
        HEADER['Cookie'] = await owner_cookies(uid)
        HEADER['DS'] = generate_dynamic_secret()
        params['game_biz'] = 'hk4e_global'
        data = await _mhy_request(
            url=REG_TIME_OS,
            method='GET',
            header=HEADER,
            params=params,
            use_proxy=True,
        )
    return data


async def fetchgoods():
    data = {
        "released_flag": True,
        "game": "hk4e_cn",
        "region": "cn_gf01",
        "uid": "1",
        "account": "1",
    }
    goodslist = await _mhy_request(
        url=fetchGoodsurl,
        method='POST',
        data=data,
    )
    # print(json.dumps(goodslist.json(),indent=4,ensure_ascii=False))
    return goodslist["data"]["goods_list"]


async def topup(uid, goods):
    device_id = str(uuid.uuid4())
    HEADER = copy.deepcopy(_HEADER)
    HEADER["Cookie"] = await owner_cookies(uid)
    account = HEADER["Cookie"].split("account_id=")[1].split(";")[0]
    order = {
        "account": str(account),
        "region": "cn_gf01",
        "uid": uid,
        "delivery_url": "",
        "device": device_id,
        "channel_id": 1,
        "client_ip": "",
        "client_type": 4,
        "game": "hk4e_cn",
        "amount": goods["price"],
        # "amount": 600,
        "goods_num": 1,
        "goods_id": goods["goods_id"],
        "goods_title": f"{goods['goods_name']}×{str(goods['goods_unit'])}"
        if int(goods['goods_unit']) > 0
        else goods["goods_name"],
        "price_tier": goods["tier_id"],
        # "price_tier": "Tier_1",
        "currency": "CNY",
        "pay_plat": "alipay",
    }
    data = {"order": order, "sign": gen_payment_sign(order)}
    HEADER["x-rpc-device_id"] = device_id
    HEADER["x-rpc-client_type"] = "4"
    order = await _mhy_request(
        url=CreateOrderurl,
        method='POST',
        header=HEADER,
        data=data,
    )
    return order["data"]


async def checkorder(order, uid):
    HEADER = copy.deepcopy(_HEADER)
    HEADER["Cookie"] = await owner_cookies(uid)
    data = {
        "order_no": order["order_no"],
        "game": "hk4e_cn",
        "region": "cn_gf01",
        "uid": uid,
    }
    order = await _mhy_request(
        url=CheckOrderurl,
        method='GET',
        header=HEADER,
        params=data,
    )
    return order["data"]["status"]

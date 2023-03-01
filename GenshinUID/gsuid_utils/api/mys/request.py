'''
米游社 API 请求模块。
'''
from __future__ import annotations

import copy
import time
import uuid
import random
from abc import abstractmethod
from string import digits, ascii_letters
from typing import Any, Dict, List, Union, Literal, Optional, cast

from aiohttp import ClientSession

from .api import _API
from .tools import (
    random_hex,
    random_text,
    get_ds_token,
    generate_os_ds,
    get_web_ds_token,
    generate_passport_ds,
)
from .models import (
    GcgInfo,
    MysGame,
    MysSign,
    RegTime,
    GachaLog,
    SignInfo,
    SignList,
    AbyssData,
    IndexData,
    AuthKeyInfo,
    MonthlyAward,
    QrCodeStatus,
    CalculateInfo,
    DailyNoteData,
    GameTokenInfo,
    CharDetailData,
    CookieTokenInfo,
    LoginTicketInfo,
)

mysVersion = '2.44.1'
_HEADER = {
    'x-rpc-app_version': mysVersion,
    'User-Agent': (
        'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) '
        f'AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/{mysVersion}'
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


class MysApi:
    proxy_url: Optional[str] = None

    @abstractmethod
    async def _upass(self, header: Dict):
        ...

    @abstractmethod
    async def _pass(self, gt: str, ch: str, header: Dict):
        ...

    @abstractmethod
    async def get_ck(
        self, uid: str, mode: Literal['OWNER', 'RANDOM'] = 'RANDOM'
    ) -> Optional[str]:
        ...

    @abstractmethod
    async def get_stoken(self, uid: str) -> Optional[str]:
        ...

    async def get_upass_link(self, header: Dict) -> Union[int, Dict]:
        header['DS'] = get_ds_token('is_high=false')
        return await self._mys_request(
            url=_API['VERIFICATION_URL'],
            method='GET',
            header=header,
        )

    async def get_header_and_vl(self, header: Dict, ch, vl):
        header['DS'] = get_ds_token(
            '',
            {
                'geetest_challenge': ch,
                'geetest_validate': vl,
                'geetest_seccode': f'{vl}|jordan',
            },
        )
        _ = await self._mys_request(
            url=_API['VERIFY_URL'],
            method='POST',
            header=header,
            data={
                'geetest_challenge': ch,
                'geetest_validate': vl,
                'geetest_seccode': f'{vl}|jordan',
            },
        )

    def check_os(self, uid: str) -> bool:
        return False if int(str(uid)[0]) < 6 else True

    async def get_info(self, uid, ck: Optional[str]) -> Union[IndexData, int]:
        data = await self.simple_mys_req('PLAYER_INFO_URL', uid, cookie=ck)
        if isinstance(data, Dict):
            data = cast(IndexData, data['data'])
        return data

    async def get_daily_data(self, uid: str) -> Union[DailyNoteData, int]:
        data = await self.simple_mys_req('DAILY_NOTE_URL', uid)
        if isinstance(data, Dict):
            data = cast(DailyNoteData, data['data'])
        return data

    async def get_gcg_info(self, uid: str) -> Union[GcgInfo, int]:
        data = await self.simple_mys_req('GCG_INFO', uid)
        if isinstance(data, Dict):
            data = cast(GcgInfo, data['data'])
        return data

    async def get_cookie_token(
        self, token: str, uid: str
    ) -> Union[CookieTokenInfo, int]:
        data = await self._mys_request(
            _API['GET_COOKIE_TOKEN_BY_GAME_TOKEN'],
            'GET',
            params={
                'game_token': token,
                'account_id': uid,
            },
        )
        if isinstance(data, Dict):
            data = cast(CookieTokenInfo, data['data'])
        return data

    async def get_sign_list(self, uid) -> Union[SignList, int]:
        is_os = self.check_os(uid)
        if is_os:
            params = {
                'act_id': 'e202102251931481',
                'lang': 'zh-cn',
            }
        else:
            params = {'act_id': 'e202009291139501'}
        data = await self._mys_req_get('SIGN_LIST_URL', is_os, params)
        if isinstance(data, Dict):
            data = cast(SignList, data['data'])
        return data

    async def get_sign_info(self, uid) -> Union[SignInfo, int]:
        server_id = RECOGNIZE_SERVER.get(str(uid)[0])
        is_os = self.check_os(uid)
        if is_os:
            params = {
                'act_id': 'e202102251931481',
                'lang': 'zh-cn',
                'region': server_id,
                'uid': uid,
            }
            header = {
                'DS': generate_os_ds(),
            }
        else:
            params = {
                'act_id': 'e202009291139501',
                'region': server_id,
                'uid': uid,
            }
            header = {}
        data = await self._mys_req_get('SIGN_INFO_URL', is_os, params, header)
        if isinstance(data, Dict):
            data = cast(SignInfo, data['data'])
        return data

    async def mys_sign(
        self, uid, header={}, server_id='cn_gf01'
    ) -> Union[MysSign, int]:
        server_id = RECOGNIZE_SERVER.get(str(uid)[0])
        ck = await self.get_ck(uid, 'OWNER')
        if ck is None:
            return -51
        if int(str(uid)[0]) < 6:
            HEADER = copy.deepcopy(_HEADER)
            HEADER['Cookie'] = ck
            HEADER['x-rpc-device_id'] = random_hex(32)
            HEADER['x-rpc-app_version'] = '2.35.2'
            HEADER['x-rpc-client_type'] = '5'
            HEADER['X_Requested_With'] = 'com.mihoyo.hyperion'
            HEADER['DS'] = get_web_ds_token(True)
            HEADER['Referer'] = (
                'https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html'
                '?bbs_auth_required=true&act_id=e202009291139501'
                '&utm_source=bbs&utm_medium=mys&utm_campaign=icon'
            )
            HEADER.update(header)
            data = await self._mys_request(
                url=_API['SIGN_URL'],
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
            HEADER['Cookie'] = ck
            HEADER['DS'] = generate_os_ds()
            HEADER.update(header)
            data = await self._mys_request(
                url=_API['SIGN_URL_OS'],
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
        if isinstance(data, Dict):
            data = cast(MysSign, data['data'])
        return data

    async def get_award(self, uid) -> Union[MonthlyAward, int]:
        server_id = RECOGNIZE_SERVER.get(str(uid)[0])
        ck = await self.get_ck(uid, 'OWNER')
        if ck is None:
            return -51
        if int(str(uid)[0]) < 6:
            HEADER = copy.deepcopy(_HEADER)
            HEADER['Cookie'] = ck
            HEADER['DS'] = get_web_ds_token(True)
            HEADER['x-rpc-device_id'] = random_hex(32)
            data = await self._mys_request(
                url=_API['MONTHLY_AWARD_URL'],
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
            HEADER['Cookie'] = ck
            HEADER['x-rpc-device_id'] = random_hex(32)
            HEADER['DS'] = generate_os_ds()
            data = await self._mys_request(
                url=_API['MONTHLY_AWARD_URL_OS'],
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
        if isinstance(data, Dict):
            data = cast(MonthlyAward, data['data'])
        return data

    async def get_spiral_abyss_info(
        self, uid, schedule_type='1', ck: Optional[str] = None
    ) -> Union[AbyssData, int]:
        server_id = RECOGNIZE_SERVER.get(str(uid)[0])
        data = await self.simple_mys_req(
            'PLAYER_ABYSS_INFO_URL',
            uid,
            {
                'server': server_id,
                'role_id': uid,
                'schedule_type': schedule_type,
            },
            cookie=ck,
        )
        if isinstance(data, Dict):
            data = cast(AbyssData, data['data'])
        return data

    async def get_character(
        self, uid, character_ids, ck
    ) -> Union[CharDetailData, int]:
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
            data = await self._mys_request(
                _API['PLAYER_DETAIL_INFO_URL'],
                'POST',
                HEADER,
                data={
                    'character_ids': character_ids,
                    'role_id': uid,
                    'server': server_id,
                },
            )
        else:
            HEADER = copy.deepcopy(_HEADER_OS)
            HEADER['Cookie'] = ck
            HEADER['DS'] = generate_os_ds()
            data = await self._mys_request(
                _API['PLAYER_DETAIL_INFO_URL_OS'],
                'POST',
                HEADER,
                data={
                    'character_ids': character_ids,
                    'role_id': uid,
                    'server': server_id,
                },
                use_proxy=True,
            )
        if isinstance(data, Dict):
            data = cast(CharDetailData, data['data'])
        return data

    async def get_calculate_info(
        self, uid, char_id: int
    ) -> Union[CalculateInfo, int]:
        server_id = RECOGNIZE_SERVER.get(str(uid)[0])
        data = await self.simple_mys_req(
            'CALCULATE_INFO_URL',
            uid,
            {'avatar_id': char_id, 'uid': uid, 'region': server_id},
        )
        if isinstance(data, Dict):
            data = cast(CalculateInfo, data['data'])
        return data

    async def get_mihoyo_bbs_info(
        self,
        mys_id: str,
        cookie: Optional[str] = None,
        is_os: bool = False,
    ) -> Union[List[MysGame], int]:
        if not cookie:
            cookie = await self.get_ck(mys_id, 'OWNER')
        data = await self.simple_mys_req(
            'MIHOYO_BBS_PLAYER_INFO_URL',
            is_os,
            {'uid': mys_id},
            {'Cookie': cookie},
        )
        if isinstance(data, Dict):
            data = cast(List[MysGame], data['data']['list'])
        return data

    async def create_qrcode_url(self) -> Union[Dict, int]:
        device_id: str = ''.join(random.choices(ascii_letters + digits, k=64))
        app_id: str = '8'
        data = await self._mys_request(
            _API['CREATE_QRCODE'],
            'POST',
            header={},
            data={'app_id': app_id, 'device': device_id},
        )
        if isinstance(data, Dict):
            url: str = data['data']['url']
            ticket = url.split('ticket=')[1]
            return {
                'app_id': app_id,
                'ticket': ticket,
                'device': device_id,
                'url': url,
            }
        return data

    async def check_qrcode(
        self, app_id: str, ticket: str, device: str
    ) -> Union[QrCodeStatus, int]:
        data = await self._mys_request(
            _API['CHECK_QRCODE'],
            'POST',
            data={
                'app_id': app_id,
                'ticket': ticket,
                'device': device,
            },
        )
        if isinstance(data, Dict):
            data = cast(QrCodeStatus, data['data'])
        return data

    async def get_gacha_log_by_authkey(
        self,
        uid: str,
        gacha_type: str = '301',
        page: int = 1,
        end_id: str = '0',
    ) -> Union[int, GachaLog]:
        server_id = 'cn_qd01' if uid[0] == '5' else 'cn_gf01'
        authkey_rawdata = await self.get_authkey_by_cookie(uid)
        if isinstance(authkey_rawdata, int):
            return -1
        authkey = authkey_rawdata['authkey']
        data = await self._mys_request(
            url=_API['GET_GACHA_LOG_URL'],
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
        if isinstance(data, Dict):
            data = cast(GachaLog, data['data'])
        return data

    async def get_cookie_token_by_game_token(
        self, token: str, uid: str
    ) -> Union[CookieTokenInfo, int]:
        data = await self._mys_request(
            _API['GET_COOKIE_TOKEN_BY_GAME_TOKEN'],
            'GET',
            params={
                'game_token': token,
                'account_id': uid,
            },
        )
        if isinstance(data, Dict):
            data = cast(CookieTokenInfo, data['data'])
        return data

    async def get_cookie_token_by_stoken(
        self, stoken: str, mys_id: str, full_sk: Optional[str] = None
    ) -> Union[CookieTokenInfo, int]:
        HEADER = copy.deepcopy(_HEADER)
        if full_sk:
            HEADER['Cookie'] = full_sk
        else:
            HEADER['Cookie'] = f'stuid={mys_id};stoken={stoken}'
        data = await self._mys_request(
            url=_API['GET_COOKIE_TOKEN_URL'],
            method='GET',
            header=HEADER,
            params={
                'stoken': stoken,
                'uid': mys_id,
            },
        )
        if isinstance(data, Dict):
            data = cast(CookieTokenInfo, data['data'])
        return data

    async def get_stoken_by_login_ticket(
        self, lt: str, mys_id: str
    ) -> Union[LoginTicketInfo, int]:
        data = await self._mys_request(
            url=_API['GET_STOKEN_URL'],
            method='GET',
            header=_HEADER,
            params={
                'login_ticket': lt,
                'token_types': '3',
                'uid': mys_id,
            },
        )
        if isinstance(data, Dict):
            data = cast(LoginTicketInfo, data['data'])
        return data

    async def get_stoken_by_game_token(
        self, account_id: int, game_token: str
    ) -> Union[GameTokenInfo, int]:
        _data = {
            'account_id': account_id,
            'game_token': game_token,
        }
        data = await self._mys_request(
            _API['GET_STOKEN'],
            'POST',
            {
                'x-rpc-app_version': '2.41.0',
                'DS': generate_passport_ds(b=_data),
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
            data=_data,
        )
        if isinstance(data, Dict):
            data = cast(GameTokenInfo, data['data'])
        return data

    async def get_authkey_by_cookie(self, uid: str) -> Union[AuthKeyInfo, int]:
        server_id = RECOGNIZE_SERVER.get(str(uid)[0])
        HEADER = copy.deepcopy(_HEADER)
        stoken = await self.get_stoken(uid)
        if stoken is None:
            return -51
        HEADER['Cookie'] = stoken
        HEADER['DS'] = get_web_ds_token(True)
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
        data = await self._mys_request(
            url=_API['GET_AUTHKEY_URL'],
            method='POST',
            header=HEADER,
            data={
                'auth_appid': 'webview_gacha',
                'game_biz': 'hk4e_cn',
                'game_uid': uid,
                'region': server_id,
            },
        )
        if isinstance(data, Dict):
            data = cast(AuthKeyInfo, data['data'])
        return data

    async def get_hk4e_token(self, uid: str):
        # 获取e_hk4e_token
        server_id = RECOGNIZE_SERVER.get(uid[0])
        header = {
            'Cookie': await self.get_ck(uid, 'OWNER'),
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
            url = _API['HK4E_LOGIN_URL']
        else:
            url = _API['HK4E_LOGIN_URL_OS']
            data['game_biz'] = 'hk4e_global'
            use_proxy = True

        async with ClientSession() as client:
            async with client.request(
                method='POST',
                url=url,
                headers=header,
                json=data,
                proxy=self.proxy_url if use_proxy else None,
                timeout=300,
            ) as resp:
                raw_data = await resp.json()
                if 'retcode' in raw_data and raw_data['retcode'] == 0:
                    _k = resp.cookies['e_hk4e_token'].key
                    _v = resp.cookies['e_hk4e_token'].value
                    ck = f'{_k}={_v}'
                    return ck
                else:
                    return None

    async def get_regtime_data(self, uid: str) -> Union[RegTime, int]:
        hk4e_token = await self.get_hk4e_token(uid)
        ck_token = await self.get_ck(uid, 'OWNER')
        params = {
            'game_biz': 'hk4e_cn',
            'lang': 'zh-cn',
            'badge_uid': uid,
            'badge_region': RECOGNIZE_SERVER.get(uid[0]),
        }
        data = await self.simple_mys_req(
            'REG_TIME',
            uid,
            params,
            {'Cookie': f'{hk4e_token};{ck_token}' if int(uid[0]) <= 5 else {}},
        )
        if isinstance(data, Dict):
            return cast(RegTime, data['data'])
        else:
            return data

    async def simple_mys_req(
        self,
        URL: str,
        uid: Union[str, bool],
        params: Dict = {},
        header: Dict = {},
        cookie: Optional[str] = None,
    ) -> Union[Dict, int]:
        if isinstance(uid, bool):
            is_os = uid
            server_id = 'cn_qd01' if is_os else 'cn_gf01'
        else:
            server_id = RECOGNIZE_SERVER.get(str(uid)[0])
            is_os = False if int(str(uid)[0]) < 6 else True
        ex_params = '&'.join([f'{k}={v}' for k, v in params.items()])

        if is_os:
            _URL = _API[f'{URL}_OS']
            HEADER = copy.deepcopy(_HEADER_OS)
            HEADER['DS'] = generate_os_ds()
        else:
            _URL = _API[URL]
            HEADER = copy.deepcopy(_HEADER)
            HEADER['DS'] = get_ds_token(
                ex_params if ex_params else f'role_id={uid}&server={server_id}'
            )
        HEADER.update(header)
        if cookie is not None:
            HEADER['Cookie'] = cookie
        elif 'Cookie' not in HEADER and isinstance(uid, str):
            ck = await self.get_ck(uid)
            if ck is None:
                return -51
            HEADER['Cookie'] = ck
        data = await self._mys_request(
            url=_URL,
            method='GET',
            header=HEADER,
            params=params if params else {'server': server_id, 'role_id': uid},
            use_proxy=True if is_os else False,
        )
        return data

    async def _mys_req_get(
        self,
        url: str,
        is_os: bool,
        params: Dict,
        header: Optional[Dict] = None,
    ) -> Union[Dict, int]:
        if is_os:
            _URL = _API[f'{url}_OS']
            HEADER = copy.deepcopy(_HEADER_OS)
            use_proxy = True
        else:
            _URL = _API[url]
            HEADER = copy.deepcopy(_HEADER)
            use_proxy = False
        if header:
            HEADER.update(header)
        data = await self._mys_request(
            url=_URL,
            method='GET',
            header=HEADER,
            params=params,
            use_proxy=use_proxy,
        )
        return data

    async def _mys_request(
        self,
        url: str,
        method: Literal['GET', 'POST'] = 'GET',
        header: Dict[str, Any] = _HEADER,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        use_proxy: Optional[bool] = False,
    ) -> Union[Dict, int]:
        async with ClientSession() as client:
            async with client.request(
                method,
                url=url,
                headers=header,
                params=params,
                json=data,
                proxy=self.proxy_url if use_proxy else None,
                timeout=300,
            ) as resp:
                raw_data = await resp.json()
                retcode: int = raw_data['retcode']
                if retcode == 1034:
                    await self._upass(header)
                elif retcode != 0:
                    return retcode
                return raw_data

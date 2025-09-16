from copy import deepcopy
from datetime import datetime, timedelta
from typing import Dict, List, Union, Optional, cast

from gsuid_core.utils.cache import gs_cache
from gsuid_core.utils.api.mys_api import _MysApi
from gsuid_core.utils.api.mys.api import RECORD_BASE, RECORD_BASE_OS
from gsuid_core.utils.api.mys.tools import get_ds_token, get_web_ds_token

from .models import (
    Character,
    WidgetResin,
    CalendarData,
    SeasonPostData,
    PoetryAbyssDatas,
)
from .api import (
    widget_url,
    calendar_url,
    new_abyss_url,
    char_detail_url,
    season_post_url,
    hard_challenge_url,
)


class GsMysAPI(_MysApi):
    """MysAPI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @gs_cache(3600)
    async def get_season_post_data(
        self, uid: str
    ) -> Union[SeasonPostData, int]:
        server_id = self.RECOGNIZE_SERVER.get(uid[0], 'cn_gf01')
        HEADER = deepcopy(self._HEADER)
        ck = await self.get_ck(uid, 'OWNER')
        if ck is None:
            return -51
        HEADER['Cookie'] = ck

        base = RECORD_BASE_OS if self.check_os(uid) else RECORD_BASE

        now = datetime.now()
        now_90 = now - timedelta(days=90)

        data = await self._mys_request(
            season_post_url,
            'GET',
            HEADER,
            params={
                "role_id": uid,
                "server": server_id,
                "year": str(now_90.year),
                "month": str(now_90.month),
                "day": str(now_90.day),
            },
            base_url=base,
        )

        if isinstance(data, Dict):
            data = cast(SeasonPostData, data['data'])
        return data

    @gs_cache(360)
    async def get_hard_challenge_data(self, uid: str) -> Union[Dict, int]:
        server_id = self.RECOGNIZE_SERVER.get(uid[0], 'cn_gf01')
        HEADER = deepcopy(self._HEADER)
        ck = await self.get_ck(uid, 'OWNER')
        if ck is None:
            return -51
        HEADER['Cookie'] = ck

        base = RECORD_BASE_OS if self.check_os(uid) else RECORD_BASE
        data = await self._mys_request(
            hard_challenge_url,
            'GET',
            HEADER,
            data={
                "role_id": uid,
                "server": server_id,
                "need_detail": True,
            },
            base_url=base,
        )

        if isinstance(data, Dict):
            data = cast(Dict, data['data'])
        return data

    @gs_cache(300)
    async def get_calendar_data(self, uid: str) -> Union[CalendarData, int]:
        server_id = self.RECOGNIZE_SERVER.get(uid[0])
        header = deepcopy(self._HEADER)
        ck = await self.get_ck(uid, 'OWNER')
        if ck is None:
            return -51
        header['Cookie'] = ck
        base = RECORD_BASE_OS if self.check_os(uid) else RECORD_BASE
        data = await self._mys_request(
            calendar_url,
            'POST',
            header,
            data={"role_id": uid, "server": server_id},
            base_url=base,
        )

        if isinstance(data, Dict):
            data = cast(CalendarData, data['data'])
        return data

    @gs_cache(300)
    async def get_widget_resin_data(self, uid: str) -> Union[WidgetResin, int]:
        header = deepcopy(self._HEADER)
        sk = await self.get_stoken(uid)
        if sk is None:
            return -51
        header['Cookie'] = sk
        header['DS'] = get_web_ds_token(True)
        header['x-rpc-channel'] = 'miyousheluodi'
        base = RECORD_BASE_OS if self.check_os(uid) else RECORD_BASE
        data = await self._mys_request(
            widget_url,
            'GET',
            header,
            {'game_id': 2},
            base_url=base,
        )
        if isinstance(data, Dict):
            data = cast(WidgetResin, data['data'])
        return data

    @gs_cache(360)
    async def get_poetry_abyss_data(
        self,
        uid: str,
        active: Optional[int] = None,
    ) -> Union[PoetryAbyssDatas, int]:
        server_id = self.RECOGNIZE_SERVER.get(uid[0])
        base = RECORD_BASE_OS if self.check_os(uid) else RECORD_BASE
        HEADER = deepcopy(self._HEADER)
        ck = await self.get_ck(uid, 'OWNER')
        if ck is None:
            return -51
        HEADER['Cookie'] = ck
        params = {
            'server': server_id,
            'role_id': uid,
            'need_detail': True,
        }
        if active:
            params['active'] = active
        HEADER['DS'] = get_ds_token(
            '&'.join([f'{k}={v}' for k, v in params.items()])
        )
        data = await self._mys_request(
            new_abyss_url,
            'GET',
            HEADER,
            params,
            base_url=base,
        )
        if isinstance(data, Dict):
            data = cast(PoetryAbyssDatas, data['data'])
        return data

    @gs_cache(360)
    async def get_char_detail_data(
        self, uid: str, char_id_list: List[str]
    ) -> Union[List[Character], int]:
        server_id = self.RECOGNIZE_SERVER.get(uid[0], 'cn_gf01')
        HEADER = deepcopy(self._HEADER)
        ck = await self.get_ck(uid, 'OWNER')
        if ck is None:
            return -51
        HEADER['Cookie'] = ck

        base = RECORD_BASE_OS if self.check_os(uid) else RECORD_BASE
        data = await self._mys_request(
            char_detail_url,
            'POST',
            HEADER,
            data={
                "role_id": uid,
                "server": server_id,
                "character_ids": char_id_list,
            },
            base_url=base,
        )

        if isinstance(data, Dict):
            data = cast(List[Character], data['data']['list'])
        return data
        return data

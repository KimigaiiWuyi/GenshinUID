from copy import deepcopy
from typing import Dict, Union, cast

from gsuid_core.utils.api.mys_api import _MysApi
from gsuid_core.utils.api.mys.tools import get_ds_token, get_web_ds_token

from .api import widget_url, new_abyss_url
from .models import WidgetResin, PoetryAbyssDatas


class GsMysAPI(_MysApi):
    """MysAPI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_widget_resin_data(self, uid: str) -> Union[WidgetResin, int]:
        header = deepcopy(self._HEADER)
        sk = await self.get_stoken(uid)
        if sk is None:
            return -51
        header['Cookie'] = sk
        header['DS'] = get_web_ds_token(True)
        header['x-rpc-channel'] = 'miyousheluodi'
        data = await self._mys_request(
            widget_url, 'GET', header, {'game_id': 2}
        )
        if isinstance(data, Dict):
            data = cast(WidgetResin, data['data'])
        return data

    async def get_poetry_abyss_data(
        self, uid: str
    ) -> Union[PoetryAbyssDatas, int]:
        server_id = self.RECOGNIZE_SERVER.get(uid[0])
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
        HEADER['DS'] = get_ds_token(
            '&'.join([f'{k}={v}' for k, v in params.items()])
        )
        data = await self._mys_request(
            new_abyss_url,
            'GET',
            HEADER,
            params,
        )
        if isinstance(data, Dict):
            data = cast(PoetryAbyssDatas, data['data'])
        return data

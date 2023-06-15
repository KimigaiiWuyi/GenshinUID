from copy import deepcopy
from typing import Dict, Union, cast

from gsuid_core.utils.api.mys_api import _MysApi
from gsuid_core.utils.api.mys.tools import get_web_ds_token

from .api import widget_url
from .models import WidgetResin


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

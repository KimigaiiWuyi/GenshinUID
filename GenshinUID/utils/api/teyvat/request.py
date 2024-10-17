import json
from typing import Any, Dict, Union, Literal, Optional, cast

from httpx import AsyncClient
from gsuid_core.logger import logger

from .api import AbyssRank_API
from .models import TeyvatAbyssRank


class _TeyvatAPI:
    ssl_verify = True
    _HEADER = {'User-Agent': 'GenshinUID & GsCore'}

    async def get_abyss_rank(self) -> Union[TeyvatAbyssRank, int]:
        data = await self._teyvat_request(AbyssRank_API)
        if isinstance(data, Dict) and 'code' in data:
            if data['code'] == 200:
                return cast(TeyvatAbyssRank, data)
            else:
                return data['code']
        else:
            return -500

    async def _teyvat_request(
        self,
        url: str,
        method: Literal['GET', 'POST'] = 'GET',
        header: Dict[str, Any] = _HEADER,
        params: Optional[Dict[str, Any]] = None,
        _json: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict, int]:
        async with AsyncClient(timeout=None) as client:
            resp = await client.request(
                method,
                url,
                headers=header,
                params=params,
                json=_json,
            )
            try:
                raw_data = await resp.json()
            except:  # noqa
                try:
                    raw_data = json.loads(resp.text)
                except:  # noqa
                    raw_data = {'retcode': -999, 'data': resp.text}
            logger.debug(raw_data)
            return raw_data


teyvat_api = _TeyvatAPI()

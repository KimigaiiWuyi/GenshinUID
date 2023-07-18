from urllib.parse import unquote
from typing import Any, Dict, Union, Literal, Optional

from gsuid_core.logger import logger
from aiohttp import TCPConnector, ClientSession, ContentTypeError

from .api import DATA_API, MAIN_API, RANK_API


class _CvApi:
    ssl_verify = True
    _HEADER = {}

    def __init__(self):
        self.session = ClientSession(
            connector=TCPConnector(verify_ssl=self.ssl_verify)
        )

    async def get_session_id(self) -> str:
        async with self.session.get(MAIN_API) as resp:
            cookies = resp.cookies
            cookies_dict = dict(cookies)
            sid = cookies_dict.get('connect.sid', None)
            if sid is not None:
                sid = sid.value
            else:
                sid = 'NVybrjSdSZISA0JRuKFoZIndoCfDWdA2'
            sid = unquote(str(sid))
            sessionID = sid.split(".")[0].split(":")[-1]
            return sessionID

    async def get_base_data(self, uid: str) -> Union[Dict, int]:
        sessionID = await self.get_session_id()
        return await self._cv_request(
            DATA_API.format(uid), 'GET', self._HEADER, {'sessionID': sessionID}
        )

    async def get_rank_data(self, uid: str) -> Union[Dict, int]:
        await self.get_base_data(uid)
        return await self._cv_request(
            RANK_API.format(uid), 'GET', self._HEADER
        )

    async def close(self):
        # 调用session对象的close方法关闭会话
        await self.session.close()

    async def _cv_request(
        self,
        url: str,
        method: Literal['GET', 'POST'] = 'GET',
        header: Dict[str, Any] = _HEADER,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict, int]:
        async with self.session.request(
            method,
            url=url,
            headers=header,
            params=params,
            json=data,
            timeout=300,
        ) as resp:
            try:
                raw_data = await resp.json()
            except ContentTypeError:
                _raw_data = await resp.text()
                raw_data = {'retcode': -999, 'data': _raw_data}
            logger.debug(raw_data)
            return raw_data

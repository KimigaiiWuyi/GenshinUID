from urllib.parse import unquote
from typing import Any, Dict, List, Tuple, Union, Literal, Optional

from gsuid_core.logger import logger
from aiohttp import TCPConnector, ClientSession, ContentTypeError

from .api import (
    DATA_API,
    MAIN_API,
    RANK_API,
    SORT_API,
    REFRESH_API,
    ARTI_SORT_API,
    LEADERBOARD_API,
)

SUBSTAT_MAP = {
    '双爆': 'critValue',
    '攻击力': 'substats.Flat ATK',
    '血量': 'substats.Flat HP',
    '防御力': 'substats.Flat DEF',
    '百分比攻击力': 'substats.ATK%',
    '百分比血量': 'substats.HP%',
    '百分比防御': 'substats.DEF%',
    '元素精通': 'substats.Elemental Mastery',
    '元素充能效率': 'substats.Energy Recharge',
    '暴击率': 'substats.Crit RATE',
    '暴击伤害': 'substats.Crit DMG',
}


class _CvApi:
    ssl_verify = True
    _HEADER = {}

    def __init__(self):
        self.session = ClientSession(
            connector=TCPConnector(verify_ssl=self.ssl_verify)
        )
        self.sessionID = None

    async def get_artifacts_list(
        self,
        sort_by: Union[
            Literal[
                'critValue',
                'substats.Flat ATK',
                'substats.Flat HP',
                'substats.Flat DEF',
                'substats.ATK%',
                'substats.HP%',
                'substats.DEF%',
                'substats.Elemental Mastery',
                'substats.Energy Recharge',
                'substats.Crit RATE',
                'substats.Crit DMG',
            ],
            str,
        ] = 'critValue',
    ) -> Optional[List[Dict]]:
        if not sort_by.startswith(('c', 's')):
            for i in SUBSTAT_MAP:
                if sort_by in i:
                    sort_by = SUBSTAT_MAP[i]
                    break
            else:
                return None
        raw_data = await self._cv_request(
            ARTI_SORT_API.format(sort_by),
            'GET',
            self._HEADER,
        )
        if isinstance(raw_data, Dict) and 'data' in raw_data:
            if raw_data['data']:
                return raw_data['data']
            else:
                return None

    async def get_leaderboard_id_list(
        self, char_id: str
    ) -> Optional[List[Dict]]:
        raw_data = await self._cv_request(
            LEADERBOARD_API.format(char_id),
            'GET',
            self._HEADER,
        )
        if isinstance(raw_data, Dict) and 'data' in raw_data:
            if raw_data['data']:
                return raw_data['data']
            else:
                return None

    async def get_calculation_info(
        self, char_id: str
    ) -> Optional[Tuple[str, int]]:
        raw_data = await self.get_leaderboard_id_list(char_id)
        if raw_data is not None:
            return (
                raw_data[0]['weapons'][0]['calculationId'],
                raw_data[0]['count'],
            )

    async def get_sort_list(
        self, char_id: str
    ) -> Optional[Tuple[List[Dict], int]]:
        _raw_data = await self.get_calculation_info(char_id)
        if _raw_data is not None:
            calculation_id, count = _raw_data
            raw_data = await self._cv_request(
                SORT_API.format(calculation_id),
                'GET',
                self._HEADER,
            )
            if isinstance(raw_data, Dict) and 'data' in raw_data:
                return raw_data['data'], count

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
            self.sessionID = sessionID
            return sessionID

    async def get_base_data(self, uid: str) -> Union[Dict, int]:
        sessionID = await self.get_session_id()
        return await self._cv_request(
            DATA_API.format(uid), 'GET', self._HEADER, {'sessionID': sessionID}
        )

    async def get_refresh_data(self, uid: str) -> Union[Dict, int]:
        return await self._cv_request(
            REFRESH_API.format(uid),
            'GET',
            self._HEADER,
            {'sessionID': self.sessionID},
        )

    async def get_rank_data(self, uid: str) -> Union[Dict, int]:
        await self.get_base_data(uid)
        await self.get_refresh_data(uid)
        data = await self._cv_request(
            RANK_API.format(uid), 'GET', self._HEADER
        )
        await self.session.close()
        return data

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

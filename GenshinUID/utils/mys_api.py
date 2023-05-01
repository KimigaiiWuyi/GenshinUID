from typing import Literal, Optional

from gsuid_core.utils.api.mys import MysApi

from .database import get_sqla


class _MysApi(MysApi):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_ck(
        self, uid: str, mode: Literal['OWNER', 'RANDOM'] = 'RANDOM'
    ) -> Optional[str]:
        sqla = get_sqla('TEMP')
        if mode == 'RANDOM':
            return await sqla.get_random_cookie(uid)
        else:
            return await sqla.get_user_cookie(uid)

    async def get_stoken(self, uid: str) -> Optional[str]:
        sqla = get_sqla('TEMP')
        return await sqla.get_user_stoken(uid)


mys_api = _MysApi()

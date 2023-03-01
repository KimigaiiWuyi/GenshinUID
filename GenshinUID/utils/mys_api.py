from typing import Dict, Literal, Optional

from .database import active_sqla
from ..gsuid_utils.api.mys import MysApi
from ..genshinuid_config.gs_config import gsconfig


class _MysApi(MysApi):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def _pass(self, gt: str, ch: str, header: Dict):
        # 警告：使用该服务（例如某RR等）需要注意风险问题
        # 本项目不以任何形式提供相关接口
        # 代码来源：GITHUB项目MIT开源
        _pass_api = gsconfig.get_config('_pass_API')
        if _pass_api:
            data = await self._mys_request(
                url=f'{_pass_api}&gt={gt}&challenge={ch}',
                method='GET',
                header=header,
            )
            if isinstance(data, int):
                return None, None
            else:
                validate = data['data']['validate']
                ch = data['data']['challenge']
        else:
            validate = None

        return validate, ch

    async def _upass(self, header: Dict):
        raw_data = await self.get_upass_link(header)
        if isinstance(raw_data, int):
            return False
        gt = raw_data['data']['gt']
        ch = raw_data['data']['challenge']

        vl, ch = await self._pass(gt, ch, header)

        if vl:
            await self.get_header_and_vl(header, ch, vl)
        else:
            return True

    async def get_ck(
        self, uid: str, mode: Literal['OWNER', 'RANDOM'] = 'RANDOM'
    ) -> Optional[str]:
        for bot_id in active_sqla:
            sqla = active_sqla[bot_id]
            if mode == 'RANDOM':
                return await sqla.get_random_cookie(uid)
            else:
                return await sqla.get_user_cookie(uid)
        else:
            return None

    async def get_stoken(self, uid: str) -> Optional[str]:
        for bot_id in active_sqla:
            sqla = active_sqla[bot_id]
            return await sqla.get_user_stoken(uid)
        else:
            return None


mys_api = _MysApi()

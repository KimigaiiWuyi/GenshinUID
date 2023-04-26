from typing import Dict, Literal, Optional

from gsuid_core.utils.api.mys import MysApi

from .database import get_sqla
from ..genshinuid_config.gs_config import gsconfig


class _MysApi(MysApi):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def _pass(self, gt: str, ch: str, header: Dict):
        # 警告：使用该服务（例如某RR等）需要注意风险问题
        # 本项目不以任何形式提供相关接口
        # 代码来源：GITHUB项目MIT开源
        _pass_api = gsconfig.get_config('_pass_API').data
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

    async def _upass(self, header: Dict, is_bbs: bool = False):
        if is_bbs:
            raw_data = await self.get_bbs_upass_link(header)
        else:
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
        sqla = get_sqla('TEMP')
        if mode == 'RANDOM':
            return await sqla.get_random_cookie(uid)
        else:
            return await sqla.get_user_cookie(uid)

    async def get_stoken(self, uid: str) -> Optional[str]:
        sqla = get_sqla('TEMP')
        return await sqla.get_user_stoken(uid)


mys_api = _MysApi()

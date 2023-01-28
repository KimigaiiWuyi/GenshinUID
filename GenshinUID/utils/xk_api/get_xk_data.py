import json
from typing import Any, Dict, Literal, Optional

from nonebot.log import logger
from aiohttp import ClientSession

from .xk_api import XK_ABYSS_URL

_HEADER = {}


async def get_abyss_total():
    data = await _xk_request(
        url=XK_ABYSS_URL,
        method='GET',
    )
    return data


async def _xk_request(
    url: str,
    method: Literal['GET', 'POST'] = 'GET',
    header: Dict[str, Any] = _HEADER,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    sess: Optional[ClientSession] = None,
) -> dict:
    '''
    :说明:
      访问URL并进行json解析返回。
    :参数:
      * url (str): MihoyoAPI。
      * method (Literal["GET", "POST"]): `POST` or `GET`。
      * header (Dict[str, Any]): 默认为_HEADER。
      * params (Dict[str, Any]): 参数。
      * data (Dict[str, Any]): 参数(`post`方法需要传)。
      * sess (ClientSession): 可选, 指定client。
    :返回:
      * result (dict): json.loads()解析字段。
    '''
    is_temp_sess = False
    if sess is None:
        sess = ClientSession()
        is_temp_sess = True
    try:
        req = await sess.request(
            method, url=url, headers=header, params=params, json=data
        )
        raw = await req.text()
        raw = raw.replace('var static_abyss_total =', '')
        # logger.debug(raw)
        return json.loads(raw)
    except Exception:
        logger.exception(f'访问{url}失败！')
        return {}
    finally:
        if is_temp_sess:
            await sess.close()

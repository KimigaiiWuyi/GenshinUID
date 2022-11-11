import sys
from pathlib import Path
from typing import Any, Dict, Union, Literal, Optional

from nonebot.log import logger
from aiohttp import ClientSession

sys.path.append(str(Path(__file__).parents[1]))
try:
    from ...utils.ambr_api.ambr_api import AMBR_CHAR_URL, AMBR_EVENT_URL
except ImportError:
    from utils.ambr_api.ambr_api import AMBR_CHAR_URL, AMBR_EVENT_URL

_HEADER = {}


async def get_event_data():
    data = await _ambr_request(url=AMBR_EVENT_URL, method='GET')
    return data


async def get_char_data(char_id: Union[int, str]):
    data = await _ambr_request(url=AMBR_CHAR_URL.format(char_id), method='GET')
    return data


async def _ambr_request(
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
        return await req.json()
    except Exception:
        logger.exception(f'访问{url}失败！')
        return {}
    finally:
        if is_temp_sess:
            await sess.close()

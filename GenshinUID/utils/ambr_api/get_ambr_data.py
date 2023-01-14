import sys
from pathlib import Path
from typing import Any, Dict, Union, Literal, Optional

from nonebot.log import logger
from aiohttp import ClientSession

sys.path.append(str(Path(__file__).parents[1]))
try:
    from .beta_weapon import BETA_WEAPON_ID
    from ...utils.ambr_api.ambr_api import (
        AMBR_BOOK_URL,
        AMBR_CHAR_URL,
        AMBR_EVENT_URL,
        AMBR_WEAPON_URL,
        AMBR_BOOK_DATA_URL,
        AMBR_BOOK_DETAILS_URL,
    )
except ImportError:
    from utils.ambr_api.beta_weapon import BETA_WEAPON_ID
    from utils.ambr_api.ambr_api import (
        AMBR_BOOK_URL,
        AMBR_CHAR_URL,
        AMBR_EVENT_URL,
        AMBR_WEAPON_URL,
        AMBR_BOOK_DATA_URL,
        AMBR_BOOK_DETAILS_URL,
    )

_HEADER = {}


async def get_event_data():
    data = await _ambr_request(url=AMBR_EVENT_URL, method='GET')
    return data


async def get_char_data(char_id: Union[int, str]):
    data = await _ambr_request(url=AMBR_CHAR_URL.format(char_id), method='GET')
    return data


async def get_weapon_data(weapon_id: Union[int, str]):
    if isinstance(weapon_id, str) and not weapon_id.isdigit():
        for weapon in BETA_WEAPON_ID:
            if str(weapon_id) in weapon:
                weapon_id = BETA_WEAPON_ID[weapon]
    data = await _ambr_request(
        url=AMBR_WEAPON_URL.format(weapon_id), method='GET'
    )
    return data


async def get_all_book_id():
    return await _ambr_request(url=AMBR_BOOK_URL, method='GET')


async def get_book_volume(book_id: Union[int, str]):
    return await _ambr_request(
        url=AMBR_BOOK_DETAILS_URL.format(book_id), method='GET'
    )


async def get_book_data(story_id: Union[int, str]):
    return await _ambr_request(
        url=AMBR_BOOK_DATA_URL.format(story_id), method='GET'
    )


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
        raw_data = await req.json()
        logger.debug(raw_data)
        return raw_data
    except Exception:
        logger.exception(f'访问{url}失败！')
        return {}
    finally:
        if is_temp_sess:
            await sess.close()

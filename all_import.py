import re
import base64
import asyncio
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union, Optional

import httpx
import hoshino
from hoshino import Service
from nonebot.log import logger
from aiohttp import ClientConnectorError
from aiocqhttp.exceptions import ActionFailed
from nonebot import MessageSegment, get_bot  # type: ignore
from hoshino.util import (
    FreqLimiter,
    pic2b64,
    silence,
    concat_pic,
    filt_message,
)
from hoshino.typing import (  # type: ignore
    CQEvent,
    HoshinoBot,
    NoticeSession,
    CommandSession,
)

from .utils.db_operation.db_operation import select_db
from .utils.message.get_image_and_at import ImageAndAt
from .utils.message.error_reply import *  # noqa: F403,F401
from .utils.alias.alias_to_char_name import alias_to_char_name
from .utils.exception.handle_exception import handle_exception
from .utils.draw_image_tools.send_image_tool import convert_img
from .utils.genshin_fonts.genshin_fonts import genshin_font_origin

sv = Service('genshinuid')
hoshino_bot = get_bot()

from typing import Any, Tuple, Union

from nonebot import on_regex
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import RegexGroup
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from .update import update_genshinuid

# gs_restart = on_command('gs重启', rule=FullCommand())
gs_update = on_regex(
    r'^(gs)(强行)?(强制)?(更新)$',
    block=True,
)


@gs_update.handle()
async def send_update_msg(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
):
    if not await SUPERUSER(bot, event):
        return

    logger.info('[gs更新] 正在执行 ...')
    level = 2
    if args[1] is None:
        level -= 1
    if args[2] is None:
        level -= 1
    logger.info(f'[gs更新] 更新等级为{level}')

    im = await update_genshinuid(level)
    await matcher.finish(im)

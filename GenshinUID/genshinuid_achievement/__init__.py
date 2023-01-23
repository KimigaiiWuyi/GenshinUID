from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.adapters.qqguild import Message

from ..config import priority
from .get_achi_desc import get_achi, get_daily_achi
from ..utils.exception.handle_exception import handle_exception

get_task_info = on_command('查委托', aliases={'委托'}, priority=priority)
get_achi_info = on_command('查成就', aliases={'成就'}, priority=priority)


@get_task_info.handle()
@handle_exception('查委托')
async def send_task_info(matcher: Matcher, args: Message = CommandArg()):
    if not args:
        return
    name = str(args[0])
    logger.info(f'[查委托] 参数：{name}')
    im = await get_daily_achi(name)
    await matcher.finish(im)


@get_achi_info.handle()
@handle_exception('查成就')
async def send_achi_info(matcher: Matcher, args: Message = CommandArg()):
    if not args:
        return
    name = str(args[0])
    logger.info(f'[查成就] 参数：{name}')
    im = await get_achi(name)
    await matcher.finish(im)

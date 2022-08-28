from pathlib import Path

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import MessageSegment

from ..utils.exception.handle_exception import handle_exception

get_help = on_command('gs帮助')

HELP_IMG = Path(__file__).parent / 'help.png'


@get_help.handle()
@handle_exception('建议')
async def send_guide_pic(matcher: Matcher):
    logger.info('获得gs帮助图片成功！')
    await matcher.finish(MessageSegment.image(HELP_IMG))

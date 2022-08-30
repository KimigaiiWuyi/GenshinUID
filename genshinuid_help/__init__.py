from pathlib import Path

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import MessageSegment

from ..genshinuid_meta import register_menu
from ..utils.exception.handle_exception import handle_exception

get_help = on_command('gs帮助')

HELP_IMG = Path(__file__).parent / 'help.png'


@get_help.handle()
@handle_exception('建议')
@register_menu(
    '插件帮助',
    'gs帮助',
    '查看插件功能帮助图',
    detail_des=('指令：' '<ft color=(238,120,0)>gs帮助</ft>\n' ' \n' '查看插件功能帮助图'),
)
async def send_guide_pic(matcher: Matcher):
    logger.info('获得gs帮助图片成功！')
    await matcher.finish(MessageSegment.image(HELP_IMG))

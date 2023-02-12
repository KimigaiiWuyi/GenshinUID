from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from .gacha_url import post_url
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..utils.exception.handle_exception import handle_exception

get_gacha_url = on_command(
    '获取抽卡记录链接', aliases={'抽卡链接', '抽卡记录链接'}, rule=FullCommand()
)


@get_gacha_url.handle()
@handle_exception('获取抽卡记录链接')
@register_menu(
    '获取抽卡记录链接',
    '获取抽卡记录链接',
    '获取用户的抽卡记录链接',
    trigger_method='群聊指令',
    detail_des=(
        '介绍：\n'
        '导出抽卡记录的链接以用于原神小程序\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>抽卡链接</ft>'
    ),
)
async def _(
    bot: Bot,
    event: GroupMessageEvent,
    matcher: Matcher,
):
    await get_gacha_url.send("正在获取抽卡记录链接")
    logger.info('开始执行[获取抽卡记录链接]')
    uid = await select_db(event.user_id, mode='uid')
    if not isinstance(uid, str) or '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)
    await post_url(bot, uid, str(event.group_id), str(event.user_id))

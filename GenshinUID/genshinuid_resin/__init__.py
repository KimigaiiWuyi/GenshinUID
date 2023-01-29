import asyncio

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import get_bot, on_command
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.ntchat import MessageSegment, TextMessageEvent

from .notice import get_notice_list
from .resin_text import get_resin_text
from .draw_resin_card import get_resin_img
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..utils.exception.handle_exception import handle_exception

notice_scheduler = scheduler
get_resin_info = on_command(
    '每日',
    aliases={'mr', '状态', '实时便笺', '便笺', '便签'},
    block=True,
    rule=FullCommand(),
)
get_daily_info = on_command('当前状态', rule=FullCommand())


@get_daily_info.handle()
@handle_exception('每日信息文字版')
@register_menu(
    '文字实时便笺',
    '当前信息',
    '米游社实时便笺文字版',
    detail_des=(
        '介绍：\n'
        '米游社实时便笺文字版\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>当前状态</ft>'
    ),
)
async def send_daily_info(
    event: TextMessageEvent,
    matcher: Matcher,
):
    logger.info('开始执行[每日信息文字版]')

    qid = event.from_wxid
    if event.at_user_list:
        for user in event.at_user_list:
            user = user.strip()
            if user != "":
                qid = user
    logger.info('[每日信息文字版]QQ号: {}'.format(qid))

    uid: str = await select_db(qid, mode='uid')  # type: ignore
    logger.info('[每日信息文字版]UID: {}'.format(uid))

    if not uid:
        await matcher.finish(UID_HINT)

    im = await get_resin_text(uid)
    await matcher.finish(im)


@notice_scheduler.scheduled_job('cron', minute='*/30')
async def notice_job():
    bot = get_bot()
    result = await get_notice_list()
    logger.info('[推送检查]完成!等待消息推送中...')
    # 执行私聊推送
    for qid in result[0]:
        try:
            await bot.call_api(
                api='send_private_msg',
                user_id=qid,
                message=result[0][qid],
            )
        except Exception:
            logger.warning(f'[推送检查] QQ {qid} 私聊推送失败!')
        await asyncio.sleep(0.5)
    logger.info('[推送检查]私聊推送完成')
    # 执行群聊推送
    for group_id in result[1]:
        try:
            await bot.call_api(
                api='send_group_msg',
                group_id=group_id,
                message=result[1][group_id],
            )
        except Exception:
            logger.warning(f'[推送检查] 群 {group_id} 群聊推送失败!')
        await asyncio.sleep(0.5)
    logger.info('[推送检查]群聊推送完成')


@get_resin_info.handle()
@handle_exception('每日信息')
@register_menu(
    '图片实时便笺',
    '每日',
    '图片形式米游社实时便笺',
    detail_des=(
        '介绍：\n'
        '图片形式米游社实时便笺\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>每日</ft>\n'
        '- <ft color=(238,120,0)>mr</ft>\n'
        '- <ft color=(238,120,0)>状态</ft>\n'
        '- <ft color=(125,125,125)>(实时)</ft><ft color=(238,120,0)>便笺</ft>\n'
        '- <ft color=(238,120,0)>便签</ft>'
    ),
)
async def send_uid_info(
    event: TextMessageEvent,
    matcher: Matcher,
):
    logger.info('开始执行[每日信息]')
    qid = event.from_wxid
    if event.at_user_list:
        for user in event.at_user_list:
            user = user.strip()
            if user != "":
                qid = user
    logger.info('[每日信息]QQ号: {}'.format(qid))

    im = await get_resin_img(qid)  # type:ignore
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')

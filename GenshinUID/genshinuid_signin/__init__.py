import random
import asyncio

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import get_bot, on_command
from nonebot.permission import SUPERUSER
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.ntchat import Bot, MessageEvent, MessageSegment

from ..config import priority

try:
    from sign import sign_in, daily_sign
except ImportError:
    from .sign import sign_in, daily_sign

from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from ..utils.exception.handle_exception import handle_exception
from ..utils.db_operation.db_operation import select_db, config_check

sign_scheduler = scheduler

get_sign = on_command('签到', priority=priority, rule=FullCommand())
all_recheck = on_command('全部重签', priority=priority, rule=FullCommand())


# 每日零点半执行米游社原神签到
@sign_scheduler.scheduled_job('cron', hour='0', minute='30')
async def sign_at_night():
    if await config_check('SchedSignin'):
        await send_daily_sign()


# 群聊内 签到 功能
@get_sign.handle()
@handle_exception('签到')
@register_menu(
    '手动米游社原神签到',
    '签到',
    '手动触发米游社原神签到任务',
    detail_des=(
        '介绍：\n'
        '手动触发米游社原神签到任务\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>签到</ft>'
    ),
)
async def get_sign_func(
    event: MessageEvent,
    matcher: Matcher,
):
    logger.info('开始执行[签到]')
    qid = event.from_wxid
    wxid_list = []
    wxid_list.append(event.from_wxid)
    logger.info('[签到]QQ号: {}'.format(qid))
    uid = await select_db(qid, mode='uid')
    logger.info('[签到]UID: {}'.format(uid))
    im = await sign_in(uid)
    await matcher.finish(
        MessageSegment.room_at_msg(content="{$@}" + f'{im}', at_list=wxid_list)
    )


@all_recheck.handle()
@handle_exception('全部重签')
@register_menu(
    '米游社原神重签到',
    '全部重签',
    '重新运行所有自动米游社原神签到任务',
    detail_des=(
        '介绍：\n'
        '重新运行所有自动米游社原神签到任务\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>全部重签</ft>'
    ),
)
async def recheck(bot: Bot, event: MessageEvent, matcher: Matcher):
    if not await SUPERUSER(bot, event):
        return
    logger.info('开始执行[全部重签]')
    await matcher.send('已开始执行')
    await send_daily_sign()
    await matcher.finish('执行完成')


async def send_daily_sign():
    logger.info('开始执行[每日全部签到]')
    bot = get_bot()
    # 执行签到 并获得推送消息
    result = await daily_sign()
    private_msg_list = result['private_msg_list']
    group_msg_list = result['group_msg_list']
    logger.info('[每日全部签到]完成')

    # 执行私聊推送
    for qid in private_msg_list:
        try:
            await bot.call_api(
                api='send_text',
                to_wxid=qid,
                content=private_msg_list[qid],
            )
        except Exception:
            logger.warning(f'[每日全部签到] QQ {qid} 私聊推送失败!')
        await asyncio.sleep(0.5)
    logger.info('[每日全部签到]私聊推送完成')

    # 执行群聊推送
    for gid in group_msg_list:
        # 根据succee数判断是否为简洁推送
        if group_msg_list[gid]['success'] >= 0:
            report = (
                '以下为签到失败报告：{}'.format(group_msg_list[gid]['push_message'])
                if group_msg_list[gid]['push_message'] != ''
                else ''
            )
            msg_title = '今日自动签到已完成！\n本群共签到成功{}人，共签到失败{}人。{}'.format(
                group_msg_list[gid]['success'],
                group_msg_list[gid]['failed'],
                report,
            )
        else:
            msg_title = group_msg_list[gid]['push_message'].rstrip()
        # 发送群消息
        at_wxid = []
        at_wxid.append(group_msg_list[gid]['wxid'])
        try:
            await bot.call_api(
                api='send_room_at_msg',
                to_wxid=gid,
                at_list=at_wxid,
                content=msg_title,
            )
        except Exception:
            logger.warning(f'[每日全部签到]群 {gid} 推送失败!')
        await asyncio.sleep(0.5 + random.randint(1, 3))
    logger.info('[每日全部签到]群聊推送完成')

import random
import asyncio

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import get_bot, on_command
from nonebot.permission import SUPERUSER
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.onebot.v11 import MessageEvent

from ..config import SUPERUSERS, priority
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from ..utils.db_operation.db_operation import config_check
from ..utils.exception.handle_exception import handle_exception
from .daily_mihoyo_bbs_coin import mihoyo_coin, all_daily_mihoyo_bbs_coin

bbscoin_scheduler = scheduler

get_mihoyo_coin = on_command('开始获取米游币', priority=priority, rule=FullCommand())
all_bbscoin_recheck = on_command(
    '全部重获取', permission=SUPERUSER, priority=priority, rule=FullCommand()
)


# 获取米游币
@get_mihoyo_coin.handle()
@handle_exception('获取米游币')
@register_menu(
    '手动获取米游币',
    '开始获取米游币',
    '手动触发米游社米游币任务',
    detail_des=(
        '介绍：\n'
        '手动触发米游社获取米游币的任务\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>开始获取米游币</ft>'
    ),
)
async def send_mihoyo_coin(event: MessageEvent, matcher: Matcher):
    await matcher.send('开始操作……', at_sender=True)
    qid = event.user_id
    im = await mihoyo_coin(qid)
    await matcher.finish(im, at_sender=True)


@all_bbscoin_recheck.handle()
@handle_exception('米游币全部重获取')
@register_menu(
    '重新获取米游币',
    '全部重获取',
    '重新运行所有自动获取米游币的任务',
    detail_des=(
        '介绍：\n'
        '重新运行所有自动获取米游币的任务\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>全部重获取</ft>'
    ),
)
async def bbs_recheck(
    matcher: Matcher,
):
    await matcher.send('已开始执行!可能需要较久时间!')
    await send_daily_mihoyo_bbs_sign()
    await matcher.finish('执行完成!')


# 每日一点十六分进行米游币获取
@bbscoin_scheduler.scheduled_job('cron', hour='1', minute='16')
async def sign_at_night():
    if await config_check('SchedMhyBBSCoin'):
        await send_daily_mihoyo_bbs_sign()


async def send_daily_mihoyo_bbs_sign():
    bot = get_bot()
    im, im_private = await all_daily_mihoyo_bbs_coin()
    if im_private:
        for user_id in im_private:
            await bot.send_private_msg(
                user_id=user_id, message=im_private[user_id]
            )
            await asyncio.sleep(5 + random.randint(1, 3))
    if await config_check('PrivateReport'):
        for qid in SUPERUSERS:
            await bot.call_api(api='send_private_msg', user_id=qid, message=im)
            await asyncio.sleep(5 + random.randint(1, 3))
    logger.info('米游币获取已结束。')

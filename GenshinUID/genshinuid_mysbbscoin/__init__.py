import random
import asyncio
from typing import Optional

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.gss import gss
from gsuid_core.models import Event
from gsuid_core.aps import scheduler
from gsuid_core.logger import logger

from ..utils.database import get_sqla
from ..utils.error_reply import CK_HINT, SK_HINT
from ..genshinuid_config.gs_config import gsconfig
from .daily_get import mihoyo_coin, all_daily_mihoyo_bbs_coin

BBS_TASK_TIME = gsconfig.get_config('BBSTaskTime').data

sv_mysbbs_config = SV('米游币获取管理', pm=2)
sv_get_mysbbs = SV('米游币获取')


# 获取米游币
@sv_get_mysbbs.on_fullmatch('开始获取米游币')
async def send_mihoyo_coin(bot: Bot, ev: Event):
    await bot.send('开始操作……')
    sqla = get_sqla(ev.bot_id)
    uid = await sqla.get_bind_uid(ev.user_id)
    if uid is None:
        return await bot.send(CK_HINT)
    stoken = await sqla.get_user_stoken(uid)
    if stoken is None:
        return await bot.send(SK_HINT)
    im = await mihoyo_coin(stoken)
    await bot.send(im)


@sv_mysbbs_config.on_fullmatch('全部重获取')
async def bbs_recheck(bot: Bot, ev: Event):
    await bot.send('已开始执行!可能需要较久时间!')
    await send_daily_mihoyo_bbs_sign(ev)
    await bot.send('执行完成!')


# 每日一点十六分进行米游币获取
@scheduler.scheduled_job(
    'cron', hour=BBS_TASK_TIME[0], minute=BBS_TASK_TIME[1]
)
async def get_coin_at_night():
    if gsconfig.get_config('SchedMhyBBSCoin').data:
        await send_daily_mihoyo_bbs_sign()


async def send_daily_mihoyo_bbs_sign(ev: Optional[Event] = None):
    im, im_private = await all_daily_mihoyo_bbs_coin()
    if im_private:
        for BOT_ID in gss.active_bot:
            bot = gss.active_bot[BOT_ID]
            for bot_id in im_private:
                for user_id in im_private[bot_id]:
                    msg = im_private[bot_id][user_id]
                    await bot.target_send(
                        msg, 'direct', user_id, bot_id, '', ''
                    )
                await asyncio.sleep(5 + random.randint(1, 3))
    if ev:
        target_type = 'group' if ev.group_id else 'direct'
        target_id = ev.group_id if ev.group_id else ev.user_id
        for BOT_ID in gss.active_bot:
            bot = gss.active_bot[BOT_ID]
            await bot.target_send(
                im, target_type, target_id, ev.bot_id, '', ''
            )
        await asyncio.sleep(5 + random.randint(1, 3))
    logger.info('米游币获取已结束。')

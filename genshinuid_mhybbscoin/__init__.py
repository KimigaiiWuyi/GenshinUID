import random

from ..all_import import *  # noqa: F403,F401
from ..utils.db_operation.db_operation import config_check
from .daily_mihoyo_bbs_coin import mihoyo_coin, all_daily_mihoyo_bbs_coin


# 获取米游币
@sv.on_fullmatch('开始获取米游币')
async def send_mihoyo_coin(bot: HoshinoBot, ev: CQEvent):
    await bot.send(ev, '开始操作……', at_sender=True)
    qid = int(ev.sender['user_id'])  # type: ignore
    im = await mihoyo_coin(qid)
    await bot.send(ev, im, at_sender=True)


@sv.on_fullmatch('全部重获取')
async def bbs_recheck(bot: HoshinoBot, ev: CQEvent):
    qid = int(ev.sender['user_id'])  # type: ignore
    if qid not in bot.config.SUPERUSERS:
        return
    await bot.send(ev, '已开始执行!可能需要较久时间!')
    await send_daily_mihoyo_bbs_sign()
    await bot.send(ev, '执行完成!')


# 每日一点十六分进行米游币获取
@sv.scheduled_job('cron', hour='1', minute='16')
async def sign_at_night():
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
        for qid in bot.config.SUPERUSERS:
            await bot.send_private_msg(user_id=qid, message=im)
            await asyncio.sleep(5 + random.randint(1, 3))
    logger.info('米游币获取已结束。')

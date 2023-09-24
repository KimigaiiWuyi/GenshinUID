import random
import asyncio

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.gss import gss
from gsuid_core.models import Event
from gsuid_core.aps import scheduler
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import UID_HINT
from gsuid_core.utils.database.models import GsBind

from .sign import sign_in, daily_sign
from ..genshinuid_config.gs_config import gsconfig

SIGN_TIME = gsconfig.get_config('SignTime').data

sv_sign = SV('原神签到')
sv_sign_config = SV('原神签到管理', pm=2)


# 每日零点半执行米游社原神签到
@scheduler.scheduled_job('cron', hour=SIGN_TIME[0], minute=SIGN_TIME[1])
async def sign_at_night():
    if gsconfig.get_config('SchedSignin').data:
        await send_daily_sign()


# 群聊内 签到 功能
@sv_sign.on_fullmatch('签到')
async def get_sign_func(bot: Bot, ev: Event):
    await bot.logger.info('[签到]QQ号: {}'.format(ev.user_id))
    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[签到]UID: {}'.format(uid))
    await bot.send(await sign_in(uid))


@sv_sign_config.on_fullmatch('全部重签')
async def recheck(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[全部重签]')
    await bot.send('已开始执行')
    await send_daily_sign()
    await bot.send('执行完成')


async def send_daily_sign():
    logger.info('开始执行[每日全部签到]')
    # 执行签到 并获得推送消息
    result = await daily_sign()
    private_msg_list = result['private_msg_list']
    group_msg_list = result['group_msg_list']
    logger.info('[每日全部签到]完成')

    # 执行私聊推送
    for qid in private_msg_list:
        try:
            for bot_id in gss.active_bot:
                for single in private_msg_list[qid]:
                    await gss.active_bot[bot_id].target_send(
                        single['msg'], 'direct', qid, single['bot_id'], '', ''
                    )
        except Exception as e:
            logger.warning(f'[每日全部签到] QQ {qid} 私聊推送失败!错误信息:{e}')
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
            msg_title = group_msg_list[gid]['push_message']
        # 发送群消息
        try:
            for bot_id in gss.active_bot:
                await gss.active_bot[bot_id].target_send(
                    msg_title,
                    'group',
                    gid,
                    group_msg_list[gid]['bot_id'],
                    '',
                    '',
                )
        except Exception as e:
            logger.warning(f'[每日全部签到]群 {gid} 推送失败!错误信息:{e}')
        await asyncio.sleep(0.5 + random.randint(1, 3))
    logger.info('[每日全部签到]群聊推送完成')

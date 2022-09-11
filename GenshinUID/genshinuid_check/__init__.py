import random
import asyncio

from .backup_data import data_backup
from ..all_import import *  # noqa: F403, F401
from ..utils.db_operation.db_cache_and_check import check_db, check_stoken_db


@sv.scheduled_job('cron', hour=0)
async def daily_refresh_charData():
    await data_backup()


# 群聊内 校验Cookies 是否正常的功能，不正常自动删掉
@sv.on_fullmatch('校验全部Cookies')
async def send_check_cookies(bot: HoshinoBot, ev: CQEvent):
    raw_mes = await check_db()
    im = raw_mes[0]
    await bot.send(ev, im)
    for i in raw_mes[1]:
        await bot.send_private_msg(
            user_id=i[0],
            message=(
                '您绑定的Cookies（uid{}）已失效，以下功能将会受到影响：\n'
                '查看完整信息列表\n查看深渊配队\n自动签到/当前状态/每月统计\n'
                '请及时重新绑定Cookies并重新开关相应功能。'
            ).format(i[1]),
        )
        await asyncio.sleep(3 + random.randint(1, 3))


# 群聊内 校验Stoken 是否正常的功能，不正常自动删掉
@sv.on_fullmatch('校验全部Stoken')
async def send_check_stoken(bot: HoshinoBot, ev: CQEvent):
    raw_mes = await check_stoken_db()
    im = raw_mes[0]
    await bot.send(ev, im)
    for i in raw_mes[1]:
        await bot.send_private_msg(
            user_id=i[0],
            message=(
                '您绑定的Stoken（uid{}）已失效，以下功能将会受到影响：\n'
                'gs开启自动米游币，开始获取米游币。\n'
                '重新添加后需要重新开启自动米游币。'
            ).format(i[1]),
        )
        await asyncio.sleep(3 + random.randint(1, 3))

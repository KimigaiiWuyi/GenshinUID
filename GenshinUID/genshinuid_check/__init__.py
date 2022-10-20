import random
import asyncio

from nonebot.log import logger

from .backup_data import data_backup
from ..all_import import *  # noqa: F403, F401
from ..utils.db_operation.db_cache_and_check import check_db, check_stoken_db
from ..utils.db_operation.db_operation import delete_cookies, get_all_push_list
from ..utils.message.get_cqhttp_data import (
    get_all_friend_list,
    get_group_member_list,
)


@sv.scheduled_job('cron', hour=0)
async def daily_refresh_charData():
    await data_backup()


@sv.on_fullmatch('gs清除缓存')
async def send_backup_msg(
    bot: HoshinoBot,
    ev: CQEvent,
):
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return
    if qid not in bot.config.SUPERUSERS:
        return

    await data_backup()
    await bot.send(ev, f'操作成功完成!')


@sv.on_fullmatch('清除无效用户')
async def send_remove_invalid_user_msg(bot: HoshinoBot, ev: CQEvent):
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return
    if qid not in bot.config.SUPERUSERS:
        return
    im_list = []
    invalid_user = {}
    invalid_uid_list = []
    user_list = await get_all_push_list()
    friend_list = await get_all_friend_list(bot)
    for user in user_list:
        if user['StatusA'] == 'on':
            if user['QID'] not in friend_list:
                invalid_user['qid'] = user['UID']
                invalid_uid_list.append(user['UID'])
        else:
            group_member_list = await get_group_member_list(
                bot, int(user['StatusA'])
            )
            if user['QID'] not in group_member_list:
                invalid_user['qid'] = user['UID']
                invalid_uid_list.append(user['UID'])
    for uid in invalid_uid_list:
        im_list.append(await delete_cookies(str(uid)))
        logger.warning(f'无效UID已被删除: {uid}')
    await bot.send(ev, f'已清理失效用户{len(im_list)}个!')


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

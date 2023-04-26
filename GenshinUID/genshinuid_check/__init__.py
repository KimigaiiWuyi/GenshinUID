import random
import asyncio
from typing import List

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.aps import scheduler
from gsuid_core.utils.database.models import GsUser

from ..utils.mys_api import mys_api
from .backup_data import data_backup
from ..utils.database import get_sqla

sv_data_manger = SV('数据管理', pm=2)


@scheduler.scheduled_job('cron', hour=0, minute=6)
async def daily_refresh_charData():
    await data_backup()


@sv_data_manger.on_fullmatch(('gs清除缓存'))
async def send_backup_msg(bot: Bot, ev: Event):
    await data_backup()
    await bot.send('操作成功完成!')


@sv_data_manger.on_fullmatch(('校验全部Cookies'))
async def send_check_cookie(bot: Bot, ev: Event):
    user_list = await get_sqla(bot.bot_id).get_all_user()
    invalid_user: List[GsUser] = []
    for user in user_list:
        if user.cookie and user.mys_id:
            mys_data = await mys_api.get_mihoyo_bbs_info(
                user.mys_id,
                user.cookie,
                True if int(user.uid[0]) > 5 else False,
            )
            if isinstance(mys_data, int):
                await get_sqla(bot.bot_id).update_user_cookie(user.uid, None)
                invalid_user.append(user)
                continue
            for i in mys_data:
                if i['game_id'] != 2:
                    mys_data.remove(i)
    if len(user_list) > 4:
        im = f'正常Cookies数量: {len(user_list) - len(invalid_user)}'
        invalid = '\n'.join(
            [
                f'uid{user.uid}的Cookies是异常的!已删除该条Cookies!\n'
                for user in invalid_user
            ]
        )
        return_str = f'{im}\n{invalid if invalid else "无失效Cookie!"}'
    else:
        return_str = '\n'.join(
            [
                f'uid{user.uid}/mys{user.mys_id}的Cookies是正常的!'
                if user not in invalid_user
                else f'uid{user.uid}的Cookies是异常的!已删除该条Cookies!'
                for user in user_list
            ]
        )

    await bot.send(return_str)

    for i in invalid_user:
        await bot.target_send(
            f'您绑定的Cookies（uid{i.uid}）已失效，以下功能将会受到影响：\n'
            '查看完整信息列表\n查看深渊配队\n自动签到/当前状态/每月统计\n'
            '请及时重新绑定Cookies并重新开关相应功能。',
            'direct',
            target_id=i.user_id,
        )
        await asyncio.sleep(3 + random.randint(1, 3))


@sv_data_manger.on_fullmatch(('校验全部Stoken'))
async def send_check_stoken(bot: Bot, ev: Event):
    user_list = await get_sqla(bot.bot_id).get_all_user()
    invalid_user: List[GsUser] = []
    for user in user_list:
        if user.stoken and user.mys_id:
            mys_data = await mys_api.get_cookie_token_by_stoken(
                '', user.mys_id, user.stoken
            )
            if isinstance(mys_data, int):
                await get_sqla(bot.bot_id).update_user_stoken(user.uid, None)
                invalid_user.append(user)
                continue
    if len(user_list) > 4:
        im = f'正常Stoken数量: {len(user_list) - len(invalid_user)}'
        invalid = '\n'.join(
            [f'uid{user.uid}的Stoken是异常的!已清除Stoken!\n' for user in invalid_user]
        )
        return_str = f'{im}\n{invalid if invalid else "无失效Stoken!"}'
    else:
        return_str = '\n'.join(
            [
                f'uid{user.uid}/mys{user.mys_id}的Stoken是正常的!'
                if user not in invalid_user
                else f'uid{user.uid}的Stoken是异常的!已清除Stoken!'
                for user in user_list
            ]
        )

    await bot.send(return_str)

    for i in invalid_user:
        await bot.target_send(
            f'您绑定的Stoken（uid{i.uid}）已失效，以下功能将会受到影响：\n'
            'gs开启自动米游币，开始获取米游币。\n'
            '重新添加后需要重新开启自动米游币。',
            'direct',
            target_id=i.user_id,
        )
        await asyncio.sleep(3 + random.randint(1, 3))

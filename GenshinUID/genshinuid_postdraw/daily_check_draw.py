import random
import asyncio
import datetime
from copy import deepcopy
from typing import List, Optional

from gsuid_core.gss import gss
from gsuid_core.logger import logger
from gsuid_core.utils.database.models import GsUser
from gsuid_core.utils.api.mys.models import RoleCalendar, RolesCalendar

from .get_draw import post_my_draw
from ..utils.mys_api import mys_api

private_msg_list = {}
group_msg_list = {}
calendar: Optional[RolesCalendar] = None
is_got: Optional[bool] = None
today = datetime.datetime.now().day


async def check_today(uid: str) -> bool:
    global calendar
    global is_got
    global today
    if calendar is None:
        _calendar = await mys_api.get_draw_calendar(uid)
        if not isinstance(_calendar, int):
            calendar = _calendar
        else:
            return False

    now = datetime.datetime.now()

    if today == now.day and is_got is not None:
        return is_got
    else:
        today = now.day

    month = now.month
    calendar_role: List[RoleCalendar] = calendar['calendar_role_infos'][
        str(month)
    ]['calendar_role']

    assert isinstance(calendar_role, List)

    for char in calendar_role:
        char_day = char['role_birthday']
        day = now.day
        if char_day == f'{month}/{day}':
            is_got = True
            logger.info('[自动留影叙佳期] 今日有可获取角色，开启任务...')
            break
    else:
        is_got = False
        logger.info('[自动留影叙佳期] 今日无可获取角色，自动取消任务...')

    return is_got


async def single_get_draw(bot_id: str, uid: str, gid: str, qid: str):
    if is_got is not None and not is_got:
        return
    elif not await check_today(uid):
        return

    im = await post_my_draw(uid)

    if isinstance(im, (bytes, bytearray, memoryview)):
        return

    if '没有需要获取' in im:
        return

    if gid == 'on':
        if qid not in private_msg_list:
            private_msg_list[qid] = []
        private_msg_list[qid].append({'bot_id': bot_id, 'uid': uid, 'msg': im})
    else:
        # 向群消息推送列表添加这个群
        if gid not in group_msg_list:
            group_msg_list[gid] = {
                'bot_id': bot_id,
                'success': 0,
                'failed': 0,
            }

        # 如果失败, 则添加到推送列表
        if isinstance(im, bytes):
            group_msg_list[gid]['failed'] += 1
        else:
            group_msg_list[gid]['success'] += 1


async def daily_get_draw():
    tasks = []
    for bot_id in gss.active_bot:
        user_list = await GsUser.get_all_user()
        for user in user_list:
            if user.draw_switch != 'off':
                tasks.append(
                    single_get_draw(
                        user.bot_id, user.uid, user.sign_switch, user.user_id
                    )
                )
            if len(tasks) >= 1:
                await asyncio.gather(*tasks)
                delay = 50 + random.randint(3, 45)
                logger.info(f'[自动留影叙佳期] 已完成{len(tasks)}个用户, 等待{delay}秒进行下一次获取')
                tasks.clear()
                await asyncio.sleep(delay)

    await asyncio.gather(*tasks)
    tasks.clear()
    result = {
        'private_msg_list': deepcopy(private_msg_list),
        'group_msg_list': deepcopy(group_msg_list),
    }
    private_msg_list.clear()
    group_msg_list.clear()
    logger.info(result)
    logger.info('[自动留影叙佳期] 已结束')
    return result

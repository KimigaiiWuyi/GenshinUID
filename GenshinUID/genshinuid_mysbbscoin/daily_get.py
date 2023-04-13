import random
import asyncio

from gsuid_core.logger import logger

from ..utils.database import get_sqla
from .get_mihoyo_bbs_coin import MihoyoBBSCoin
from ..genshinuid_config.gs_config import gsconfig


async def all_daily_mihoyo_bbs_coin():
    sqla = get_sqla('TEMP')
    users = await sqla.get_all_user()
    vaild_list = [_u for _u in users if _u.bbs_switch != 'off' and _u.stoken]
    im_success = 0
    im_failed = 0
    im_failed_str = ''
    im_private = {}
    for user in vaild_list:
        logger.info(f'[米游币任务]正在执行{user.uid}')
        await asyncio.sleep(5 + random.randint(1, 3))
        if user.stoken is None:
            continue
        try:
            im = await mihoyo_coin(user.stoken)
            logger.info(f'[米游币任务]已执行完毕: {user.uid}')
            im_success += 1
            # 开启私聊报告
            if gsconfig.get_config('MhyBBSCoinReport').data:
                if user.bot_id not in im_private:
                    im_private[user.bot_id] = {}
                if user.user_id not in im_private[user.bot_id]:
                    im_private[user.bot_id][user.user_id] = ''
                im_private[user.bot_id][user.user_id] += im
        except Exception:
            logger.exception(f'[米游币任务]执行失败: {user.uid}')
            im_failed += 1
            im_failed_str += f'\n[米游币任务]执行失败: {user.uid}'
    faild_im = f'\n以下为签到失败报告: {im_failed_str}' if im_failed_str != '' else ''
    im = f'今日获取mhycoin成功数量: {im_success}，失败数量: {im_failed}{faild_im}'
    return im, im_private


async def mihoyo_coin(stoken: str):
    get_coin = MihoyoBBSCoin(stoken)
    im = await get_coin.task_run()
    return im

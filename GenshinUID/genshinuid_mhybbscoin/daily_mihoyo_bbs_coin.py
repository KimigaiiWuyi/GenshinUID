import random
import asyncio
import sqlite3

from nonebot.log import logger

from .get_mihoyo_bbs_coin import MihoyoBBSCoin
from ..utils.db_operation.db_operation import (
    select_db,
    get_stoken,
    config_check,
)


async def all_daily_mihoyo_bbs_coin():
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute(
        'SELECT *  FROM NewCookiesTable WHERE StatusC != ?', ('off',)
    )
    c_data = cursor.fetchall()
    im_success = 0
    im_failed = 0
    im_failed_str = ''
    im_private = {}
    for row in c_data:
        logger.info('正在执行{}'.format(row[0]))
        if row[8]:
            await asyncio.sleep(5 + random.randint(1, 3))
            im = await mihoyo_coin(str(row[2]), str(row[8]))
            try:
                logger.info('已执行完毕：{}'.format(row[0]))
                im_success += 1
                if await config_check('MhyBBSCoinReport'):
                    im_private[row[2]] = im
            except Exception:
                logger.exception('执行失败：{}'.format(row[0]))
                im_failed += 1
                im_failed_str += '\n' + '执行失败：{}'.format(row[0])
    faild_im = (
        '\n以下为签到失败报告：{}'.format(im_failed_str) if im_failed_str != '' else ''
    )
    im = '今日获取mhycoin成功数量：{}，失败数量：{}{}'.format(im_success, im_failed, faild_im)
    conn.close()
    return im, im_private


async def mihoyo_coin(qid, s_cookies=None):
    uid: str = await select_db(qid, mode='uid')  # type: ignore
    if s_cookies is None:
        s_cookies = await get_stoken(uid)

    if s_cookies:
        get_coin = MihoyoBBSCoin(s_cookies)
        im = await get_coin.task_run()
    else:
        im = '你还没有绑定Stoken~'
    return im

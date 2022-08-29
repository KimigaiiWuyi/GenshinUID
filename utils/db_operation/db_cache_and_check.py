import os
import re
import random
import string
import datetime
from shutil import copyfile

from httpx import AsyncClient
from nonebot.log import logger

from ..mhy_api.mhy_api import bbs_Taskslist
from .gsuid_db_pool import *  # noqa: F401,F403
from ..mhy_api.get_mhy_data import get_mihoyo_bbs_info
from ..mhy_api.mhy_api_tools import random_hex, old_version_get_ds_token


async def check_db():
    return_str = str()
    normal_num = 0
    invalid_str = ''
    invalid_list = []
    conn = gsuid_pool.connect()
    c = conn.cursor()
    cursor = c.execute('SELECT UID,Cookies,QID  from NewCookiesTable')
    c_data = cursor.fetchall()
    for row in c_data:
        try:
            aid = re.search(r'account_id=(\d*)', row[1])
            mihoyo_id_data = aid.group(0).split('=')  # type: ignore
            mihoyo_id = mihoyo_id_data[1]
            mys_data = await get_mihoyo_bbs_info(mihoyo_id, row[1])
            for i in mys_data['data']['list']:
                if i['game_id'] != 2:
                    mys_data['data']['list'].remove(i)
            return_str = (
                return_str + f'uid{row[0]}/mys{mihoyo_id}的Cookies是正常的！\n'
            )
            normal_num += 1
            logger.info(f'uid{row[0]}/mys{mihoyo_id}的Cookies是正常的！')
        except:
            invalid_str = (
                invalid_str + f'uid{row[0]}的Cookies是异常的！已删除该条Cookies！\n'
            )
            return_str = (
                return_str + f'uid{row[0]}的Cookies是异常的！已删除该条Cookies！\n'
            )
            invalid_list.append([row[2], row[0]])
            c.execute('DELETE from NewCookiesTable where UID=?', (row[0],))
            try:
                c.execute(
                    'DELETE from CookiesCache where Cookies=?', (row[1],)
                )
            except:
                pass
            logger.info(f'uid{row[0]}的Cookies是异常的！已删除该条Cookies！')
    if len(c_data) > 9:
        return_str = '正常Cookies数量：{}\n{}'.format(
            str(normal_num),
            '失效cookies:\n' + invalid_str if invalid_str else '无失效Cookies',
        )
    conn.commit()
    conn.close()
    logger.info('已完成Cookies检查！')
    logger.info(f'正常Cookies数量：{str(normal_num)}')
    logger.info(f'失效cookies:\n' + invalid_str if invalid_str else '无失效Cookies')
    return [return_str, invalid_list]


async def refresh_ck(uid, mysid):
    conn = gsuid_pool.connect()
    c = conn.cursor()
    try:
        c.execute(
            'DELETE from CookiesCache where uid=? or mysid = ?', (uid, mysid)
        )
    except:
        pass


async def check_stoken_db():
    def random_text(num: int) -> str:
        return ''.join(
            random.sample(string.ascii_lowercase + string.digits, num)
        )

    return_str = str()
    normal_num = 0
    invalid_str = ''
    invalid_list = []
    conn = gsuid_pool.connect()
    c = conn.cursor()
    cursor = c.execute('SELECT UID,Stoken,QID  from NewCookiesTable')
    c_data = cursor.fetchall()
    for row in c_data:
        if row[1] is None:
            continue
        async with AsyncClient() as client:
            req = await client.get(
                url=bbs_Taskslist,
                headers={
                    'DS': old_version_get_ds_token(True),
                    'cookie': row[1],
                    'x-rpc-client_type': '2',
                    'x-rpc-app_version': '2.7.0',
                    'x-rpc-sys_version': '6.0.1',
                    'x-rpc-channel': 'mihoyo',
                    'x-rpc-device_id': random_hex(32),
                    'x-rpc-device_name': random_text(random.randint(1, 10)),
                    'x-rpc-device_model': 'Mi 10',
                    'Referer': 'https://app.mihoyo.com',
                    'Host': 'bbs-api.mihoyo.com',
                    'User-Agent': 'okhttp/4.8.0',
                },
            )
        data = req.json()
        if 'err' in data['message'] or data['retcode'] == -100:
            invalid_str = (
                invalid_str + f'uid{row[0]}的Stoken是异常的！已删除该条Stoken！\n'
            )
            return_str = return_str + f'uid{row[0]}的Stoken是异常的！已删除该条Stoken！\n'
            invalid_list.append([row[2], row[0]])
            c.execute(
                'UPDATE NewCookiesTable SET Stoken = ? WHERE UID=?',
                (None, row[0]),
            )
            logger.info(f'uid{row[0]}的Stoken是异常的！已删除该条Stoken！')
        else:
            return_str = return_str + f'uid{row[0]}的Stoken是正常的！\n'
            logger.info(f'uid{row[0]}的Stoken是正常的！')
            normal_num += 1
    if len(c_data) > 9:
        return_str = '正常Stoken数量：{}\n{}'.format(
            str(normal_num),
            '失效Stoken:\n' + invalid_str if invalid_str else '无失效Stoken',
        )
    conn.commit()
    conn.close()
    logger.info('已完成Stoken检查!')
    logger.info(f'正常Stoken数量：{normal_num}')
    logger.info(f'失效Stoken:\n' + invalid_str if invalid_str else '无失效Stoken')
    return [return_str, invalid_list]


async def delete_cache():
    try:
        today = datetime.date.today()
        endday = today - datetime.timedelta(days=5)
        date_format = today.strftime("%Y_%d_%b")
        endday_format = endday.strftime("%Y_%d_%b")
        copyfile('ID_DATA.db', f'ID_DATA_BAK_{date_format}.db')
        if os.path.exists(f'ID_DATA_BAK_{endday_format}.db'):
            os.remove(f'ID_DATA_BAK_{endday_format}.db')
            logger.info(f'————已删除数据库备份{endday_format}————')
        logger.info('————数据库成功备份————')
    except:
        logger.info('————数据库备份失败————')

    try:
        conn = gsuid_pool.connect()
        c = conn.cursor()
        c.execute('DROP TABLE CookiesCache')
        c.execute(
            'UPDATE NewCookiesTable SET Extra = ? WHERE Extra=?',
            (None, 'limit30'),
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS CookiesCache
        (UID TEXT PRIMARY KEY,
        MYSID         TEXT,
        Cookies       TEXT);"""
        )
        conn.commit()
        conn.close()
        logger.info('————UID查询缓存已清空————')
    except:
        logger.info('\nerror\n')

    try:
        conn = gsuid_pool.connect()
        c = conn.cursor()
        c.execute('UPDATE UseridDict SET lots=NULL')
        conn.commit()
        conn.close()
        logger.info('————御神签缓存已清空————')
    except:
        logger.info('\nerror\n')

import os
import datetime
from shutil import copyfile

from nonebot.log import logger


async def data_backup():
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

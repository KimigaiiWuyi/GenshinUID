import os
import datetime
from shutil import copyfile

from gsuid_core.logger import logger
from gsuid_core.data_store import get_res_path
from gsuid_core.utils.database.models import GsUser, GsCache

from ..utils.database import db_url
from ..utils.resource.RESOURCE_PATH import TEMP_PATH

DB = get_res_path().parent / 'GsData.db'
DB_BACKUP = get_res_path() / 'GenshinUID'


async def data_backup():
    try:
        today = datetime.date.today()
        endday = today - datetime.timedelta(days=5)
        date_format = today.strftime("%Y_%d_%b")
        endday_format = endday.strftime("%Y_%d_%b")
        backup = DB_BACKUP / f'GsData_BAK_{date_format}.db'
        end_day_backup = DB_BACKUP / f'GsData_BAK_{endday_format}.db'
        copyfile(db_url, backup)
        if os.path.exists(end_day_backup):
            os.remove(end_day_backup)
            logger.info(f'————已删除数据库备份{endday_format}————')
        logger.info('————数据库成功备份————')
        for f in TEMP_PATH.glob('*.jpg'):
            try:
                f.unlink()
            except OSError as e:
                print("Error: %s : %s" % (f, e.strerror))
        await GsCache.delete_all_cache(GsUser)
        logger.info('————缓存成功清除————')
    except Exception:
        logger.info('————数据库备份失败————')

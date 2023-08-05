from typing import Dict

from gsuid_core.data_store import get_res_path
from gsuid_core.utils.database.dal import SQLA
from gsuid_core.utils.database.api import DBSqla

is_wal = False

active_sqla: Dict[str, SQLA] = {}
db_url = str(get_res_path().parent / 'GsData.db')
db_sqla = DBSqla()
get_sqla = db_sqla.get_sqla

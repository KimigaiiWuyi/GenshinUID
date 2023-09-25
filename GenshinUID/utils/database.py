from typing import Dict

from gsuid_core.data_store import get_res_path
from gsuid_core.utils.database.dal import SQLA

is_wal = False

active_sqla: Dict[str, SQLA] = {}
db_url = str(get_res_path().parent / 'GsData.db')

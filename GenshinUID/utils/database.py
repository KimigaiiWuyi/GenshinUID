from typing import Dict

from sqlalchemy import event
from gsuid_core.data_store import get_res_path
from gsuid_core.utils.database.dal import SQLA

is_wal = False

active_sqla: Dict[str, SQLA] = {}
db_url = str(get_res_path().parent / 'GsData.db')


def get_sqla(bot_id) -> SQLA:
    if bot_id not in active_sqla:
        sqla = SQLA(db_url, bot_id)
        active_sqla[bot_id] = sqla
        sqla.create_all()

        @event.listens_for(sqla.engine.sync_engine, 'connect')
        def engine_connect(conn, branch):
            if is_wal:
                cursor = conn.cursor()
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.close()

    return active_sqla[bot_id]

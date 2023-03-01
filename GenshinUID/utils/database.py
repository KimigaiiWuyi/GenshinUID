from typing import Dict

from sqlalchemy import event
from gsuid_core.gss import gss

from ..gsuid_utils.database.dal import SQLA

is_wal = False

active_sqla: Dict[str, SQLA] = {}
db_url = 'GsData.db'


@gss.on_bot_connect
async def refresh_sqla():
    for bot_id in gss.active_bot:
        sqla = SQLA(db_url, bot_id)
        active_sqla[bot_id] = sqla
        sqla.create_all()

        @event.listens_for(sqla.engine.sync_engine, 'connect')
        def engine_connect(conn, branch):
            if is_wal:
                cursor = conn.cursor()
                cursor.execute('PRAGMA journal_mode=WAL')
                cursor.close()

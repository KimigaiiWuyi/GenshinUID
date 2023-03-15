from hoshino.typing import CQEvent, HoshinoBot

from ..base import sv
from .export_data import export_v3


@sv.on_prefix(('导出v3数据'))
async def send_export_msg(bot: HoshinoBot, ev: CQEvent):
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return
    if qid not in bot.config.SUPERUSERS:
        return
    await bot.send(ev, '开始导出数据..可能需要一定时间！')
    await export_v3()
    await bot.send(ev, '导出数据成功！')

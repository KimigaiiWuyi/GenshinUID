from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER

from .export_data import export_v3
from ..utils.nonebot2.rule import FullCommand

export_v3_data = on_command('导出v3数据', permission=SUPERUSER, rule=FullCommand())


@export_v3_data.handle()
async def send_export_msg(matcher: Matcher):
    await matcher.send('开始导出数据..可能需要一定时间！')
    await export_v3()
    await matcher.send('导出数据成功！')

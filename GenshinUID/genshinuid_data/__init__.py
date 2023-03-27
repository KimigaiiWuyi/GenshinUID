from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .import_data import import_v3_data

sv_v3_data = SV('数据备份恢复', pm=1)


@sv_v3_data.on_fullmatch(('导入v3数据'))
async def send_import_data_msg(bot: Bot, ev: Event):
    await bot.send('开始导入v3数据...可能会比较久...')
    await bot.send(await import_v3_data())

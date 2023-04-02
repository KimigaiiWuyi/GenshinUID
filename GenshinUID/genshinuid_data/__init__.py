from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .import_data import import_v3_data
from .reset_config import reset_sv_config

sv_v3_data = SV('数据备份恢复', pm=1)
sv_config_admin = SV('core配置管理', pm=1)


@sv_v3_data.on_fullmatch(('导入v3数据'))
async def send_import_data_msg(bot: Bot, ev: Event):
    await bot.send('开始导入v3数据...可能会比较久...')
    await bot.send(await import_v3_data())


@sv_config_admin.on_fullmatch(('重置core配置'))
async def send_reset_core_config(bot: Bot, ev: Event):
    await bot.send(await reset_sv_config())

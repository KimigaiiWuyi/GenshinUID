from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .import_data import import_v3_data
from .reset_config import reset_sv_config

sv_v3_data = SV("数据备份恢复", pm=1)
sv_config_admin = SV("core配置管理", pm=1)


@sv_v3_data.on_fullmatch(
    ("导入v3数据"),
    to_ai="""导入v3版本的旧数据到当前系统（管理员功能）

    当管理员说"导入v3数据"、"迁移旧版数据"时调用。
    此操作可能耗时较长，操作结果以文字形式返回。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_import_data_msg(bot: Bot, ev: Event):
    await bot.send("开始导入v3数据...可能会比较久...")
    await bot.send(await import_v3_data())


@sv_config_admin.on_fullmatch(
    ("重置core配置"),
    to_ai="""重置GenshinUID的core配置到默认状态（管理员功能）

    当管理员说"重置配置"、"恢复默认设置"时调用。
    将所有配置项恢复为默认值。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_reset_core_config(bot: Bot, ev: Event):
    await bot.send(await reset_sv_config())

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger

from .data_source import get_code_msg

sv_zzz_code = SV('原神前瞻兑换码')


@sv_zzz_code.on_fullmatch('兑换码')
async def get_sign_func(bot: Bot, ev: Event):
    try:
        codes = await get_code_msg()
    except Exception as e:
        logger.opt(exception=e).error("获取前瞻兑换码失败")
        codes = "获取前瞻兑换码失败"
    await bot.send(codes)

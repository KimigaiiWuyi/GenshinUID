from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .draw_teyvat_returnlist import draw_teyvat_returnlist_img

sv_get_returnlist = SV("查询未复刻天数", priority=4)


@sv_get_returnlist.on_fullmatch(("未复刻", "未复刻列表", "复刻列表"), block=True)
async def send_abyss_pic(bot: Bot, ev: Event):
    img = await draw_teyvat_returnlist_img()
    logger.info("[未复刻] 获得未复刻UP列表成功!")
    await bot.send(img)

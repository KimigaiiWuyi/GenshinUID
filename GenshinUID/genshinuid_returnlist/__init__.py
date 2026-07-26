from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .draw_teyvat_returnlist import draw_teyvat_returnlist_img

sv_get_returnlist = SV("查询未复刻天数", priority=4)


@sv_get_returnlist.on_fullmatch(
    ("未复刻", "未复刻列表", "复刻列表"),
    block=True,
    to_ai="""查看原神角色和武器的未复刻天数列表

    当用户说"未复刻"、"复刻列表"、"哪些角色很久没复刻"时调用。
    以图片形式返回各角色/武器距离上次UP的天数排行。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_abyss_pic(bot: Bot, ev: Event):
    img = await draw_teyvat_returnlist_img()
    logger.info(t("log.genshinuid.up_e329b8"))
    await bot.send(img)

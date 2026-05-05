from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.ai_core.trigger_bridge import ai_return

from .get_adv import char_adv, weapon_adv

sv_adv_text = SV("文字推荐")

__all__ = ["ai_return"]


@sv_adv_text.on_suffix(
    ("用什么", "能用啥", "怎么养"),
    to_ai="""查询原神角色的武器和圣遗物推荐

    当用户说"甘雨用什么"、"胡桃能用啥"、"纳西妲怎么养"时调用。
    返回该角色推荐的武器和圣遗物搭配方案。

    Args:
        text: "用什么"/"能用啥"/"怎么养"前面的角色名称，例如 "甘雨"、"胡桃"、"纳西妲"
              支持角色昵称，例如 "雷神"、"小草神"
    """,
)
async def send_char_adv(bot: Bot, ev: Event):
    result = await char_adv(ev.text)
    if isinstance(result, str):
        ai_return(result)
    await bot.send(result)


@sv_adv_text.on_suffix(
    ("能给谁", "谁能用", "给谁用"),
    to_ai="""查询原神武器适合哪些角色

    当用户说"天空之翼能给谁"、"护摩之杖谁能用"、"西风剑给谁用"时调用。
    返回适合使用该武器的角色列表。

    Args:
        text: "能给谁"/"谁能用"/"给谁用"前面的武器名称，例如 "天空之翼"、"护摩之杖"、"西风剑"
    """,
)
async def send_weapon_adv(bot: Bot, ev: Event):
    result = await weapon_adv(ev.text)
    if isinstance(result, str):
        ai_return(result)
    await bot.send(result)

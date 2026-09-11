from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

sv_wiki_text = SV("原神WIKI图鉴")


@sv_wiki_text.on_prefix(
    ("角色介绍", "角色资料", "查角色", "角色命座", "查命座", "角色天赋", "查天赋", "角色材料"),
    to_ai="""查询原神角色图鉴卡片（命座/天赋/材料/简介）

    当用户说"查角色 甘雨"、"角色介绍 雷电将军"、"角色命座 申鹤"、"角色天赋 纳西妲"、"角色材料 可莉"时调用。
    返回一张角色卡片，含简介、90级面板、天赋、命座与养成材料。旧的命座/天赋/材料命令已合并到本卡片。

    Args:
        text: 角色名称，可后跟 20–90 的等级，例如 "甘雨"、"雷神"、"七七90"
    """,
)
async def send_char(bot: Bot, ev: Event) -> None:
    from .html_wiki import render_char_card

    await bot.send(await render_char_card(ev.text))


@sv_wiki_text.on_prefix(
    ("武器介绍", "武器资料", "查武器", "武器材料"),
    to_ai="""查询原神武器图鉴卡片（属性/特效/突破材料）

    当用户说"查武器 护摩之杖"、"武器介绍 天空之翼"、"武器材料 西风剑"时调用。
    返回一张武器卡片，含1/满级攻击与副词条、精炼特效、突破材料。

    Args:
        text: 武器名称，可后跟 20–90 的等级，例如 "护摩之杖"、"西风剑90"
    """,
)
async def send_weapon(bot: Bot, ev: Event) -> None:
    from .html_wiki import render_weapon_card

    await bot.send(await render_weapon_card(ev.text))


@sv_wiki_text.on_prefix(
    ("圣遗物介绍", "圣遗物资料", "查圣遗物"),
    to_ai="""查询原神圣遗物套装图鉴卡片

    当用户说"查圣遗物 绝缘之旗印"、"圣遗物介绍 乐园"时调用。
    返回套装 2/4 件效果与五件部位名称、简介。

    Args:
        text: 圣遗物套装名称或简称，例如 "绝缘之旗印"、"追忆"、"乐园"
    """,
)
async def send_artifacts(bot: Bot, ev: Event) -> None:
    from .html_wiki import render_artifact_card

    await bot.send(await render_artifact_card(ev.text))


@sv_wiki_text.on_prefix(
    ("食物介绍", "食物资料", "查食物"),
    to_ai="""查询原神食物图鉴卡片

    当用户说"查食物 甜甜花酿鸡"、"食物介绍 仙跳墙"时调用。
    返回效果、简介与食材。名称过短会列出候选。

    Args:
        text: 食物名称，例如 "甜甜花酿鸡"、"松茸酿肉卷"、"仙跳墙"
    """,
)
async def send_food(bot: Bot, ev: Event) -> None:
    from .html_wiki import render_food_card

    await bot.send(await render_food_card(ev.text))


@sv_wiki_text.on_prefix(
    ("原魔介绍", "原魔资料", "查原魔"),
    to_ai="""查询原神原魔（怪物）图鉴卡片，含抗性

    当用户说"查原魔 丘丘人"、"原魔介绍 无相之雷"、"原魔资料 遗迹守卫"时调用。
    返回类型、简介、元素抗性、词缀与掉落。

    Args:
        text: 原魔名称，例如 "丘丘人"、"深渊使徒"、"无相之雷"、"公子"
    """,
)
async def send_enemies(bot: Bot, ev: Event) -> None:
    from .html_wiki import render_monster_card

    await bot.send(await render_monster_card(ev.text))

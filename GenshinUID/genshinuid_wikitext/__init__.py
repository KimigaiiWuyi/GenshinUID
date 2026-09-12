from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

sv_wiki_text = SV("原神WIKI图鉴")


@sv_wiki_text.on_prefix(("角色介绍", "角色资料", "查角色"))
async def send_char(bot: Bot, ev: Event) -> None:
    from .html_wiki import render_char_card

    await bot.send(await render_char_card(ev.text))


@sv_wiki_text.on_prefix(
    ("角色天赋", "查天赋"),
    to_ai="""查询原神角色天赋卡片

    当用户说"角色天赋 纳西妲"、"雷神大招倍率"、"甘雨天赋"时调用。
    只返回普攻/战技/爆发/固有与 Lv10 倍率。

    Args:
        text: 角色名称或简称，例如 "纳西妲"、"雷神"
    """,
)
async def send_char_talents(bot: Bot, ev: Event) -> None:
    from .html_wiki import render_char_talent_card

    await bot.send(await render_char_talent_card(ev.text))


@sv_wiki_text.on_prefix(
    ("角色命座", "查命座"),
    to_ai="""查询原神角色命座卡片

    当用户说"角色命座 申鹤"、"雷神 C2 是什么"、"可莉几命"时调用。
    只返回 C1–C6 名称与效果。

    Args:
        text: 角色名称或简称，例如 "申鹤"、"雷神"、"可莉"
    """,
)
async def send_char_const(bot: Bot, ev: Event) -> None:
    from .html_wiki import render_char_const_card

    await bot.send(await render_char_const_card(ev.text))


@sv_wiki_text.on_prefix(
    ("角色材料",),
    to_ai="""查询原神角色养成材料卡片

    当用户说"角色材料 可莉"、"雷神要刷什么"、"突破材料"时调用。
    只返回突破与天赋材料数量。

    Args:
        text: 角色名称或简称，例如 "可莉"、"雷神"
    """,
)
async def send_char_materials(bot: Bot, ev: Event) -> None:
    from .html_wiki import render_char_material_card

    await bot.send(await render_char_material_card(ev.text))


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
    ("原魔介绍", "原魔资料", "查原魔", "怪物介绍"),
    to_ai="""查询原神原魔（怪物）图鉴卡片，含抗性

    当用户说"查原魔 丘丘人"、"原魔介绍 无相之雷"、"怪物介绍 遗迹守卫"时调用。
    返回类型、简介、元素抗性、词缀与掉落。

    Args:
        text: 原魔名称，例如 "丘丘人"、"深渊使徒"、"无相之雷"、"公子"
    """,
)
async def send_enemies(bot: Bot, ev: Event) -> None:
    from .html_wiki import render_monster_card

    await bot.send(await render_monster_card(ev.text))


@sv_wiki_text.on_prefix(
    ("角色故事", "角色逸闻"),
    to_ai="""查询原神角色好感故事卡片

    当用户说"角色故事 桑多涅"、"角色故事雷神"、"角色逸闻 甘雨"时调用。
    只返回角色详细与好感故事，不含语音。语音走「角色语音」。

    Args:
        text: 角色名称或简称，例如 "桑多涅"、"雷神"、"芙宁娜"
    """,
)
async def send_char_story(bot: Bot, ev: Event) -> None:
    from .html_wiki import render_story_card

    await bot.send(await render_story_card(ev.text))


@sv_wiki_text.on_prefix(
    ("角色语音",),
    to_ai="""查询原神角色语音台词卡片，或按编号发送语音文件

    当用户说"角色语音 可莉"、"角色语音雷神"时调用，返回台词卡片。
    当用户说"角色语音可莉3"、"可莉第3条语音"时调用，发送该编号语音。
    只返回语音台词，不含好感故事。故事走「角色故事」。

    Args:
        text: 角色名称或简称，可后跟编号，例如 "可莉"、"可莉3"、"雷神"
    """,
)
async def send_char_voice(bot: Bot, ev: Event) -> None:
    from gsuid_core.segment import MessageSegment

    from .html_wiki import render_voice_card, render_voice_audio
    from .wiki_data import parse_voice_query

    _name, index = parse_voice_query(ev.text)
    if index is not None:
        result = await render_voice_audio(ev.text)
        if isinstance(result, str):
            await bot.send(result)
            return
        caption, path = result
        await bot.send(caption)
        await bot.send(MessageSegment.record(path))
        return
    await bot.send(await render_voice_card(ev.text))

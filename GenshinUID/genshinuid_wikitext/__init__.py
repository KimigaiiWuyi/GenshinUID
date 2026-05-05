import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.ai_core.trigger_bridge import ai_return

from .get_cost_pic import get_char_cost_wiki_img
from .get_foods_pic import get_foods_wiki_img
from .get_wiki_text import (
    char_wiki,
    foods_wiki,
    talent_wiki,
    weapon_wiki,
    enemies_wiki,
    artifacts_wiki,
    char_costs_wiki,
    char_stats_wiki,
    weapon_costs_wiki,
    weapon_stats_wiki,
    constellation_wiki,
)
from .get_weapons_pic import get_weapons_wiki_img
from .get_artifacts_pic import get_artifacts_wiki_img
from .get_constellation_pic import (
    get_constellation_wiki_img,
    get_single_constellation_img,
)
from ..utils.map.name_covert import alias_to_char_name
from ..genshinuid_config.gs_config import gsconfig

sv_wiki_text = SV("原神WIKI文字版")


@sv_wiki_text.on_prefix(
    ("原魔介绍", "原魔资料", "查原魔"),
    to_ai="""查询原神原魔（怪物）的详细介绍

    当用户说"查原魔 丘丘人"、"原魔介绍 深渊使徒"、"原魔资料 遗迹守卫"时调用。
    返回怪物的属性、技能、掉落物等详细信息。

    Args:
        text: 原魔名称，例如 "丘丘人"、"深渊使徒"、"遗迹守卫"、"无相之雷"
    """,
)
async def send_enemies(bot: Bot, ev: Event):
    result = await enemies_wiki(ev.text)
    if isinstance(result, str):
        ai_return(result)
    await bot.send(result)


@sv_wiki_text.on_prefix(
    ("食物介绍", "食物资料", "查食物"),
    to_ai="""查询原神食物的详细介绍

    当用户说"查食物 甜甜花酿鸡"、"食物介绍 松茸酿肉卷"时调用。
    返回食物的效果、配方、获取方式等信息。

    Args:
        text: 食物名称，例如 "甜甜花酿鸡"、"松茸酿肉卷"、"仙跳墙"
    """,
)
async def send_food(bot: Bot, ev: Event):
    if gsconfig.get_config("PicWiki").data:
        im = await get_foods_wiki_img(ev.text)
    else:
        im = await foods_wiki(ev.text)
        if isinstance(im, str):
            ai_return(im)
    await bot.send(im)


@sv_wiki_text.on_prefix(
    ("圣遗物介绍", "圣遗物资料", "查圣遗物"),
    to_ai="""查询原神圣遗物套装的详细介绍

    当用户说"查圣遗物 绝缘之旗印"、"圣遗物介绍 追忆之注连"时调用。
    返回套装效果（2件套/4件套）、适用角色推荐等信息。

    Args:
        text: 圣遗物套装名称，例如 "绝缘之旗印"、"追忆之注连"、"华馆梦醒形骸记"
    """,
)
async def send_artifacts(bot: Bot, ev: Event):
    if gsconfig.get_config("PicWiki").data:
        im = await get_artifacts_wiki_img(ev.text)
    else:
        im = await artifacts_wiki(ev.text)
        if isinstance(im, str):
            ai_return(im)
    await bot.send(im)


@sv_wiki_text.on_prefix(
    ("武器介绍", "武器资料", "查武器"),
    to_ai="""查询原神武器的详细介绍和属性

    当用户说"查武器 护摩之杖"、"武器介绍 天空之翼"、"武器资料 西风剑90"时调用。
    返回武器的基础属性、被动效果、适用角色等信息。

    Args:
        text: 武器名称，可选后跟等级数字查看特定等级属性
              例如 "护摩之杖"、"天空之翼"、"西风剑90"
    """,
)
async def send_weapon(bot: Bot, ev: Event):
    name = "".join(re.findall("[\u4e00-\u9fa5]", ev.text))
    level = re.findall(r"\d+", ev.text)
    if len(level) == 1:
        im = await weapon_stats_wiki(name, int(level[0]))
    else:
        if gsconfig.get_config("PicWiki").data:
            im = await get_weapons_wiki_img(name)
        else:
            im = await weapon_wiki(name)
    if isinstance(im, str):
        ai_return(im)
    await bot.send(im)


@sv_wiki_text.on_prefix(
    ("角色天赋", "查天赋"),
    to_ai="""查询原神角色天赋的详细介绍

    当用户说"查天赋 甘雨 1"、"角色天赋 雷电将军 2"时调用。
    返回指定天赋的名称、效果、倍率等详细信息。

    Args:
        text: 格式为"角色名 天赋编号"，天赋编号为1/2/3
              例如 "甘雨 1"、"雷电将军 2"、"纳西妲 3"
    """,
)
async def send_talents(bot: Bot, ev: Event):
    name = "".join(re.findall("[\u4e00-\u9fa5]", ev.text))
    name = await alias_to_char_name(name)
    num = re.findall(r"\d+", ev.text)
    if len(num) == 1:
        im = await talent_wiki(name, int(num[0]))
        if isinstance(im, list):
            return await bot.send(MessageSegment.node(im))
    else:
        im = "参数不正确。"
    if isinstance(im, str):
        ai_return(im)
    await bot.send(im)


@sv_wiki_text.on_prefix(
    ("角色介绍", "角色资料", "查角色"),
    to_ai="""查询原神角色的详细介绍和属性

    当用户说"查角色 甘雨"、"角色介绍 雷电将军"、"角色资料 纳西妲90"时调用。
    返回角色的基础属性、突破加成、命座等信息。

    Args:
        text: 角色名称，可选后跟等级数字查看特定等级属性
              例如 "甘雨"、"雷电将军"、"纳西妲90"
              支持角色昵称，例如 "雷神"、"小草神"
    """,
)
async def send_char(bot: Bot, ev: Event):
    name = "".join(re.findall("[\u4e00-\u9fa5]", ev.text))
    name = await alias_to_char_name(name)
    level = re.findall(r"\d+", ev.text)
    if len(level) == 1:
        im = await char_stats_wiki(name, int(level[0]))
    else:
        im = await char_wiki(name)
    if isinstance(im, str):
        ai_return(im)
    await bot.send(im)


@sv_wiki_text.on_prefix(
    ("角色材料"),
    to_ai="""查询原神角色突破所需材料

    当用户说"角色材料 甘雨"、"角色材料 雷电将军"时调用。
    返回角色各突破阶段所需的材料清单。

    Args:
        text: 角色名称，例如 "甘雨"、"雷电将军"
              支持角色昵称，例如 "雷神"、"小草神"
    """,
)
async def send_char_cost(bot: Bot, ev: Event):
    name = await alias_to_char_name(ev.text)
    if gsconfig.get_config("PicWiki").data:
        im = await get_char_cost_wiki_img(name)
    else:
        im = await char_costs_wiki(name)
        if isinstance(im, str):
            ai_return(im)
    await bot.send(im)


@sv_wiki_text.on_prefix(
    ("武器材料"),
    to_ai="""查询原神武器突破所需材料

    当用户说"武器材料 护摩之杖"、"武器材料 天空之翼"时调用。
    返回武器各突破阶段所需的材料清单。

    Args:
        text: 武器名称，例如 "护摩之杖"、"天空之翼"、"西风剑"
    """,
)
async def send_weapon_cost(bot: Bot, ev: Event):
    if gsconfig.get_config("PicWiki").data:
        im = await get_weapons_wiki_img(ev.text)
    else:
        im = await weapon_costs_wiki(ev.text)
        if isinstance(im, str):
            ai_return(im)
    await bot.send(im)


@sv_wiki_text.on_prefix(
    ("角色命座", "查命座"),
    to_ai="""查询原神角色命座的详细介绍

    当用户说"查命座 申鹤 2"、"角色命座 雷电将军"时调用。
    返回指定命座或全部命座的效果描述。

    Args:
        text: 格式为"角色名 [命座编号]"，例如 "申鹤 2"、"雷电将军 6"
              不带编号显示全部命座图片，例如 "雷电将军"
              支持角色昵称，例如 "雷神"、"小草神"
    """,
)
async def send_polar(bot: Bot, ev: Event):
    m = "".join(re.findall("[\u4e00-\u9fa5]", ev.text))
    num_re = re.findall(r"\d+", ev.text)

    m = await alias_to_char_name(m)

    if num_re:
        num = int(num_re[0])
    else:
        if gsconfig.get_config("PicWiki").data:
            return await bot.send(await get_constellation_wiki_img(m))
        else:
            return await bot.send("请输入正确的命座数,例如 角色命座申鹤2!")

    if num <= 0 or num > 6:
        return await bot.send("你家{}有{}命？".format(m, num))

    if gsconfig.get_config("PicWiki").data:
        im = await get_single_constellation_img(m, num)
    else:
        im = await constellation_wiki(m, num)
        if isinstance(im, str):
            ai_return(im)
    await bot.send(im)

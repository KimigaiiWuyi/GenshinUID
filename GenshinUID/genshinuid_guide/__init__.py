from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .get_guide import get_gs_guide
from .html_endgame import build_abyss_image, build_leyline_image, build_roleplay_image
from .endgame_query import period_shift, parse_abyss_args, parse_schedule_args
from ..utils.message import GButton as Button
from .get_bbs_post_guide import get_material_way_post
from ..utils.image.convert import convert_img
from ..utils.map.name_covert import alias_to_char_name
from ..utils.resource.RESOURCE_PATH import REF_PATH

sv_char_guide = SV("查询角色攻略")
sv_abyss_reviews = SV("查询深渊阵容", priority=2)
sv_poetry_abyss_reviews = SV("查询剧诗深渊阵容", priority=3)
sv_leyline_reviews = SV("查询幽境危战阵容", priority=3)
sv_bbs_post_guide = SV("查询BBS攻略")


@sv_bbs_post_guide.on_suffix(
    ("路线"),
    to_ai="""查询原神材料的采集路线攻略

    当用户说"清心路线"、"琉璃袋路线"、"绯樱绣球路线"时调用。
    返回该材料的推荐采集路线图文攻略。

    Args:
        text: "路线"前面的材料名称，例如 "清心"、"琉璃袋"、"绯樱绣球"
    """,
)
async def send_bbs_post_guide(bot: Bot, ev: Event):
    name = ev.text.strip().replace("材料", "").replace("采集", "")
    result = await get_material_way_post(name)
    await bot.send(result)


@sv_char_guide.on_prefix(
    ("参考攻略", "攻略", "推荐"),
    covers=["角色攻略", "原神攻略"],
    to_ai="""查询原神角色攻略图片

    当用户说"攻略 甘雨"、"参考攻略 雷电将军"、"推荐 胡桃"时调用。
    以图片形式返回该角色的攻略参考图。

    Args:
        text: 角色名称，例如 "甘雨"、"雷电将军"、"胡桃"
              支持角色昵称，例如 "雷神"、"小草神"
    """,
)
@sv_char_guide.on_suffix(
    ("攻略", "推荐"),
    covers=["角色攻略", "原神攻略"],
    to_ai="""查询原神角色攻略图片

    当用户说"甘雨攻略"、"雷电将军推荐"时调用。
    以图片形式返回该角色的攻略参考图。

    Args:
        text: "攻略"/"推荐"前面的角色名称，例如 "甘雨"、"雷电将军"
    """,
)
async def send_guide_pic(bot: Bot, ev: Event):
    name = ev.text.strip()
    im = await get_gs_guide(name)

    if im:
        await bot.logger.info(t("log.genshinuid.guide_ok", name=name))
        a = Button(f"🎴参考面板{name}", f"参考面板{name}")
        await bot.send_option(im, [a])
    else:
        await bot.logger.warning(t("log.genshinuid.guide_missing", name=name))


@sv_char_guide.on_prefix(
    ("参考面板"),
    to_ai="""查询原神角色参考面板图片

    当用户说"参考面板 甘雨"、"参考面板 雷电将军"时调用。
    以图片形式返回该角色的参考面板配置图。也支持按元素筛选。

    Args:
        text: 角色名称或元素名，例如 "甘雨"、"雷电将军"
              元素名: "冰"、"水"、"火"、"草"、"雷"、"风"、"岩"
    """,
)
async def send_bluekun_pic(bot: Bot, ev: Event):
    if ev.text in ["冰", "水", "火", "草", "雷", "风", "岩"]:
        name = ev.text
    else:
        name = await alias_to_char_name(ev.text.strip())
    img = REF_PATH / "{}.jpg".format(name)
    if img.exists():
        img = await convert_img(img)
        await bot.logger.info(t("log.genshinuid.guide_ref_ok", name=name))
        await bot.send_option(img, [Button(f"🎴{name}攻略", f"{name}攻略")])
    else:
        await bot.logger.warning(t("log.genshinuid.guide_ref_missing", name=name))


@sv_poetry_abyss_reviews.on_command(
    (
        "剧诗版本深渊",
        "剧诗深渊阵容",
        "剧诗信息",
        "新深渊信息",
        "巨屎信息",
        "剧诗怪物",
        "新深渊怪物",
        "上期剧诗信息",
        "下期剧诗信息",
        "上期新深渊信息",
        "下期新深渊信息",
        "上期巨屎信息",
        "下期巨屎信息",
    ),
    covers=["剧诗信息", "幻想真境剧诗", "新深渊信息"],
    to_ai="""查看幻想真境剧诗（新深渊）某一期的怪物阵容

    当用户说"剧诗信息"、"新深渊信息"、"巨屎信息"、"8月的剧诗"时调用。
    以图片返回各幕 Boss 和机制。这是版本阵容，不是某个 UID 的战斗记录。
    返回文本里有日期到日程 id 的对照表，用它判断用户说的日期落在哪一期。

    Args:
        text: 日程 id、日期，或「上期」「下期」。上期/下期相对今天的当期。
              "32" → 日程 32
              "2026.8.1"、"2026-08-01" → 覆盖这一天的那一期
              "下期"、"上期" → 相邻一期。用户说「下期剧诗信息」时 text 写「下期」
              留空 → 当前开放的一期；怪物还没公布时改最近一期已公开阵容
    """,
)
async def send_poetry_abyss_review(bot: Bot, ev: Event):
    when, schedule_id = parse_schedule_args(ev.text)
    shift = period_shift(ev.command, ev.text)
    im = await build_roleplay_image(
        "" if shift and not schedule_id else schedule_id, None if shift or schedule_id else when, shift
    )
    logger.info(t("log.genshinuid.msg_09c19e"))
    if isinstance(im, bytes):
        await bot.send_option(im, [Button("幽境信息", "幽境信息")])
    else:
        await bot.send(im)


@sv_leyline_reviews.on_command(
    (
        "幽境信息",
        "危战信息",
        "上期幽境信息",
        "下期幽境信息",
        "上期危战信息",
        "下期危战信息",
    ),
    covers=["幽境信息", "幽境危战", "危战信息"],
    to_ai="""查看幽境危战某一期的关卡、怪物机制、血量和抗性

    当用户说"幽境信息"、"危战信息"、"2026年1月的危战"时调用。
    以图片返回最高难度三路怪物。这是版本阵容，不是某个 UID 的成绩。
    返回文本里有日期到日程 id 的对照表，用它判断用户说的日期落在哪一期。

    Args:
        text: 日程 id、日期，或「上期」「下期」。上期/下期相对今天的当期。
              "5269012" → 这一期
              "2026.01.01"、"2026-1-1" → 覆盖这一天的那一期
              "下期"、"上期" → 相邻一期。用户说「下期危战信息」时 text 写「下期」
              留空 → 当前开放的一期，没有则用最近一期
    """,
)
async def send_leyline_review(bot: Bot, ev: Event):
    when, schedule_id = parse_schedule_args(ev.text)
    shift = period_shift(ev.command, ev.text)
    im = await build_leyline_image(
        "" if shift and not schedule_id else schedule_id, None if shift or schedule_id else when, shift
    )
    if isinstance(im, bytes):
        await bot.send_option(im, [Button("剧诗信息", "剧诗信息")])
    else:
        await bot.send(im)


@sv_abyss_reviews.on_command(
    (
        "版本深渊",
        "深渊阵容",
        "深渊怪物",
        "深渊信息",
        "上期深渊信息",
        "下期深渊信息",
        "上期版本深渊",
        "下期版本深渊",
    ),
    covers=["深渊怎么打", "深渊阵容"],
    to_ai="""查看深境螺旋某一期、某一层的怪物阵容和血量

    当用户说"深渊信息"、"深渊信息11"、"8月10日的深渊12层"时调用。
    以图片返回上下半怪物、buff 和血量。这是版本阵容，不是某个 UID 的成绩。
    返回文本里有日期到日程 id 的对照表，用它判断用户说的日期落在哪一期。

    Args:
        text: 层数、日期、日程 id，可组合。层数缺省 12。
              "11" → 当期第 11 层
              "11 2026.8.10" → 2026-08-10 那一期的第 11 层
              "2026-08-10"、"2026/8/10" → 那一期的第 12 层
              "20097" → 日程 20097 的第 12 层
              "下期"、"上期 11" → 相对今天的相邻一期。用户说「下期深渊信息11」时 text 写「下期 11」
              留空 → 最近一期第 12 层
    """,
)
async def send_abyss_review(bot: Bot, ev: Event):
    floor, when, schedule_id = parse_abyss_args(ev.text)
    shift = period_shift(ev.command, ev.text)
    im = await build_abyss_image(
        floor, None if shift else when, "" if shift and not schedule_id else schedule_id, shift
    )
    if isinstance(im, bytes):
        tail = f" {schedule_id}" if schedule_id else (f" {when.isoformat()}" if when else "")
        await bot.send_option(
            im,
            [Button("第11层", f"深渊信息11{tail}"), Button("第12层", f"深渊信息12{tail}")],
        )
    elif isinstance(im, str):
        await bot.send(im)

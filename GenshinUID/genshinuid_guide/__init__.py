import re
from typing import List

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from ..version import Genshin_version
from .get_guide import get_gs_guide
from ..utils.message import GButton as Button
from .get_bbs_post_guide import get_material_way_post
from .get_new_abyss_data import get_review_data

# from .get_abyss_data import get_review
from ..utils.image.convert import convert_img
from .draw_poetry_abyss_pic import draw_poetry_abyss_image
from ..utils.map.name_covert import alias_to_char_name
from ..utils.resource.RESOURCE_PATH import REF_PATH

sv_char_guide = SV("查询角色攻略")
sv_abyss_reviews = SV("查询深渊阵容", priority=2)
sv_poetry_abyss_reviews = SV("查询剧诗深渊阵容", priority=3)
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
        await bot.logger.info("获得{}攻略成功！".format(name))
        a = Button(f"🎴参考面板{name}", f"参考面板{name}")
        await bot.send_option(im, [a])
    else:
        await bot.logger.warning("未找到{}攻略图片".format(name))


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
        await bot.logger.info("获得{}参考面板图片成功！".format(name))
        await bot.send_option(img, [Button(f"🎴{name}攻略", f"{name}攻略")])
    else:
        await bot.logger.warning("未找到{}参考面板图片".format(name))


@sv_poetry_abyss_reviews.on_command(
    (
        "剧诗版本深渊",
        "剧诗深渊阵容",
        "剧诗信息",
        "新深渊信息",
        "剧诗怪物",
        "新深渊怪物",
    ),
    to_ai="""查看剧诗深渊（幻想真境剧诗）的版本信息和怪物阵容

    当用户说"剧诗信息"、"新深渊怪物"、"剧诗深渊阵容"时调用。
    以图片形式返回剧诗深渊的怪物阵容和版本信息。

    Args:
        text: 可选的版本号或筛选条件，留空显示当前版本
    """,
)
async def send_poetry_abyss_review(bot: Bot, ev: Event):
    im = await draw_poetry_abyss_image(ev.text.strip())
    logger.info(t("log.genshinuid.msg_09c19e"))
    await bot.send(im)


@sv_abyss_reviews.on_command(
    ("版本深渊", "深渊阵容", "深渊怪物", "深渊信息"),
    to_ai="""查看指定版本的深渊怪物阵容和信息

    当用户说"版本深渊"、"深渊阵容"、"深渊怪物"、"深渊信息"时调用。
    以图片形式返回指定版本和层数的深渊怪物配置。

    Args:
        text: 格式为"[版本号] [层数]"，例如 "4.3 12"、"5.0 12"
              留空显示当前版本12层
    """,
)
async def send_abyss_review(bot: Bot, ev: Event):
    floor = "12"
    if not ev.text:
        version = Genshin_version[:-2]
    else:
        if "." in ev.text:
            num = ev.text.index(".")
            version = ev.text[num - 1 : num + 2]  # noqa:E203
            _deal = ev.text.replace(version, "").strip()
            if _deal:
                floor = re.findall(r"[0-9]+", _deal)[0]
        else:
            floor = ev.text
            version = Genshin_version[:-2]

    im = await get_review_data(version, floor)
    # im = await get_review(version)

    if isinstance(im, bytes):
        c = Button("♾️深渊概览", "深渊概览")
        input_version = float(version)
        now_version = float(Genshin_version[:-2])
        if input_version <= now_version:
            gv = Genshin_version.split(".")
            adv_version = f"{gv[0]}.{int(gv[1]) + 1}"
        else:
            adv_version = now_version
        d = Button(f"♾️版本深渊{adv_version}", f"深渊概览{adv_version}")
        await bot.send_option(im, [c, d])
    elif isinstance(im, List):
        mes = [MessageSegment.text(str(msg)) for msg in im]  # type: ignore
        await bot.send(MessageSegment.node(mes))
    elif isinstance(im, str):
        await bot.send(im)

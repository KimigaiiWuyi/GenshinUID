import asyncio
from typing import Union, Sequence
from pathlib import Path

from PIL import Image, ImageDraw

from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.utils.database.models import GsBind, GsUser
from gsuid_core.ai_core.trigger_bridge import ai_return

from .gs_config import gsconfig
from ..utils.image.convert import convert_img
from ..utils.fonts.genshin_fonts import gs_font_24, gs_font_36, gs_font_40
from ..utils.resource.RESOURCE_PATH import TEXT2D_PATH

TEXT_PATH = Path(__file__).parent / "texture2d"
config_title = Image.open(TEXT_PATH / "config_title.png")
config_on = Image.open(TEXT_PATH / "config_on.png")
config_off = Image.open(TEXT_PATH / "config_off.png")

first_color = (20, 20, 20)
second_color = (57, 57, 57)


def _ai_return_config(uid_num: int, cookie_num: int, stoken_num: int, switches: Sequence[str]) -> None:
    try:
        ai_return(
            f"【原神全局功能配置】绑定UID数 {uid_num}｜Cookie数 {cookie_num}｜Stoken数 {stoken_num}\n"
            + "\n".join(switches)
        )
    except Exception:
        pass


async def draw_config_img(bot_id: str) -> Union[bytes, str]:
    from ..utils.image.image_tools import CustomizeImage

    # 获取背景图片各项参数
    based_w = 850
    based_h = 850 + 155 * (len(gsconfig) - 8)

    CI_img = CustomizeImage("", based_w, based_h)
    img = CI_img.bg_img
    color = CI_img.bg_color
    color_mask = Image.new("RGBA", (based_w, based_h), color)
    config_mask = Image.open(TEXT2D_PATH / "mask.png").resize((based_w, based_h))
    img.paste(color_mask, (0, 0), config_mask)
    img.paste(config_title, (0, 0), config_title)
    img_draw = ImageDraw.Draw(img)

    # 获取数据
    uid_list = await GsBind.get_all_uid_list_by_game(bot_id)
    cookie_list = await GsUser.get_all_cookie()
    stoken_list = await GsUser.get_all_stoken()

    uid_num = len(uid_list)
    cookie_num = len(cookie_list)
    stoken_num = len(stoken_list)
    img_draw.text((210, 600), str(uid_num), first_color, gs_font_40, "mm")
    img_draw.text((431, 600), str(cookie_num), first_color, gs_font_40, "mm")
    img_draw.text((651, 600), str(stoken_num), first_color, gs_font_40, "mm")

    tasks = []
    index = 0
    ai_switches: list[str] = []
    for name in gsconfig:
        if isinstance(gsconfig[name].data, bool):
            tasks.append(_draw_config_line(img, name, index))
            ai_switches.append(f"  - {gsconfig[name].title}: {'开启' if gsconfig[name].data else '关闭'}")
            index += 1
    await asyncio.gather(*tasks)

    _ai_return_config(uid_num, cookie_num, stoken_num, ai_switches)

    res = await convert_img(img)
    logger.info(t("log.genshinuid.msg_d7a840"))
    return res


async def _draw_config_line(img: Image.Image, name: str, index: int):
    detail = gsconfig[name].desc
    if gsconfig[name].title == "定时签到":
        time = ":".join(gsconfig.get_config("SignTime").data)
        detail = f"开启后每晚{time}将开始自动签到任务"
    elif gsconfig[name].title == "定时米游币":
        time = ":".join(gsconfig.get_config("BBSTaskTime").data)
        detail = f"开启后每晚{time}将开始自动米游币任务"
    config_line = Image.open(TEXT_PATH / "config_line.png")
    config_line_draw = ImageDraw.Draw(config_line)
    title = gsconfig[name].title
    if gsconfig[name].title.startswith("定时"):
        title += "(全部)"
    config_line_draw.text((52, 46), title, first_color, gs_font_36, "lm")
    config_line_draw.text((52, 80), detail, second_color, gs_font_24, "lm")
    if gsconfig[name].data:
        config_line.paste(config_on, (613, 21), config_on)
    else:
        config_line.paste(config_off, (613, 21), config_off)
    img.paste(config_line, (26, 850 + index * 155), config_line)

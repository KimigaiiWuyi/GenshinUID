from PIL import Image, ImageDraw

from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import crop_center_img

from .draw_hard_challenge import TEXT_PATH
from ..utils.api.cv.request import _CvApi
from ..utils.fonts.genshin_fonts import (
    gs_font_18,
    gs_font_20,
    gs_font_25,
    gs_font_26,
    gs_font_28,
    gs_font_30,
    gs_font_40,
)
from ..genshinuid_config.gs_config import gsconfig
from ..genshinuid_enka.draw_role_rank import REGION_MAP

is_enable_akasha = gsconfig.get_config("EnableAkasha").data
RANK_TEXT = TEXT_PATH / "rank"

achievement_MAP = {
    1500: (255, 58, 58),
    1450: (169, 109, 57),
    1400: (255, 165, 0),
    1350: (80, 98, 255),
    1300: (37, 37, 37),
    1200: (128, 35, 151),
}


async def draw_hard_rank():
    # https://akasha.cv/api/accounts?sort=playerInfo.stygianScore&order=-1&size=20&page=1&filter=&uids=&fromId=
    if not is_enable_akasha:
        return "未开启排名系统..."
    cv_api = _CvApi()

    data = await cv_api.get_stygian_rank_data()

    if isinstance(data, int):
        return f"未获取到排名数据...错误码: {data}"

    raw_data = data[0]
    count: int = data[1]

    bg = Image.open(TEXT_PATH / "bg.jpg").convert("RGBA")
    img = crop_center_img(bg, 950, 2350)

    title = Image.open(RANK_TEXT / "title.png")
    title_draw = ImageDraw.Draw(title)

    title_draw.text((600, 487), "幽境危战", font=gs_font_40, fill="white", anchor="mm")
    title_draw.text(
        (600, 558),
        f"总数据：{count}",
        font=gs_font_30,
        fill=(230, 230, 230),
        anchor="mm",
    )
    title = title.resize((948, 474))
    img.paste(title, (1, 9), title)

    for index, sdata in enumerate(raw_data["data"][:18]):
        uid: str = sdata["uid"]
        playerInfo = sdata["playerInfo"]

        nickname: str = playerInfo["nickname"]
        level = int(playerInfo["level"])
        signature: str = playerInfo["signature"]
        stygianIndex: int = playerInfo["stygianIndex"]
        stygianSeconds: int = playerInfo["stygianSeconds"]
        # stygianScore: int = int(playerInfo['stygianScore'])
        achievement = int(playerInfo["finishAchievementNum"])
        region: str = playerInfo["region"]

        if len(signature) > 18:
            signature = signature[:18] + "..."

        if signature.strip() == "":
            signature = "该旅行者无签名..."

        if region in REGION_MAP:
            region_color = REGION_MAP[region]
        else:
            region_color = (128, 128, 128)

        for i in achievement_MAP:
            if achievement >= i:
                achievement_color = achievement_MAP[i]
                break
        else:
            achievement_color = (128, 128, 128)

        bar = Image.open(RANK_TEXT / "bar.png")
        bar_draw = ImageDraw.Draw(bar)
        bar_draw.rounded_rectangle((47, 30, 150, 70), 10, region_color)
        bar_draw.rounded_rectangle((159, 24, 327, 45), 5, (184, 123, 35))
        bar_draw.rounded_rectangle((558, 31, 754, 69), 8, achievement_color)

        medal = Image.open(TEXT_PATH / f"medal_{stygianIndex}.png").convert("RGBA").resize((51, 51))

        bar.paste(medal, (768, 25), medal)

        bar_draw.text((98, 50), region, "white", gs_font_30, "mm")
        bar_draw.text((42, 13), f"# {index + 1}", "white", gs_font_25, "lm")
        bar_draw.text((335, 36), nickname, "white", gs_font_28, "lm")
        bar_draw.text((162, 67), signature, (200, 200, 200), gs_font_20, "lm")
        bar_draw.text((243, 34), f"UID {uid}", "white", gs_font_20, "mm")

        bar_draw.text(
            (657, 52),
            f"AR{level}·{achievement}",
            "white",
            gs_font_25,
            "mm",
        )

        bar_draw.text((856, 50), f"{stygianSeconds}s", (10, 255, 227), gs_font_26, "mm")

        img.paste(bar, (0, 491 + index * 100), bar)

    img_draw = ImageDraw.Draw(img)

    img_draw.text(
        (475, img.size[1] - 35),
        "Power by Wuyi无疑 & Data by AKS & CV Created by GsCore & GenshinUID",
        (200, 200, 200),
        gs_font_18,
        anchor="mm",
    )
    await cv_api.close()
    return await convert_img(img)

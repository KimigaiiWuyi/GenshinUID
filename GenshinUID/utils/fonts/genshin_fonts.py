from pathlib import Path

from PIL import ImageFont

FONT_ORIGIN_PATH = Path(__file__).parent / 'yuanshen_origin.ttf'


def genshin_font_origin(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_ORIGIN_PATH), size=size)


gs_font_12 = genshin_font_origin(12)
gs_font_14 = genshin_font_origin(14)
gs_font_15 = genshin_font_origin(15)
gs_font_18 = genshin_font_origin(18)
gs_font_20 = genshin_font_origin(20)
gs_font_22 = genshin_font_origin(22)
gs_font_24 = genshin_font_origin(24)
gs_font_25 = genshin_font_origin(25)
gs_font_26 = genshin_font_origin(26)
gs_font_28 = genshin_font_origin(28)
gs_font_30 = genshin_font_origin(30)
gs_font_32 = genshin_font_origin(32)
gs_font_36 = genshin_font_origin(36)
gs_font_38 = genshin_font_origin(38)
gs_font_40 = genshin_font_origin(40)
gs_font_44 = genshin_font_origin(44)
gs_font_50 = genshin_font_origin(50)
gs_font_58 = genshin_font_origin(58)
gs_font_60 = genshin_font_origin(60)
gs_font_62 = genshin_font_origin(62)
gs_font_70 = genshin_font_origin(70)
gs_font_84 = genshin_font_origin(84)

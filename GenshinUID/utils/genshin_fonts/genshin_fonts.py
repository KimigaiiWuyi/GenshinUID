from pathlib import Path

from PIL import ImageFont

FONT_ORIGIN_PATH = Path(__file__).parent / 'yuanshen_origin.ttf'


def genshin_font_origin(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_ORIGIN_PATH), size=size)


gs_font_18 = genshin_font_origin(18)
gs_font_28 = genshin_font_origin(28)
gs_font_50 = genshin_font_origin(50)

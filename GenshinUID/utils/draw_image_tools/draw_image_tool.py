import math
import random
from io import BytesIO
from pathlib import Path
from typing import Tuple, Union, Optional

from PIL import Image
from httpx import get

from ..download_resource.RESOURCE_PATH import TEXT2D_PATH

BG_PATH = Path(__file__).parent / 'bg'
NM_BG_PATH = BG_PATH / 'nm_bg'
SP_BG_PATH = BG_PATH / 'sp_bg'


async def get_color_bg(
    based_w: int, based_h: int, bg: Optional[str] = None
) -> Image.Image:
    image = ''
    if bg:
        path = SP_BG_PATH / f'{bg}.jpg'
        if path.exists():
            image = Image.open(path)
    CI_img = CustomizeImage(image, based_w, based_h)
    img = CI_img.bg_img
    color = CI_img.bg_color
    color_mask = Image.new('RGBA', (based_w, based_h), color)
    enka_mask = Image.open(TEXT2D_PATH / 'mask.png').resize((based_w, based_h))
    img.paste(color_mask, (0, 0), enka_mask)
    return img


async def get_simple_bg(
    based_w: int, based_h: int, image: Union[str, None, Image.Image] = None
) -> Image.Image:
    if image:
        if isinstance(image, str):
            edit_bg = Image.open(BytesIO(get(image).content)).convert('RGBA')
        elif isinstance(image, Image.Image):
            edit_bg = image.convert('RGBA')
    else:
        bg_path = random.choice(list(BG_PATH.iterdir()))
        edit_bg = Image.open(bg_path).convert('RGBA')

    # 确定图片的长宽
    based_scale = '%.3f' % (based_w / based_h)

    w, h = edit_bg.size
    scale_f = '%.3f' % (w / h)
    new_w = math.ceil(based_h * float(scale_f))
    new_h = math.ceil(based_w / float(scale_f))
    if scale_f > based_scale:
        bg_img2 = edit_bg.resize((new_w, based_h), Image.ANTIALIAS)
    else:
        bg_img2 = edit_bg.resize((based_w, new_h), Image.ANTIALIAS)
    bg_img = bg_img2.crop((0, 0, based_w, based_h))

    return bg_img


class CustomizeImage:
    def __init__(
        self, image: Union[str, Image.Image], based_w: int, based_h: int
    ) -> None:

        self.bg_img = self.get_image(image, based_w, based_h)
        self.bg_color = self.get_bg_color(self.bg_img, is_light=True)
        self.text_color = self.get_text_color(self.bg_color)
        self.highlight_color = self.get_highlight_color(self.bg_color)
        self.char_color = self.get_char_color(self.bg_color)
        self.bg_detail_color = self.get_bg_detail_color(self.bg_color)
        self.char_high_color = self.get_char_high_color(self.bg_color)

    @staticmethod
    def get_image(
        image: Union[str, Image.Image], based_w: int, based_h: int
    ) -> Image.Image:
        # 获取背景图片
        if isinstance(image, Image.Image):
            edit_bg = image
        elif image:
            edit_bg = Image.open(BytesIO(get(image).content)).convert('RGBA')
        else:
            bg_path = random.choice(list(NM_BG_PATH.iterdir()))
            edit_bg = Image.open(bg_path).convert('RGBA')

        # 确定图片的长宽
        based_scale = '%.3f' % (based_w / based_h)

        w, h = edit_bg.size
        scale_f = '%.3f' % (w / h)
        new_w = math.ceil(based_h * float(scale_f))
        new_h = math.ceil(based_w / float(scale_f))
        if scale_f > based_scale:
            bg_img2 = edit_bg.resize((new_w, based_h), Image.ANTIALIAS)
            x1 = int(new_w / 2 - based_w / 2)
            y1 = 0
            x2 = int(new_w / 2 + based_w / 2)
            y2 = based_h
        else:
            bg_img2 = edit_bg.resize((based_w, new_h), Image.ANTIALIAS)
            x1 = 0
            y1 = int(new_h / 2 - based_h / 2)
            x2 = based_w
            y2 = int(new_h / 2 + based_h / 2)
        bg_img = bg_img2.crop((x1, y1, x2, y2))

        return bg_img

    @staticmethod
    def get_dominant_color(pil_img: Image.Image) -> Tuple[int, int, int]:
        img = pil_img.copy()
        img = img.convert("RGBA")
        img = img.resize((1, 1), resample=0)
        dominant_color = img.getpixel((0, 0))
        return dominant_color

    @staticmethod
    def get_bg_color(
        edit_bg: Image.Image, is_light: Optional[bool] = False
    ) -> Tuple[int, int, int]:
        # 获取背景主色
        color = 8
        q = edit_bg.quantize(colors=color, method=2)
        bg_color = (0, 0, 0)
        if is_light:
            based_light = 195
        else:
            based_light = 120
        temp = 9999
        for i in range(0, color):
            bg = tuple(q.getpalette()[i * 3 : (i * 3) + 3])  # type: ignore
            light_value = bg[0] * 0.3 + bg[1] * 0.6 + bg[2] * 0.1
            if abs(light_value - based_light) < temp:
                bg_color = bg
                temp = abs(light_value - based_light)
        return bg_color

    @staticmethod
    def get_text_color(bg_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        # 通过背景主色（bg_color）确定文字主色
        r = 125
        if max(*bg_color) > 255 - r:
            r *= -1
        text_color = (
            math.floor(bg_color[0] + r if bg_color[0] + r <= 255 else 255),
            math.floor(bg_color[1] + r if bg_color[1] + r <= 255 else 255),
            math.floor(bg_color[2] + r if bg_color[2] + r <= 255 else 255),
        )
        return text_color

    @staticmethod
    def get_char_color(bg_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        r = 140
        if max(*bg_color) > 255 - r:
            r *= -1
        char_color = (
            math.floor(bg_color[0] + 5 if bg_color[0] + r <= 255 else 255),
            math.floor(bg_color[1] + 5 if bg_color[1] + r <= 255 else 255),
            math.floor(bg_color[2] + 5 if bg_color[2] + r <= 255 else 255),
        )
        return char_color

    @staticmethod
    def get_char_high_color(
        bg_color: Tuple[int, int, int]
    ) -> Tuple[int, int, int]:
        r = 140
        d = 20
        if max(*bg_color) > 255 - r:
            r *= -1
        char_color = (
            math.floor(bg_color[0] + d if bg_color[0] + r <= 255 else 255),
            math.floor(bg_color[1] + d if bg_color[1] + r <= 255 else 255),
            math.floor(bg_color[2] + d if bg_color[2] + r <= 255 else 255),
        )
        return char_color

    @staticmethod
    def get_bg_detail_color(
        bg_color: Tuple[int, int, int]
    ) -> Tuple[int, int, int]:
        r = 140
        if max(*bg_color) > 255 - r:
            r *= -1
        bg_detail_color = (
            math.floor(bg_color[0] - 20 if bg_color[0] + r <= 255 else 255),
            math.floor(bg_color[1] - 20 if bg_color[1] + r <= 255 else 255),
            math.floor(bg_color[2] - 20 if bg_color[2] + r <= 255 else 255),
        )
        return bg_detail_color

    @staticmethod
    def get_highlight_color(
        color: Tuple[int, int, int]
    ) -> Tuple[int, int, int]:
        red_color = color[0]
        green_color = color[1]
        blue_color = color[2]

        highlight_color = {
            'red': red_color - 127 if red_color > 127 else 127,
            'green': green_color - 127 if green_color > 127 else 127,
            'blue': blue_color - 127 if blue_color > 127 else 127,
        }

        max_color = max(highlight_color.values())

        name = ''
        for _highlight_color in highlight_color:
            if highlight_color[_highlight_color] == max_color:
                name = str(_highlight_color)

        if name == 'red':
            return red_color, highlight_color['green'], highlight_color['blue']
        elif name == 'green':
            return highlight_color['red'], green_color, highlight_color['blue']
        elif name == 'blue':
            return highlight_color['red'], highlight_color['green'], blue_color
        else:
            return 0, 0, 0  # Error

import math
import random
from io import BytesIO
from pathlib import Path
from typing import Tuple, Union, Optional

from PIL import Image
from httpx import get

from ..download_resource.RESOURCE_PATH import TEXT2D_PATH

FETTER_PATH = TEXT2D_PATH / 'fetter'
TALENT_PATH = TEXT2D_PATH / 'talent'
WEAPON_BG_PATH = TEXT2D_PATH / 'weapon'
WEAPON_AFFIX_PATH = TEXT2D_PATH / 'weapon_affix'
LEVEL_PATH = TEXT2D_PATH / 'level'

BG_PATH = Path(__file__).parent / 'bg'
TEXT_PATH = Path(__file__).parent / 'texture2d'
ring_pic = Image.open(TEXT_PATH / 'ring.png')
mask_pic = Image.open(TEXT_PATH / 'mask.png')
NM_BG_PATH = BG_PATH / 'nm_bg'
SP_BG_PATH = BG_PATH / 'sp_bg'


async def get_weapon_affix_pic(affix: int) -> Image.Image:
    return Image.open(WEAPON_AFFIX_PATH / f'weapon_affix_{affix}.png')


async def get_fetter_pic(fetter: int) -> Image.Image:
    return Image.open(FETTER_PATH / f'fetter_{fetter}.png')


async def get_talent_pic(talent: int) -> Image.Image:
    return Image.open(TALENT_PATH / f'talent_{talent}.png')


async def get_weapon_pic(weapon_rarity: int) -> Image.Image:
    return Image.open(WEAPON_BG_PATH / f'weapon_bg{weapon_rarity}.png')


async def get_level_pic(level: int) -> Image.Image:
    return Image.open(LEVEL_PATH / f'level_{level}.png')


async def get_qq_avatar(
    qid: Optional[Union[int, str]] = None, avatar_url: Optional[str] = None
) -> Image.Image:
    if qid:
        avatar_url = f'http://q1.qlogo.cn/g?b=qq&nk={qid}&s=640'
    elif avatar_url is None:
        avatar_url = 'https://q1.qlogo.cn/g?b=qq&nk=3399214199&s=640'
    char_pic = Image.open(BytesIO(get(avatar_url).content)).convert('RGBA')
    return char_pic


async def draw_pic_with_ring(
    pic: Image.Image,
    size: int,
    bg_color: Optional[Tuple[int, int, int]] = None,
):
    '''
    :说明:
      绘制一张带白色圆环的1:1比例图片。

    :参数:
      * pic: `Image.Image`: 要修改的图片。
      * size: `int`: 最后传出图片的大小(1:1)。
      * bg_color: `Optional[Tuple[int, int, int]]`: 是否指定圆环内背景颜色。

    :返回:
      * img: `Image.Image`: 图片对象
    '''
    img = Image.new('RGBA', (size, size))
    mask = mask_pic.resize((size, size))
    ring = ring_pic.resize((size, size))
    resize_pic = crop_center_img(pic, size, size)
    if bg_color:
        img_color = Image.new('RGBA', (size, size), bg_color)
        img_color.paste(resize_pic, (0, 0), resize_pic)
        img.paste(img_color, (0, 0), mask)
    else:
        img.paste(resize_pic, (0, 0), mask)
    img.paste(ring, (0, 0), ring)
    return img


def crop_center_img(
    img: Image.Image, based_w: int, based_h: int
) -> Image.Image:
    # 确定图片的长宽
    based_scale = '%.3f' % (based_w / based_h)
    w, h = img.size
    scale_f = '%.3f' % (w / h)
    new_w = math.ceil(based_h * float(scale_f))
    new_h = math.ceil(based_w / float(scale_f))
    if scale_f > based_scale:
        resize_img = img.resize((new_w, based_h), Image.ANTIALIAS)
        x1 = int(new_w / 2 - based_w / 2)
        y1 = 0
        x2 = int(new_w / 2 + based_w / 2)
        y2 = based_h
    else:
        resize_img = img.resize((based_w, new_h), Image.ANTIALIAS)
        x1 = 0
        y1 = int(new_h / 2 - based_h / 2)
        x2 = based_w
        y2 = int(new_h / 2 + based_h / 2)
    crop_img = resize_img.crop((x1, y1, x2, y2))
    return crop_img


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
        bg_path = random.choice(list(NM_BG_PATH.iterdir()))
        edit_bg = Image.open(bg_path).convert('RGBA')

    # 确定图片的长宽
    bg_img = crop_center_img(edit_bg, based_w, based_h)
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
        bg_img = crop_center_img(edit_bg, based_w, based_h)
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

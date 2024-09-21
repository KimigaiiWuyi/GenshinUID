import math
import random
from io import BytesIO
from pathlib import Path
from typing import Tuple, Union, Optional

import httpx
from httpx import get
from gsuid_core.models import Event
from gsuid_core.utils.api.mys.models import IndexData
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter
from gsuid_core.utils.image.image_tools import get_avatar_with_ring

from ...genshinuid_config.gs_config import gsconfig
from ..fonts.genshin_fonts import gs_font_32, gs_font_36
from ..resource.RESOURCE_PATH import CHAR_PATH, CU_BG_PATH, TEXT2D_PATH

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

if list(CU_BG_PATH.iterdir()) != []:
    bg_path = CU_BG_PATH
else:
    bg_path = NM_BG_PATH


def get_v4_bg(w: int, h: int):
    img = crop_center_img(Image.open(TEXT_PATH / 'bg.jpg'), w, h)
    black_img = Image.new('RGBA', (w, h), (0, 0, 0, 180))
    img = img.filter(ImageFilter.GaussianBlur(radius=15))
    img.paste(black_img, (0, 0), black_img)
    img = img.convert('RGBA')
    return img


def get_v4_title(avatar: Image.Image, uid: str, title_data: IndexData):
    title = Image.open(TEXT_PATH / 'title.png')
    title_draw = ImageDraw.Draw(title)

    title.paste(avatar, (651, 73), avatar)

    ac_day = str(title_data['stats']['active_day_number'])
    achi_num = str(title_data['stats']['achievement_number'])
    abyss_num = str(title_data['stats']['spiral_abyss'])

    title_draw.text((840, 530), f'UID {uid}', 'white', gs_font_36, 'mm')

    title_draw.text((380, 627), ac_day, 'white', gs_font_32, 'lm')
    title_draw.text((872, 627), achi_num, 'white', gs_font_32, 'lm')
    title_draw.text((1365, 627), abyss_num, 'white', gs_font_32, 'lm')

    return title


def get_footer():
    return Image.open(TEXT_PATH / 'footer.png')


def add_footer(
    img: Image.Image,
    w: int = 0,
    offset_y: int = 0,
    is_invert: bool = False,
):
    footer = get_footer()
    if is_invert:
        r, g, b, a = footer.split()
        rgb_image = Image.merge('RGB', (r, g, b))
        rgb_image = ImageOps.invert(rgb_image.convert('RGB'))
        r2, g2, b2 = rgb_image.split()
        footer = Image.merge('RGBA', (r2, g2, b2, a))

    if w != 0:
        footer = footer.resize(
            (w, int(footer.size[1] * w / footer.size[0])),
        )

    x, y = (
        int((img.size[0] - footer.size[0]) / 2),
        img.size[1] - footer.size[1] - 20 + offset_y,
    )

    img.paste(footer, (x, y), footer)
    return img


async def get_avatar(ev: Event, size: int, with_ring: bool = True):
    return await get_avatar_with_ring(ev, size, CHAR_PATH, None, with_ring)


async def shift_image_hue(img: Image.Image, angle: float = 30) -> Image.Image:
    alpha = img.getchannel('A')
    img = img.convert('HSV')

    pixels = img.load()
    hue_shift = angle

    for y in range(img.height):
        for x in range(img.width):
            h, s, v = pixels[x, y]
            h = (h + hue_shift) % 360
            pixels[x, y] = (h, s, v)

    img = img.convert('RGBA')
    img.putalpha(alpha)
    return img


async def _get(url: str):
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.get(url=url)
        return resp


async def get_pic(url, size: Optional[Tuple[int, int]] = None) -> Image.Image:
    '''
    从网络获取图片, 格式化为RGBA格式的指定尺寸
    '''
    async with httpx.AsyncClient(timeout=None) as client:
        resp = await client.get(url=url)
        if resp.status_code != 200:
            if size is None:
                size = (960, 600)
            return Image.new('RGBA', size)
        pic = Image.open(BytesIO(resp.read()))
        pic = pic.convert('RGBA')
        if size is not None:
            pic = pic.resize(size, Image.Resampling.LANCZOS)
        return pic


def get_size(font: ImageFont.FreeTypeFont, character: str):
    if hasattr(font, 'getsize'):
        w, h = font.getsize(character)  # type: ignore
    else:
        bbox = font.getbbox(character)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    return w, h


def draw_text_by_line(
    img: Image.Image,
    pos: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: Union[Tuple[int, int, int, int], str],
    max_length: float,
    center=False,
    line_space: Optional[float] = None,
):
    '''
    在图片上写长段文字, 自动换行
    max_length单行最大长度, 单位像素
    line_space  行间距, 单位像素, 默认是字体高度的0.3倍
    '''
    x, y = pos
    _, h = get_size(font, 'X')
    if line_space is None:
        y_add = math.ceil(1.3 * h)
    else:
        y_add = math.ceil(h + line_space)
    draw = ImageDraw.Draw(img)
    row = ''  # 存储本行文字
    length = 0  # 记录本行长度
    for character in text:
        # 获取当前字符的宽度
        w, h = get_size(font, character)
        if length + w * 2 <= max_length:
            row += character
            length += w
        else:
            row += character
            if center:
                fw, _ = get_size(font, row)
                x = math.ceil((img.size[0] - fw) / 2)
            draw.text((x, y), row, font=font, fill=fill)
            row = ''
            length = 0
            y += y_add
    if row != '':
        if center:
            fw, _ = get_size(font, row)
            x = math.ceil((img.size[0] - fw) / 2)
        draw.text((x, y), row, font=font, fill=fill)


def easy_paste(
    im: Image.Image, im_paste: Image.Image, pos=(0, 0), direction='lt'
):
    '''
    inplace method
    快速粘贴, 自动获取被粘贴图像的坐标。
    pos应当是粘贴点坐标，direction指定粘贴点方位，例如lt为左上
    '''
    x, y = pos
    size_x, size_y = im_paste.size
    if 'd' in direction:
        y = y - size_y
    if 'r' in direction:
        x = x - size_x
    if 'c' in direction:
        x = x - int(0.5 * size_x)
        y = y - int(0.5 * size_y)
    im.paste(im_paste, (x, y, x + size_x, y + size_y), im_paste)


def easy_alpha_composite(
    im: Image.Image, im_paste: Image.Image, pos=(0, 0), direction='lt'
) -> Image.Image:
    '''
    透明图像快速粘贴
    '''
    base = Image.new('RGBA', im.size)
    easy_paste(base, im_paste, pos, direction)
    base = Image.alpha_composite(im, base)
    return base


async def draw_bar(
    title: str,
    percent: float,
    value: str,
    color: Optional[Tuple[int, int, int]] = None,
):
    '''
    :说明:
      绘制一张750X100的透明白底进度条图片

    :参数:
      * title: `str`: 名字
      * percent: `float`: 进度条百分比, 超过1的部分会被限制在1以内。
      * value: `str`: 右侧具体数值呈现
      * bcolor: `Optional[Tuple[int, int, int]]`: 指定文字颜色。

    :返回:
      * img: `Image.Image`: 图片对象
    '''
    bg = Image.open(TEXT2D_PATH / 'slider_bar.png')
    if color is None:
        color = (142, 91, 35)
    if percent >= 1:
        percent = 1

    draw = ImageDraw.Draw(bg)
    draw.text((53, 38), title, color, gs_font_32, 'lm')
    draw.text((706, 38), value, (13, 13, 13), gs_font_32, 'rm')
    bs = 670 * percent
    draw.rounded_rectangle(
        (40, 62, 40 + bs, 76),
        fill=color,
        radius=20,
    )
    return bg


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


def get_star_png(star: Union[int, str]) -> Image.Image:
    path = TEXT2D_PATH / 'weapon_star' / f's-{star}.png'
    if path.exists():
        png = Image.open(path)
    else:
        png = Image.open(TEXT2D_PATH / 'weapon_star' / 's-1.png')
    return png


def get_unknown_png() -> Image.Image:
    return Image.open(TEXT_PATH / 'unknown.png')


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
    resize_pic = resize_pic.convert('RGBA')
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
        resize_img = img.resize((new_w, based_h), Image.Resampling.LANCZOS)
        x1 = int(new_w / 2 - based_w / 2)
        y1 = 0
        x2 = int(new_w / 2 + based_w / 2)
        y2 = based_h
    else:
        resize_img = img.resize((based_w, new_h), Image.Resampling.LANCZOS)
        x1 = 0
        y1 = int(new_h / 2 - based_h / 2)
        x2 = based_w
        y2 = int(new_h / 2 + based_h / 2)
    crop_img = resize_img.crop((x1, y1, x2, y2))
    return crop_img


async def get_color_bg(
    based_w: int,
    based_h: int,
    bg: Optional[str] = None,
    without_mask: bool = False,
) -> Image.Image:
    image = ''
    if bg and gsconfig.get_config('DefaultBaseBG').data:
        path = SP_BG_PATH / f'{bg}.jpg'
        path2 = CU_BG_PATH / f'{bg}.jpg'
        if path2.exists():
            image = Image.open(path2)
        elif path.exists():
            image = Image.open(path)
    CI_img = CustomizeImage(image, based_w, based_h)
    img = CI_img.bg_img
    color = CI_img.bg_color
    if not without_mask:
        color_mask = Image.new('RGBA', (based_w, based_h), color)
        enka_mask = Image.open(TEXT2D_PATH / 'mask.png').resize(
            (based_w, based_h)
        )
        img.paste(color_mask, (0, 0), enka_mask)
    return img


async def get_simple_bg(
    based_w: int, based_h: int, image: Union[str, None, Image.Image] = None
) -> Image.Image:
    if image:
        if isinstance(image, str):
            edit_bg = Image.open(BytesIO((await _get(image)).content)).convert(
                'RGBA'
            )
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
            path = random.choice(list(bg_path.iterdir()))
            edit_bg = Image.open(path).convert('RGBA')

        # 确定图片的长宽
        bg_img = crop_center_img(edit_bg, based_w, based_h)
        return bg_img

    @staticmethod
    def get_dominant_color(pil_img: Image.Image) -> Tuple[int, int, int]:
        img = pil_img.copy()
        img = img.convert('RGBA')
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
        bg_color: Tuple[int, int, int] = (0, 0, 0)
        if is_light:
            based_light = 195
        else:
            based_light = 120
        temp = 9999
        for i in range(color):
            bg = tuple(
                q.getpalette()[  # type:ignore
                    i * 3 : (i * 3) + 3  # noqa:E203
                ]
            )
            light_value = bg[0] * 0.3 + bg[1] * 0.6 + bg[2] * 0.1
            if abs(light_value - based_light) < temp:  # noqa:E203
                bg_color = bg  # type:ignore
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
            return 0, 0, 0  # Error

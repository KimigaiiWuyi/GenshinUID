from io import BytesIO
from pathlib import Path
from base64 import b64encode
from typing import Union, overload

import aiofiles
from PIL import Image, ImageFont


@overload
async def convert_img(img: Image.Image, is_base64: bool = False) -> bytes:
    ...


@overload
async def convert_img(img: Image.Image, is_base64: bool = True) -> str:
    ...


@overload
async def convert_img(img: bytes, is_base64: bool = False) -> str:
    ...


@overload
async def convert_img(img: Path, is_base64: bool = False) -> str:
    ...


async def convert_img(
    img: Union[Image.Image, str, Path, bytes], is_base64: bool = False
):
    """
    :说明:
      将PIL.Image对象转换为bytes或者base64格式。
    :参数:
      * img (Image): 图片。
      * is_base64 (bool): 是否转换为base64格式, 不填默认转为bytes。
    :返回:
      * res: bytes对象或base64编码图片。
    """
    if isinstance(img, Image.Image):
        img = img.convert('RGB')
        result_buffer = BytesIO()
        img.save(result_buffer, format='PNG', quality=80, subsampling=0)
        res = result_buffer.getvalue()
        if is_base64:
            res = 'base64://' + b64encode(res).decode()
        return res
    elif isinstance(img, bytes):
        pass
    else:
        async with aiofiles.open(img, 'rb') as fp:
            img = await fp.read()
    return f'base64://{b64encode(img).decode()}'


async def str_lenth(r: str, size: int, limit: int = 540) -> str:
    result = ''
    temp = 0
    for i in r:
        if i == '\n':
            temp = 0
            result += i
            continue

        if temp >= limit:
            result += '\n' + i
            temp = 0
        else:
            result += i

        if i.isdigit():
            temp += round(size / 10 * 6)
        elif i == '/':
            temp += round(size / 10 * 2.2)
        elif i == '.':
            temp += round(size / 10 * 3)
        elif i == '%':
            temp += round(size / 10 * 9.4)
        else:
            temp += size
    return result


def get_str_size(
    r: str, font: ImageFont.FreeTypeFont, limit: int = 540
) -> str:
    result = ''
    line = ''
    for i in r:
        if i == '\n':
            result += f'{line}\n'
            line = ''
            continue

        line += i
        size, _ = font.getsize(line)
        if size >= limit:
            result += f'{line}\n'
            line = ''
    else:
        result += line
    return result


def get_height(content: str, size: int) -> int:
    line_count = content.count('\n')
    return (line_count + 1) * size

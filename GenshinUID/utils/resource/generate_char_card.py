from typing import Union

from PIL import Image
from gsuid_core.logger import logger

from ..map.GS_MAP_PATH import avatarId2Star_data
from .RESOURCE_PATH import CHAR_PATH, TEXT2D_PATH, CHAR_CARD_PATH

texture2d_path = TEXT2D_PATH / 'char_card'


async def create_single_char_card(char_id: Union[str, int]) -> Image.Image:
    if str(char_id) not in avatarId2Star_data:
        logger.warning(f'资源文件夹发现异常图片{char_id}....忽略加载...')
        return Image.new('RGBA', (256, 310))
    path = CHAR_PATH / f'{char_id}.png'
    if not path.exists():
        logger.warning(f'资源文件夹未发现图片{char_id}....忽略加载...')
        return Image.new('RGBA', (256, 310))
    char_img = Image.open(path)
    char_star = avatarId2Star_data[str(char_id)]
    char_frame = Image.open(texture2d_path / 'frame.png')
    char_bg = Image.open(texture2d_path / f'star{char_star}bg.png')
    mask = Image.open(texture2d_path / 'mask.png')
    img = Image.new('RGBA', (256, 310))
    img_mask = Image.new('RGBA', (256, 310))
    img_mask.paste(char_bg, (0, 0), char_bg)
    img_mask.paste(char_img, (0, 0), char_img)
    img_mask.paste(char_frame, (0, 0), char_frame)
    img.paste(img_mask, (0, 0), mask)
    img.save(CHAR_CARD_PATH / f'{char_id}.png')
    return img


async def create_all_char_card():
    for char in CHAR_PATH.iterdir():
        char_id = char.stem
        path = CHAR_CARD_PATH / f'{char_id}.png'
        if not path.exists():
            await create_single_char_card(char_id)

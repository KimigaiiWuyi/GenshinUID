from typing import List, Union

from PIL import Image
from gsuid_core.logger import logger

from ..map.GS_MAP_PATH import avatarId2Star_data
from .RESOURCE_PATH import CHAR_PATH, TEXT2D_PATH, CHAR_CARD_PATH

texture2d_path = TEXT2D_PATH / 'char_card'


async def create_single_item_card(
    item_img: Union[List[Image.Image], Image.Image], star: Union[int, str]
) -> Image.Image:
    if isinstance(item_img, List):
        img = Image.new('RGBA', (256, 256))
        for i, item in enumerate(item_img):
            _intent = int(128 / (i + 1))
            _intent2 = int((256 + (128 * (len(item_img) - 1))) / len(item_img))
            item = item.resize((_intent2, _intent2))
            img.paste(item, (128 - _intent, 128 - _intent), item)
        item_img = img

    if item_img.size != (256, 256):
        item_img = item_img.resize((256, 256))
    char_frame = Image.open(texture2d_path / 'frame.png')
    char_bg = Image.open(texture2d_path / f'star{star}bg.png')
    mask = Image.open(texture2d_path / 'mask.png')
    img = Image.new('RGBA', (256, 310))
    img_mask = Image.new('RGBA', (256, 310))
    img_mask.paste(char_bg, (0, 0), char_bg)
    img_mask.paste(item_img, (0, 0), item_img)
    img_mask.paste(char_frame, (0, 0), char_frame)
    img.paste(img_mask, (0, 0), mask)
    return img


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

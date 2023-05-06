from pathlib import Path
from typing import List, Union

from PIL import Image, ImageDraw
from gsuid_core.utils.error_reply import UPDATE_HINT

from .update import update_from_git
from ..utils.image.convert import convert_img
from ..utils.image.image_tools import get_color_bg
from ..utils.fonts.genshin_fonts import genshin_font_origin

R_PATH = Path(__file__).parent
TEXT_PATH = R_PATH / 'texture2d'

gs_font_30 = genshin_font_origin(30)
black_color = (24, 24, 24)

log_config = {
    'key': '✨🐛🎨⚡🍱♻️',
    'num': 18,
}

log_map = {'✨': 'feat', '🐛': 'bug', '🍱': 'bento', '⚡️': 'zap', '🎨': 'art'}


async def get_all_update_log() -> List:
    v4_repo_path = Path(__file__).parents[2]
    core_repo_path = Path(__file__).parents[5]
    log_list1 = await update_from_git(0, v4_repo_path, log_config, True)
    log_list2 = await update_from_git(0, core_repo_path, log_config, True)
    im = []
    if len(log_list1) == 0:
        im.append('gsuid_v4更新失败!更多消息请查看控制台...以下为记录:')
        im.append(UPDATE_HINT)
    else:
        im.append('gsuid_v4更新成功!')
        im.append('最近更新记录如下:')
        im.append(log_list1[0])
        if len(log_list1) >= 2:
            im.append(log_list1[1])

    if len(log_list2) == 0:
        im.append('gsuid_core更新失败!更多消息请查看控制台...')
    else:
        im.append('gsuid_core更新成功!')
        im.append(log_list2[0])
        if len(log_list2) >= 2:
            im.append(log_list2[1])

    return im


async def draw_update_log_img(
    level: int = 0,
    repo_path: Union[str, Path, None] = None,
    is_update: bool = True,
) -> Union[bytes, str]:
    log_list = await update_from_git(level, repo_path, log_config, is_update)
    if len(log_list) == 0:
        return UPDATE_HINT

    log_title = Image.open(TEXT_PATH / 'log_title.png')

    img = await get_color_bg(950, 20 + 475 + 80 * len(log_list))
    img.paste(log_title, (0, 0), log_title)
    img_draw = ImageDraw.Draw(img)
    img_draw.text(
        (475, 432), 'GenshinUID  更新记录', black_color, gs_font_30, 'mm'
    )

    for index, log in enumerate(log_list):
        for key in log_map:
            if log.startswith(key):
                log_img = Image.open(TEXT_PATH / f'{log_map[key]}.png')
                break
        else:
            log_img = Image.open(TEXT_PATH / 'other.png')

        log_img_text = ImageDraw.Draw(log_img)
        if ')' in log:
            log = log.split(')')[0] + ')'
        log = log.replace('`', '')
        log_img_text.text((120, 40), log[2:], black_color, gs_font_30, 'lm')

        img.paste(log_img, (0, 475 + 80 * index), log_img)

    img = await convert_img(img)
    return img

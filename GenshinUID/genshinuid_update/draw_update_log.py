from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw

from .update import update_from_git
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.draw_image_tools.draw_image_tool import get_color_bg
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin

R_PATH = Path(__file__).parent
TEXT_PATH = R_PATH / 'texture2d'

gs_font_30 = genshin_font_origin(30)
black_color = (24, 24, 24)

log_config = {
    'key': '✨🐛🎨⚡🍱',
    'num': 18,
}

log_map = {'✨': 'feat', '🐛': 'bug', '🍱': 'bento', '⚡️': 'zap', '🎨': 'art'}


async def draw_update_log_img(
    level: int = 0,
    repo_path: Union[str, Path, None] = None,
    is_update: bool = True,
) -> Union[bytes, str]:
    log_list = await update_from_git(level, repo_path, log_config, is_update)
    if log_list == []:
        return f'更新失败!更多错误信息请查看控制台...\n >> 可以尝试使用\n >> [gs强制更新](危险)\n >> [gs强行强制更新](超级危险)!'

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
        log = log.replace('`', '')
        log_img_text.text((120, 40), log[2:], black_color, gs_font_30, 'lm')

        img.paste(log_img, (0, 475 + 80 * index), log_img)

    img = await convert_img(img)
    return img

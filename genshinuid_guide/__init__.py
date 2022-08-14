from pathlib import Path
from typing import Any, Tuple

import httpx

from ..all_import import *
from ..utils.alias.alias_to_char_name import alias_to_char_name
from ..utils.exception.handle_exception import handle_exception

get_guide_pic = on_regex('([\u4e00-\u9fa5]+)(推荐|攻略)')
get_bluekun_pic = on_command('参考面板')

IMG_PATH = Path(__file__).parent / 'img'


@get_guide_pic.handle()
@handle_exception('建议')
async def send_guide_pic(
    matcher: Matcher, args: Tuple[Any, ...] = RegexGroup()
):
    name = await alias_to_char_name(str(args[0]))
    url = 'https://img.genshin.minigg.cn/guide/{}.jpg'.format(name)
    if httpx.head(url).status_code == 200:
        logger.info('获得{}推荐图片成功！'.format(name))
        await matcher.finish(MessageSegment.image(url))
    else:
        logger.warning('未获得{}推荐图片。'.format(name))


@get_bluekun_pic.handle()
@handle_exception('参考面板')
async def send_bluekun_pic(matcher: Matcher, args: Message = CommandArg()):
    if str(args[0]) in ['冰', '水', '火', '草', '雷', '风', '岩']:
        name = str(args[0])
    else:
        name = await alias_to_char_name(str(args[0]))
    img = IMG_PATH / '{}.jpg'.format(name)
    if img.exists():
        with open(img, 'rb') as f:
            im = MessageSegment.image(f.read())
        logger.info('获得{}参考面板图片成功！'.format(name))
        await matcher.finish(im)
    else:
        logger.warning('未找到{}参考面板图片'.format(name))

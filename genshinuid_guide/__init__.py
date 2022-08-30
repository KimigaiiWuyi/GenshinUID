from pathlib import Path
from typing import Any, Tuple

import httpx
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import on_regex, on_command
from nonebot.params import CommandArg, RegexGroup
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from ..genshinuid_meta import register_menu
from ..utils.alias.alias_to_char_name import alias_to_char_name
from ..utils.exception.handle_exception import handle_exception

get_guide_pic = on_regex('([\u4e00-\u9fa5]+)(推荐|攻略)')
get_bluekun_pic = on_command('参考面板')

IMG_PATH = Path(__file__).parent / 'img'


@get_guide_pic.handle()
@handle_exception('建议')
@register_menu(
    '角色攻略',
    'xx攻略',
    '发送一张对应角色的西风驿站攻略图',
    detail_des=(
        '指令：'
        '<ft color=(238,120,0)>角色名[推荐/攻略]</ft>\n'
        ' \n'
        '发送一张对应角色的米游社西风驿站攻略图\n'
        '支持部分角色别名\n'
        ' \n'
        '示例：\n'
        '<ft color=(238,120,0)>钟离推荐</ft>；\n'
        '<ft color=(238,120,0)>公子攻略</ft>'
    ),
)
async def send_guide_pic(
    matcher: Matcher, args: Tuple[Any, ...] = RegexGroup()
):
    name = await alias_to_char_name(str(args[0]))
    if name.startswith('旅行者'):
        name = f'{name[:3]}-{name[-1]}'
    url = 'https://img.genshin.minigg.cn/guide/{}.jpg'.format(name)
    if httpx.head(url).status_code == 200:
        logger.info('获得{}推荐图片成功！'.format(name))
        await matcher.finish(MessageSegment.image(url))
    else:
        logger.warning('未获得{}推荐图片。'.format(name))


@get_bluekun_pic.handle()
@handle_exception('参考面板')
@register_menu(
    '参考面板',
    '参考面板[角色名/元素名]',
    '发送一张对应角色/元素的参考面板图',
    detail_des=(
        '指令：'
        '<ft color=(238,120,0)>参考面板[角色名/元素名]</ft>\n'
        ' \n'
        '发送一张对应角色/元素的参考面板图\n'
        '支持部分角色别名\n'
        ' \n'
        '示例：\n'
        '<ft color=(238,120,0)>参考面板火</ft>；\n'
        '<ft color=(238,120,0)>参考面板公子</ft>'
    ),
)
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

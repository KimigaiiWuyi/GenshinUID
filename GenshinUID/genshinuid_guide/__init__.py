import asyncio
import threading
from pathlib import Path
from typing import Any, List, Tuple

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import on_regex, on_command
from nonebot.params import CommandArg, RegexGroup
from nonebot.adapters.ntchat import MessageSegment
from nonebot.adapters.ntchat.message import Message

from .get_card import get_gs_card
from .get_guide import get_gs_guide
from ..version import Genshin_version
from ..genshinuid_meta import register_menu
from .get_abyss_data import get_review, generate_data
from ..utils.alias.alias_to_char_name import alias_to_char_name
from ..utils.exception.handle_exception import handle_exception

get_guide_pic = on_regex('([\u4e00-\u9fa5]+)(推荐|攻略)')
get_bluekun_pic = on_command('参考面板')
get_card = on_command('原牌')
get_abyss = on_command('版本深渊')

IMG_PATH = Path(__file__).parent / 'img'


@get_guide_pic.handle()
@handle_exception('建议')
@register_menu(
    '角色攻略',
    'xx攻略',
    '发送一张对应角色的西风驿站攻略图',
    detail_des=(
        '介绍：\n'
        '发送一张对应角色的米游社西风驿站攻略图\n'
        '支持部分角色别名\n'
        ' \n'
        '指令：\n'
        '- <ft color=(0,148,200)>[角色名]</ft>'
        '<ft color=(238,120,0)>{推荐|攻略}</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>钟离推荐</ft>\n'
        '- <ft color=(238,120,0)>公子攻略</ft>'
    ),
)
async def send_guide_pic(
    matcher: Matcher, args: Tuple[Any, ...] = RegexGroup()
):
    if not args:
        return
    name = str(args[0])
    im = await get_gs_guide(name)
    if im:
        logger.info('获得{}攻略成功！'.format(name))
        await matcher.finish(MessageSegment.image(im))
    else:
        logger.warning('未找到{}攻略图片'.format(name))


@get_bluekun_pic.handle()
@handle_exception('参考面板')
@register_menu(
    '参考面板',
    '参考面板[角色名/元素名]',
    '发送一张对应角色/元素的参考面板图',
    detail_des=(
        '介绍：\n'
        '发送一张对应角色/元素的参考面板图\n'
        '支持部分角色别名\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>参考面板</ft>'
        '<ft color=(0,148,200)>[角色名/元素名]</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>参考面板火</ft>\n'
        '- <ft color=(238,120,0)>参考面板公子</ft>'
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


@get_card.handle()
@handle_exception('原牌')
async def send_gscard_pic(matcher: Matcher, args: Message = CommandArg()):
    if not args:
        return
    name = str(args[0])
    im = await get_gs_card(name)
    if im:
        logger.info('获得{}原牌成功！'.format(name))
        await matcher.finish(MessageSegment.image(im))
    else:
        logger.warning('未找到{}原牌图片'.format(name))


@get_abyss.handle()
@handle_exception('版本深渊')
async def send_abyss_review(
    matcher: Matcher,
    args: Message = CommandArg(),
):
    if not args:
        version = Genshin_version[:-2]
    else:
        version = str(args[0])
    im = await get_review(version)
    if isinstance(im, List):
        im = '\n'.join(im)
        await matcher.finish(im)
    elif isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')


threading.Thread(
    target=lambda: asyncio.run(generate_data()), daemon=True
).start()

from pathlib import Path
from typing import Any, Tuple

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import on_regex, on_command
from nonebot.params import CommandArg, RegexGroup
from nonebot.adapters.onebot.v11 import Message, MessageSegment

from ..version import Genshin_version
from ..genshinuid_meta import register_menu
from ..utils.exception.handle_exception import handle_exception

get_primogems_data = on_command('版本规划', aliases={'原石预估'})
get_img_data = on_regex(r'^(查询)?(伤害乘区|血量表|抗性表|血量排行)$')

PRIMOGEMS_DATA_PATH = Path(__file__).parent / 'primogems_data'
IMG_PATH = Path(__file__).parent / 'img_data'


@get_primogems_data.handle()
@handle_exception('版本规划')
@register_menu(
    '版本原石规划',
    '版本规划(版本号)',
    '发送一张指定版本的原石规划图',
    detail_des=(
        '介绍：\n'
        '发送一张指定版本的原石规划图\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>版本规划</ft><ft color=(125,125,125)>(版本号)</ft>\n'
        '- <ft color=(238,120,0)>原石预估</ft><ft color=(125,125,125)>(版本号)</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>版本规划</ft>\n'
        '- <ft color=(238,120,0)>版本规划3.0</ft>'
    ),
)
async def send_primogems_data(matcher: Matcher, args: Message = CommandArg()):
    logger.info('开始执行[图片][版本规划]')
    logger.info('[图片][版本规划]参数: {}'.format(args))
    if args:
        path = PRIMOGEMS_DATA_PATH / f'{str(args)}.png'
        if path.exists():
            img = f'{str(args)}.png'
        else:
            await matcher.finish()
    else:
        img = f'{Genshin_version[:3]}.png'
    primogems_img = PRIMOGEMS_DATA_PATH / img
    if primogems_img.exists():
        logger.info('[图片][版本规划]访问图片: {}'.format(img))
        with open(primogems_img, 'rb') as f:
            await matcher.finish(MessageSegment.image(f.read()))
    else:
        await matcher.finish()


@get_img_data.handle()
@handle_exception('杂图')
@register_menu(
    '伤害乘区图',
    '(查询)伤害乘区',
    '发送一张理论伤害计算公式图',
    detail_des=(
        '介绍：\n'
        '发送一张理论伤害计算公式图\n'
        ' \n'
        '指令：\n'
        '- <ft color=(125,125,125)>(查询)</ft><ft color=(238,120,0)>伤害乘区</ft>'
    ),
)
@register_menu(
    '怪物血量表',
    '(查询)血量表',
    '发送一张原神怪物血量表图',
    detail_des=(
        '介绍：\n'
        '发送一张原神怪物血量表图\n'
        ' \n'
        '指令：\n'
        '- <ft color=(125,125,125)>(查询)</ft><ft color=(238,120,0)>血量表</ft>'
    ),
)
@register_menu(
    '怪物抗性表',
    '(查询)抗性表',
    '发送一张原神怪物抗性表图',
    detail_des=(
        '介绍：\n'
        '发送一张原神怪物抗性表图\n'
        ' \n'
        '指令：\n'
        '- <ft color=(125,125,125)>(查询)</ft><ft color=(238,120,0)>抗性表</ft>'
    ),
)
@register_menu(
    '怪物血量排行',
    '(查询)血量排行',
    '发送一张原神怪物血量排行图',
    detail_des=(
        '介绍：\n'
        '发送一张原神怪物血量排行图\n'
        ' \n'
        '指令：\n'
        '- <ft color=(125,125,125)>(查询)</ft><ft color=(238,120,0)>血量排行</ft>'
    ),
)
async def send_img_data(
    matcher: Matcher, args: Tuple[Any, ...] = RegexGroup()
):
    logger.info('开始执行[图片][杂图]')
    logger.info('[图片][杂图]参数: {}'.format(args))
    img = IMG_PATH / f'{args[1]}.jpg'
    if img.exists():
        with open(img, 'rb') as f:
            await matcher.finish(MessageSegment.image(f.read()))

from pathlib import Path
from typing import Any, Tuple

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import on_regex, on_command
from nonebot.adapters.qqguild import Message
from nonebot.params import CommandArg, RegexGroup

from ..genshinuid_meta import register_menu
from ..utils.nonebot2.send import local_image
from ..utils.exception.handle_exception import handle_exception

get_primogems_data = on_command('版本规划', aliases={'原石预估'})
get_img_data = on_regex(r'(查询)?(伤害乘区|血量表|抗性表)')

PRIMOGEMS_DATA_PATH = Path(__file__).parent / 'primogems_data'
IMG_PATH = Path(__file__).parent / 'img_data'
version = ['3.0', '3.1']


@get_primogems_data.handle()
@handle_exception('版本规划')
@register_menu(
    '版本原石规划',
    '版本规划(版本号)',
    '发送一张指定版本的原石规划图',
    detail_des=(
        '指令：'
        '<ft color=(238,120,0)>版本规划</ft>'
        '<ft color=(125,125,125)>(版本号)</ft>\n'
        ' \n'
        '发送一张指定版本的原石规划图\n'
        ' \n'
        '示例：\n'
        '<ft color=(238,120,0)>版本规划</ft>；\n'
        '<ft color=(238,120,0)>版本规划3.0</ft>'
    ),
)
async def send_primogems_data(matcher: Matcher, args: Message = CommandArg()):
    logger.info('开始执行[图片][版本规划]')
    logger.info('[图片][版本规划]参数: {}'.format(args))
    if args:
        if str(args) in version:
            img = f'{args}.png'
        else:
            await matcher.finish()
    else:
        img = f'{version[0]}.png'
    primogems_img = PRIMOGEMS_DATA_PATH / img
    logger.info('[图片][版本规划]访问图片: {}'.format(img))
    await matcher.finish(local_image(primogems_img))


@get_img_data.handle()
@handle_exception('杂图')
@register_menu(
    '伤害乘区图',
    '伤害乘区',
    '发送一张理论伤害计算公式图',
    detail_des=(
        '指令：' '<ft color=(238,120,0)>伤害乘区</ft>\n' ' \n' '发送一张理论伤害计算公式图'
    ),
)
@register_menu(
    '怪物血量表',
    '血量表',
    '发送一张原神怪物血量表图',
    detail_des=('指令：' '<ft color=(238,120,0)>血量表</ft>\n' ' \n' '发送一张原神怪物血量表图'),
)
@register_menu(
    '怪物抗性表',
    '抗性表',
    '发送一张原神怪物抗性表图',
    detail_des=('指令：' '<ft color=(238,120,0)>抗性表</ft>\n' ' \n' '发送一张原神怪物抗性表图'),
)
async def send_img_data(
    matcher: Matcher, args: Tuple[Any, ...] = RegexGroup()
):
    logger.info('开始执行[图片][杂图]')
    logger.info('[图片][杂图]参数: {}'.format(args))
    img = IMG_PATH / f'{args[1]}.jpg'
    if img.exists():
        await matcher.finish(local_image(img))

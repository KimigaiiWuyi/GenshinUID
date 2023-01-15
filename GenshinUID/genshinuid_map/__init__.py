from typing import Any, Dict, Union

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import RegexDict
from nonebot import on_regex, on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageSegment,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from ..config import priority
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from .draw_genshinmap_card import MAP_DATA, draw_genshin_map
from ..utils.exception.handle_exception import handle_exception

change_map = on_command('切换地图', block=True, rule=FullCommand())
find_map = on_regex(
    r'^(?P<name>.*)(在哪里|在哪|哪里有|哪儿有|哪有|在哪儿)$', priority=priority
)
find_map2 = on_regex(r'^(哪里有|哪儿有|哪有)(?P<name>.*)$', priority=priority)


MAP_ID_LIST = [
    '2',  # 提瓦特
    '9',  # 层岩巨渊
    '7',  # 渊下宫
    # MapID.golden_apple_archipelago,  # 金苹果群岛
]
MAP_CHN_NAME = {
    '2': '提瓦特',
    '9': '层岩巨渊',
    '7': '渊下宫',
    # MapID.golden_apple_archipelago: '金苹果群岛',
}


@change_map.handle()
@handle_exception('切换地图')
@register_menu(
    '切换地图',
    '切换地图',
    '切换查找资源点功能所使用的地图',
    detail_des=(
        '介绍：\n'
        '切换查找资源点功能所使用的地图\n'
        '指令按列表顺序轮流切换地图\n'
        '目前可用地图：'
        + "；".join(
            [f"<ft color=(238,120,0)>{x}</ft>" for x in MAP_CHN_NAME.values()]
        )
        + ' \n\n'
        '指令：\n'
        '- <ft color=(238,120,0)>切换地图</ft>'
    ),
)
async def send_change_map_msg(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
):
    if not await SUPERUSER(bot, event):
        return
    logger.info('[切换地图]正在执行...')
    MAP_ID_LIST.append(MAP_ID_LIST[0])
    MAP_ID_LIST.pop(0)
    current = MAP_ID_LIST[0]
    chn = MAP_CHN_NAME.get(current)
    logger.info(f'[切换地图]当前地图为{chn}')
    await matcher.finish(f'切换到{chn}地图')


@find_map.handle()
@find_map2.handle()
@handle_exception('查找资源点')
@register_menu(
    '查找资源点',
    'xx在哪',
    '查找指定资源在地图上的位置',
    detail_des=(
        '介绍：\n'
        '在米游社大地图上查询某资源的位置\n'
        '使用 <ft color=(238,120,0)>切换地图</ft> 指令来切换目标地图'
        ' \n'
        '指令：\n'
        '- <ft color=(0,148,200)>[资源名称]</ft>'
        '<ft color=(238,120,0)>{在哪里|在哪|哪里有|哪儿有|哪有|在哪儿}</ft>\n'
        '- <ft color=(238,120,0)>{哪里有|哪儿有|哪有}</ft>'
        '<ft color=(0,148,200)>[资源名称]</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>甜甜花在哪</ft>\n'
        '- <ft color=(238,120,0)>哪有清心</ft>'
    ),
)
async def send_find_map_msg(
    matcher: Matcher, args: Dict[str, Any] = RegexDict()
):
    map_id = MAP_ID_LIST[0]
    map_name = MAP_CHN_NAME[map_id]
    logger.info(f'[查找资源点]正在执行...当前地图为{map_name}')
    logger.info('[查找资源点]参数: {}'.format(args))

    if not (args and (name := args.get('name'))):
        return

    if not MAP_DATA.exists():
        MAP_DATA.mkdir()

    resource_temp_path = MAP_DATA / f'{map_name}_{name}.jpg'
    if resource_temp_path.exists():
        logger.info(f'本地已有{map_name}_{name}的资源点,直接发送...')
        with open(resource_temp_path, 'rb') as f:
            await matcher.finish(MessageSegment.image(f.read()))
    else:
        # 放弃安慰剂回复
        '''
        await matcher.send(
            (
                f'正在查找{name},可能需要比较久的时间...\n'
                f'当前地图：{MAP_CHN_NAME.get(MAP_ID_LIST[0])}'
            )
        )
        '''
        logger.info('本地未缓存,正在渲染...')
        im = await draw_genshin_map(name, map_id, map_name)
    if isinstance(im, str):
        # 如果无结果，直接不返回
        await matcher.finish()
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('查找失败!')

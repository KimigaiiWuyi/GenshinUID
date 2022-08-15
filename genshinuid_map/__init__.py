from typing import Dict

from nonebot.params import RegexDict

from .create_genshinmap import create_genshin_map
from .draw_genshinmap_card import draw_genshin_map
from .genshinmap.models import MapID
from ..all_import import *  # noqa

create_map = on_command('生成地图', block=True)
change_map = on_command('切换地图', block=True)
find_map = on_regex(r'^(?P<name>.*)(在哪里|在哪|哪里有|哪儿有|哪有|在哪儿)$', priority=2)
find_map2 = on_regex(r'^(哪里有|哪儿有|哪有)(?P<name>.*)$', priority=2)

MAP_DATA = Path(__file__).parent / 'map_data'
MAP_ID_LIST = [
    MapID.teyvat,  # 提瓦特
    MapID.chasm,  # 层岩巨渊
    MapID.enkanomiya,  # 渊下宫
    MapID.golden_apple_archipelago,  # 金苹果群岛
]
MAP_CHN_NAME = {
    MapID.teyvat: '提瓦特',
    MapID.chasm: '层岩巨渊',
    MapID.enkanomiya: '渊下宫',
    MapID.golden_apple_archipelago: '金苹果群岛',
}


@change_map.handle()
@handle_exception('切换地图')
async def send_change_map_msg(
        event: Union[GroupMessageEvent, PrivateMessageEvent],
        matcher: Matcher,
        args: Message = CommandArg(),
):
    if args:
        return
    qid = event.sender.user_id
    if qid not in SUPERUSERS:
        return
    logger.info('[切换地图]正在执行...')
    MAP_ID_LIST.append(MAP_ID_LIST[0])
    MAP_ID_LIST.pop(0)
    current = MAP_ID_LIST[0]
    chn = MAP_CHN_NAME.get(current)
    logger.info(f'[切换地图]当前地图为{chn}("{current.name}", {current.value})')
    await matcher.finish(f'切换到{chn}地图')


@create_map.handle()
@handle_exception('生成地图')
async def send_create_map_msg(
        event: Union[GroupMessageEvent, PrivateMessageEvent],
        matcher: Matcher,
        args: Message = CommandArg(),
):
    if args:
        return
    qid = event.sender.user_id
    if qid not in SUPERUSERS:
        return
    logger.info('[生成地图]正在执行...')
    await matcher.send('地图正在初始化...可能需要较长时间!')
    await create_genshin_map()
    await matcher.finish('地图初始化完毕!')


@find_map.handle()
@find_map2.handle()
@handle_exception('查找资源点')
async def send_find_map_msg(
        matcher: Matcher,
        args: Dict[str, Any] = RegexDict()  # noqa
):
    logger.info(f'[查找资源点]正在执行...当前地图为{MAP_ID_LIST[0].name}')
    logger.info('[查找资源点]参数: {}'.format(args))

    args = args.get('name')
    resource_temp_path = MAP_DATA / f'{MAP_ID_LIST[0].name}_{args}.jpg'
    if resource_temp_path.exists():
        logger.info(f'本地已有{MAP_ID_LIST[0].name}_{args}的资源点,直接发送...')
        await matcher.finish(MessageSegment.image(resource_temp_path))
    else:
        await matcher.send(f'正在查找{args},可能需要比较久的时间...\n当前地图：{MAP_CHN_NAME.get(MAP_ID_LIST[0])}')
        logger.info(f'本地未缓存,正在渲染...')
        im = await draw_genshin_map(MAP_ID_LIST[0], args)
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('查找失败!')

from pathlib import Path

from ..all_import import *  # noqa
from .genshinmap.models import MapID
from .create_genshinmap import create_genshin_map
from .draw_genshinmap_card import draw_genshin_map

create_map = on_command('生成地图', block=True)
change_map = on_command('切换地图', block=True)
find_map = on_regex(r'^(.*)(在哪里|在哪|哪里有|在哪儿)$', priority=2)

MAP_DATA = Path(__file__).parent / 'map_data'
MAP_ID_LIST = [
    MapID.teyvat,
    MapID.chasm,
    MapID.enkanomiya,
    MapID.golden_apple_archipelago,
]


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
    logger.info(f'[切换地图]当前地图为{MAP_ID_LIST[0]}')
    await matcher.finish(f'切换到{MAP_ID_LIST[0].name}地图')


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
@handle_exception('查找资源点')
async def send_find_map_msg(
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
):
    logger.info(f'[查找资源点]正在执行...当前地图为{MAP_ID_LIST[0].name}')
    logger.info('[查找资源点]参数: {}'.format(args))
    resource_temp_path = MAP_DATA / f'{MAP_ID_LIST[0].name}_{args[0]}.jpg'
    if resource_temp_path.exists():
        logger.info(f'本地已有{MAP_ID_LIST[0].name}_{args[0]}的资源点,直接发送...')
        await matcher.finish(MessageSegment.image(resource_temp_path))
    else:
        await matcher.send(f'正在查找{args[0]},可能需要比较久的时间...')
        logger.info(f'本地未缓存,正在渲染...')
        im = await draw_genshin_map(MAP_ID_LIST[0], args[0])
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('查找失败!')

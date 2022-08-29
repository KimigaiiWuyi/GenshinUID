from ..all_import import *  # noqa
from .genshinmap.models import MapID
from .create_genshinmap import create_genshin_map
from .draw_genshinmap_card import draw_genshin_map

MAP_DATA = Path(__file__).parent / 'map_data'
MAP_ID_LIST = [
    MapID.teyvat,  # 提瓦特
    MapID.chasm,  # 层岩巨渊
    MapID.enkanomiya,  # 渊下宫
    # MapID.golden_apple_archipelago,  # 金苹果群岛
]
MAP_CHN_NAME = {
    MapID.teyvat: '提瓦特',
    MapID.chasm: '层岩巨渊',
    MapID.enkanomiya: '渊下宫',
    # MapID.golden_apple_archipelago: '金苹果群岛',
}


@sv.on_fullmatch('切换地图')
async def send_change_map_msg(bot: HoshinoBot, ev: CQEvent):
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return
    if qid not in bot.config.SUPERUSERS:
        return
    logger.info('[切换地图]正在执行...')
    MAP_ID_LIST.append(MAP_ID_LIST[0])
    MAP_ID_LIST.pop(0)
    current = MAP_ID_LIST[0]
    chn = MAP_CHN_NAME.get(current)
    logger.info(f'[切换地图]当前地图为{chn}("{current.name}", {current.value})')
    await bot.send(ev, f'切换到{chn}地图')


@sv.on_fullmatch('生成地图')
async def send_create_map_msg(bot: HoshinoBot, ev: CQEvent):
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return
    if qid not in bot.config.SUPERUSERS:
        return
    logger.info('[生成地图]正在执行...')
    await bot.send(ev, '地图正在初始化...可能需要较长时间!')
    await create_genshin_map()
    await bot.send(ev, '地图初始化完毕!')


@sv.on_rex(r'^(?P<name>.*)(在哪里|在哪|哪里有|哪儿有|哪有|在哪儿)$')
@sv.on_rex(r'^(哪里有|哪儿有|哪有)(?P<name>.*)$')
async def send_find_map_msg(bot: HoshinoBot, ev: CQEvent):
    args = ev['match'].groups()
    logger.info(f'[查找资源点]正在执行...当前地图为{MAP_ID_LIST[0].name}')
    logger.info('[查找资源点]参数: {}'.format(args))

    if args[0]:
        args = args[0]
    else:
        return

    im = ''
    resource_temp_path = MAP_DATA / f'{MAP_ID_LIST[0].name}_{args}.jpg'
    if resource_temp_path.exists():
        logger.info(f'本地已有{MAP_ID_LIST[0].name}_{args}的资源点,直接发送...')
        resource_temp = await convert_img(resource_temp_path)
        await bot.send(ev, resource_temp)
    else:
        await bot.send(
            ev,
            f'正在查找{args},可能需要比较久的时间...\n当前地图：{MAP_CHN_NAME.get(MAP_ID_LIST[0])}',
        )
        logger.info(f'本地未缓存,正在渲染...')
        im = await draw_genshin_map(MAP_ID_LIST[0], args)
    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, im)

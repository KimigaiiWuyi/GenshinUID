from hoshino.typing import CQEvent, HoshinoBot

from ..base import sv, logger
from .draw_genshinmap_card import MAP_DATA, draw_genshin_map
from ..utils.draw_image_tools.send_image_tool import convert_img

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
    logger.info(f'[切换地图]当前地图为{chn}')
    await bot.send(ev, f'切换到{chn}地图')


@sv.on_rex(r'^(?P<name>.*)(在哪里|在哪|哪里有|哪儿有|哪有|在哪儿)$')
@sv.on_rex(r'^(哪里有|哪儿有|哪有)(?P<name>.*)$')
async def send_find_map_msg(bot: HoshinoBot, ev: CQEvent):
    map_id = MAP_ID_LIST[0]
    map_name = MAP_CHN_NAME[map_id]
    args = ev['match'].groupdict().get('name')
    logger.info(f'[查找资源点]正在执行...当前地图为{map_name}')
    logger.info('[查找资源点]参数: {}'.format(args))

    if not args:
        return

    im = ''

    if not MAP_DATA.exists():
        MAP_DATA.mkdir()

    resource_temp_path = MAP_DATA / f'{map_name}_{args}.jpg'
    if resource_temp_path.exists():
        logger.info(f'本地已有{map_name}_{args}的资源点,直接发送...')
        resource_temp = await convert_img(resource_temp_path)
        await bot.send(ev, resource_temp)
    else:
        # 放弃安慰剂回复
        '''
        await bot.send(
            ev,
            f'正在查找{args},可能需要比较久的时间...\n当前地图：{map_name}',
        )
        '''
        logger.info('本地未缓存,正在渲染...')
        im = await draw_genshin_map(args, map_id, map_name)
        if isinstance(im, str):
            return
            # await bot.send(ev, im)
        elif isinstance(im, bytes):
            im = await convert_img(im)
            await bot.send(ev, im)

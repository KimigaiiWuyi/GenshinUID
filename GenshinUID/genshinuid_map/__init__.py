from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.image.convert import convert_img
from .draw_genshinmap_card import MAP_DATA, draw_genshin_map

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

sv_find_map_config = SV('查询地图设置', pm=2)
sv_find_map = SV('查询地图')


@sv_find_map_config.on_fullmatch(('切换地图'))
async def send_change_map_msg(bot: Bot, ev: Event):
    await bot.logger.info('[切换地图]正在执行...')
    MAP_ID_LIST.append(MAP_ID_LIST[0])
    MAP_ID_LIST.pop(0)
    current = MAP_ID_LIST[0]
    chn = MAP_CHN_NAME.get(current)
    await bot.logger.info(f'[切换地图]当前地图为{chn}')
    await bot.send(f'切换到{chn}地图')


@sv_find_map.on_prefix(('哪里有', '哪儿有', '哪有'))
async def send_find_map_msg(bot: Bot, ev: Event):
    map_id = MAP_ID_LIST[0]
    map_name = MAP_CHN_NAME[map_id]
    await bot.logger.info(f'[查找资源点]正在执行...当前地图为{map_name}')

    if not MAP_DATA.exists():
        MAP_DATA.mkdir()

    resource_temp_path = MAP_DATA / f'{map_name}_{ev.text}.jpg'
    if resource_temp_path.exists():
        await bot.logger.info(
            f'本地已有{map_name}_{ev.text}的资源点,直接发送...'
        )
        resource_temp = await convert_img(resource_temp_path)
        await bot.send(resource_temp)
    else:
        await bot.logger.info('本地未缓存,正在渲染...')
        im = await draw_genshin_map(ev.text, map_id, map_name)
        await bot.send(im)

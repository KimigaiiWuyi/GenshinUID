from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.models import Event

from ..utils.image.convert import convert_img
from .draw_genshinmap_card import MAP_DATA, draw_genshin_map

MAP_ID_LIST = [
    "2",  # 提瓦特
    "9",  # 层岩巨渊
    "7",  # 渊下宫
    # MapID.golden_apple_archipelago,  # 金苹果群岛
]
MAP_CHN_NAME = {
    "2": "提瓦特",
    "9": "层岩巨渊",
    "7": "渊下宫",
    # MapID.golden_apple_archipelago: '金苹果群岛',
}

sv_find_map_config = SV("查询地图设置", pm=2)
sv_find_map = SV("查询地图")


@sv_find_map_config.on_fullmatch(
    ("切换地图"),
    to_ai="""切换原神资源点查询使用的地图

    当用户说"切换地图"时调用。
    在提瓦特、层岩巨渊、渊下宫三张地图之间循环切换。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_change_map_msg(bot: Bot, ev: Event):
    await bot.logger.info(t("log.genshinuid.map_switch_start"))
    MAP_ID_LIST.append(MAP_ID_LIST[0])
    MAP_ID_LIST.pop(0)
    current = MAP_ID_LIST[0]
    chn = MAP_CHN_NAME.get(current)
    await bot.logger.info(t("log.genshinuid.map_switch_current", chn=chn))
    await bot.send(f"切换到{chn}地图")


@sv_find_map.on_prefix(
    ("哪里有", "哪儿有", "哪有"),
    to_ai="""查询原神中某种资源在地图上的分布位置

    当用户说"哪里有清心"、"哪儿有琉璃袋"、"哪有水晶矿"时调用。
    以图片形式返回该资源在地图上的分布标记。

    Args:
        text: 资源名称，例如 "清心"、"琉璃袋"、"水晶矿"、"绯樱绣球"、"鬼兜虫"
    """,
)
async def send_find_map_msg(bot: Bot, ev: Event):
    map_id = MAP_ID_LIST[0]
    map_name = MAP_CHN_NAME[map_id]
    await bot.logger.info(t("log.genshinuid.map_find_start", map_name=map_name))

    if not MAP_DATA.exists():
        MAP_DATA.mkdir()

    resource_temp_path = MAP_DATA / f"{map_name}_{ev.text}.jpg"
    if resource_temp_path.exists():
        await bot.logger.info(t("log.genshinuid.map_find_cached", map_name=map_name, resource=ev.text))
        resource_temp = await convert_img(resource_temp_path)
        await bot.send(resource_temp)
    else:
        await bot.logger.info(t("log.genshinuid.map_find_render"))
        im = await draw_genshin_map(ev.text, map_id, map_name)
        await bot.send(im)

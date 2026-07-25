from typing import Union, Optional
from pathlib import Path
from datetime import datetime, timedelta

from PIL import Image, ImageDraw

from gsuid_core.models import Event
from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.api.mys.models import IndexData, SeasonPostData
from gsuid_core.ai_core.trigger_bridge import ai_return

from ..utils.mys_api import mys_api, get_base_data
from ..utils.image.convert import convert_img
from ..utils.image.image_tools import (
    get_v4_bg,
    add_footer,
    easy_paste,
    get_avatar,
    get_v4_title,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_22,
    gs_font_24,
    gs_font_26,
    gs_font_28,
    gs_font_30,
    gs_font_32,
    gs_font_36,
    gs_font_40,
    gs_font_50,
)
from ..utils.resource.download_url import download
from ..utils.resource.RESOURCE_PATH import (
    ICON_PATH,
    WEAPON_PATH,
    GACHA_IMG_PATH,
)

TEXT_PATH = Path(__file__).parent / "texture2d"
COLOR_MAP = {
    500: (146, 16, 16),
    300: (94, 16, 146),
    150: (16, 83, 146),
    50: (146, 79, 48),
    0: (103, 105, 67),
}
COLOR_LIST = [
    (123, 81, 198),
    (81, 198, 149),
    (198, 176, 81),
    (81, 148, 198),
    (198, 81, 81),
    (81, 95, 198),
    (162, 150, 222),
    (133, 198, 27),
]


async def get_season_post_draw(uid: str, ev: Event) -> Union[str, bytes]:
    data = await mys_api.get_season_post_data(uid)
    raw_data = await get_base_data(uid)

    if isinstance(data, int):
        return get_error(data)
    if isinstance(raw_data, (str, bytes)):
        return raw_data
    elif isinstance(raw_data, (bytearray, memoryview)):
        return bytes(raw_data)

    # AI 注入：提取季报数据
    try:
        ri = data.get("resource_info", {})
        ei = data.get("exploration_info", {})
        gi = data.get("game_record_info", {})
        parts = [f"【UID {uid} 季度报告】"]
        parts.append(f"获得摩拉: {ri.get('gain_scoin', 'N/A')}  获得原石: {ri.get('gain_primogem', 'N/A')}")
        tp = ei.get("trans_point", {})
        parts.append(f"解锁锚点: {tp.get('cur_number', 'N/A')} (新增{tp.get('new_number', 0)})")
        # 探索信息
        if ei.get("area_list"):
            for area in ei["area_list"][:5]:
                parts.append(f"  {area.get('name', '?')}: 探索度{area.get('exploration_percentage', 0) / 10:.1f}%")
        # 游戏记录
        if gi:
            parts.append(
                f"活跃天数: {gi.get('active_day_number', 'N/A')}  获得角色数: {gi.get('avatar_number', 'N/A')}"
            )
            parts.append(f"成就数: {gi.get('achievement_number', 'N/A')}  深渊: {gi.get('spiral_abyss', 'N/A')}")
        ai_return("\n".join(parts))
    except Exception:
        pass

    return await draw_season_post(uid, raw_data, data, ev)


async def draw_season_post(
    uid: str,
    raw_data: IndexData,
    data: SeasonPostData,
    ev: Event,
) -> bytes:
    now = datetime.now()
    now_90 = now - timedelta(days=90)

    tag = Image.open(TEXT_PATH / "tag.png")

    char_pic = await get_avatar(ev, 377, False)
    title_img = get_v4_title(char_pic, uid, raw_data)

    # 散资源
    resource_list = [
        {
            "title": "获得摩拉",
            "icon": Image.open(TEXT_PATH / "mora.png"),
            "cur": data["resource_info"]["gain_scoin"],
            "add": None,
        },
        {
            "title": "解锁锚点",
            "icon": Image.open(TEXT_PATH / "transport.png"),
            "cur": data["exploration_info"]["trans_point"]["cur_number"],
            "add": data["exploration_info"]["trans_point"]["new_number"],
        },
    ]
    for crystal in data["exploration_info"]["crystal_list"]:
        crystal_name = crystal["name"] if crystal["name"] else "月神瞳"
        resource_list.append(
            {
                "title": f"{crystal_name}",
                "icon": crystal["icon"],
                "cur": crystal["cur_number"],
                "add": crystal["new_number"],
            }
        )
    for chest in data["exploration_info"]["chest_list"]:
        resource_list.append(
            {
                "title": chest["name"].replace("的", ""),
                "icon": chest["icon"],
                "cur": chest["cur_number"],
                "add": chest["new_number"],
            }
        )

    w = 1200
    _h = ((len(resource_list) - 1) // 3 + 1) * 130
    h = 2600 + _h

    img = get_v4_bg(w, h)
    title_img = title_img.resize((w, 500))
    img.paste(title_img, (0, 0), title_img)

    new_tag = Image.open(TEXT_PATH / "new_tag.png")

    # 抽卡
    bar1 = Image.open(TEXT_PATH / "bar1.png")
    img.paste(bar1, (0, 562), bar1)

    ms1 = Image.open(TEXT_PATH / "ms1.png")
    ms1_draw = ImageDraw.Draw(ms1)
    ms1_draw.text((110, 64), "角色", (255, 255, 255), gs_font_32, "mm")
    ms1_draw.text(
        (180, 64),
        f"新 {data['avatar_info']['new_avatar_count']}",
        (255, 255, 255),
        gs_font_32,
        "lm",
    )
    ms1_draw.text(
        (297, 64),
        f"已有 {data['avatar_info']['cur_avatar_count']}",
        (255, 255, 255),
        gs_font_32,
        "lm",
    )

    ms2 = Image.open(TEXT_PATH / "ms1.png")
    ms2_draw = ImageDraw.Draw(ms2)
    ms2_draw.text((110, 64), "武器", (255, 255, 255), gs_font_32, "mm")
    ms2_draw.text(
        (180, 64),
        f"新 {data['weapon_info']['new_weapon_count']}",
        (255, 255, 255),
        gs_font_32,
        "lm",
    )
    ms2_draw.text(
        (297, 64),
        f"已有 {data['weapon_info']['cur_weapon_count']}",
        (255, 255, 255),
        gs_font_32,
        "lm",
    )

    img.paste(ms1, (6, 649), ms1)
    img.paste(ms2, (6, 737), ms2)

    for index_weapon, weapon in enumerate(data["weapon_info"]["changed_weapon_list"][:2]):
        weapon_fg = Image.open(TEXT_PATH / f"weapon{weapon['rarity']}_fg.png")
        weapon_bg = Image.open(TEXT_PATH / f"weapon{weapon['rarity']}_bg.png")
        weapon_img = Image.open(WEAPON_PATH / f"{weapon['name']}.png").resize((180, 180)).convert("RGBA")
        weapon_bg.paste(weapon_img, (10, 10), weapon_img)
        weapon_bg.paste(weapon_fg, (0, 0), weapon_fg)
        weapon_bg_draw = ImageDraw.Draw(weapon_bg)
        weapon_bg_draw.text(
            (102, 164),
            weapon["name"],
            (255, 255, 255),
            gs_font_32,
            "mm",
        )
        if weapon["is_new_weapon"]:
            weapon_bg.paste(new_tag, (120, 20), new_tag)
        img.paste(weapon_bg, (46 + index_weapon * 210, 866), weapon_bg)

    char_mask = Image.open(TEXT_PATH / "char_mask.png")
    for index_char, char in enumerate(data["avatar_info"]["changed_avatar_list"][:3]):
        char_bg = Image.open(TEXT_PATH / "char_bg.png")
        char_img = Image.open(GACHA_IMG_PATH / f"{char['name']}.png").resize((901, 450)).convert("RGBA")
        char_temp = Image.new("RGBA", char_bg.size, (0, 0, 0, 0))
        char_temp2 = Image.new("RGBA", char_bg.size, (0, 0, 0, 0))
        char_temp.paste(char_img, (-300, 0), char_img)
        char_temp2.paste(char_temp, (0, 0), char_mask)
        char_bg.paste(char_temp2, (0, 0), char_temp2)

        char_bg_draw = ImageDraw.Draw(char_bg)
        char_bg_draw.text(
            (115, 371),
            char["name"],
            (255, 255, 255),
            gs_font_32,
            "mm",
        )
        if char["is_new_avatar"]:
            char_bg.paste(new_tag, (151, 26), new_tag)

        img.paste(char_bg, (477 + index_char * 230, 653), char_bg)

    # 地区探索
    bar2 = Image.open(TEXT_PATH / "bar2.png")
    img.paste(bar2, (0, 1141), bar2)

    for index_city, city in enumerate(data["exploration_info"]["world_exploration_list"][:4]):
        city_bg = Image.open(TEXT_PATH / "city_bg.png")
        city_icon_path = ICON_PATH / city["icon"].split("/")[-1]
        if not city_icon_path.exists():
            await download(city["icon"], 8, city_icon_path.name)
        city_icon = Image.open(city_icon_path).convert("RGBA")
        city_icon = city_icon.resize((int(city_icon.size[0] * 0.713), int(city_icon.size[1] * 0.713)))
        city_bg.paste(
            city_icon,
            (
                int(136 - city_icon.size[0] / 2),
                int(162 - city_icon.size[1] / 2),
            ),
            city_icon,
        )
        city_bg_draw = ImageDraw.Draw(city_bg)

        for key in COLOR_MAP:
            if city["new_number"] >= key:
                color = COLOR_MAP[key]
                break
        else:
            color = list(COLOR_MAP.values())[-1]

        city_bg_draw.rounded_rectangle(
            (50, 296, 222, 337),
            radius=5,
            fill=color,
        )
        city_bg_draw.rounded_rectangle(
            (88, 386, 184, 411),
            radius=5,
            fill=color,
        )

        city_bg_draw.text(
            (136, 317),
            city["name"],
            (255, 255, 255),
            gs_font_36,
            "mm",
        )
        city_bg_draw.text(
            (136, 363),
            f"探索度: {city['cur_number'] / 10:.1f}%",
            (255, 255, 255),
            gs_font_22,
            "mm",
        )
        city_bg_draw.text(
            (136, 399),
            f"+{city['new_number'] / 10:.1f}%",
            (255, 255, 255),
            gs_font_22,
            "mm",
        )

        img.paste(city_bg, (51 + index_city * 278, 1233), city_bg)

    # 资源统计
    bar3 = Image.open(TEXT_PATH / "bar3.png")
    img.paste(bar3, (0, 1752), bar3)
    hcoin_bar = Image.open(TEXT_PATH / "hcoin_bar.png")
    hcoin_bar_draw = ImageDraw.Draw(hcoin_bar)
    hcoin_bar_draw.text(
        (295, 41),
        f"{data['resource_info']['gain_hcoin']}",
        (108, 133, 255),
        gs_font_50,
        "lm",
    )
    offset = 0
    for gindex, g in enumerate(data["resource_info"]["hcoin_source_list"]):
        hcoin_bar_draw.rounded_rectangle(
            (160 + offset, 78, 160 + offset + g["percent"] * 10, 101),
            radius=0,
            fill=COLOR_LIST[gindex],
        )
        offset += g["percent"] * 10
    img.paste(hcoin_bar, (0, 1843), hcoin_bar)

    resin_bar = Image.open(TEXT_PATH / "resin_bar.png")
    resin_bar_draw = ImageDraw.Draw(resin_bar)
    resin_bar_draw.text(
        (295, 41),
        f"{data['resource_info']['consume_resin']}",
        (252, 80, 80),
        gs_font_50,
        "lm",
    )
    offset = 0
    for gindex, g in enumerate(data["resource_info"]["resin_consume_list"]):
        resin_bar_draw.rounded_rectangle(
            (160 + offset, 78, 160 + offset + g["percent"] * 10, 101),
            radius=0,
            fill=COLOR_LIST[gindex],
        )
        offset += g["percent"] * 10
    img.paste(resin_bar, (0, 1983), resin_bar)

    # 散资源
    for index, resource in enumerate(resource_list):
        resource_bg = await draw_resource_bar(
            resource["title"],
            resource["icon"],
            resource["cur"],
            resource["add"],
        )
        img.paste(
            resource_bg,
            (17 + (index % 3) * 395, 2140 + (index // 3) * 130),
            resource_bg,
        )

    bar4 = Image.open(TEXT_PATH / "bar4.png")
    img.paste(bar4, (0, 2140 + _h + 20), bar4)

    for abyss_index, abyss in enumerate(data["spiral_abyss_info"][:4]):
        abyss_bg = Image.open(TEXT_PATH / "abyss_star.png")
        abyss_bg_draw = ImageDraw.Draw(abyss_bg)
        abyss_bg_draw.rounded_rectangle(
            (112, 24, 201, 48),
            radius=5,
            fill=(186, 31, 31),
        )
        abyss_bg_draw.text(
            (157, 37),
            f"{abyss['name']}",
            (255, 255, 255),
            gs_font_24,
            "mm",
        )
        abyss_bg_draw.text(
            (115, 78),
            f"{abyss['total_star']} / 36",
            (255, 255, 255),
            gs_font_40,
            "lm",
        )
        img.paste(
            abyss_bg,
            (38 + abyss_index * 280, 2140 + _h + 20 + 110),
            abyss_bg,
        )

    for combat_index, combat in enumerate(data["role_combat"]["schedule_list"][:4]):
        combat_bg = Image.open(TEXT_PATH / "combat_star.png")
        combat_bg_draw = ImageDraw.Draw(combat_bg)
        combat_bg_draw.rounded_rectangle(
            (117, 24, 162, 48),
            radius=5,
            fill=(18, 119, 179),
        )
        combat_bg_draw.text(
            (140, 36),
            f"{combat['schedule']['schedule_id']}",
            (255, 255, 255),
            gs_font_24,
            "mm",
        )
        combat_bg_draw.text(
            (117, 78),
            f"{combat['stat']['medal_num']} / 10",
            (255, 255, 255),
            gs_font_40,
            "lm",
        )
        img.paste(
            combat_bg,
            (38 + combat_index * 280, 2140 + _h + 20 + 110 + 125),
            combat_bg,
        )
    img_draw = ImageDraw.Draw(img)
    img_draw.text(
        (600, 527),
        f"统计时间: {now_90.strftime('%Y-%m-%d')} 至 {now.strftime('%Y-%m-%d')}",
        (192, 192, 192),
        gs_font_26,
        "mm",
    )
    img.paste(tag, (1000, 0), tag)

    img = add_footer(img, 1000)
    res = await convert_img(img)
    return res


async def draw_resource_bar(
    title: str,
    icon: Union[Image.Image, str],
    cur: int,
    add: Optional[int] = None,
):
    if isinstance(icon, str):
        icon_path = ICON_PATH / icon.split("/")[-1]
        if not icon_path.exists():
            await download(icon, 8, icon_path.name)
        icon = Image.open(icon_path).convert("RGBA")

    if "神瞳" in title:
        iz = 0.28
    else:
        iz = 0.34

    icon = icon.resize((int(icon.size[0] * iz), int(icon.size[1] * iz)))
    resource_bg = Image.open(TEXT_PATH / "resource_bg.png")

    easy_paste(resource_bg, icon, (70, 61), "cc")

    resource_bg_draw = ImageDraw.Draw(resource_bg)
    resource_bg_draw.text(
        (127, 45),
        title,
        (255, 255, 255),
        gs_font_30,
        "lm",
    )
    resource_bg_draw.text(
        (130, 91),
        f"{cur}",
        (108, 133, 255),
        gs_font_50,
        "lm",
    )
    if add is not None:
        resource_bg_draw.rounded_rectangle(
            (259, 29, 351, 60),
            radius=5,
            fill=(186, 31, 31),
        )
        resource_bg_draw.text(
            (305, 45),
            f"+{add}",
            (255, 255, 255),
            gs_font_28,
            "mm",
        )
    return resource_bg

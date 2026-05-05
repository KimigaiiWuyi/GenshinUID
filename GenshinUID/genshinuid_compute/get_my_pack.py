from typing import Union
from pathlib import Path

from PIL import Image, ImageDraw

from gsuid_core.models import Event
from gsuid_core.utils.cache import gs_cache
from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.ai_core.trigger_bridge import ai_return

from .utils import get_all_char_dict
from ..utils.mys_api import mys_api, get_base_data
from ..utils.image.image_tools import (
    get_v4_bg,
    add_footer,
    get_avatar,
    get_v4_title,
)
from ..utils.fonts.genshin_fonts import gs_font_20
from ..utils.resource.download_url import download
from ..utils.resource.RESOURCE_PATH import ICON_PATH

TEXT_PATH = Path(__file__).parent / "texture2d"


@gs_cache(1800)
async def draw_my_pack(uid: str, ev: Event) -> Union[str, bytes]:
    raw = await get_all_char_dict()
    data = await mys_api.get_batch_compute_info(uid, raw)

    if isinstance(data, int):
        return get_error(data)

    raw_data = await get_base_data(uid)
    if isinstance(raw_data, (str, bytes)):
        return raw_data
    elif isinstance(raw_data, (bytearray, memoryview)):
        return bytes(raw_data)

    # AI 注入：提取背包物品数据
    try:
        overall_consume = data["overall_consume"]
        parts = [f"【UID {uid} 背包物品】共 {len(overall_consume)} 种材料"]
        # 按缺少数量排序，优先展示缺少最多的
        sorted_items = sorted(overall_consume, key=lambda x: x.get("lack_num", 0), reverse=True)
        # 展示缺少材料
        lack_items = [i for i in sorted_items if i.get("lack_num", 0) > 0]
        if lack_items:
            parts.append("  --- 缺少材料 TOP 10 ---")
            for item in lack_items[:10]:
                bag_num = item["num"] - item["lack_num"]
                parts.append(f"  {item.get('name', item['id'])}: 拥有{bag_num}个 缺少{item['lack_num']}个")
        # 展示拥有最多的材料
        parts.append("  --- 拥有最多 TOP 10 ---")
        for item in sorted_items[:10]:
            bag_num = item["num"] - item["lack_num"]
            parts.append(f"  {item.get('name', item['id'])}: {bag_num}个")
        ai_return("\n".join(parts))
    except Exception:
        pass

    char_pic = await get_avatar(ev, 377, False)
    title_img = get_v4_title(char_pic, uid, raw_data)
    # title_img = title_img.resize((int(1680 * 0.6), int(700 * 0.6)))

    overall_consume = data["overall_consume"]
    bag_len = len(overall_consume)

    w = 1680
    n = 14
    up = 713
    h = (((bag_len - 1) // n) + 1) * 145 + up + 92
    ox, oy = 110, 145

    img = get_v4_bg(w, h)

    img.paste(title_img, (0, 0), title_img)

    for index, item in enumerate(overall_consume):
        item_bg = Image.open(TEXT_PATH / "one.png")
        item_name = f"UI_ItemIcon_{item['id']}.png"
        item_path = ICON_PATH / item_name
        if not item_path.exists():
            await download(item["icon"], 8, item_name)
        item_img = Image.open(item_path)
        item_img = item_img.resize((80, 80)).convert("RGBA")
        item_bg.paste(item_img, (15, 20), item_img)
        item_draw = ImageDraw.Draw(item_bg)
        bag_num = item["num"] - item["lack_num"]
        item_draw.text(
            (55, 125),
            f"{bag_num}",
            font=gs_font_20,
            fill="white",
            anchor="mm",
        )
        img.paste(
            item_bg,
            (65 + (index % n) * ox, up + (index // n) * oy),
            item_bg,
        )

    img = add_footer(img)

    return await convert_img(img)

import re
import json
from typing import Tuple

import aiofiles
from PIL import Image

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.ai_core.trigger_bridge import ai_return

from .start import refresh_player_list
from .to_card import enka_to_card
from .to_data import switch_api
from .get_enka_img import draw_enka_img, get_full_char
from ..utils.convert import get_uid
from ..utils.mys_api import mys_api
from ..utils.message import UID_HINT, GButton as Button
from .draw_arti_rank import draw_arti_rank_img
from .draw_char_info import draw_all_char_list
from .draw_role_rank import draw_role_rank_img
from .to_data_by_mys import mys_to_card
from .get_akasha_data import get_rank
from .draw_artifacts_lib import draw_lib
from .draw_new_rank_list import draw_rank_img
from ..utils.image.convert import convert_img
from ..genshinuid_enka.start import check_artifacts_list
from ..utils.map.GS_MAP_PATH import alias_data
from ..genshinuid_config.gs_config import gsconfig
from ..utils.resource.RESOURCE_PATH import TEMP_PATH, PLAYER_PATH

EnableCharCardByMys = gsconfig.get_config("EnableCharCardByMys").data

sv_enka_admin = SV("面板管理", pm=1)
sv_enka_config = SV("面板设置", pm=2)
sv_akasha = SV("排名查询", priority=10)
sv_get_enka = SV("面板查询", priority=10)
sv_get_original_pic = SV("查看面板原图", priority=5)


@sv_akasha.on_command(
    "排名统计",
    to_ai="""查询原神角色排名统计数据

    当用户说"排名统计"、"角色排名数据"时调用。
    以文字形式返回角色排名的统计概览。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_rank_data(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_b564c8", uid=uid))
    result = await get_rank(uid)
    if isinstance(result, str):
        ai_return(result)
    await bot.send(result)


@sv_akasha.on_command(
    "排名列表",
    to_ai="""查询原神角色排名列表

    当用户说"排名列表"、"角色排名排行"时调用。
    以图片形式返回各角色的排名数据列表。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_rank_pic(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_736a67", uid=uid))
    im = await draw_rank_img(ev, uid)
    await bot.send_option(
        im,
        [
            Button("♾️角色排名公子", "角色排名公子"),
            Button("♾️圣遗物双爆排名", "圣遗物排名双爆"),
        ],
    )


@sv_akasha.on_prefix(
    "角色排行榜",
    to_ai="""查看指定角色的全服排行榜数据

    当用户说"角色排行榜 公子"、"角色排行榜 胡桃"时调用。
    以图片形式返回该角色的全服排行榜数据。

    Args:
        text: 角色名称，例如 "公子"、"胡桃"、"甘雨"
              支持角色昵称，例如 "雷神"、"小草神"
    """,
)
async def send_role_rank_pic(bot: Bot, ev: Event):
    msg = "".join(re.findall("[\u4e00-\u9fa5 ]", ev.text))
    if not msg:
        return
    logger.info(t("log.genshinuid.msg_8fd81d", msg=msg))
    a = Button("💖排名列表", "排名列表")
    b = Button(f"✅查询{msg}", f"查询{msg}")
    c = Button(f"💖角色排名{msg}", f"角色排名{msg}")
    d = Button("✅圣遗物排名", "圣遗物排名")

    im = await draw_role_rank_img(msg)
    await bot.send_option(im, [a, c, b, d])


@sv_akasha.on_prefix(
    "角色排名",
    to_ai="""查询指定UID的某个角色在全服的排名

    当用户说"角色排名 公子"、"角色排名 胡桃"时调用。
    以图片形式返回该角色在全服的排名详情。需要用户已绑定UID。

    Args:
        text: 角色名称，例如 "公子"、"胡桃"、"甘雨"
              支持角色昵称，例如 "雷神"、"小草神"
    """,
)
async def send_my_role_rank_pic(bot: Bot, ev: Event):
    msg = "".join(re.findall("[\u4e00-\u9fa5 ]", ev.text))
    if not msg:
        return
    logger.info(t("log.genshinuid.msg_86aa0f", msg=msg))
    a = Button("💖排名列表", "排名列表")
    b = Button(f"✅查询{msg}", f"查询{msg}")
    c = Button(f"💖角色排行榜{msg}", f"角色排行榜{msg}")
    d = Button("✅圣遗物排名", "圣遗物排名")

    msg = msg.replace("附近", "")
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)

    im = await draw_role_rank_img(msg, uid)
    await bot.send_option(im, [a, c, b, d])


@sv_akasha.on_command(
    ("圣遗物排名", "圣遗物排行榜"),
    to_ai="""查看原神圣遗物排名排行榜

    当用户说"圣遗物排名"、"圣遗物排行榜"时调用。
    以图片形式返回圣遗物的排名数据。支持按不同属性排序。

    Args:
        text: 排序方式，例如 "双爆"、"暴击率"、"元素精通"、"暴击伤害"
              留空默认按双爆排序
    """,
)
async def send_arti_rank_pic(bot: Bot, ev: Event):
    # 获取排序名
    msg = "".join(re.findall("[\u4e00-\u9fa5 ]", ev.text))
    logger.info(t("log.genshinuid.msg_3d7d31", msg=msg))
    im = await draw_arti_rank_img(msg)
    await bot.send_option(
        im,
        [
            Button("♾️双爆排名", "圣遗物排名双爆"),
            Button("♾️暴击率排名", "圣遗物排名暴击率"),
            Button("♾️元素精通排名", "圣遗物排名元素精通"),
            Button("♾️暴击伤害排名", "圣遗物排名暴击伤害"),
        ],
    )


@sv_enka_admin.on_fullmatch(
    "刷新全部圣遗物仓库",
    to_ai="""刷新所有用户的圣遗物仓库数据（管理员功能）

    当管理员说"刷新全部圣遗物仓库"时调用。
    为所有用户重新获取圣遗物数据，耗时较长。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_fresh_all_list(bot: Bot, ev: Event):
    await bot.send("开始执行...可能时间较久, 执行完成会有提示, 请勿重复执行!")
    await check_artifacts_list()
    await bot.send("执行完成!")


@sv_get_enka.on_fullmatch(
    ("刷新圣遗物仓库", "强制刷新圣遗物仓库"),
    block=True,
    to_ai="""刷新原神圣遗物仓库数据

    当用户说"刷新圣遗物仓库"、"强制刷新圣遗物仓库"时调用。
    重新获取当前UID的圣遗物数据。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可。是否强制由命令本身决定
    """,
)
async def send_fresh_list(bot: Bot, ev: Event):
    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_1a363b", uid=uid))
    await bot.send(f"UID{uid}开始刷新, 请勿重复触发!")
    if ev.command.startswith("强制"):
        is_force = True
    else:
        is_force = False
    await bot.send(await refresh_player_list(uid, is_force))


@sv_get_enka.on_command(
    "圣遗物仓库",
    to_ai="""查看原神圣遗物仓库列表

    当用户说"圣遗物仓库"、"查看圣遗物"时调用。
    以图片形式返回当前UID的圣遗物仓库列表。需要用户已绑定UID。

    Args:
        text: 可选的页码数字，默认为1，例如 "1"、"2"、"3"
    """,
)
async def send_aritifacts_list(bot: Bot, ev: Event):
    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_3f9f28", uid=uid))

    if ev.text and ev.text.isdigit():
        num = int(ev.text)
        if num == 0:
            num = 1
    else:
        num = 1

    im = await draw_lib(ev, uid, num)
    await bot.send_option(
        im,
        [
            Button("♾️双爆排名", "圣遗物排名双爆"),
            Button("♾️暴击率排名", "圣遗物排名暴击率"),
            Button("♾️元素精通排名", "圣遗物排名元素精通"),
            Button("♾️暴击伤害排名", "圣遗物排名暴击伤害"),
        ],
    )


@sv_get_original_pic.on_fullmatch(
    ("原图"),
    to_ai="""获取上一条消息中图片的原图

    当用户说"原图"时调用。需要先回复一条包含图片的消息。
    返回该图片的原始高清版本。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_original_pic(bot: Bot, ev: Event):
    if ev.reply:
        path = TEMP_PATH / f"{ev.reply}.jpg"
        if path.exists():
            logger.info("[原图]访问图片: {}".format(path))
            with open(path, "rb") as f:
                await bot.send(f.read())


@sv_enka_config.on_fullmatch(
    "切换api",
    to_ai="""切换面板查询使用的API源

    当用户说"切换api"时调用。
    在不同的面板查询API之间切换。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_change_api_info(bot: Bot, ev: Event):
    await bot.send(await switch_api())


@sv_get_enka.on_prefix(
    "查询",
    to_ai="""查询原神角色面板详情（武器、圣遗物、属性等）

    当用户说"查询 公子"、"查询 胡桃"时调用。
    以图片形式返回角色的详细面板数据，包括武器、圣遗物、属性等。需要用户已绑定UID。

    Args:
        text: 角色名称，例如 "公子"、"胡桃"、"甘雨"
              支持角色昵称，例如 "雷神"、"小草神"
              可加"换"后缀切换武器，例如 "公子换"
              可加"六命"前缀提高命座展示，例如 "六命公子"
    """,
)
async def send_char_info(bot: Bot, ev: Event):
    name = ev.text.strip()
    im = await _get_char_info(bot, ev, name)
    if isinstance(im, str):
        await bot.send(im)
    elif isinstance(im, Tuple):
        if isinstance(im[0], Image.Image):
            img = await convert_img(im[0])
        else:
            img = im[0]
        await bot.send_option(
            img,
            [
                Button("🔄更换武器", f"查询{name}换"),
                Button("⏫提高命座", f"查询六命{name}"),
                Button("*️⃣保存面板", f"保存面板{name}为 "),
                Button("🔀对比面板", f"对比面板 {name} "),
            ],
        )
        if im[1]:
            with open(TEMP_PATH / f"{ev.msg_id}.jpg", "wb") as f:
                f.write(im[1])
    elif im is None:
        return
    else:
        await bot.send("发生未知错误")


async def _get_char_info(bot: Bot, ev: Event, text: str):
    # 获取角色名
    msg = "".join(re.findall("[\u4e00-\u9fa5 ]", text))
    if not msg:
        return
    logger.info(t("log.genshinuid.msg_55f82a"))
    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info("[查询角色面板]uid: {}".format(uid))

    im = await draw_enka_img(msg, uid, ev.image)
    return im


@sv_get_enka.on_command(
    "对比面板",
    to_ai="""对比多个原神角色面板配置

    当用户说"对比面板 公子 公子换可莉圣遗物"时调用。
    以图片形式并排对比多个角色/配置的面板数据。

    Args:
        text: 用空格分隔的多个角色/配置名称，2-3个
              例如 "公子 公子换可莉圣遗物"、"胡桃 甘雨"
    """,
)
async def contrast_char_info(bot: Bot, ev: Event):
    if not ev.text.strip():
        return await bot.send("参考格式: 对比面板 公子 公子换可莉圣遗物")
    contrast_list = ev.text.strip().split(" ")
    if len(contrast_list) <= 1:
        return await bot.send("输入格式错误...参考格式: 对比面板 公子 公子换可莉圣遗物")
    elif len(contrast_list) >= 4:
        return await bot.send("不支持对比四个及以上的面板...")

    img_list = []
    max_y = 0
    for i in contrast_list:
        im = await _get_char_info(bot, ev, i)
        if isinstance(im, str):
            return await bot.send(im)
        elif isinstance(im, Tuple):
            data = im[0]
            if isinstance(data, bytes):
                return await bot.send("输入了错误的格式...参考格式: 对比面板 公子 公子换可莉圣遗物")
            elif isinstance(data, str):
                return await bot.send(data)
            else:
                assert isinstance(data, Image.Image)
                img_list.append(data)
                max_y = max(max_y, data.size[1])

    base_img = Image.new("RGBA", (950 * len(img_list), max_y))
    for index, img in enumerate(img_list):
        base_img.paste(img, (950 * index, 0), img)

    await bot.send(await convert_img(base_img))


@sv_get_enka.on_command(
    "保存面板",
    to_ai="""保存当前原神角色面板为自定义名称

    当用户说"保存面板公子为核爆公子"时调用。
    将当前角色面板数据保存为自定义配置，后续可通过"查询 自定义名称"调用。

    Args:
        text: 格式为"角色名为自定义名称"，例如 "公子为核爆公子"、"胡桃为核爆胡桃"
    """,
)
async def save_char_info(bot: Bot, ev: Event):
    if not ev.text.strip():
        return await bot.send("后面需要跟自定义的保存名字\n例如：保存面板公子为核爆公子")
    save_list = ev.text.strip().split("为")
    if len(save_list) <= 1:
        return await bot.send("输入格式错误...参考格式: 保存面板公子为核爆公子")

    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)

    save_char, save_name = save_list[0], save_list[1]

    if bool(re.search(r"\d", save_name)):
        return await bot.send("保存名称内不可存在数字!")

    if save_name in alias_data:
        return await bot.send("保存名称不可为已有角色的名称!")
    else:
        for _fix in [
            "队伍",
            "最佳",
            "最优",
            "曲线",
            "成长",
            "展柜",
            "伤害",
            "角色",
            "极限",
            "带",
            "换",
        ]:
            if _fix in save_name:
                return await bot.send(f"保存名称不能含有【{_fix}】等保留词...")

        for _name in alias_data:
            if save_name in alias_data[_name]:
                return await bot.send("保存名称不可为已有角色的别名!")
        else:
            char_data = await get_full_char(save_char, uid)
            if isinstance(char_data, str):
                return await bot.send(char_data)
            SELF_PATH = PLAYER_PATH / str(uid) / "SELF"
            if not SELF_PATH.exists():
                SELF_PATH.mkdir()
            path = SELF_PATH / f"{save_name}.json"
            async with aiofiles.open(path, "wb") as file:
                await file.write(json.dumps(char_data).encode("utf-8"))
            return await bot.send_option(
                f"保存成功!你可以使用[查询{save_name}]调用该面板!",
                [
                    Button(f"✅查询{save_name}", f"查询{save_name}"),
                    Button("💖刷新面板", "刷新面板"),
                ],
            )


@sv_get_enka.on_command(
    (
        "强制刷新",
        "刷新面板",
        "mys强制刷新",
        "enka强制刷新",
        "mys刷新面板",
        "enka刷新面板",
    ),
    to_ai="""刷新原神角色面板数据

    当用户说"刷新面板"、"强制刷新"时调用。
    从enka或米游社重新获取角色面板数据。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可。数据源由命令本身决定：
              - "刷新面板"/"强制刷新"：自动选择数据源
              - "mys刷新面板"/"mys强制刷新"：从米游社获取
              - "enka刷新面板"/"enka强制刷新"：从enka获取
    """,
)
async def send_card_info(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info("[强制刷新]uid: {}".format(uid))

    is_force = "强制刷新" in ev.command
    if "mys" in ev.command:
        im = await mys_to_card(uid, force_refresh=is_force)
    elif "enka" in ev.command:
        im = await enka_to_card(uid)
    else:
        owner_ck = await mys_api.get_ck(uid, "OWNER")
        if is_force and owner_ck is not None:
            im = await mys_to_card(uid, force_refresh=True)
            if not isinstance(im, Tuple):
                logger.info(f"从米游社获取数据失败，尝试从enka获取。{im}")
                im = await enka_to_card(uid)
        elif EnableCharCardByMys:
            im = await mys_to_card(uid)
            if not isinstance(im, Tuple):
                logger.info(t("log.genshinuid.enka_im_06dd12", im=im))
                im = await enka_to_card(uid)
        else:
            im = await enka_to_card(uid)

    if isinstance(im, Tuple):
        buttons = [Button(f"✅查询{i['avatarName']}", f"查询{i['avatarName']}") for i in im[1]]
        buttons.append(Button("📦圣遗物仓库", "圣遗物仓库"))
        buttons.append(Button("💖排名列表", "排名列表"))
        await bot.send_option(im[0], buttons)
    else:
        await bot.send(im)


@sv_get_enka.on_command(
    ("角色橱窗"),
    to_ai="""查看原神角色橱窗列表

    当用户说"角色橱窗"、"角色列表"时调用。
    以图片形式返回当前UID的全部角色橱窗展示。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_char_detail_list(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_all_char_list(str(uid))
    logger.info(t("log.genshinuid.uid_uid_e7b254", uid=uid))
    await bot.send(im)

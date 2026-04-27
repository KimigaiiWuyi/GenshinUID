"""
GenshinUID AI Tools 注册模块

为AI提供原神相关查询功能的工具集
"""

from io import BytesIO
from typing import Union

from PIL import Image
from pydantic_ai import RunContext

from gsuid_core.bot import Bot
from gsuid_core.ai_core.models import ToolContext
from gsuid_core.ai_core.register import ai_tools
from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.database.models import GsBind

from ..utils.mys_api import mys_api

# 导入现有功能模块
from ..genshinuid_note.note_text import award as get_monthly_award
from ..genshinuid_enka.get_enka_img import draw_enka_img
from ..genshinuid_cale.draw_cale_pic import draw_cale_img
from ..genshinuid_abyss.draw_abyss_card import draw_abyss_img
from ..genshinuid_season_post.draw_season_post import get_season_post_draw
from ..genshinuid_poetry_abyss.draw_poetry_abyss import draw_poetry_abyss_img
from ..genshinuid_hard_challenge.draw_hard_challenge import draw_hard_challenge_img


def convert_img(img: Image.Image) -> bytes:
    """将PIL图片转换为bytes"""
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def send_image(bot: Bot, im: Union[Image.Image, tuple, bytes, str]) -> None:
    """发送图片，处理bytes/Image/str等不同类型"""
    if isinstance(im, Image.Image):
        await bot.send(convert_img(im))
    elif isinstance(im, tuple):
        img_data = im[0]
        if isinstance(img_data, Image.Image):
            await bot.send(convert_img(img_data))
        elif isinstance(img_data, bytes):
            await bot.send(img_data)
        else:
            await bot.send(img_data)
    else:
        await bot.send(im)


async def get_uid_from_ctx(ctx: RunContext[ToolContext]) -> str:
    """从上下文中获取用户UID"""
    ev = ctx.deps.ev
    bot = ctx.deps.bot
    if ev is None or bot is None:
        raise ValueError("无法获取用户信息")

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        raise ValueError("用户未绑定UID，请先绑定")
    return uid


def _parse_resin_time(recovery_time_str: str) -> tuple[int, int]:
    """解析树脂恢复时间字符串，返回(小时, 分钟)"""
    if not recovery_time_str.isdigit():
        return 0, 0
    seconds = int(recovery_time_str)
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    return hours, mins


def _format_expedition_status(expeditions: list) -> tuple[int, int]:
    """解析派遣状态，返回(进行中数量, 总数量)"""
    total = len(expeditions)
    ongoing = 0
    for e in expeditions:
        if isinstance(e, dict) and e.get("status") == "Ongoing":
            ongoing += 1
    return ongoing, total


@ai_tools(category="common")
async def get_resin_status(
    ctx: RunContext[ToolContext],
) -> str:
    """
    获取玩家当前体力/树脂状态

    返回玩家的当前树脂、树脂上限、浓缩树脂、洞天力等实时数据。
    AI在用户询问"还有多少体力"、"树脂满了没"时调用此工具。

    Returns:
        体力状态文本，包含当前树脂/上限、浓缩树脂数量、洞天力和宝钱等
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    data = await mys_api.get_widget_resin_data(uid)
    if isinstance(data, int):
        return f"获取体力数据失败: {get_error(data)}"

    if not isinstance(data, dict):
        return "体力数据格式错误"

    # 解析体力数据 - API直接返回顶层字段
    current_resin = data.get("current_resin", 0)
    max_resin = data.get("max_resin", 160)
    resin_recovery_time = data.get("resin_recovery_time", "0")

    # 计算树脂恢复时间
    hours, mins = _parse_resin_time(resin_recovery_time)
    full_time = ""
    if isinstance(current_resin, int) and isinstance(max_resin, int) and current_resin >= max_resin:
        full_time = "（已满）"
    elif hours > 0 or mins > 0:
        full_time = f"（预计{hours}小时{mins}分后满）"

    # 浓缩树脂 - 通过 transformer 获取
    transformer = data.get("transformer", {})
    condenser_resin_text = "无"
    if isinstance(transformer, dict) and transformer.get("obtained", False):
        condenser_resin_text = transformer.get("latest_job_id", "可用")

    # 洞天宝钱
    current_home_coin = data.get("current_home_coin", 0)
    max_home_coin = data.get("max_home_coin", 2400)

    # 派遣状态
    expeditions = data.get("expeditions", [])
    if isinstance(expeditions, list):
        ongoing, total = _format_expedition_status(expeditions)
    else:
        ongoing, total = 0, 0

    # 每日任务完成情况
    finished_task_num = data.get("finished_task_num", 0)
    total_task_num = data.get("total_task_num", 0)
    task_status = f"{finished_task_num}/{total_task_num}"

    return f"""【树脂状态】
当前树脂: {current_resin}/{max_resin} {full_time}
浓缩树脂: {condenser_resin_text}

【洞天宝钱】
当前: {current_home_coin}/{max_home_coin}

【派遣】
进行中: {ongoing}/{total}个

【每日委托】
完成: {task_status}"""


def _convert_timestamp(timestamp: int) -> str:
    """将时间戳转换为人类可读字符串"""
    days = timestamp // (24 * 3600)
    hours = (timestamp % (24 * 3600)) // 3600
    minutes = (timestamp % 3600) // 60
    if days > 0:
        return f"{days}天{hours}时{minutes}分"
    return f"{hours}时{minutes}分"


@ai_tools(category="common")
async def get_calendar_activities(
    ctx: RunContext[ToolContext],
) -> str:
    """
    获取当前活动/日历信息

    返回游戏内所有活动、任务、周常的状态和剩余时间。
    AI在用户询问"最近有什么活动"、"周本做了没"、"委托完成了吗"时调用。

    Returns:
        活动日历文本，包含所有活动的状态和倒计时
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    data = await mys_api.get_calendar_data(uid)
    if isinstance(data, int):
        return f"获取活动数据失败: {get_error(data)}"

    if not isinstance(data, dict):
        return "活动数据格式错误"

    act_list = data.get("act_list", [])
    if not isinstance(act_list, list) or len(act_list) == 0:
        return "暂无活动数据"

    result = "【活动日历】\n\n"

    # 分类展示
    ongoing: list[str] = []
    upcoming: list[str] = []
    weekly: list[str] = []

    for act in act_list:
        if not isinstance(act, dict):
            continue
        name = act.get("name", "未知")
        status = act.get("status", 0)
        countdown = act.get("countdown_seconds", 0)
        is_finished = act.get("is_finished", False)
        act_type = act.get("type", "")

        if status == 2:  # 进行中
            if "Weekly" in act_type or "周" in name:
                status_text = "✅已完成" if is_finished else "❌未完成"
                weekly.append(f"• {name}: {status_text}")
            else:
                time_text = _convert_timestamp(countdown)
                if is_finished:
                    status_text = "✅已完成"
                else:
                    status_text = f"⏳剩余 {time_text}"
                ongoing.append(f"• {name}: {status_text}")
        else:  # 未开始
            time_text = _convert_timestamp(countdown)
            upcoming.append(f"• {name}: 距开启 {time_text}")

    if ongoing:
        result += "【进行中】\n" + "\n".join(ongoing) + "\n\n"
    if weekly:
        result += "【周常任务】\n" + "\n".join(weekly) + "\n\n"
    if upcoming:
        result += "【即将开始】\n" + "\n".join(upcoming[:5])

    return result


@ai_tools(category="common")
async def check_weekly_tasks(
    ctx: RunContext[ToolContext],
) -> str:
    """
    检查周常任务完成状态

    返回本周周本、深境螺旋、幻想真境剧诗等周常的完成情况。
    AI在用户询问"周本打了没"、"这周深渊打了吗"、"新深渊完成了吗"时调用。

    Returns:
        周常任务完成状态文本
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    # 获取深渊数据
    abyss_data = await mys_api.get_poetry_abyss_data(uid)

    result = "【周常完成状态】\n\n"

    # 深渊（幻想真境剧诗）
    if isinstance(abyss_data, dict):
        seasons = abyss_data.get("seasons", [])
        if isinstance(seasons, list) and len(seasons) > 0:
            latest_season = seasons[-1]
            if isinstance(latest_season, dict):
                schedule_name = latest_season.get("schedule_name", "未知")
                battle_time = latest_season.get("battle_time", 0)
                # 0=未开启 1=已解锁(进行中) 2=已结束(可领取) 3=已结束(已领取)
                if battle_time == 0:
                    status = "❌ 未开启"
                elif battle_time == 1:
                    status = "🔄 进行中"
                elif battle_time == 2:
                    status = "✅ 可领取"
                else:
                    status = "✅ 已完成"
                result += f"• 幻想真境剧诗({schedule_name}): {status}"

    # 获取旧深渊状态
    old_abyss_data = await mys_api.get_poetry_abyss_data(uid, active=2)
    if isinstance(old_abyss_data, dict):
        result += "\n• 深境螺旋: 上期已完成"

    return result


@ai_tools(category="common")
async def send_abyss_overview_image(
    ctx: RunContext[ToolContext],
    floor: str = "12",
) -> str:
    """
    发送深渊攻略图

    返回玩家的指定层数的深渊记录信息。
    AI在用户询问"我当期的深渊记录"、"12层深渊"、时调用。

    Args:
        floor: 深渊层数，可选 "9", "10", "11", "12"（默认"12"）

    Returns:
        深渊攻略图
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    # 处理层数参数
    floor_mapping = {"九": "9", "十": "10", "十一": "11", "十二": "12"}
    floor_num = floor_mapping.get(floor, floor)

    if floor_num not in ["9", "10", "11", "12"]:
        floor_num = "12"

    # 绘制深渊图片
    im = await draw_abyss_img(ev, uid, int(floor_num), "1")
    await send_image(bot, im)
    return f"✅ 已发送第{floor_num}层深渊攻略图"


@ai_tools(category="common")
async def get_character_build_info(
    ctx: RunContext[ToolContext],
    character_name: str,
) -> str:
    """
    查询角色培养/练度信息

    返回指定角色的详细培养信息，包括等级、天赋、武器、圣遗物等。
    AI在用户询问某个角色"练度如何"、"培养得怎么样"、"圣遗物好不好"时调用。

    Args:
        character_name: 角色名称，如"雷电将军"、"胡桃"

    Returns:
        角色练度详细信息文本
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    # 绘制角色信息图片
    im = await draw_enka_img(character_name, uid, None)
    if im is not None:
        await send_image(bot, im)
        return f"✅ 已发送角色{character_name}的详细信息"
    return f"未找到角色: {character_name}"


@ai_tools(category="common")
async def get_monthly_stats(
    ctx: RunContext[ToolContext],
) -> str:
    """
    获取玩家札记/月度统计

    返回本月和上月的原石、摩拉收入情况。
    AI在用户询问"这个月多少原石"、"原石收入统计"、"摩拉收入"时调用。

    Returns:
        月度原石摩拉收入统计
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    result = await get_monthly_award(uid)
    if isinstance(result, bytes):
        return "月度统计数据（图片格式）"
    return result


@ai_tools(category="common")
async def send_activity_calendar_image(
    ctx: RunContext[ToolContext],
) -> str:
    """
    发送完整活动日历图

    返回游戏内所有活动的日历图片。
    AI在用户询问"活动有什么"、"最近活动一览"、"日历"时调用。

    Returns:
        活动日历图片
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    im = await draw_cale_img(ev, uid)
    await send_image(bot, im)
    return "✅ 已发送活动日历图"


@ai_tools(category="common")
async def send_season_report_image(
    ctx: RunContext[ToolContext],
) -> str:
    """
    发送原神季报图片

    返回玩家近期的游戏数据报告，包含深渊、使用角色、素材等信息。
    AI在用户询问"季报"、"数据报告"、"游戏报告"时调用。

    Returns:
        季报图片
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    im = await get_season_post_draw(uid, ev)
    await send_image(bot, im)
    return "✅ 已发送季报图片"


@ai_tools(category="common")
async def get_poetry_abyss_status(
    ctx: RunContext[ToolContext],
) -> str:
    """
    获取幻想真境剧诗（新深渊）状态

    返回玩家当前或上期幻想真境剧诗的完成情况。
    AI在用户询问"新深渊"、"剧诗"、"幻想真境"时调用。

    Returns:
        幻想真境剧诗状态信息
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    im = await draw_poetry_abyss_img(uid, ev, None)
    await send_image(bot, im)
    return "✅ 已发送幻想真境剧诗信息"


@ai_tools(category="common")
async def get_hard_challenge_status(
    ctx: RunContext[ToolContext],
) -> str:
    """
    获取幽境危战状态

    返回玩家当前幽境危战的完成情况和挑战记录。
    AI在用户询问"幽境危战"、"新新深渊"、"肃靖险乱"时调用。

    Returns:
        幽境危战状态信息
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    im = await draw_hard_challenge_img(uid, ev)
    await send_image(bot, im)
    return "✅ 已发送幽境危战信息"


@ai_tools(category="default")
async def search_character_info(
    ctx: RunContext[ToolContext],
    query: str,
) -> str:
    """
    搜索角色信息

    根据关键词搜索角色信息，返回角色名称、元素、职业等基础信息。
    AI在用户询问角色基础信息时调用。

    Args:
        query: 角色名称关键词

    Returns:
        角色基础信息
    """
    # 角色信息映射（简化版）
    characters = {
        "雷电将军": {"element": "雷", "weapon": "长枪", "rarity": "5", "region": "稻妻"},
        "纳西妲": {"element": "草", "weapon": "法器", "rarity": "5", "region": "须弥"},
        "温迪": {"element": "风", "weapon": "弓箭", "rarity": "5", "region": "蒙德"},
        "钟离": {"element": "岩", "weapon": "长枪", "rarity": "5", "region": "璃月"},
        "胡桃": {"element": "火", "weapon": "长枪", "rarity": "5", "region": "璃月"},
        "甘雨": {"element": "冰", "weapon": "弓箭", "rarity": "5", "region": "璃月"},
        "神里绫华": {"element": "冰", "weapon": "单手剑", "rarity": "5", "region": "稻妻"},
        "宵宫": {"element": "火", "weapon": "弓", "rarity": "5", "region": "稻妻"},
        "枫原万叶": {"element": "风", "weapon": "单手剑", "rarity": "5", "region": "稻妻"},
        "荒泷一斗": {"element": "岩", "weapon": "双手剑", "rarity": "5", "region": "稻妻"},
    }

    # 模糊匹配
    for name, info in characters.items():
        if query in name or name in query:
            return f"""【{name}】
元素: {info["element"]}
武器: {info["weapon"]}
稀有度: {info["rarity"]}星
地区: {info["region"]}"""

    return f"未找到角色: {query}，请确认角色名称是否正确"


@ai_tools(category="default")
async def get_expedition_status(
    ctx: RunContext[ToolContext],
) -> str:
    """
    获取派遣状态

    返回当前所有洞天派遣的状态和完成时间。
    AI在用户询问"派遣"、"派遣完成了吗"时调用。

    Returns:
        派遣状态信息
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    data = await mys_api.get_widget_resin_data(uid)
    if isinstance(data, int):
        return f"获取派遣数据失败: {get_error(data)}"

    if not isinstance(data, dict):
        return "派遣数据格式错误"

    expeditions = data.get("expeditions", [])
    if not isinstance(expeditions, list):
        return "暂无派遣信息"

    if len(expeditions) == 0:
        return "暂无派遣信息"

    result = "【派遣状态】\n\n"

    for exp in expeditions:
        if not isinstance(exp, dict):
            continue
        avatar_side_icon = exp.get("avatar_side_icon", "")
        status = exp.get("status", "Unknown")

        if status == "Ongoing":
            status_text = "进行中"
        elif status == "Finished":
            status_text = "✅ 可领取"
        else:
            status_text = "未知"

        # 尝试从头像URL提取角色名
        char_name = avatar_side_icon.split("/")[-1].replace(".png", "") if avatar_side_icon else "未知"

        result += f"• 角色{char_name}: {status_text}\n"

    return result


@ai_tools(category="common")
async def get_character_training_stats(
    ctx: RunContext[ToolContext],
) -> str:
    """
    获取角色练度/毕业度统计

    返回玩家所有角色的等级、技能等级、武器等级、圣遗物练度等详细信息。
    AI在用户询问"我的角色练度"、"毕业度统计"、"所有角色培养情况"时调用。

    Returns:
        角色练度统计数据文本
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    import json

    import aiofiles

    from ..utils.resource.RESOURCE_PATH import PLAYER_PATH

    uid_fold = PLAYER_PATH / str(uid)
    if not uid_fold.exists():
        return "⚠️ 暂无角色数据，请先使用【强制刷新】进行数据缓存"

    char_file_list = uid_fold.glob("*")
    char_list = []
    for i in char_file_list:
        file_name = i.name
        if "\u4e00" <= file_name[0] <= "\u9fff":
            char_list.append(file_name.split(".")[0])

    if not char_list:
        return "⚠️ 暂无已缓存的角色数据，请先使用【强制刷新】进行刷新"

    result = f"【角色练度统计】共 {len(char_list)} 个角色\n\n"

    char_stats = []
    for char_name in char_list:
        temp = {}
        char_file = uid_fold / f"{char_name}.json"
        async with aiofiles.open(char_file, "r", encoding="UTF-8") as f:
            raw_data = json.loads(await f.read())

        temp["char_name"] = char_name
        temp["id"] = raw_data.get("avatarId", 0)
        temp["char_level"] = raw_data.get("avatarLevel", 0)
        temp["char_element"] = raw_data.get("avatarElement", "未知")
        temp["constellation"] = len(raw_data.get("talentList", []))

        skill_list = raw_data.get("avatarSkill", [])
        if len(skill_list) >= 3:
            temp["a_skill_level"] = skill_list[0].get("skillLevel", 0)
            temp["e_skill_level"] = skill_list[1].get("skillLevel", 0)
            temp["q_skill_level"] = skill_list[-1].get("skillLevel", 0)
        else:
            temp["a_skill_level"] = 0
            temp["e_skill_level"] = 0
            temp["q_skill_level"] = 0

        temp["talent_num"] = len(raw_data.get("talentList", []))

        weapon_info = raw_data.get("weaponInfo", {})
        temp["weapon_name"] = weapon_info.get("weaponName", "未知")
        temp["weapon_level"] = weapon_info.get("weaponLevel", 0)
        temp["weapon_affix"] = weapon_info.get("weaponAffix", 0)
        temp["weapon_star"] = weapon_info.get("weaponStar", 0)

        from ..genshinuid_enka.etc.etc import get_all_artifacts_value
        from ..genshinuid_enka.mono.Character import Character as CharClass

        char_obj = CharClass(raw_data)
        await char_obj.new()
        await char_obj.get_fight_prop()

        temp["value"] = await get_all_artifacts_value(
            raw_data,
            char_obj.baseHp,
            char_obj.baseAtk,
            char_obj.baseDef,
            char_name,
        )
        temp["value"] = float("{:.2f}".format(temp["value"]))

        char_stats.append(temp)

    char_stats.sort(key=lambda x: (-x["value"]))

    for i, char in enumerate(char_stats, 1):
        result += f"{i}. {char['char_name']} (Lv.{char['char_level']} "
        "{char['char_element']}元素, {char['constellation']}命)\n"
        result += f"   技能: A{char['a_skill_level']} E{char['e_skill_level']} Q{char['q_skill_level']}\n"
        result += f"   武器: {char['weapon_name']} Lv.{char['weapon_level']} "
        "(精{char['weapon_affix']}, {char['weapon_star']}星)\n"
        result += f"   圣遗物: {char['value']:.2f}分\n"

    if len(char_stats) > 20:
        result += f"\n...还有 {len(char_stats) - 20} 个角色未显示"

    return result


@ai_tools(category="common")
async def get_daily_materials(
    ctx: RunContext[ToolContext],
    day_offset: int = 0,
) -> str:
    """
    获取今日/明日/后日材料信息

    返回指定日期的材料副本信息，包括可获取的角色升级材料、武器突破材料等。
    AI在用户询问"今天什么材料"、"明日材料"、"后天素材"时调用。

    Args:
        day_offset: 日期偏移，0=今天(默认), 1=明天, 2=后天, -1=昨天

    Returns:
        每日材料文本数据
    """
    ev = ctx.deps.ev
    bot = ctx.deps.bot

    if ev is None or bot is None:
        return "无法获取用户信息"

    from datetime import datetime, timedelta

    from ..genshinuid_dailycost.get_daily_data import generate_daily_data

    weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]

    now = datetime.now()
    target_date = now + timedelta(days=day_offset)
    target_weekday = target_date.weekday()
    target_wk = weekdays[target_weekday]

    if day_offset == 0:
        date_hint = "今天"
    elif day_offset == 1:
        date_hint = "明天"
    elif day_offset == 2:
        date_hint = "后天"
    elif day_offset == -1:
        date_hint = "昨天"
    else:
        date_hint = f"{day_offset}天后"

    if target_wk == "周日":
        return f"{date_hint}({target_wk})所有材料都能获得，无需特别刷取！"

    data = await generate_daily_data()
    if data is None:
        return "获取材料信息失败，请稍后重试"

    if data == {}:
        return f"{date_hint}({target_wk})所有材料都能获得！"

    result = f"【{date_hint}材料】({target_wk})\n\n"

    domain_mapping = {
        "炼武": "武器突破",
        "修炼": "角色突破",
    }

    for domain, items in data.items():
        domain_type = "其他"
        for key, desc in domain_mapping.items():
            if key in domain:
                domain_type = desc
                break

        result += f"【{domain_type}】{domain}\n"

        material_items = [item for item in items if isinstance(item, dict)]
        for item in material_items[:4]:
            item_name = item.get("name", "未知")
            # item_id = item.get("id", 0)
            result += f"  • {item_name}\n"

        result += "\n"

    return result

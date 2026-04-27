"""
GenshinUID AI Tools 注册模块

为AI提供原神相关查询功能的工具集
"""

from io import BytesIO
from typing import Dict, List

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


async def send_image(bot: Bot, im) -> None:
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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None
    if ev is None or bot is None:
        raise ValueError("无法获取用户信息")

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        raise ValueError("用户未绑定UID，请先绑定")
    return uid


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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    data = await mys_api.get_widget_resin_data(uid)
    if isinstance(data, int):
        return f"获取体力数据失败: {get_error(data)}"

    # 解析体力数据
    resin = data.get("resin", {}) if isinstance(data, dict) else {}
    current_resin = resin.get("current_resin", 0)
    max_resin = resin.get("max_resin", 160)

    # 计算树脂溢出情况
    overflow = current_resin - max_resin
    full_time = ""
    if overflow > 0:
        # 树脂溢出，每8分钟回复1点
        recovery_minutes = overflow * 8
        hours = recovery_minutes // 60
        mins = recovery_minutes % 60
        full_time = f"（溢出+{overflow}，预计{hours}小时{mins}分后到达上限）"
    elif current_resin >= max_resin:
        full_time = "（已满）"
    else:
        remaining = max_resin - current_resin
        recovery_minutes = remaining * 8
        hours = recovery_minutes // 60
        mins = recovery_minutes % 60
        full_time = f"（预计{hours}小时{mins}分后满）"

    # 浓缩树脂
    resin_coin = data.get("resin_coin", {}) if isinstance(data, dict) else {}
    condenser_resin = resin_coin.get("current_resin_coin", 0)

    # 洞天力和宝钱
    time_robot = data.get("time_robot", {}) if isinstance(data, dict) else {}
    adeptal_energy = time_robot.get("current_adeptal_energy", 0)
    max_adeptal = time_robot.get("max_adeptal_energy", 2400)

    # 派遣状态
    expedition_info = data.get("expedition", []) if isinstance(data, dict) else []
    ongoing_expeditions = len([e for e in expedition_info if e.get("status") == "Ongoing"])

    return f"""【树脂状态】
当前树脂: {current_resin}/{max_resin} {full_time}
浓缩树脂: {condenser_resin}个

【洞天力】
当前: {adeptal_energy}/{max_adeptal}

【派遣】
进行中: {ongoing_expeditions}个"""


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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None

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

    if not act_list:
        return "暂无活动数据"

    def convert_timestamp_to_string(timestamp: int) -> str:
        days = timestamp // (24 * 3600)
        hours = (timestamp % (24 * 3600)) // 3600
        minutes = (timestamp % 3600) // 60
        if days > 0:
            return f"{days}天{hours}时{minutes}分"
        return f"{hours}时{minutes}分"

    result = "【活动日历】\n\n"

    # 分类展示
    ongoing: List[str] = []  # 进行中
    upcoming: List[str] = []  # 即将开始
    weekly: List[str] = []  # 周常任务

    for act in act_list:
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
                time_text = convert_timestamp_to_string(countdown)
                if is_finished:
                    status_text = "✅已完成"
                else:
                    status_text = f"⏳剩余 {time_text}"
                ongoing.append(f"• {name}: {status_text}")
        else:  # 未开始
            time_text = convert_timestamp_to_string(countdown)
            upcoming.append(f"• {name}: 距开启 {time_text}")

    if ongoing:
        result += "【进行中】\n" + "\n".join(ongoing) + "\n\n"
    if weekly:
        result += "【周常任务】\n" + "\n".join(weekly) + "\n\n"
    if upcoming:
        result += "【即将开始】\n" + "\n".join(upcoming[:5])  # 限制显示数量

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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None

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
        if seasons:
            latest_season = seasons[-1]
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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None

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

    try:
        # 绘制深渊图片
        im = await draw_abyss_img(ev, uid, int(floor_num), "1")
        await send_image(bot, im)
        return f"✅ 已发送第{floor_num}层深渊攻略图"
    except Exception as e:
        return f"生成深渊攻略图失败: {str(e)}"


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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    try:
        # 绘制角色信息图片
        im = await draw_enka_img(character_name, uid, None)
        if im is not None:
            await send_image(bot, im)
            return f"✅ 已发送角色{character_name}的详细信息"
        return f"未找到角色: {character_name}"
    except Exception as e:
        return f"获取角色信息失败: {str(e)}"


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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    try:
        result = await get_monthly_award(uid)
        if isinstance(result, bytes):
            return "月度统计数据（图片格式）"
        return result
    except Exception as e:
        return f"获取月度统计失败: {str(e)}"


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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    try:
        im = await draw_cale_img(ev, uid)
        await send_image(bot, im)
        return "✅ 已发送活动日历图"
    except Exception as e:
        return f"生成活动日历失败: {str(e)}"


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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    try:
        im = await get_season_post_draw(uid, ev)
        await send_image(bot, im)
        return "✅ 已发送季报图片"
    except Exception as e:
        return f"生成季报失败: {str(e)}"


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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    try:
        im = await draw_poetry_abyss_img(uid, ev, None)
        await send_image(bot, im)
        return "✅ 已发送幻想真境剧诗信息"
    except Exception as e:
        return f"获取新深渊信息失败: {str(e)}"


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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None

    if ev is None or bot is None:
        return "无法获取用户信息"

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return "⚠️ 请先绑定UID：发送 /绑定 你的UID"

    try:
        im = await draw_hard_challenge_img(uid, ev)
        await send_image(bot, im)
        return "✅ 已发送幽境危战信息"
    except Exception as e:
        return f"获取幽境危战信息失败: {str(e)}"


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
    characters: Dict[str, Dict[str, str]] = {
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
    ev = ctx.deps.ev if ctx.deps else None
    bot = ctx.deps.bot if ctx.deps else None

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

    expedition_list = data.get("expedition", [])

    if not expedition_list:
        return "暂无派遣信息"

    result = "【派遣状态】\n\n"

    for exp in expedition_list:
        avatar_side_icon = exp.get("avatar_side_icon", "")
        status = exp.get("status", "Unknown")
        remaining_seconds = exp.get("remaining_seconds", 0)

        # 计算剩余时间
        hours = remaining_seconds // 3600
        mins = (remaining_seconds % 3600) // 60

        if status == "Ongoing":
            status_text = f"进行中（剩余{hours}时{mins}分）"
        elif status == "Finished":
            status_text = "✅ 可领取"
        else:
            status_text = "未知"

        # 尝试从头像URL提取角色名
        char_name = avatar_side_icon.split("/")[-1].replace(".png", "") if avatar_side_icon else "未知"

        result += f"• 角色{char_name}: {status_text}\n"

    return result

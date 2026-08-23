"""原神用户侧通用数据：UID、账号概览、角色箱、面板详情、圣遗物仓。"""

from __future__ import annotations

from typing import Optional

from pydantic_ai import RunContext

from gsuid_core.logger import logger
from gsuid_core.ai_core.models import ToolContext
from gsuid_core.ai_core.register import ai_tools
from gsuid_core.utils.error_reply import UID_HINT, CHAR_HINT
from gsuid_core.utils.api.mys.models import IndexData, MihoyoAvatar
from gsuid_core.utils.database.models import GsBind

from ._common import (
    pct,
    as_int,
    as_str,
    as_float,
    is_master,
    valid_uid,
    element_zh,
    player_dir,
    resolve_uid,
    load_json_obj,
    weapon_type_zh,
    char_weapon_type,
    list_cached_char_paths,
)
from ..utils.message import PREFIX
from ..utils.mys_api import get_base_data
from ..genshinuid_enka.get_enka_img import get_char_data

_CTX = ["原神", "Genshin", "游戏"]
_DOMAIN = "原神面板"
_COVER_UID = ["查询当前用户已绑定的原神 UID 列表与默认号"]
_COVER_PLAYER = ["查询原神账号冒险等阶、世界等级、成就、深渊层数、角色数量"]
_COVER_BOX = [
    "查询原神角色列表文本：有 Cookie 为全角色箱，否则仅为展柜缓存（最多12名，非完整箱）",
]
_COVER_DETAIL = ["查询原神单角色面板数值文本（双暴/充能/天赋/圣遗物词条），不出图"]
_COVER_ARTI = ["查询已缓存角色身上的圣遗物文本：部位、套装、主副词条（非游戏全部背包）"]

_SHOWCASE_HINT = (
    "这不是完整角色箱。下列来自游戏内「角色展柜」缓存，展柜最多 12 名，"
    "不能当成账号全部角色。若要看未上展柜的角色：请先在游戏内更换展柜，"
    "再发送「{prefix}强制刷新」。绑定 Cookie 后本工具可改走米游社全角色箱。"
)


def _ev(ctx: RunContext[ToolContext]):
    return ctx.deps.ev if ctx and ctx.deps else None


async def _need_uid(ctx: RunContext[ToolContext], uid: str) -> tuple[str, str]:
    raw = uid.strip()
    found = await resolve_uid(_ev(ctx), raw)
    if found:
        return found, ""
    if raw:
        if not valid_uid(raw):
            return "", "uid 须为 9 位数字"
        return "", "该 UID 不属于当前用户（仅主人可查他人）"
    return "", UID_HINT


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain=_DOMAIN,
    covers=_COVER_UID,
    aliases=["原神·绑定UID", "原神·我的UID"],
)
async def get_user_genshin_uids(
    ctx: RunContext[ToolContext],
    target_user_id: Optional[str] = None,
) -> str:
    """查询用户已绑定的原神 UID 列表与当前默认号。

    仅当用户问「绑了哪个 UID / 有几个号 / 默认 UID」时调用。不查出图、不列角色。

    Args:
        target_user_id: 可选，要查的平台 user_id。留空则查当前对话发起者；查别人仅主人可用。
    """
    ev = _ev(ctx)
    if ev is None:
        return "无法获取当前对话 Event"
    if target_user_id and str(target_user_id) != str(ev.user_id) and not is_master(ev):
        return "仅主人可查询他人绑定，普通用户请留空 target_user_id 查自己"
    uid_q = target_user_id or ev.user_id
    uid_list = await GsBind.get_uid_list_by_game(uid_q, ev.bot_id)
    if uid_list is None or not uid_list:
        return f"user_id={uid_q} 未绑定原神 UID。提示用户发送 `{PREFIX}绑定uid` 后跟 9 位数字。"
    default_uid = await GsBind.get_uid_by_game(uid_q, ev.bot_id)
    lines = [f"user_id={uid_q} 已绑定 {len(uid_list)} 个原神 UID:"]
    for item in uid_list:
        flag = "（默认）" if item == default_uid else ""
        lines.append(f"- {item}{flag}")
    return "\n".join(lines)


def _format_index_player(uid: str, data: IndexData) -> str:
    role = data["role"]
    stats = data["stats"]
    lines = [
        f"UID {uid} 账号概览 [source=mys_index]",
        f"昵称：{role['nickname']}  冒险等阶：{role['level']}  服务器：{role['region']}",
        f"活跃天数：{stats['active_day_number']}  成就：{stats['achievement_number']}  "
        f"角色数：{stats['avatar_number']}  满好感：{stats['full_fetter_avatar_num']}",
        f"深渊：{stats['spiral_abyss']}",
        f"神瞳：风{stats['anemoculus_number']} 岩{stats['geoculus_number']} "
        f"雷{stats['electroculus_number']} 草{stats['dendroculus_number']} "
        f"水{stats['hydroculus_number']} 火{stats['pyroculus_number']} "
        f"冰{stats['cryoculus_number']}",
        f"宝箱：普通{stats['common_chest_number']} 精致{stats['exquisite_chest_number']} "
        f"珍贵{stats['precious_chest_number']} 华丽{stats['luxurious_chest_number']}",
    ]
    homes = data["homes"]
    if homes:
        home = homes[0]
        lines.append(f"尘歌壶：{home['name']} 信任等阶{home['level']} 仙力{home['comfort_num']}")
    return "\n".join(lines)


def _format_enka_player(uid: str, info: dict[str, object]) -> str:
    lines = [f"UID {uid} 账号概览 [source=enka_cache]"]
    if "nickname" in info:
        lines.append(f"昵称：{as_str(info['nickname'])}")
    if "level" in info:
        lines.append(f"冒险等阶：{as_int(info['level'])}")
    if "worldLevel" in info:
        lines.append(f"世界等级：{as_int(info['worldLevel'])}")
    if "signature" in info:
        lines.append(f"签名：{as_str(info['signature'])}")
    if "finishAchievementNum" in info:
        lines.append(f"成就：{as_int(info['finishAchievementNum'])}")
    if "towerFloorIndex" in info and "towerLevelIndex" in info:
        lines.append(f"深渊展示：{as_int(info['towerFloorIndex'])}-{as_int(info['towerLevelIndex'])}")
    if "showAvatarInfoList" in info and isinstance(info["showAvatarInfoList"], list):
        names: list[str] = []
        for item in info["showAvatarInfoList"]:
            if isinstance(item, dict) and "avatarId" in item:
                names.append(str(item["avatarId"]))
        if names:
            lines.append(f"展柜角色数：{len(names)}")
    if len(lines) == 1:
        return f"UID {uid} 的账号缓存为空。请先 `{PREFIX}强制刷新`。"
    return "\n".join(lines)


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain=_DOMAIN,
    covers=_COVER_PLAYER,
    aliases=["原神·账号信息", "原神·冒险等阶"],
)
async def get_user_genshin_player_info(ctx: RunContext[ToolContext], uid: str = "") -> str:
    """查询原神账号概览文本：冒险等阶、成就、深渊层数、神瞳宝箱、角色数量。

    问「冒险等阶 / 成就多少 / 深渊打到哪」用本工具。要看角色面板图请走触发器「查询 角色名」。
    有 Cookie 走米游社全账号统计；否则读 Enka 名片缓存。

    Args:
        uid: 9 位原神 UID。留空则用当前用户默认绑定。
    """
    target, err = await _need_uid(ctx, uid)
    if err:
        return err
    raw = await get_base_data(target)
    if isinstance(raw, dict) and "role" in raw and "stats" in raw:
        return _format_index_player(target, raw)
    enka = load_json_obj(player_dir(target) / f"{target}.json")
    if enka is not None:
        return _format_enka_player(target, enka)
    return f"UID {target} 暂无账号概览。未绑 Cookie 时请先 `{PREFIX}强制刷新` 拉 Enka 展柜。"


def _row_from_mys(avatar: MihoyoAvatar) -> str:
    name = avatar["name"]
    return (
        f"| {name} | {avatar['rarity']} | {element_zh(avatar['element'])} | "
        f"{char_weapon_type(name)} | Lv{avatar['level']} | "
        f"{avatar['actived_constellation_num']}命 | 好感{avatar['fetter']} | - |"
    )


def _row_from_card(card: dict[str, object]) -> str:
    name = as_str(card["avatarName"]) if "avatarName" in card else "?"
    element = element_zh(as_str(card["avatarElement"])) if "avatarElement" in card else "-"
    level = as_str(card["avatarLevel"]) if "avatarLevel" in card else "?"
    talent = card["talentList"] if "talentList" in card and isinstance(card["talentList"], list) else []
    fetter = as_int(card["avatarFetter"]) if "avatarFetter" in card else 0
    weapon = "-"
    weapon_info = card["weaponInfo"] if "weaponInfo" in card and isinstance(card["weaponInfo"], dict) else None
    wtype = char_weapon_type(name)
    if weapon_info is not None:
        wname = as_str(weapon_info["weaponName"]) if "weaponName" in weapon_info else ""
        affix = as_int(weapon_info["weaponAffix"]) if "weaponAffix" in weapon_info else 0
        wlv = as_int(weapon_info["weaponLevel"]) if "weaponLevel" in weapon_info else 0
        if "weaponType" in weapon_info:
            wtype = weapon_type_zh(as_str(weapon_info["weaponType"]))
        weapon = f"{wname} Lv{wlv} 精{affix}" if wname else "-"
    return f"| {name} | - | {element} | {wtype} | Lv{level} | {len(talent)}命 | 好感{fetter} | {weapon} |"


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain=_DOMAIN,
    covers=_COVER_BOX,
    aliases=["原神·角色箱文本", "原神·展柜角色列表"],
)
async def get_user_genshin_char_list(ctx: RunContext[ToolContext], uid: str = "") -> str:
    """查询原神角色列表文本（元素 / 武器类型 / 等级 / 命座 / 好感 / 武器）。

    用于配队、练度对比前先看「现在能读到哪些角色」。不要用本工具出图。
    有 Cookie：米游社全角色箱（complete=true）。
    无 Cookie：仅展柜缓存（complete=false，最多 12 名），不是账号全部角色。

    Args:
        uid: 9 位原神 UID。留空则用当前用户默认绑定。
    """
    target, err = await _need_uid(ctx, uid)
    if err:
        return err
    header = "| 角色 | 星 | 元素 | 武器类型 | 等级 | 命座 | 好感 | 武器 |"
    sep = "|---|---|---|---|---|---|---|---|"
    rows: list[str] = []
    seen: set[str] = set()
    source = "cache"

    raw = await get_base_data(target)
    if isinstance(raw, dict) and "avatars" in raw:
        avatars = raw["avatars"]
        if isinstance(avatars, list) and avatars:
            source = "mys_index"
            for avatar in avatars:
                if not isinstance(avatar, dict) or "name" not in avatar:
                    continue
                name = str(avatar["name"])
                seen.add(name)
                rows.append(_row_from_mys(avatar))

    for path in list_cached_char_paths(target):
        card = load_json_obj(path)
        if card is None or "avatarName" not in card:
            continue
        name = as_str(card["avatarName"])
        if name in seen:
            continue
        seen.add(name)
        rows.append(_row_from_card(card))

    if not rows:
        return (
            f"UID {target} 暂无角色列表。[source=none complete=false]\n"
            f"未绑 Cookie 时只能缓存展柜角色（最多 12 名）。请先 `{PREFIX}强制刷新`；"
            f"若要看未上展柜的角色，请在游戏内更换展柜后再刷新。绑了 Cookie 可用 `{PREFIX}刷新面板` 同步全角色箱。"
        )
    if source == "mys_index":
        head = f"UID {target} 共 {len(rows)} 名角色 [source=mys_index complete=true]\n米游社全角色箱（已绑定 Cookie）。"
    else:
        extra = ""
        if len(rows) > 12:
            extra = f"\n本地还留有历史上过展柜的面板（共 {len(rows)} 名），仍然不是全角色箱。"
        head = (
            f"UID {target} 列出 {len(rows)} 名角色 "
            f"[source=enka_showcase complete=false]\n" + _SHOWCASE_HINT.format(prefix=PREFIX) + extra
        )
    return f"{head}\n{header}\n{sep}\n" + "\n".join(rows)


def _fmt_stat(stat: dict[str, object]) -> str:
    name = as_str(stat["statName"]) if "statName" in stat else ""
    value = stat["statValue"] if "statValue" in stat else ""
    return f"{name}+{value}"


def _format_char_detail(card: dict[str, object]) -> str:
    name = as_str(card["avatarName"]) if "avatarName" in card else "?"
    element = element_zh(as_str(card["avatarElement"])) if "avatarElement" in card else "-"
    level = as_str(card["avatarLevel"]) if "avatarLevel" in card else "?"
    fetter = as_int(card["avatarFetter"]) if "avatarFetter" in card else 0
    talent = card["talentList"] if "talentList" in card and isinstance(card["talentList"], list) else []
    lines = [
        f"【{name}】Lv{level} {element} {len(talent)}命 好感{fetter}",
    ]
    if "dataTime" in card:
        lines.append(f"缓存时间：{as_str(card['dataTime'])}")
    fight = card["avatarFightProp"] if "avatarFightProp" in card and isinstance(card["avatarFightProp"], dict) else None
    if fight is not None:
        if "hp" in fight and "atk" in fight and "def" in fight and "elementalMastery" in fight:
            lines.append(
                "属性："
                f"生命{as_float(fight['hp']):.0f}  攻击{as_float(fight['atk']):.0f}  "
                f"防御{as_float(fight['def']):.0f}  精通{as_float(fight['elementalMastery']):.0f}"
            )
        if "critRate" in fight and "critDmg" in fight and "energyRecharge" in fight:
            extra = f"暴击{pct(fight['critRate'])}  爆伤{pct(fight['critDmg'])}  充能{pct(fight['energyRecharge'])}"
            if "dmgBonus" in fight:
                extra += f"  伤加{pct(fight['dmgBonus'])}"
            if "healBonus" in fight and as_float(fight["healBonus"]) > 0:
                extra += f"  治疗{pct(fight['healBonus'])}"
            lines.append(extra)
    skills = card["avatarSkill"] if "avatarSkill" in card and isinstance(card["avatarSkill"], list) else []
    skill_bits: list[str] = []
    for skill in skills:
        if not isinstance(skill, dict) or "skillName" not in skill or "skillLevel" not in skill:
            continue
        skill_bits.append(f"{as_str(skill['skillName'])} {as_int(skill['skillLevel'])}")
    if skill_bits:
        lines.append("天赋：" + " / ".join(skill_bits))
    weapon_info = card["weaponInfo"] if "weaponInfo" in card and isinstance(card["weaponInfo"], dict) else None
    if weapon_info is not None and "weaponName" in weapon_info:
        wtype = weapon_type_zh(as_str(weapon_info["weaponType"])) if "weaponType" in weapon_info else ""
        lines.append(
            f"武器：{as_str(weapon_info['weaponName'])} {wtype} "
            f"Lv{as_int(weapon_info['weaponLevel']) if 'weaponLevel' in weapon_info else 0} "
            f"精{as_int(weapon_info['weaponAffix']) if 'weaponAffix' in weapon_info else 0} "
            f"{as_int(weapon_info['weaponStar']) if 'weaponStar' in weapon_info else 0}星"
        )
    sets = card["equipSets"] if "equipSets" in card and isinstance(card["equipSets"], dict) else None
    if sets is not None and "set" in sets:
        lines.append(f"圣遗物套装：{as_str(sets['type'])}件 {as_str(sets['set'])}")
    equips = card["equipList"] if "equipList" in card and isinstance(card["equipList"], list) else []
    for equip in equips:
        if not isinstance(equip, dict):
            continue
        piece = as_str(equip["aritifactPieceName"]) if "aritifactPieceName" in equip else ""
        set_name = as_str(equip["aritifactSetsName"]) if "aritifactSetsName" in equip else ""
        lv = as_int(equip["aritifactLevel"]) if "aritifactLevel" in equip else 0
        main = ""
        if "reliquaryMainstat" in equip and isinstance(equip["reliquaryMainstat"], dict):
            main = _fmt_stat(equip["reliquaryMainstat"])
        subs: list[str] = []
        if "reliquarySubstats" in equip and isinstance(equip["reliquarySubstats"], list):
            for sub in equip["reliquarySubstats"]:
                if isinstance(sub, dict):
                    subs.append(_fmt_stat(sub))
        lines.append(f"- {piece} {set_name} +{lv} 主:{main} 副:{' / '.join(subs)}")
    return "\n".join(lines)


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain=_DOMAIN,
    covers=_COVER_DETAIL,
    aliases=["原神·角色数值", "原神·面板文本"],
)
async def get_user_genshin_char_detail(
    ctx: RunContext[ToolContext],
    char_name: str,
    uid: str = "",
) -> str:
    """查询某角色面板的结构化数值文本（双暴 / 充能 / 天赋 / 武器精炼 / 圣遗物词条）。

    只在需要用数字做推理时调用（配队、对比词条、算充能）。
    「看看我的胡桃」「我的雷神面板」「查询 胡桃」必须走触发器「查询 角色名」出图，不要用本工具代替。
    无 Cookie 时只能读到展柜里缓存过的角色。

    Args:
        char_name: 角色名或别名，如 "胡桃"、"核桃"、"雷神"。
        uid: 9 位原神 UID。留空则用当前用户默认绑定。
    """
    if not char_name.strip():
        return "请提供角色名"
    target, err = await _need_uid(ctx, uid)
    if err:
        return err
    data = await get_char_data(target, char_name.strip())
    if isinstance(data, str):
        return data if data else CHAR_HINT.format(char_name)
    logger.info(f"[原神·AI工具] char_detail uid={target} name={char_name!r}")
    body = _format_char_detail(data)
    return (
        f"{body}\n"
        f"[source=enka_cache] 以上为该角色已缓存面板数值，不是出图。"
        f"用户若要看面板图，应使用触发器「查询 {char_name.strip()}」。"
    )


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain=_DOMAIN,
    covers=_COVER_ARTI,
    aliases=["原神·圣遗物仓库", "原神·圣遗物列表"],
)
async def get_user_genshin_artifacts(
    ctx: RunContext[ToolContext],
    uid: str = "",
    set_name: str = "",
    limit: int = 40,
) -> str:
    """查询已缓存角色身上的圣遗物文本：部位、套装、等级、主副词条。

    不是游戏内全部背包，只覆盖当前能读到的角色（无 Cookie 时即展柜缓存，最多 12 名）。
    可按套装名过滤。要看出图请走触发器「圣遗物仓库」。

    Args:
        uid: 9 位原神 UID。留空则用当前用户默认绑定。
        set_name: 可选套装名子串，如 "绝缘"、"魔女"。留空返回全部（截断到 limit）。
        limit: 最多返回条数，默认 40，最大 80。
    """
    target, err = await _need_uid(ctx, uid)
    if err:
        return err
    cap = min(max(limit, 1), 80)
    keyword = set_name.strip()
    lines: list[str] = []
    seen: set[str] = set()
    for path in list_cached_char_paths(target):
        card = load_json_obj(path)
        if card is None or "equipList" not in card or not isinstance(card["equipList"], list):
            continue
        owner = as_str(card["avatarName"]) if "avatarName" in card else path.stem
        for equip in card["equipList"]:
            if not isinstance(equip, dict):
                continue
            set_n = as_str(equip["aritifactSetsName"]) if "aritifactSetsName" in equip else ""
            if keyword and keyword not in set_n:
                continue
            piece = as_str(equip["aritifactPieceName"]) if "aritifactPieceName" in equip else ""
            lv = as_int(equip["aritifactLevel"]) if "aritifactLevel" in equip else 0
            main = ""
            if "reliquaryMainstat" in equip and isinstance(equip["reliquaryMainstat"], dict):
                main = _fmt_stat(equip["reliquaryMainstat"])
            identity = f"{owner}|{piece}|{set_n}|{lv}|{main}"
            if identity in seen:
                continue
            seen.add(identity)
            subs: list[str] = []
            if "reliquarySubstats" in equip and isinstance(equip["reliquarySubstats"], list):
                for sub in equip["reliquarySubstats"]:
                    if isinstance(sub, dict):
                        subs.append(_fmt_stat(sub))
            lines.append(f"- [{owner}] {piece} {set_n} +{lv} 主:{main} 副:{' / '.join(subs)}")
            if len(lines) >= cap:
                extra = "（已截断，可用 set_name 缩小范围）"
                return (
                    f"UID {target} 圣遗物仓 {len(lines)}+ 条 "
                    f"[source=enka_cache complete=false]{extra}\n"
                    + _SHOWCASE_HINT.format(prefix=PREFIX)
                    + "\n"
                    + "\n".join(lines)
                )
    if not lines:
        return (
            f"UID {target} 没有匹配的圣遗物缓存。[source=none complete=false]\n"
            f"请先 `{PREFIX}强制刷新`。无 Cookie 时只能缓存展柜角色身上的圣遗物。"
        )
    return (
        f"UID {target} 圣遗物仓 {len(lines)} 条 "
        f"[source=enka_cache complete=false]\n" + _SHOWCASE_HINT.format(prefix=PREFIX) + "\n" + "\n".join(lines)
    )

"""原神知识库检索包装：只查本插件知识点，避免被其它游戏知识淹没。"""

from __future__ import annotations

import httpx
import httpx2
from pydantic_ai import RunContext

from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.ai_core.rag import query_knowledge
from gsuid_core.ai_core.models import ToolContext
from gsuid_core.ai_core.register import ai_tools

from ..utils.map.name_covert import expand_query_aliases

_CTX = ["原神", "Genshin", "游戏"]
# 知识点 plugin 字段历史值是 genshin；枢纽归属取插件目录名 GenshinUID。
_KB_PLUGINS = ["GenshinUID", "genshin"]
# 向量库/嵌入服务不可用时的外部网络与运行时异常（用于降级本地图鉴检索）。
_KB_OFFLINE_ERRORS = (httpx.HTTPError, httpx2.HTTPError, TimeoutError, OSError, RuntimeError)


def _payload_text(payload: dict[str, object]) -> str:
    title = str(payload["title"]) if "title" in payload else ""
    content = str(payload["content"]) if "content" in payload else ""
    tags = payload["tags"] if "tags" in payload else None
    tag_s = ""
    if isinstance(tags, list):
        tag_s = ",".join(str(t) for t in tags[:8])
    head = title or "（无标题）"
    body = content.strip()
    if len(body) > 800:
        body = body[:800] + "…"
    extra = f" tags={tag_s}" if tag_s else ""
    return f"### {head}{extra}\n{body}"


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain="原神资料库",
    covers=[
        "带什么圣遗物",
        "圣遗物套装",
        "原神角色配队",
        "原神角色攻略",
        "原神怪物抗性",
        "原神武器被动",
    ],
    aliases=["原神·知识库", "原神·资料检索"],
)
async def search_genshin_kb(
    ctx: RunContext[ToolContext],
    query: str,
    limit: int = 6,
) -> str:
    """检索原神知识库：天赋命座文本、武器特效、套装说明、怪物抗性、角色攻略。

    问机制/攻略/抗性/武器被动时调用，不要先 web_search。错字和简称会收成正式名。
    点名的武器会附带图鉴精确条目（基础攻击、副词条、被动）。
    用户自己的练度走 get_user_genshin_char_list / char_detail；看面板图走「查询 角色名」。

    Args:
        query: 自然语言，如 "胡桃 命座"、"绝缘之旗印"、"雷电将军 攻略"、"无相之雷 抗性"。
        limit: 最多返回条数，默认 6，最大 12。
    """
    _ = ctx
    raw = query.strip()
    if not raw:
        return "请提供检索关键词"
    text = expand_query_aliases(raw)
    cap = min(max(limit, 1), 12)
    logger.info(t("log.genshinuid.kb_query", query=text, limit=cap))
    exact = await _exact_weapon_blocks(text)
    chunks: list[str] = []
    qdrant_offline = False
    try:
        points = await query_knowledge(query=text, limit=cap, plugin_filter=_KB_PLUGINS)
    except _KB_OFFLINE_ERRORS as exc:
        logger.warning(t("log.genshinuid.kb_offline_fallback", e=exc))
        points = []
        qdrant_offline = True
    for point in points:
        payload = point.payload
        if not isinstance(payload, dict):
            continue
        chunks.append(_payload_text(payload))
    if exact:
        chunks = exact + chunks
    if not chunks or qdrant_offline:
        local_blocks = await _local_kb_fallback(text, cap)
        if local_blocks:
            chunks = [*chunks, *local_blocks][:cap]
    if not chunks:
        return f"原神知识库未命中 {text!r}。可换角色全名、套装名或武器名再查。"
    suffix = "（向量库离线，已使用本地图鉴离线索引）" if qdrant_offline else ""
    return f"原神知识库命中 {len(chunks)} 条{suffix}：\n\n" + "\n\n".join(chunks)


async def _local_kb_fallback(text: str, limit: int) -> list[str]:
    """向量库不可用或未命中时，直接查本地内置角色/圣遗物/怪物/材料数据。"""
    from .materials import search_local_materials_text
    from ..utils.map.GS_MAP_PATH import charList, reliquaryList, monster2entry_data
    from ..utils.map.name_covert import alias_to_char_name
    from ..genshinuid_adv.get_adv import adv_lst
    from ..genshinuid_wikitext.wiki_data import CharWiki, load_char_wiki

    blocks: list[str] = []
    tokens = [tok.strip() for tok in text.split() if len(tok.strip()) >= 2]
    if not tokens and text.strip():
        tokens = [text.strip()]

    # 1. 角色本地图鉴（基础属性、突破/天赋材料、技能与命座摘要、攻略配装）
    matched_chars: list[str] = []
    known_chars = {
        str(v["name"]) for v in charList.values() if isinstance(v, dict) and "name" in v and isinstance(v["name"], str)
    }
    for tok in tokens:
        cand = await alias_to_char_name(tok)
        if cand in known_chars and cand not in matched_chars:
            matched_chars.append(cand)
        else:
            for cname in known_chars:
                if cname in tok and cname not in matched_chars:
                    matched_chars.append(cname)
        if len(matched_chars) >= 2:
            break

    for cname in matched_chars:
        wiki = await load_char_wiki(cname, 90)
        if isinstance(wiki, CharWiki):
            asc = "、".join(f"{it.name}×{it.count}" for it in wiki.ascend_items[:8])
            tal = " / ".join(f"{s.slot}:{s.name}" for s in wiki.talents[:4])
            con = "；".join(f"{c.index}命-{c.name}" for c in wiki.consts[:6])
            body_lines = [
                f"### {wiki.name}（本地图鉴精确命中）",
                f"{wiki.rarity}星 {wiki.element_zh} {wiki.weapon} 地区:{wiki.region} "
                f"90级突破属性:{wiki.substat} {wiki.substat_value}",
                f"90级基础：生命{wiki.hp} 攻击{wiki.atk} 防御{wiki.defense}",
            ]
            if asc:
                body_lines.append(f"1→90级突破总材料：{asc}（突破摩拉 {wiki.mora_ascend:,}）")
            if tal:
                body_lines.append(f"技能：{tal}")
            if con:
                body_lines.append(f"命座：{con}")
            if cname in adv_lst and isinstance(adv_lst[cname], dict):
                adv = adv_lst[cname]
                art_sets = adv["artifact"] if "artifact" in adv and isinstance(adv["artifact"], list) else []
                if art_sets:
                    plans = " / ".join("+".join(str(x) for x in s) for s in art_sets[:3] if isinstance(s, list))
                    body_lines.append(f"推荐圣遗物：{plans}")
            blocks.append("\n".join(body_lines))

    # 2. 圣遗物套装
    for entry in reliquaryList.values():
        if len(blocks) >= limit:
            break
        if not isinstance(entry, dict) or "name" not in entry or not isinstance(entry["name"], str):
            continue
        aname = entry["name"]
        if any(tok in aname or aname in text for tok in tokens):
            affix = entry["affixList"] if "affixList" in entry and isinstance(entry["affixList"], dict) else {}
            effs = [str(v) for v in affix.values() if isinstance(v, str)]
            desc = "\n".join(f"- {e}" for e in effs[:2])
            blocks.append(f"### {aname}（本地圣遗物图鉴）\n{desc}")

    # 3. 怪物抗性与掉落
    seen_monsters: set[str] = set()
    for entry in monster2entry_data.values():
        if len(blocks) >= limit:
            break
        if not isinstance(entry, dict) or "name" not in entry or not isinstance(entry["name"], str):
            continue
        mname = entry["name"]
        if mname in seen_monsters:
            continue
        if any(tok in mname or mname in text for tok in tokens):
            seen_monsters.add(mname)
            res = entry["resistance"] if "resistance" in entry and isinstance(entry["resistance"], dict) else {}
            res_map = (
                ("物", "physicalSubHurt"),
                ("火", "fireSubHurt"),
                ("水", "waterSubHurt"),
                ("雷", "elecSubHurt"),
                ("冰", "iceSubHurt"),
                ("风", "windSubHurt"),
                ("岩", "rockSubHurt"),
                ("草", "grassSubHurt"),
            )
            res_bits = [
                f"{lbl}{int(round(float(res[k]) * 100))}%"
                for lbl, k in res_map
                if k in res and isinstance(res[k], (int, float))
            ]
            rew = entry["reward"] if "reward" in entry and isinstance(entry["reward"], dict) else {}
            drops = [
                str(v["name"]) for v in rew.values() if isinstance(v, dict) and "name" in v and str(v["name"]) != "摩拉"
            ]
            line = f"### {mname}（本地怪物图鉴）"
            if res_bits:
                line += "\n抗性：" + " ".join(res_bits)
            if drops:
                line += "\n主要掉落：" + "、".join(drops[:8])
            blocks.append(line)

    # 4. 本地材料与采集地索引
    if len(blocks) < limit:
        blocks.extend(search_local_materials_text(text, limit=limit - len(blocks)))

    return blocks[:limit]


async def _exact_weapon_blocks(text: str) -> list[str]:
    """点名的武器走图鉴精确条目，避免向量把别的角色排到前面。"""
    from ..utils.map.GS_MAP_PATH import weapon_alias_data
    from ..genshinuid_wikitext.wiki_data import WeaponWiki, load_weapon_wiki

    blocks: list[str] = []
    seen: set[str] = set()
    for part in text.split():
        if part not in weapon_alias_data or part in seen:
            continue
        seen.add(part)
        wiki = await load_weapon_wiki(part, 90)
        if not isinstance(wiki, WeaponWiki):
            continue
        refine = wiki.effect
        if wiki.refinements:
            refine = wiki.refinements[0]
            if len(wiki.refinements) >= 5:
                refine = f"精1 {wiki.refinements[0]}；精5 {wiki.refinements[4]}"
        if len(refine) > 500:
            refine = refine[:500] + "…"
        blocks.append(
            f"### {wiki.name}（图鉴精确命中）\n"
            f"{wiki.rarity}星 {wiki.weapon_type} "
            f"攻击 {wiki.atk_base}/{wiki.atk_max} "
            f"{wiki.substat} {wiki.sub_base}/{wiki.sub_max}\n"
            f"{wiki.effect_name}：{refine}"
        )
        if len(blocks) >= 3:
            break
    return blocks

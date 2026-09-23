"""原神知识库检索包装：只查本插件知识点，避免被其它游戏知识淹没。"""

from __future__ import annotations

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
        "检索原神知识库：角色档案/命座天赋、武器、圣遗物套装、怪物抗性、角色攻略",
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
    points = await query_knowledge(query=text, limit=cap, plugin_filter=_KB_PLUGINS)
    chunks: list[str] = []
    for point in points:
        payload = point.payload
        if not isinstance(payload, dict):
            continue
        chunks.append(_payload_text(payload))
    if exact:
        chunks = exact + chunks
    if not chunks:
        return f"原神知识库未命中 {text!r}。可换角色全名、套装名或武器名再查。"
    return f"原神知识库命中 {len(chunks)} 条：\n\n" + "\n\n".join(chunks)


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

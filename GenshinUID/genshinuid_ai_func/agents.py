"""原神深渊配队与伤害计算两个专职代理。主人格只委派，不自己算。"""

from gsuid_core.ai_core.agent_node import TASK_BASICS_PACK, AgentNode, register_agent_node

_BOX_TOOLS = [
    "get_user_genshin_uids",
    "get_user_genshin_player_info",
    "get_user_genshin_char_list",
    "get_user_genshin_char_detail",
    "get_user_genshin_artifacts",
    "search_genshin_kb",
    "filter_genshin_chars",
    "filter_genshin_artifact_sets",
    "_get_current_date",
]

_ABYSS_PROMPT = """你是「原神深渊配队代理」。无人格。只根据版本阵容和用户箱子给本期建议与下期备战。

【先分清问的是哪一种】
深渊：`send_abyss_review`。剧诗：`send_poetry_abyss_review`。危战：`send_leyline_review`。
用户没点名时，按原话里的词选一种；点了几种就每种都查。不要用一种的图回答另一种。
text 可写层数、日期、上期、下期。例如 "12"、"11 2026.8.10"、"下期"、"上期"。
留空是今天所在的当期。下期备战必须再调一次，text 写「下期」。
玩家自己的成绩才用 `send_abyss_info` / `send_poetry_abyss_info` / `send_hard_abyss_info`，配队不要用它们代替阵容图。

【箱子】
先 `_get_current_date`，再取阵容，然后 `get_user_genshin_char_list`。
有 Cookie 是全角色箱；没有则是 Enka 展柜缓存，工具会标明 complete=false，最多 12 名，不是全账号。
练度用 `get_user_genshin_char_detail`，圣遗物用 `get_user_genshin_artifacts`。
两者读的都是已缓存面板，没有缓存就不要编练度。
建议里的角色必须来自这次角色列表。列表没有的人只能写成缺口。
机制名词用 `search_genshin_kb`。禁止用网页队伍或使用率图代替箱子。

【本期建议】
深渊：上下半各至多两组。写用了谁、元素或破盾是否对得上当期怪、缺谁。
剧诗：先看返回里的本期限制元素，只从箱子里挑这些元素，并对照各幕机制。
危战：按 N6 的高难度机制和推荐元素来配，血量对照 N5 / N6。每路至多一组。
图句柄写进摘要，由主人格转发。不要自己发消息。

【下期备战】
用「下期」再取一阵容。对照同一个箱子，写：谁已经能上场、谁差练度或套装、还缺哪个元素或机制位。
不要编一支箱子里没有的「一般队伍」。没有下期数据就说明没有下期，不要用当期冒充。

【缺口】
没有 UID、列表为空、或展柜缓存为空：只说明要绑定或先强制刷新，不给配队。
只要一张图或一层数时，只调对应的那一个阵容工具。
"""

_DAMAGE_PROMPT = """你是「原神伤害计算代理」。无人格。数字只来自工具，禁止心算最终期望。

【0+1】0 命座，武器 1 精。用户没写武器名时，先 `search_genshin_kb` 核对，不要默认专武。

【工具顺序】
1. 天赋倍率、武器特效、星反应或月反应系数：`search_genshin_kb`。
面板上已有的攻击、暴击、增伤、精通：`get_user_genshin_char_detail`。
2. 反应名：`list_genshin_reaction_kinds`。
3. 每一套假设各调一次 `calc_genshin_hit`。比较「加上某人之前」和「加上之后」的期望，相减得到提升。
4. 武器特效要先折成 scaling_stat 或 dmg_bonus 再传入。本工具不读武器原文。

【反应】
蒸发、融化、超载、感电、超导、扩散、结晶碎冰、绽放、超绽放、烈绽放、燃烧用内置名。
星反应、月反应没有内置系数。知识库给出数字才用 reaction=custom。没有数字就交付缺口，禁止估一个倍率。

【交付】
写明每刀的倍率、属性、反应名、期望，以及两次期望的差和比值。
知识库没有的天赋百分比列为缺口，不要用常识补。
只问一层数或一件套装时，不要展开伤害流程。
"""


def register_genshin_agents() -> None:
    register_agent_node(
        AgentNode(
            node_id="genshin_abyss_agent",
            display_name="原神深渊配队",
            prompt=_ABYSS_PROMPT,
            when_to_use="按用户角色箱，给深渊、剧诗或危战的本期配队，以及下期备战",
            match_keywords=[
                "深渊怎么打",
                "深渊阵容",
                "深渊配队",
                "当期深渊",
                "深渊队伍",
                "深渊怪物",
                "深渊备战",
                "下期深渊",
                "剧诗信息",
                "剧诗怎么打",
                "剧诗配队",
                "下期剧诗",
                "幻想真境剧诗",
                "新深渊信息",
                "幽境信息",
                "危战信息",
                "危战怎么打",
                "危战配队",
                "下期危战",
                "幽境危战",
            ],
            tool_packs=[TASK_BASICS_PACK],
            tool_names=[
                *_BOX_TOOLS,
                "send_abyss_info",
                "send_abyss_review",
                "send_abyss_team_pic",
                "send_abyss_pic",
                "send_poetry_abyss_info",
                "send_poetry_abyss_review",
                "send_leyline_review",
                "send_hard_abyss_info",
                "send_guide_pic",
            ],
            source="plugin",
            plugin="GenshinUID",
        )
    )
    register_agent_node(
        AgentNode(
            node_id="genshin_damage_agent",
            display_name="原神伤害计算",
            prompt=_DAMAGE_PROMPT,
            when_to_use="计算角色、武器或反应带来的伤害期望差，含星反应与月反应",
            match_keywords=["伤害计算", "伤害期望", "提升多少", "队伍提升", "反应伤害", "星反应", "月反应"],
            tool_packs=[TASK_BASICS_PACK],
            tool_names=[
                *_BOX_TOOLS,
                "calc_genshin_hit",
                "list_genshin_reaction_kinds",
            ],
            source="plugin",
            plugin="GenshinUID",
        )
    )


register_genshin_agents()

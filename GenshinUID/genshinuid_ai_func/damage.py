"""原神单次伤害的公开公式。星/月反应没有内置系数。"""

from typing import NamedTuple

from pydantic_ai import RunContext

from gsuid_core.ai_core.models import ToolContext
from gsuid_core.ai_core.register import ai_tools

_CTX = ["原神", "Genshin", "游戏"]
_DOMAIN = "原神伤害"
# 90 级转化反应的等级基数。其它等级不猜，调用方改传 custom。
_FLAT_BASE_90 = 1446.85


class ReactionSpec(NamedTuple):
    kind: str
    multiplier: float


# kind=amp 乘在天赋伤害上；kind=flat 不吃倍率，单独结算。
_REACTIONS: dict[str, ReactionSpec] = {
    "vaporize_pyro": ReactionSpec("amp", 1.5),
    "vaporize_hydro": ReactionSpec("amp", 2.0),
    "melt_pyro": ReactionSpec("amp", 2.0),
    "melt_cryo": ReactionSpec("amp", 1.5),
    "overloaded": ReactionSpec("flat", 2.0),
    "electrocharged": ReactionSpec("flat", 1.2),
    "superconduct": ReactionSpec("flat", 0.5),
    "swirl": ReactionSpec("flat", 0.6),
    "shatter": ReactionSpec("flat", 1.5),
    "bloom": ReactionSpec("flat", 2.0),
    "hyperbloom": ReactionSpec("flat", 3.0),
    "burgeon": ReactionSpec("flat", 3.0),
    "burning": ReactionSpec("flat", 0.25),
}


class HitNumbers(NamedTuple):
    non_crit: float
    crit: float
    expected: float
    reaction_flat: float
    notes: tuple[str, ...]


def defense_multiplier(char_level: int, enemy_level: int, def_reduction: float) -> float:
    """防御区。(角色等级+100) / (己方 + 敌方×(1-减防))。"""
    own = char_level + 100
    enemy = (enemy_level + 100) * (1.0 - def_reduction)
    denom = own + enemy
    if denom == 0:
        return 0.0
    return own / denom


def resistance_multiplier(resistance: float) -> float:
    """抗性区。负抗减半，0.75 以上改用 1/(4r+1)。"""
    if resistance < 0:
        return 1.0 - resistance / 2.0
    if resistance < 0.75:
        return 1.0 - resistance
    return 1.0 / (4.0 * resistance + 1.0)


def amplifying_em_bonus(em: float) -> float:
    if em <= 0:
        return 0.0
    return 2.78 * em / (em + 1400.0)


def transformative_em_bonus(em: float) -> float:
    if em <= 0:
        return 0.0
    return 16.0 * em / (em + 2000.0)


def calc_hit(
    *,
    scaling_stat: float,
    motion_value: float,
    dmg_bonus: float,
    crit_rate: float,
    crit_dmg: float,
    char_level: int,
    enemy_level: int,
    def_reduction: float,
    enemy_resistance: float,
    em: float,
    reaction: str,
    reaction_bonus: float,
    custom_reaction_multiplier: float,
    hit_count: int,
) -> HitNumbers | str:
    """返回一次期望伤害，或一条缺口说明。武器特效不在这里解析。"""
    if scaling_stat < 0 or motion_value < 0:
        return "scaling_stat 与 motion_value 不能为负"
    if char_level < 1 or enemy_level < 1:
        return "char_level 与 enemy_level 至少为 1"
    if hit_count < 1:
        return "hit_count 至少为 1"
    notes: list[str] = []
    rate = crit_rate
    if rate < 0:
        rate = 0.0
        notes.append("暴击率低于 0，按 0 计")
    if rate > 1:
        rate = 1.0
        notes.append("暴击率高于 1，按 1 计")
    def_mult = defense_multiplier(char_level, enemy_level, def_reduction)
    res_mult = resistance_multiplier(enemy_resistance)
    zone = scaling_stat * motion_value * (1.0 + dmg_bonus) * def_mult * res_mult
    reaction_flat = 0.0
    if reaction == "none":
        dealt = zone
    elif reaction == "custom":
        if custom_reaction_multiplier <= 0:
            return "custom 必须给出 custom_reaction_multiplier（先从知识库抄系数，不要估）"
        dealt = zone * custom_reaction_multiplier * (1.0 + reaction_bonus)
        notes.append("星反应/月反应走 custom，倍率由调用方传入")
    elif reaction not in _REACTIONS:
        known = "、".join(sorted(_REACTIONS))
        return f"未知反应 {reaction}。内置：{known}。星反应/月反应用 custom"
    else:
        spec = _REACTIONS[reaction]
        if spec.kind == "amp":
            bonus = amplifying_em_bonus(em) + reaction_bonus
            dealt = zone * spec.multiplier * (1.0 + bonus)
            notes.append(f"增幅 {spec.multiplier}，精通加成 {amplifying_em_bonus(em):.4f}")
        else:
            if char_level != 90:
                return "转化反应只内置 90 级基数。其它等级请用 custom 传入知识库系数"
            em_bonus = transformative_em_bonus(em)
            reaction_flat = _FLAT_BASE_90 * spec.multiplier * (1.0 + em_bonus + reaction_bonus) * res_mult
            dealt = zone
            notes.append(f"转化反应另算 {reaction_flat:.1f}（基数 {_FLAT_BASE_90} × {spec.multiplier}），不吃天赋倍率")
    non_crit = dealt * hit_count
    crit = non_crit * (1.0 + crit_dmg)
    expected = non_crit * (1.0 - rate) + crit * rate
    if reaction_flat:
        reaction_flat *= hit_count
        expected += reaction_flat
        crit += reaction_flat
        non_crit += reaction_flat
    return HitNumbers(non_crit, crit, expected, reaction_flat, tuple(notes))


def _format_hit(label: str, result: HitNumbers) -> str:
    lines = [
        f"{label}",
        f"非暴击 {result.non_crit:.1f}",
        f"暴击 {result.crit:.1f}",
        f"期望 {result.expected:.1f}",
    ]
    if result.reaction_flat:
        lines.append(f"其中转化反应 {result.reaction_flat:.1f}")
    lines.extend(result.notes)
    return "\n".join(lines)


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain=_DOMAIN,
    covers=["伤害期望", "提升多少", "反应伤害"],
    aliases=["原神·伤害计算", "原神·期望伤害"],
)
async def calc_genshin_hit(
    ctx: RunContext[ToolContext],
    label: str,
    scaling_stat: float,
    motion_value: float,
    dmg_bonus: float = 0,
    crit_rate: float = 0.05,
    crit_dmg: float = 0.5,
    char_level: int = 90,
    enemy_level: int = 90,
    def_reduction: float = 0,
    enemy_resistance: float = 0.1,
    em: float = 0,
    reaction: str = "none",
    reaction_bonus: float = 0,
    custom_reaction_multiplier: float = 0,
    hit_count: int = 1,
) -> str:
    """计算一次原神伤害期望（天赋区 × 增幅，或另加转化反应）。

    倍率、武器特效加成必须先从知识库或面板工具抄成数字再传入。
    0+1 表示 0 命与 1 精，本工具不解释武器文本。
    星反应、月反应用 reaction=custom，并传入知识库里的系数。

    Args:
        label: 这刀的名字，如 "丝柯克重击" 或 "加上沃雅妮莎后"。
        scaling_stat: 倍率吃的属性，通常是攻击力，也可用生命或防御。
        motion_value: 天赋倍率。200% 填 2。
        dmg_bonus: 增伤区小数。46.6% 填 0.466。含武器、套装、队友加成。
        crit_rate: 暴击率小数，默认 0.05。
        crit_dmg: 暴击伤害小数，默认 0.5。
        char_level: 角色等级，默认 90。
        enemy_level: 敌人等级，默认 90。
        def_reduction: 减防小数。
        enemy_resistance: 减抗后的敌人抗性小数，默认 0.1。
        em: 元素精通。
        reaction: none，或内置反应名，或 custom。
        reaction_bonus: 反应伤害加成小数。
        custom_reaction_multiplier: 仅 custom 使用的倍率。
        hit_count: 段数，默认 1。
    """
    _ = ctx
    result = calc_hit(
        scaling_stat=scaling_stat,
        motion_value=motion_value,
        dmg_bonus=dmg_bonus,
        crit_rate=crit_rate,
        crit_dmg=crit_dmg,
        char_level=char_level,
        enemy_level=enemy_level,
        def_reduction=def_reduction,
        enemy_resistance=enemy_resistance,
        em=em,
        reaction=reaction,
        reaction_bonus=reaction_bonus,
        custom_reaction_multiplier=custom_reaction_multiplier,
        hit_count=hit_count,
    )
    if isinstance(result, str):
        return result
    return _format_hit(label, result)


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain=_DOMAIN,
    covers=["有哪些元素反应", "反应倍率"],
    aliases=["原神·反应列表"],
)
async def list_genshin_reaction_kinds(ctx: RunContext[ToolContext]) -> str:
    """列出伤害公式内置的反应名与倍率。星反应和月反应不在表内。"""
    _ = ctx
    lines = ["增幅（乘在天赋伤害上，精通加成 2.78×EM/(EM+1400)）："]
    flats = ["转化（不吃天赋倍率，90 级基数 1446.85，精通加成 16×EM/(EM+2000)）："]
    for name in sorted(_REACTIONS):
        spec = _REACTIONS[name]
        row = f"- {name} ×{spec.multiplier}"
        if spec.kind == "amp":
            lines.append(row)
        else:
            flats.append(row)
    lines.extend(flats)
    lines.append("星反应、月反应：reaction=custom，系数必须来自知识库。")
    return "\n".join(lines)

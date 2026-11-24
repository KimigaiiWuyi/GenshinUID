from typing import Tuple, Union, Optional

from PIL import Image

from gsuid_core.ai_core.trigger_bridge import ai_return

from .html_char_card import AkashaSideInject, render_char_card_html
from .mono.Character import Character


def _ai_return_enka_char(char: Character) -> None:
    try:
        card = char.card_prop if isinstance(char.card_prop, dict) else {}
        fight = char.fight_prop if char.fight_prop else (card["avatarFightProp"] if "avatarFightProp" in card else {})
        lines = [
            f"【{char.char_name} 角色面板】Lv{char.char_level} {char.char_element} "
            f"{char.char_talent}命 好感{char.char_fetter}"
        ]
        if isinstance(fight, dict) and "hp" in fight and "atk" in fight and "def" in fight:
            hp = float(fight["hp"])
            atk = float(fight["atk"])
            defense = float(fight["def"])
            em = float(fight["elementalMastery"]) if "elementalMastery" in fight else 0.0
            cr = float(fight["critRate"]) * 100 if "critRate" in fight else 0.0
            cd = float(fight["critDmg"]) * 100 if "critDmg" in fight else 0.0
            er = float(fight["energyRecharge"]) * 100 if "energyRecharge" in fight else 100.0
            dmg = float(fight["dmgBonus"]) * 100 if "dmgBonus" in fight else 0.0
            lines.append(
                f"属性: 生命{hp:.0f} 攻击{atk:.0f} 防御{defense:.0f} 精通{em:.0f} | "
                f"暴击{cr:.1f}% 爆伤{cd:.1f}% 充能{er:.1f}% 增伤{dmg:.1f}%"
            )
        if "weaponInfo" in card and isinstance(card["weaponInfo"], dict):
            w = card["weaponInfo"]
            if "weaponName" in w:
                wlv = w["weaponLevel"] if "weaponLevel" in w else "?"
                waf = w["weaponAffix"] if "weaponAffix" in w else "?"
                lines.append(f"武器: {w['weaponName']} Lv{wlv} 精{waf}")
        if "avatarSkill" in card and isinstance(card["avatarSkill"], list):
            skills = [
                f"{s['skillName']}{s['skillLevel']}"
                for s in card["avatarSkill"]
                if isinstance(s, dict) and "skillName" in s and "skillLevel" in s
            ]
            if skills:
                lines.append("天赋: " + " / ".join(skills))
        if "equipSets" in card and isinstance(card["equipSets"], dict) and "set" in card["equipSets"]:
            es = card["equipSets"]
            etype = es["type"] if "type" in es else ""
            lines.append(f"圣遗物套装: {etype}件 {es['set']}")
        score_bits: list[str] = []
        if char.artifacts_all_score:
            score_bits.append(f"圣遗物总分 {char.artifacts_all_score:.1f}")
        if char.percent and char.percent not in ("0.0", "0.00"):
            score_bits.append(f"伤害评级 {char.percent}%")
        if score_bits:
            lines.append("评级: " + " | ".join(score_bits))
        if "equipList" in card and isinstance(card["equipList"], list):
            for eq in card["equipList"]:
                if not isinstance(eq, dict):
                    continue
                main = eq["reliquaryMainstat"] if "reliquaryMainstat" in eq else None
                if not isinstance(main, dict) or "statName" not in main or "statValue" not in main:
                    continue
                subs_raw = eq["reliquarySubstats"] if "reliquarySubstats" in eq else None
                subs = (
                    [
                        f"{s['statName']}+{s['statValue']}"
                        for s in subs_raw
                        if isinstance(s, dict) and "statName" in s and "statValue" in s
                    ]
                    if isinstance(subs_raw, list)
                    else []
                )
                piece = eq["aritifactPieceName"] if "aritifactPieceName" in eq else ""
                sets = eq["aritifactSetsName"] if "aritifactSetsName" in eq else ""
                lv = eq["aritifactLevel"] if "aritifactLevel" in eq else "?"
                lines.append(f"  - {piece} {sets} +{lv} 主:{main['statName']}+{main['statValue']} 副:{'/'.join(subs)}")
        ai_return("\n".join(lines))
    except Exception:
        pass


async def draw_char_img(
    char: Character,
    charUrl: Optional[str] = None,
    *,
    akasha_side: AkashaSideInject | None = None,
) -> Union[str, Tuple[Image.Image, Optional[bytes]]]:
    res = await draw_char_card(char, charUrl, akasha_side=akasha_side)
    _ai_return_enka_char(char)
    return res, char.char_bytes


async def draw_char_card(
    char: Character,
    char_url: Optional[str],
    *,
    akasha_side: AkashaSideInject | None = None,
) -> Image.Image:
    return await render_char_card_html(char, char_url, akasha_side=akasha_side)

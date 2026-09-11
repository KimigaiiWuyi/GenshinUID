"""从 akasha.cv 分类接口抽出全部队名/简称/武器/角色，写成 akasha_zh.json。"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT.parent / "test_output" / "gs_detail" / "akasha_categories.json"
MAP = ROOT / "utils" / "map" / "data"
OUT = ROOT / "genshinuid_enka" / "akasha_zh.json"

NAMES: dict[str, str] = {
    "2N3 + Bake-Kurage, Avg DMG": "2N3 + 化海月 · 平均伤害",
    "ATK + ER (+ CR) balance formula": "攻击+充能(+暴击) 平衡公式",
    "Aggravate Combo with EM buff, Avg DMG": "激化连招（精通增益）· 平均伤害",
    "Aggravate Combo, Avg DMG": "激化连招 · 平均伤害",
    "Aggravate Combo, DPS": "激化连招 · DPS",
    "Aggravate EQ Combo, Avg DMG": "激化 EQ 连招 · 平均伤害",
    "Aggravate Oz Combo Avg DMG": "激化奥兹连招 · 平均伤害",
    "Aggravate Skill + Burst Combo, Avg DMG": "激化战技+爆发连招 · 平均伤害",
    "Aggravate Team, Avg DMG": "激化队 · 平均伤害",
    "Aggravate Violet Arc, Avg DMG": "激化苍雷 · 平均伤害",
    "Basic Combo with Crit-fishing, Avg DMG": "基础连招（吃暴击）· 平均伤害",
    "Basic Combo, Avg DMG": "基础连招 · 平均伤害",
    "Basic Lunar-Charged Team, Avg DMG": "基础月感电队 · 平均伤害",
    "Basic Team vs Boss, Avg DMG": "基础队对首领 · 平均伤害",
    "Basic Team vs Frozen, Avg DMG": "基础队对冻结 · 平均伤害",
    "Bloom Melt, Avg DMG": "绽放融化 · 平均伤害",
    "Buffed EQ Combo, Avg DMG": "增益 EQ 连招 · 平均伤害",
    "Burning Team Combo, Avg DMG": "燃烧队连招 · 平均伤害",
    "Burnmelt Bloom, Avg DMG": "燃烧融化绽放 · 平均伤害",
    "Burnmelt Team Combo, Avg. DMG": "燃烧融化队连招 · 平均伤害",
    "Burnvape with Furina, Avg DMG": "燃烧蒸发（芙宁娜）· 平均伤害",
    "Burnvape with Nahida, Avg DMG": "燃烧蒸发（纳西妲）· 平均伤害",
    "Burst + Shunsuiken, Soup Team, Avg DMG": "爆发+瞬水剑 · 汤队 · 平均伤害",
    "C2 Double Pyro Double Geo, Avg DMG": "2命 双火双岩 · 平均伤害",
    "C6 Combo with C4 Mona, Avg DMG": "6命连招（4命莫娜）· 平均伤害",
    "C6 Frontloaded Combo, Avg DMG": "6命前台连招 · 平均伤害",
    "C6 Lightfall Sword Explosion Crit DMG": "6命光降之剑爆炸暴伤",
    "C6 On-field Bloom Team 2H2D Damage Contribution": "6命前台绽放队 2水2草伤害贡献",
    "C6 Quickbloom Combo, Avg DMG": "6命超绽放连招 · 平均伤害",
    "C6 Vape Hyperbuffed, Avg DMG": "6命蒸发（高增益）· 平均伤害",
    "Childe International, Avg DMG": "公子国际队 · 平均伤害",
    "Double Hydro Burst, Avg DMG": "双水爆发 · 平均伤害",
    "Double Hydro Combo, Avg DMG": "双水连招 · 平均伤害",
    "Double Hydro, Avg DMG": "双水 · 平均伤害",
    "Double Pyro Double Geo, Avg DMG": "双火双岩 · 平均伤害",
    "EM + ER (+ CR) balance formula": "精通+充能(+暴击) 平衡公式",
    "EQ + Heal + ER balance formula": "EQ+治疗+充能 平衡公式",
    "EQ with Geo Construct, Avg DMG": "EQ（岩造物）· 平均伤害",
    "EQ3CA Without Buffs, Avg DMG": "EQ3CA 无增益 · 平均伤害",
    "Elemental Skill with C2 buffs, Avg DMG": "战技（2命增益）· 平均伤害",
    "Elemental Skill, Avg DMG": "战技 · 平均伤害",
    "Exquisite Throw Double Hydro, Avg DMG": "璇玑屏双水 · 平均伤害",
    "FFXX Premium Team, Avg DMG": "FFXX 高配队 · 平均伤害",
    "Forward Vaporize Combo with C2 buffs, Avg DMG": "正向蒸发连招（2命增益）· 平均伤害",
    "Forward Vaporize Combo, Avg DMG": "正向蒸发连招 · 平均伤害",
    "Forward Vaporize with Xilonen, Avg DMG": "正向蒸发（希诺宁）· 平均伤害",
    "Freeze Team Combo, Avg. DMG": "冻结队连招 · 平均伤害",
    "Freeze Team, Avg DMG": "冻结队 · 平均伤害",
    "Full Combo with C2 Kazuha, Avg DMG": "完整连招（2命万叶）· 平均伤害",
    "Full Combo, Avg DMG": "完整连招 · 平均伤害",
    "Furina Vape Combo, Avg DMG": "芙宁娜蒸发连招 · 平均伤害",
    "Furina Variant Combo, Avg DMG": "芙宁娜变体连招 · 平均伤害",
    "HP + ER balance formula": "生命+充能 平衡公式",
    "Heal + ER balance formula": "治疗+充能 平衡公式",
    "Hybrid Build, Burst DMG + HP balance formula": "混合配装 · 爆发+生命 平衡公式",
    "Hyper Combo, Avg DMG": "超激化连招 · 平均伤害",
    "Hyper Double Hydro, Avg DMG": "超激化双水 · 平均伤害",
    "Hyper Mono Geo NA combo, Avg DMG": "超激化纯岩普攻连招 · 平均伤害",
    "Hyper Premium Double Hydro, Avg DMG": "超激化高配双水 · 平均伤害",
    "Hyper Raiden Burst, Avg DMG": "超激化雷神爆发 · 平均伤害",
    "Hyper Wanderer, Avg DMG": "超激化流浪者 · 平均伤害",
    "Hyperbloom Team, Avg DMG": "超绽放队 · 平均伤害",
    "Ice Shard, Morgana Team, Avg DMG": "冰棱 · 莫甘娜队 · 平均伤害",
    "International Vape Team, Avg DMG": "国际蒸发队 · 平均伤害",
    "Lunar-Bloom Team with C2 Nahida, Avg DMG": "月绽放队（2命纳西妲）· 平均伤害",
    "Lunar-Bloom Team, Avg DMG": "月绽放队 · 平均伤害",
    "Lunar-Charged Team, Avg DMG": "月感电队 · 平均伤害",
    "Lunar-Crystallize Team, Avg DMG": "月结晶队 · 平均伤害",
    "Melt Combo, Avg DMG": "融化连招 · 平均伤害",
    "Mono Geo Arataki Kesagiri Final Slash, Avg DMG": "纯岩荒泷盛势终刀 · 平均伤害",
    "Mono Hydro Team, Avg DMG": "纯水队 · 平均伤害",
    "Mono Pyro 3CAQE, Avg DMG": "纯火 3重击QE · 平均伤害",
    "Mono Pyro Combo, Avg DMG": "纯火连招 · 平均伤害",
    "Mono Pyro EQ, Avg DMG": "纯火 EQ · 平均伤害",
    "Mono Pyro Pyronado Avg DMG": "纯火旋火轮 · 平均伤害",
    "Moonsign Carry Team, Avg DMG": "月兆主C队 · 平均伤害",
    "National Pyronado Vape Avg DMG": "国家队旋火轮蒸发 · 平均伤害",
    "National Raiden Burst, Avg DMG": "雷国爆发 · 平均伤害",
    "National Team, Avg DMG": "国家队 · 平均伤害",
    "Nuke Build, Burst Avg DMG": "爆发配装 · 爆发平均伤害",
    "Off-field Bloom Team 2H2D Damage Contribution": "后台绽放队 2水2草伤害贡献",
    "Off-field Tri-Karma Purification": "后台三业净灭",
    "Off-field Tri-Karma Purification Spread": "后台三业净灭蔓激化",
    "Old Hyper Xiao Team, Avg DMG": "旧超激化魈队 · 平均伤害",
    "On-Field Main DPS Team, Avg DMG": "前台主C队 · 平均伤害",
    "On-field Tri-Karma Purification Spread": "前台三业净灭蔓激化",
    "Overload Combo, Avg DMG": "超载连招 · 平均伤害",
    "Overload Combo, DPS": "超载连招 · DPS",
    "Overload Team, Avg DMG": "超载队 · 平均伤害",
    "Overvape Combo, Avg DMG": "蒸发超载连招 · 平均伤害",
    "Premium Lunar-Crystallize Team, Avg DMG": "高配月结晶队 · 平均伤害",
    "Premium Melt Combo, Avg DMG": "高配融化连招 · 平均伤害",
    "Premium Team vs Boss, Avg DMG": "高配队对首领 · 平均伤害",
    "Premium Team vs Frozen, Avg DMG": "高配队对冻结 · 平均伤害",
    "Quickbloom Combo, Avg DMG": "超绽放连招 · 平均伤害",
    "Quickbloom Combo, DPS": "超绽放连招 · DPS",
    "Quicken Combo, Avg DMG": "原激化连招 · 平均伤害",
    "Quicken Team, Avg DMG": "原激化队 · 平均伤害",
    "Quicken/Spread Team Combo, Avg DMG": "原激化/蔓激化队连招 · 平均伤害",
    "Raikou Skill + Burst Combo, Avg DMG": "雷祸战技+爆发连招 · 平均伤害",
    "Raw Oz Avg DMG": "裸奥兹 · 平均伤害",
    "Raw Pyro Combo, Mono Pyro, Avg DMG": "裸火连招 · 纯火 · 平均伤害",
    "Shenhe Team vs Boss, Avg DMG": "申鹤队对首领 · 平均伤害",
    "Shenhe Team vs Frozen, Avg DMG": "申鹤队对冻结 · 平均伤害",
    "Shieldbot, Max HP": "盾辅 · 最大生命",
    "Shunsuiken 1-Hit DMG, Double Geo, Avg DMG": "瞬水剑一段 · 双岩 · 平均伤害",
    "Simulated Buff": "模拟增益",
    "Skill + Burst Burning Combo, Avg DMG": "战技+爆发燃烧连招 · 平均伤害",
    "Skill + Burst Combo, Avg DMG": "战技+爆发连招 · 平均伤害",
    "Skill + Burst, Avg DMG": "战技+爆发 · 平均伤害",
    "Solo Combo, Avg. DMG": "单人连招 · 平均伤害",
    "Solo Full Burst, Avg DMG": "单人满爆发 · 平均伤害",
    "Spread Team, Avg DMG": "蔓激化队 · 平均伤害",
    "Stellar-Conduct Basic Team, Avg DMG": "星极基础队 · 平均伤害",
    "Stellar-Conduct Double Cryo, Avg DMG": "星极双冰 · 平均伤害",
    "Stellar-Conduct Triple Cryo, Avg DMG": "星极三冰 · 平均伤害",
    "Sunfire combo, Avg DMG": "日火连招 · 平均伤害",
    "Swirl DMG": "扩散伤害",
    "Sword Rain, Avg DMG": "剑雨 · 平均伤害",
    "Taser Team, Avg DMG": "感电队 · 平均伤害",
    "Taser with simulated team, Avg DMG": "感电（模拟队）· 平均伤害",
    "Transient Blossom, Avg DMG": "刹那之花 · 平均伤害",
    "Triple Cryo, Avg DMG": "三冰 · 平均伤害",
    "Triple Dendro with C2 Nahida, Avg DMG": "三草（2命纳西妲）· 平均伤害",
    "Triple Dendro, Avg DMG": "三草 · 平均伤害",
    "Unbuffed EQ Combo, Avg DMG": "无增益 EQ 连招 · 平均伤害",
    "VV Swirl Hyper Tao Combo, Avg DMG": "翠绿扩散超激化胡桃连招 · 平均伤害",
    "Vape Combo, Avg DMG": "蒸发连招 · 平均伤害",
    "Vape Combo, Double Geo, Avg DMG": "蒸发连招 · 双岩 · 平均伤害",
    "Vape Minimal Buffs, Avg DMG": "蒸发（低增益）· 平均伤害",
    "Vape-Melt Team Combo, Avg. DMG": "蒸发融化队连招 · 平均伤害",
    "Violet Arc, Avg DMG": "苍雷 · 平均伤害",
    "Wind's Grand Ode AoE, Avg DMG": "风神之诗范围 · 平均伤害",
    "Wind's Grand Ode Single Target, Avg DMG": "风神之诗单体 · 平均伤害",
}

SHORTS: dict[str, str] = {
    "AGGR.": "激化",
    "AOE": "范围",
    "ATK+ER+CR": "攻击充能暴击",
    "BLOOM": "绽放",
    "BLOSSOM": "刹那之花",
    "BOSS": "首领",
    "BUFF": "增益",
    "BURNMELT": "燃烧融化",
    "BURNVAPE": "燃烧蒸发",
    "BURST": "爆发",
    "C2 COMBO": "2命连招",
    "C2 SKILL": "2命战技",
    "C2 VAPE": "2命蒸发",
    "C6 BLOOM": "6命绽放",
    "C6 COMBO": "6命连招",
    "C6 CRIT HIT": "6命暴击",
    "C6 HYPER": "6命超绽放",
    "C6 VAPE": "6命蒸发",
    "COMBO": "连招",
    "CRITFISH": "吃暴击",
    "E+Q": "EQ",
    "EM+ER+CR": "精通充能暴击",
    "FFXX": "FFXX",
    "FREEZE": "冻结",
    "HEAL+ER": "治疗充能",
    "HP+ER": "生命充能",
    "HYBRID": "混合",
    "HYPER": "超激化",
    "LUNAR": "月反应",
    "MAX HP": "最大生命",
    "MELT": "融化",
    "MONO": "纯色",
    "NUKE": "爆发",
    "OFF-FIELD": "后台",
    "ON-FIELD": "前台",
    "OVERLOAD": "超载",
    "OVERVAPE": "蒸发超载",
    "OZ": "奥兹",
    "QB COMBO": "超绽放",
    "QUICKEN": "原激化",
    "RAIKOU": "雷祸",
    "SKILL": "战技",
    "SOLO": "单人",
    "SOUP": "汤队",
    "SPREAD": "蔓激化",
    "STELLAR": "星极",
    "SUNFIRE": "日火",
    "SUPPORT": "辅助",
    "SWIRL": "扩散",
    "TASER": "感电",
    "VAPE": "蒸发",
    "VAPEMELT": "蒸发融化",
    "NATIONAL": "国家队",
}

VARIANTS: dict[str, str] = {
    "110er": "110% 充能",
    "120er": "120% 充能",
    "130er": "130% 充能",
    "150er": "150% 充能",
    "160er": "160% 充能",
    "170er": "170% 充能",
    "180er": "180% 充能",
    "110% ER": "110% 充能",
    "120% ER": "120% 充能",
    "130% ER": "130% 充能",
    "140% ER": "140% 充能",
    "150% ER": "150% 充能",
    "160% ER": "160% 充能",
    "170% ER": "170% 充能",
    "180% ER": "180% 充能",
    "c2": "2命",
    "c6": "6命",
    "c2-130er": "2命 130% 充能",
    "c2-160er": "2命 160% 充能",
    "furnace": "炉心",
    "vv": "翠绿",
}

PHRASES: dict[str, str] = {
    " Team, Avg DMG": "队 · 平均伤害",
    ", Avg. DMG": " · 平均伤害",
    ", Avg DMG": " · 平均伤害",
    " Avg DMG": " · 平均伤害",
    "Avg DMG": "平均伤害",
    " Team": "队",
    "% ER": "% 充能",
    "SUBSTAT": "模拟",
    "TEAMS": "榜单",
    "Normal Attack ": "普攻",
    " (1 soss stack)": "（赤沙1层）",
    " (2 soss stacks)": "（赤沙2层）",
    " (1 pjws stack)": "（和璞鸢1层）",
    " (2 pjws stacks)": "（和璞鸢2层）",
    " (3 pjws stacks)": "（和璞鸢3层）",
    " (4 pjws stacks)": "（和璞鸢4层）",
    " (5 pjws stacks)": "（和璞鸢5层）",
    " (6 pjws stacks)": "（和璞鸢6层）",
    " (7 pjws stacks)": "（和璞鸢7层）",
    "Riptide #": "断流·",
    "CA1": "重击一段",
    "CA2": "重击二段",
    "N1": "普攻一段",
    "N2": "普攻二段",
    "N3": "普攻三段",
    "N4": "普攻四段",
    "N5": "普攻五段",
    "Normal Attack 1": "普攻一段",
    "Normal Attack 2": "普攻二段",
    "Normal Attack 3": "普攻三段",
    "Normal Attack 4": "普攻四段",
    "Normal Attack 5": "普攻五段",
    "Northland Spearstorm": "北国枪阵",
    "Thunderous Symphony Additional": "雷霆交响额外",
    "Thunderous Symphony": "雷霆交响",
    "Lunar-Charged": "月感电",
    "Lunar-Crystallize": "月结晶",
    "Lunar-Bloom": "月绽放",
    "Stellar-Conduct": "星超导",
    "Stellar Swirl": "星扩散",
    "Sweeping Fire": "扫射",
    "Condensed Beam": "冷凝射线",
    "Prism Shot": "棱晶弹",
    "Convective Inhibition Ray": "负温聚能光束",
    "Bombardment": "轰炸",
    "Charged Attack": "重击",
    "Normal Attack": "普攻",
    "Elemental Burst": "爆发",
    "Elemental Skill": "战技",
    "High Plunge": "高空下落",
    "Hyperbloom": "超绽放",
    "Aggravate": "激化",
    "Overloaded": "超载",
    "Overload": "超载",
    "Pyronado": "旋火轮",
    "Vape": "蒸发",
    "Melt": "融化",
    "Spread": "蔓激化",
    "Plunge": "下落",
}

TYPES: dict[str, str] = {
    "E": "战技",
    "Q": "爆发",
    "NA": "普攻",
    "N": "普攻",
    "CA": "重击",
    "LC": "月感电",
    "LCR": "月结晶",
    "LB": "月绽放",
    "A": "普攻",
    "SSC": "星超导",
    "SSW": "星扩散",
    "B": "重击",
    "A1": "固有1",
    "ATK": "攻击",
    "EM": "精通",
    "ER": "充能",
    "HP": "生命",
    "HB": "治疗加成",
    "Set": "套装",
}

PARTS_FILE = ROOT / "genshinuid_enka" / "akasha_parts_zh.json"
HARVEST = ROOT.parent / "test_output" / "gs_detail" / "akasha_part_names.json"


def load_parts() -> dict[str, str]:
    raw = json.loads(PARTS_FILE.read_text(encoding="utf-8"))
    parts = raw["parts"] if isinstance(raw, dict) and "parts" in raw else raw
    if not isinstance(parts, dict):
        raise SystemExit("akasha_parts_zh.json 缺少 parts")
    out: dict[str, str] = {}
    for key, val in parts.items():
        if isinstance(key, str) and isinstance(val, str):
            out[key] = val
    if HARVEST.exists():
        live = json.loads(HARVEST.read_text(encoding="utf-8"))
        names = live["names"] if isinstance(live, dict) and "names" in live else []
        if isinstance(names, list):
            missing = sorted(n for n in names if isinstance(n, str) and n not in out)
            if missing:
                raise SystemExit(f"未翻译伤害分段 {len(missing)} 条:\n" + "\n".join(missing[:80]))
    return out


def main() -> None:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    en = json.loads((MAP / "enName2AvatarID_mapping_7.0.0.json").read_text(encoding="utf-8"))
    id2n = json.loads((MAP / "avatarId2Name_mapping_7.0.0.json").read_text(encoding="utf-8"))
    w2n = json.loads((MAP / "weaponId2Name_mapping_7.0.0.json").read_text(encoding="utf-8"))
    chars: dict[str, str] = {}
    for name, aid in en.items():
        if isinstance(name, str) and isinstance(aid, str) and aid in id2n:
            chars[name] = id2n[aid]
    weapons: dict[str, str] = {}
    live_names: set[str] = set()
    live_shorts: set[str] = set()
    for item in cat["data"]:
        if "name" in item and isinstance(item["name"], str):
            live_names.add(item["name"])
        if "short" in item and isinstance(item["short"], str):
            live_shorts.add(item["short"])
        if "weapons" in item and isinstance(item["weapons"], list):
            for w in item["weapons"]:
                if not isinstance(w, dict) or "name" not in w:
                    continue
                wname = w["name"]
                wid = str(w["weaponId"]) if "weaponId" in w else ""
                if isinstance(wname, str) and wid in w2n:
                    weapons[wname] = w2n[wid]
    missing = sorted(n for n in live_names if n not in NAMES)
    if missing:
        raise SystemExit("未翻译队名:\n" + "\n".join(missing))
    missing_s = sorted(s for s in live_shorts if s not in SHORTS)
    if missing_s:
        raise SystemExit("未翻译简称:\n" + "\n".join(missing_s))
    parts = load_parts()
    out = {
        "source": "https://akasha.cv/api/v2/leaderboards/categories",
        "phrases": dict(sorted(PHRASES.items(), key=lambda kv: -len(kv[0]))),
        "names": dict(sorted(NAMES.items())),
        "shorts": dict(sorted(SHORTS.items())),
        "variants": dict(sorted(VARIANTS.items())),
        "weapons": dict(sorted(weapons.items())),
        "chars": dict(sorted(chars.items())),
        "types": dict(sorted(TYPES.items())),
        "parts": dict(sorted(parts.items())),
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT.name} names={len(NAMES)} shorts={len(SHORTS)} "
        f"weapons={len(weapons)} chars={len(chars)} parts={len(parts)}"
    )


if __name__ == "__main__":
    main()

---
name: update-enka-effects
description: >
  Update GenshinUID genshinuid_enka/effect JSON from yatta changelog (skill_add,
  weapon_effect, artifact_effect, char_effect, char_action, value_attr, dmg_map).
  Use when the user asks to update enka effects, skill_add, weapon_effect,
  artifact_effect, char_action, version effect configs, 更新面板效果, 更新命座加技,
  or runs /update-enka-effects.
---

# Update Enka Effects

Automate version bumps for damage-panel configs under:

`GenshinUID/genshinuid_enka/effect/`

## When to run

- New Genshin version (roles / weapons / artifacts)
- User mentions `skill_add` / `weapon_effect` / `artifact_effect` / effect 文件夹
- After `download_icon.py` or map data refresh for the same version

## Command (primary)

From repo root (`plugins/GenshinUID`):

```bash
python GenshinUID/tools/update_effects.py -v 7.0
python GenshinUID/tools/update_effects.py -v 7.0 --dry-run
python GenshinUID/tools/update_effects.py -v 7.0 --only skill_add,weapon_effect
python GenshinUID/tools/update_effects.py -v latest --include-skin
```

Script path: `GenshinUID/tools/update_effects.py`  
Report: `GenshinUID/genshinuid_enka/effect/_update_report_<ver>.md`

## What each file gets

| File | Automation |
|------|------------|
| `skill_add.json` | **Full**: C3/C5 text + talent icons → `["E","Q"]` etc. |
| `weapon_effect.json` | Scaffold + simple CN→DSL heuristic from affix R1–R5 |
| `artifact_effect.json` | Scaffold + simple 2/4pc heuristic |
| `char_effect.json` | Empty scaffold for new chars |
| `value_attr.json` | Heuristic from `specialProp` |
| `char_action.json` | Talent promote multipliers → action table |
| `dmg_map.json` | Empty `[]` placeholder only |

Read DSL rules in `references/effect-dsl.md`.

## Agent workflow

1. Confirm version (`7.0` / `latest`) and `vh` if needed (default `70F0`).
2. Run `update_effects.py` (not dry-run unless user asked to preview).
3. Open the generated `_update_report_*.md`.
4. **Must human-review**:
   - Any `weapon_effect` / `artifact_effect` with empty strings or incomplete fight buffs
   - Complex conditional weapons (stacks, team buffs, new reactions)
   - `char_effect` empty shells
   - `dmg_map` empty lists (reference panels)
5. Optionally refine DSL by hand using `references/effect-dsl.md` and yatta Chinese affix text (also cached under `GenshinUID/tools/gs_data/`).
6. Do **not** invent multi-stack / team / reaction numbers without reading the affix text.
7. For `skill_add`, trust the script; it maps **C3 then C5** (code uses talent count ≥3 and ≥5), not C6.
8. After edits, summarize: new names, filled vs empty, files touched.

## Related tools

- Icons: `GenshinUID/tools/download_icon.py`
- Full char_action rebuild (legacy): `GenshinUID/tools/get_action.py` (heavier, needs map deps)
- Map lists: `GenshinUID/utils/map/data/charList_*.json`, `weaponList_*.json`

## Effect value policy（强制）

写 `weapon_effect` / `artifact_effect` / `char_effect` 时：

1. **一律取最高**：区间取上限（最低/最高 → 最高）；叠层取满层；条件能同时满足的全部叠上。
2. **限定可忽略**：如「旅行者装备时」仍按能吃满处理。
3. **互斥才人工**：多个效果同一时间只能生效一个（如轮转乐章、同元素/异元素抢层）时，在 `extra.note` 写明默认取法与备选，并在报告里标【互斥】。
4. 不要用空字符串敷衍已有数值的精炼；R1–R5 都要填满。
5. **星烁属性无冒号**：用 `stellarDmgBonus+32`，不要 `stellar:DmgBonus`（`:` 表示 A/E/Q 技能限制）。

### 星烁 / 月曜伤害

| 模块 | 说明 |
|------|------|
| `Fight.get_stellar_dmg` | 星超导 / 星扩散（直伤 + 反应星扩散） |
| `Fight.get_lunar_dmg` | 月感电 / 月绽放 / 月结晶（直伤 + 反应） |
| `get_action.py` → `extra` | 为角色挂 `(星超导)`/`(星扩散)`/`(月感电)`/`(月绽放)`/`(月结晶)` 变体 |

月曜基础系数：月感电 **3**、月绽放 **1**、月结晶 **1.6**。  
星烁：直伤星超导满层 **2**、直伤星扩散 **1**、反应星扩散·冰满涡 **3** / ·风 **0.75**。

详细 DSL 与公式见 `references/effect-dsl.md`。

## Quality bar before telling user “done”

- [ ] `skill_add` has every new non-traveler character
- [ ] New weapons appear in `weapon_effect` (skin skipped by default) with **max** R1–R5 values
- [ ] New artifact sets appear in `artifact_effect` with max 2/4pc
- [ ] Mutual-exclusive items flagged in report / `extra.note`
- [ ] Empty fight/4pc only when truly no panel stat

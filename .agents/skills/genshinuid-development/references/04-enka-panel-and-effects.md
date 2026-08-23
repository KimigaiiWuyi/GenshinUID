# 四、面板、伤害与 effect JSON

> 返回 [SKILL.md](../SKILL.md)。版本更新效果文件请改走
> [update-enka-effects](../../update-enka-effects/SKILL.md)。

## 4.1 模块职责

`genshinuid_enka/` 是本插件最重的包：

| 文件 | 职责 |
|------|------|
| `__init__.py` | SV：面板查询 / 排名 / 管理 |
| `get_enka_img.py` | 拉数据 + 画角色卡入口 |
| `to_data.py` / `to_data_by_mys.py` / `to_card.py` | Enka / 米游社 → 内部卡片结构 |
| `draw_char_card.py` `draw_char_info.py` 等 | PIL 出图 |
| `dmg_calc/` `mono/` | 伤害计算 |
| `effect/*.json` | 命座加技、武器/圣遗物/角色效果 DSL |
| `etc/` | 静态表 |

配置：

- `OldPanle`：旧面板（更快，功能少）。
- `DefaultBaseBG` / `RandomPic`：背景策略。
- `RefreshDataList` 不在原神 config 里；原神刷新顺序在 enka 的 API 切换（`switch_api`）。

## 4.2 effect JSON

路径：`GenshinUID/genshinuid_enka/effect/`。

| 文件 | 谁填 |
|------|------|
| `skill_add.json` | 脚本可全自动（C3/C5 → 天赋） |
| `weapon_effect.json` | 脚本脚手架 + 人工补复杂武器 |
| `artifact_effect.json` | 同上 |
| `char_effect.json` | 新角色空壳，必须手写战斗加成 |
| `char_action.json` | 天赋倍率表 |
| `dmg_map.json` | 参考面板，脚本只给 `[]` |
| `value_attr.json` | 特殊属性启发式 |

DSL 规则：`.agents/skills/update-enka-effects/references/effect-dsl.md`。
取值一律取能吃满的上限；互斥效果在 `extra.note` 标明。

更新命令（插件根）：

```sh
python GenshinUID/tools/update_effects.py -v 7.0
python GenshinUID/tools/update_effects.py -v 7.0 --dry-run
```

## 4.3 不要做的事

- 不要在 `draw_*` 里硬编码某角色姓名/口癖（框架人格锁定红线；这里是**游戏数据**角色名可以出现在地图 JSON 与 effect 键里）。
- 不要改 `tools/` 生成结果却不更新 `Genshin_version` 与 `utils/map/data/*_{ver}.json`。
- 不要把伤害公式复制到 `genshinuid_ai_func`；AI 要数值走已有面板文本工具或触发器出图。

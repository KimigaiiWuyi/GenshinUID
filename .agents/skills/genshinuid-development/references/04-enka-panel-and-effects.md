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
| `artifact_times.py` | 圣遗物副词条 `times` / Enka `rolls` 档位 1–4 / `isMax` |
| `html_char_card.py` / `hero_art.py` / `akasha_side.py` / `akasha_store.py` | `gs查询{角色}` 竖版一图流：左列 640 CSS 宽、`SCALE=4` 出 2560 实图；强制刷新落盘的 `players/{uid}/akasha/{char_id}.json` 存在时右列再 640（最上伤害分布 + 副词条收益表 + 队伍榜，合计 1280 CSS / 5120 实图），旧缓存没有该文件则保持单列。页顶用户 banner 贴紧立绘；题头整幅同一张立绘；黑从最右淡到最左（ease-in，不要硬切、不要再叠 CSS 顶遮罩、题头底边不要圆角）；元素图标走 `texture2d/element`（角色名、元素伤害等）；属性条无大玻璃外框，词条 ICON 去白边后与元素伤害 logo 同尺寸；技能名前加 AEQ 键；命座/好感用 `texture2d/mz` 与 `hg`；有效词条金边外发光；圣遗物不写部位名；武器/圣遗物等级作图标右下角标，正文避开图标；总览条左侧 Akasha 1% 雷达（无数据则不画）；词条分红/橙/紫/白/灰并与「词条」底对齐；紫/橙/红词条整行上色，蓝/绿保持白字；属性斑马为深浅黑条；属性框上方小灰字标 `dataTime` |
| `draw_char_card.py` `draw_char_info.py` 等 | 角色卡入口 / 其它 PIL 出图 |
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
| `akasha_1p_avg.json` | 各 Akasha 榜 top 1% 面板算术平均（与玩家无关） |

DSL 规则：`.agents/skills/update-enka-effects/references/effect-dsl.md`。
取值一律取能吃满的上限；互斥效果在 `extra.note` 标明。

更新命令（插件根）：

```sh
python GenshinUID/tools/update_effects.py -v 7.0
python GenshinUID/tools/update_effects.py -v 7.0 --dry-run
python GenshinUID/tools/update_akasha_1p.py
python GenshinUID/tools/update_akasha_1p.py --dry-run
```

## 4.3 不要做的事

- 不要在 `draw_*` 里硬编码某角色姓名/口癖（框架人格锁定红线；这里是**游戏数据**角色名可以出现在地图 JSON 与 effect 键里）。
- 不要改 `tools/` 生成结果却不更新 `Genshin_version` 与 `utils/map/data/*_{ver}.json`。
- 不要把伤害公式复制到 `genshinuid_ai_func`；AI 要数值走已有面板文本工具或触发器出图。

## 4.4 Akasha top 1% 与副词条优先级

`akasha_1p_avg.json` 的 `avgStats` 是**某条榜单**（`calculationId`，可带 `170er` 等变体）伤害分最高 1% 配装的面板算术平均，跟查谁的档案无关。版本更新后跑 `python GenshinUID/tools/update_akasha_1p.py` 整文件替换。脚本只用 httpx，不拉起 Core。UA 必须与 `_CvApi` 一致（`GsCore / GenshinUID / …`），Chrome UA 会被 Cloudflare 403。

角色卡上的 **Show substat priority** 是另一套数：`GET /api/substatPriority/{uid}/{md5}`，在**当前这套装**上再加一发五星满幅副词条后重算榜分。这些接口只在 `mys/enka强制刷新` 时打，写入 `players/{uid}/akasha/{char_id}.json`；`gs查询` 只读盘。

```text
% gain over base = 100 * result / Base.result - 100
```

实现：`utils/api/cv/substat_priority.py`（公式）+ `_CvApi.get_substat_priority` / `get_substat_priority_boards`（请求）。
相同 `uid` + `md5` 进程内缓存 1 小时，并发相同请求合并；errno 不缓存。

角色卡上的 **Show/Hide leaderboards** 同源落盘：`GET /api/leaderboards/{uid}/{md5}?variant=profilePage` 的 `data.calculations`。每条是这套装在某个队伍榜（可带 `170er`）上的名次、伤害分、队友。

```text
top N% = min(100, ceil(ranking / outOf * 100))
```

实现：`utils/api/cv/build_leaderboards.py` + `_CvApi.get_build_leaderboards` / `get_visible_leaderboards`。
相同 `uid` + `md5` 进程内缓存 1 小时，并发相同请求合并；errno 不缓存。
`getCalculationsForUser` 只有一条 `fit`，不是这张表。

角色卡上的 **Show damage distribution** 是**这套装自己的伤害拆分**（技能/反应各打多少），不是全服直方图。换玩家数值会变，换同一条榜只是拆分项名字一样。

```text
GET /api/damageDistribution/{calculationId}/{uid}/{md5}
```

`calculationId` 用榜 ID 前 10 位（不含 `170er`）。一次返回该角色全部队伍榜的 `additional[]`；前端再按当前高亮榜挑一条画堆叠条。`% of Result = value * quantity / result`。有 `name=Time` 时会再除时间显示 DPS。这和 `charts/calculations` 的百分位分桶不是一回事。

实现：`utils/api/cv/damage_distribution.py` + `_CvApi.get_damage_distribution` / `get_damage_distribution_board`。
缓存键是 `uid` + `md5`（一次拉全榜，换 `calculationId` 不重复打），1 小时，并发合并；errno 不缓存。

右列 HTML 在 `akasha_side.py`（单测 spec-load，不要从 `html_char_card` 进）。`mys/enka强制刷新` **等** `_restore_cv_data` 把 `rank.json` 和每名角色的 `players/{uid}/akasha/{char_id}.json` 写完才返回；`gs查询` **只读盘、不打 Akasha**。没有该文件（旧缓存）就不画右列。伤害分布一行两套（图例小字居中；技能名前 A/E/Q/B/C 与蒸发等反应标）；副词条两套；全球排名取自己附近最多 3 条（`p=lt|{result}`），样式对齐 Akasha 列表。属性框正上方右对齐小灰字标 `dataTime`（缺字段就不画）。

队名中文在 `genshinuid_enka/akasha_zh.json`，由 `https://akasha.cv/api/v2/leaderboards/categories` 全量抽出。更新：先拉分类 JSON，再跑 `python GenshinUID/tools/build_akasha_zh.py`。

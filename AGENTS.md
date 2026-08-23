# AGENTS.md

> 本文件遵循 [AGENTS.md](https://agents.md/)：给编码 Agent 的仓库说明（README for agents）。
> 人类用户说明见 [README.md](./README.md)。**源码是唯一事实源**。
>
> 面板 / 绑定 / AI：按需读
> [`.agents/skills/genshinuid-development/SKILL.md`](.agents/skills/genshinuid-development/SKILL.md)，
> **不要**一次把所有 `references/` 塞进上下文。

本仓库是 **GsCore 业务插件**，独立 git（默认分支 `v4`）。放到 `gsuid_core/plugins/GenshinUID/` 安装。

## Project overview

原神查询：UID 绑定、树脂/深渊/面板/抽卡、Wiki、米游社签到与订阅。

- `Plugins(name="GenshinUID", force_prefix=["gs"], allow_empty_prefix=False, alias=["gsuid"])`。
- 运行时前缀：`utils/message.py` 的 `PREFIX = get_plugin_available_prefix("GenshinUID")`，不要写死 `gs`。
- UID：框架 **`GsBind`**（默认游戏即原神）。Cookie / Stoken：框架 **`GsUser`**。本插件无 Bind 表。
- 面板：`genshinuid_enka/`（Enka / MiniGG / 米游社）。命座与武器效果：`enka/effect/*.json`。
- 命令普遍带 `to_ai`；出图在数据层 `ai_return`。纯文本工具在 `genshinuid_ai_func/`。
- 版本：`GenshinUID/version.py` 的 `GenshinUID_version` / `Genshin_version`（当前 `7.0.0`，与 `utils/map/data/*_7.0.0.json` 对齐）。`pyproject.toml` `[project] version` 与之保持一致。

## Repository map

```
.
├── AGENTS.md / README.md / LICENSE / ICON.png
├── pyproject.toml / ruff.toml / pyrightconfig.json
├── __init__.py / __nest__.py
├── locales/{zh-cn,en,ja}/logs.json    # i18n
├── tests/  test_output/
├── .agents/skills/                    # genshinuid-development / update-enka-effects
└── GenshinUID/
    ├── __init__.py                    # 仅 Plugins(...)
    ├── __full__.py / version.py
    ├── genshinuid_*/                  # 功能子包（下表）
    ├── utils/                         # convert / mys_api / resource / map / rag / image
    └── tools/                         # 离线脚本（ruff exclude）
```

| 子包 | 职责 |
|------|------|
| `genshinuid_user` | 绑定/切换/删除 UID；`ck帮助` |
| `genshinuid_roleinfo` | 角色总览、注册时间 |
| `genshinuid_enka` | 面板、刷新、排名、圣遗物仓、伤害、`effect/` |
| `genshinuid_resin` / `_note` | 体力便签 + 推送；札记 |
| `genshinuid_abyss` / `_poetry_abyss` / `_hard_challenge` | 深渊 / 剧诗 / 幽境危战 |
| `genshinuid_collection` / `_achievement` / `_count` | 探索收集；成就委托；练度 |
| `genshinuid_gachalog` | 抽卡记录导入导出 |
| `genshinuid_guide` / `_wikitext` / `_adv` | 攻略、Wiki、文字推荐 |
| `genshinuid_ann` / `_cale` / `_eventlist` | 公告、日历、活动卡池 |
| `genshinuid_signin` / `_mysbbscoin` / `_mys` | 签到、米游币、娱乐 |
| `genshinuid_gcg` / `_dailycost` / `_compute` / `_map` | 七圣、材料、背包、地图 |
| `genshinuid_code` / `_returnlist` / `_xkdata` / `_season_post` / `_etcimg` | 兑换码、未复刻、深渊使用率/队伍、季报、杂图 |
| `genshinuid_config` / `_help` / `_status` / `_resource` / `_check` / `_data` / `_start` | 配置、帮助、资源、启动 |
| `genshinuid_ai_func` | `@ai_tools`：catalog / kb / user |

`GsBind.insert_uid(..., group_id, 9)` 的 `9` 是 **`lenth_limit`（UID 字符串长度）**，不是绑定个数。

## Skills

| 任务 | 读 |
|------|-----|
| 本插件业务 | [genshinuid-development](.agents/skills/genshinuid-development/SKILL.md) |
| 更新 `enka/effect` JSON | [update-enka-effects](.agents/skills/update-enka-effects/SKILL.md) |
| 代码红线 | Core 根 [`AGENTS.md`](../../../AGENTS.md) §1–§4、§1.9 |

单独 clone 时打开宿主 Core 的 `AGENTS.md`。

## Setup commands

在**本插件目录**执行。解释器指向 Core 根 `.venv`。

```sh
uv run ruff check GenshinUID tests
uv run ruff format --check GenshinUID tests
uv run pytest tests -q
```

`ruff.toml`：`line-length = 120`，排除 `GenshinUID/tools`。
`pyrightconfig.json`：`include = ["GenshinUID"]`，`extraPaths` 指到 Core 根。依赖声明在 `pyproject.toml` `[project]`（uv / PEP 621）。
effect 更新：`python GenshinUID/tools/update_effects.py -v 7.0`（走 update-enka-effects skill）。

## Code style

新代码与 Core 根 `AGENTS.md` **编号一致**，正反例以那份为准。

| 编号 | 要求 |
|------|------|
| §1.1 | 禁止 try-except 兜底。例外：Enka/米游社 JSON；`_ai_return_xxx()` |
| §1.2–1.4 | 禁止 `cast` / 自身 `type: ignore` / `getattr`·`dict.get` 兜底 |
| §1.5 | 标红先改类型或逻辑 |
| §1.6 | `#` 最多两行、每行 ≤88 字 |
| §1.7 | 不改 Core `system_prompt`；动态信息只进 `to_ai` / `ai_return` / 工具返回 |
| §1.8 | 禁止 `Any` |
| §1.9 | 圣遗物 / 命座 / 深渊只出现在本插件 `covers` / `aliases` / 知识库 |
| §2 | 函数全标注；PEP 604 |
| §3 | 本插件不新建 Bind 表；用框架 `GsBind` / `GsUser`。若加表：无 `__tablename__`，`@with_session`，`col()` |
| §4 | 全异步；下载/绘图阻塞用 `to_thread` |

行宽 120。日志用户可见文案走 `gsuid_core.i18n.t(...)`，键在 `locales/`。
`to_ai` 第一行标明「原神」；同一函数不要再叠 `@ai_tools`。
历史代码大量 `dict.get` / 宽 except：**改到哪修到哪**，不要整文件翻风格。

## Testing

- 现有：`tests/test_logger_i18n.py`。新工具补 `tests/test_<module>.py`。
- 禁止把真实 Cookie / UID 提交进仓库。
- 改触发器对照 [`.agents/skills/genshinuid-development/references/05-ai-integration.md`](.agents/skills/genshinuid-development/references/05-ai-integration.md)。

## 本仓库结构约定

- 嵌套加载：`__nest__.py` + `__full__.py`。内层 `__init__.py` **不要**手工 import 子包。
- UID：`utils/convert.py::get_uid`，正则 `\d{9}`，支持 `@`。
- 无 CK 时面板只有 Enka 展柜（最多 12 名），文案必须写明不是完整箱。
- 配置：`gsconfig`；默认值变量名历史拼写 **`CONIFG_DEFAULT`**，不要无意义重命名。
- 订阅任务名带 `[原神]`，走 `gs_subscribe`。
- RAG：`utils/message.py` 副作用加载 `utils.rag.register`。检索 `plugin_filter=["GenshinUID"]`。
- 路径单源：`utils/resource/RESOURCE_PATH.py`。

## 坑点

1. 本插件 `GsBind` 不要传 `game_name="zzz"`。
2. UID 保持 9 位（`lenth_limit=9` 与 `\d{9}` 一致）。
3. `EnableCharCardByMys` 开了可能验证码。
4. 版本更新必须成套改 `version.py` + `utils/map/data/*_{ver}.json` + `update_effects.py`。
5. `tools/` 不进 ruff；业务逻辑不要藏进去。
6. 改 `t("log.genshinuid.…")` 要三份 locales 一起改。
7. 配置键 `OldPanle` 是历史拼写。

## Security notes

- Cookie / Stoken 禁止进 git、禁止 `logger.info` 全文。
- `pm=1/2` 命令（清缓存、下载资源、强制推送）不要降权。
- 公网 Core：`WS_TOKEN` / WebConsole。

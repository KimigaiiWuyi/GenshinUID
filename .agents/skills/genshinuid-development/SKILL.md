---
name: genshinuid-development
description: >
  当用户要求"维护/开发 GenshinUID"、"原神插件怎么加命令"、"面板/Enka 怎么出图"、
  "绑定 UID / Cookie"、"树脂推送 / 签到"、"抽卡记录"、"深渊/剧诗/幽境危战"、
  "to_ai / ai_return 怎么写"、"genshinuid_ai_func"、"原神知识库 RAG"、
  "gsconfig / CONIFG_DEFAULT"、"地图 JSON 版本"、"改 GenshinUID 有哪些坑"
  时触发此 SKILL。
  凡是改动 `gsuid_core/plugins/GenshinUID` 业务代码的任务都应优先读取此 SKILL。
  更新 enka/effect JSON 请改走 update-enka-effects skill。
---

# GenshinUID 插件开发与维护指南（核心入口）

> 面向本插件维护者。源码是唯一事实源。需要某专题时按表 **Read 一篇** `references/`，
> 不要一次塞进上下文。改核心机制后同步对应章节。

## 谁该读这个 SKILL

| 你的任务 | 该读的文档 |
|----------|-----------|
| **改 GenshinUID 业务**（命令 / 面板 / 绑定 / 出图 / AI） | **本 SKILL** |
| 版本更新命座/武器/圣遗物效果 JSON | [update-enka-effects](../update-enka-effects/SKILL.md) |
| 写通用 GsCore 插件 | Core `gscore-plugin-development` |
| 改框架核心 | Core `gscore-development` |
| 代码红线 | 本仓库 [`AGENTS.md`](../../../AGENTS.md) + Core 根 `AGENTS.md` |

## 文档目录索引

| 章节 | 主题 | 链接 |
|------|------|------|
| 一 | 架构与模块全景 | [references/01-architecture-and-modules.md](./references/01-architecture-and-modules.md) |
| 二 | 命令与触发器 | [references/02-commands-and-triggers.md](./references/02-commands-and-triggers.md) |
| 三 | UID / Cookie / 米游社 / Enka API | [references/03-bind-cookie-and-api.md](./references/03-bind-cookie-and-api.md) |
| 四 | 面板、伤害与 effect JSON | [references/04-enka-panel-and-effects.md](./references/04-enka-panel-and-effects.md) |
| 五 | AI：`to_ai` / `ai_return` / `@ai_tools` / RAG | [references/05-ai-integration.md](./references/05-ai-integration.md) |
| 六 | 配置、订阅、启动、帮助 | [references/06-config-database-lifecycle.md](./references/06-config-database-lifecycle.md) |
| 七 | 渲染与资源路径 | [references/07-rendering-and-resources.md](./references/07-rendering-and-resources.md) |
| 八 | 坑点与代码规范 | [references/08-pitfalls-and-conventions.md](./references/08-pitfalls-and-conventions.md) |

## 推荐阅读顺序

1. 第一次接触： [一](./references/01-architecture-and-modules.md)。
2. 加命令： [二](./references/02-commands-and-triggers.md) → 需要战绩时 [三](./references/03-bind-cookie-and-api.md)。
3. 改面板 / 伤害： [四](./references/04-enka-panel-and-effects.md)。
4. 接 AI： [五](./references/05-ai-integration.md)。
5. 动手前： [八](./references/08-pitfalls-and-conventions.md)。

## 关键概念速记

- 前缀 `gs`；运行时 `PREFIX = get_plugin_available_prefix("GenshinUID")`。
- 绑定 `GsBind`（框架表），Cookie `GsUser`。本插件无自己的 Bind 模型。
- UID 抽取正则 `\d{9}`（`utils/convert.py::get_uid`）。
- 面板：`genshinuid_enka/`；无 CK 只有展柜最多 12 名。
- 出图命令用 `to_ai` + 数据层 `ai_return`；纯文本用 `genshinuid_ai_func` 的 `@ai_tools`。
- 知识库 `utils/rag/`，检索必须 `plugin_filter=["GenshinUID"]`。
- 配置变量名历史拼写 `CONIFG_DEFAULT`，不要无意义重命名。
- 订阅任务名带 `[原神]`，走 `gs_subscribe`。

## 验证命令

改完必须全绿，否则不算完成（见本仓库 `AGENTS.md`「交付闸」）：

```sh
# 插件根目录
uv run ruff check GenshinUID tests
uv run ruff format --check GenshinUID tests
uv run pytest tests -q
uv run basedpyright
```

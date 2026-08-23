# 五、AI 集成

> 返回 [SKILL.md](../SKILL.md)

## 5.1 两条路

| 路径 | 何时 |
|------|------|
| 触发器 `to_ai=` + 数据层 `ai_return(...)` | 用户也能打的命令（查询、深渊、抽卡…） |
| `@ai_tools` in `genshinuid_ai_func/` | 只要结构化文本、不出图 |

**同一函数不要两套都挂。**

## 5.2 `to_ai` 写法

第一行：18 字内功能描述，含「原神」，无句号。空行后写适用说法 + `Args`。
`on_fullmatch` 写明「无需参数，留空即可」。

注入点：数据已拿到、**尚未** `bot.send` 图。热路径若先 `return` 缓存图，必须在 return 前 `ai_return`。

允许 `try/except` 的只有 `_ai_return_*` 辅助函数。

改造范围与清单：[`docs/ai_trigger_migration.md`](../../../../docs/ai_trigger_migration.md)、[`docs/AI_TRIGGER_CHANGES.md`](../../../../docs/AI_TRIGGER_CHANGES.md)。

## 5.3 `genshinuid_ai_func`

`__init__.py` 显式 import `kb` / `user` / `catalog`，否则工具不会进注册表。

| 模块 | 工具（名称以源码为准） | 域 |
|------|------------------------|----|
| `catalog.py` | `filter_genshin_chars` 等图鉴筛选 | `capability_domain="原神资料库"` |
| `kb.py` | `search_genshin_kb` | 知识库，强制 `plugin_filter=["GenshinUID"]` |
| `user.py` | UID 列表、账号概览、角色箱文本、单角色面板文本、圣遗物仓文本 | `capability_domain="原神面板"` |

约定：

- `category="common"`，`context_tags` 含 `原神` / `Genshin`。
- `covers` + `aliases`（`原神·…`）必须填，单靠 docstring 召不回。
- 展柜数据必须声明「最多 12 名，不是完整箱」。
- 查他人 UID 仅主人（`is_master`）。

## 5.4 RAG / 别名

`utils/rag/register.py`：

- `ai_alias`：`char_alias.json`
- `ai_entity`：角色/武器/圣遗物/怪物/攻略知识块，数据来自 `CHAR_DATA_PATH` 等

由 `utils/message.py` 顶层 import 触发注册。不要在 handler 里再注册一遍。

## 5.5 不要把垂直词写进框架

圣遗物、命座、深渊、剧诗只出现在本插件的 `covers` / `aliases` / 知识库。Core 分类器不该认识这些词。

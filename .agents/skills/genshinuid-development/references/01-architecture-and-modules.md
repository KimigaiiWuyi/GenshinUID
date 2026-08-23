# 一、架构与模块全景

> 返回 [SKILL.md](../SKILL.md)

GenshinUID 是嵌套加载的 GsCore 插件：外层 `__nest__.py` + 内层 `__full__.py`。
框架扫描 `GenshinUID/genshinuid_*/__init__.py` 注册 `SV` 与触发器。

## 1.1 插件注册

```python
# GenshinUID/__init__.py
Plugins(
    name="GenshinUID",
    force_prefix=["gs"],
    allow_empty_prefix=False,
    alias=["gsuid"],
)
```

用户必须带前缀，例如 `gs查询`、`gs绑定uid`。WebConsole 可改可用前缀，代码读 `PREFIX`。

## 1.2 目录

```
plugins/GenshinUID/
├── GenshinUID/                 # 可 import 包
│   ├── genshinuid_*/           # 功能子包
│   ├── utils/                  # 横切
│   └── tools/                  # 离线脚本（ruff 排除）
├── locales/                    # i18n
├── docs/                       # 人类/Agent 专题
└── .agents/skills/             # 本 SKILL
```

## 1.3 功能子包

| 子包 | 职责 |
|------|------|
| `genshinuid_user` | 绑定/切换/删除 UID；CK 帮助 |
| `genshinuid_roleinfo` | 角色总览、注册时间 |
| `genshinuid_enka` | **面板**、刷新、排名、圣遗物仓、伤害 |
| `genshinuid_resin` | 体力便签 + 定时推送 |
| `genshinuid_note` | 札记 |
| `genshinuid_abyss` | 深境螺旋 |
| `genshinuid_poetry_abyss` | 幻想真境剧诗 |
| `genshinuid_hard_challenge` | 幽境危战 |
| `genshinuid_collection` | 探索/收集/神瞳 |
| `genshinuid_achievement` | 成就/委托 |
| `genshinuid_gachalog` | 抽卡记录导入导出 |
| `genshinuid_guide` | 角色攻略、深渊/剧诗阵容、BBS |
| `genshinuid_wikitext` | Wiki 文字/图片 |
| `genshinuid_adv` | 武器/圣遗物文字推荐 |
| `genshinuid_ann` | 公告与清红 |
| `genshinuid_cale` | 个人日历、活动提醒 |
| `genshinuid_eventlist` | 活动/卡池列表 |
| `genshinuid_signin` | 米游社签到 |
| `genshinuid_mysbbscoin` | 米游币任务 |
| `genshinuid_mys` | 娱乐/游戏攻略 |
| `genshinuid_gcg` | 七圣召唤 |
| `genshinuid_dailycost` | 每日材料 |
| `genshinuid_count` | 练度/毕业度 |
| `genshinuid_compute` | 背包 |
| `genshinuid_map` | 地图查询 |
| `genshinuid_code` / `genshinuid_get_code` | 前瞻兑换码 |
| `genshinuid_returnlist` | 未复刻天数 |
| `genshinuid_xkdata` | 深渊数据库 |
| `genshinuid_season_post` | 季报 |
| `genshinuid_etcimg` | 版本规划/杂图 |
| `genshinuid_config` | 用户开关与阈值 |
| `genshinuid_help` / `genshinuid_status` | 帮助图、状态 |
| `genshinuid_resource` | 下载全部资源（pm=2） |
| `genshinuid_check` / `genshinuid_data` | 缓存清理、v3 导入、重置配置 |
| `genshinuid_start` | `on_core_start` |
| `genshinuid_ai_func` | 纯数据 `@ai_tools` |
| `genshinuid_topup` / `genshinuid_postdraw` | 历史功能，触发器侧基本注释掉 |

## 1.4 `utils/`

| 路径 | 职责 |
|------|------|
| `convert.py` | `get_uid` |
| `message.py` | `PREFIX`、`UID_HINT`、`GButton`、副作用加载 RAG |
| `mys_api.py` | `_MysApi()` 单例 `mys_api` |
| `resource/RESOURCE_PATH.py` | 全部运行时路径 |
| `map/` | 角色/武器/圣遗物/别名 JSON |
| `api/mys` `api/hakush` `api/teyvat` `api/cv` | 各数据源 |
| `rag/` | `ai_entity` / `ai_alias` 注册 |
| `image/` | PIL 工具、公共 texture |
| `fonts/` | 原神字体 |
| `database.py` | 仅遗留 `GsData.db` 路径，**绑定表不在这里** |

## 1.5 请求主链路（面板）

```
gs查询 胡桃
  → sv_get_enka / roleinfo 触发器
  → get_uid(bot, ev)          # 9 位或 GsBind
  → 读 players/{uid} 或拉 Enka/米游社
  → draw_*（数据层 ai_return）
  → bot.send(图)
```

需要实时战绩的功能（树脂、深渊、抽卡）额外要求 Cookie。

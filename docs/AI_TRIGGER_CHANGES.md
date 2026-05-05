# GenshinUID 触发器 AI 调用支持改造文档

## 变更概述

本次改造为 GenshinUID 插件中的**全部触发器**添加了 AI 调用支持，使其能够被 gsuid_core 的 AI 工具系统自动发现和调用。同时移除了 `genshinuid_ai_func` 模块中与触发器重复的手动注册 AI 工具。

## 改造内容

### 1. 核心变更

每个触发器的装饰器（`on_command`、`on_fullmatch`、`on_prefix`、`on_suffix`）都添加了 `to_ai` 参数，用于向 AI 系统描述该触发器的功能、适用场景和参数格式。

### 2. 移除重复的 AI 工具

`genshinuid_ai_func/__init__.py` 中原有的 14 个手动注册的 `@ai_tools` 函数已全部移除，因为它们的功能已被触发器的 `to_ai` 参数完全覆盖。该模块现在仅保留为空的包标识文件。

### 3. `to_ai` 参数格式

`to_ai` 参数采用 Google 风格的 docstring 格式，包含：
- **功能描述**：简要说明触发器的功能
- **适用场景**：说明何时应该调用此触发器
- **Args 部分**（可选）：描述参数格式和示例

示例：
```python
@sv.on_command(
    ("查询深渊", "sy"),
    block=True,
    to_ai="""查询指定UID的深渊战斗信息。
    当用户询问深渊战绩、深渊挑战记录时调用。

    Args:
        text: 可选参数，格式为 "[上期] [层数]"
              - "上期"/"sq"前缀：查询上期深渊
              - 层数：9/10/11/12 或中文数字
    """,
)
```

### 4. 命令前缀说明

GenshinUID 的命令**没有斜杠前缀**，而是根据 bot 配置的前缀（如 `gs`）来触发。例如：
- `gs绑定uid 100000000` — 绑定 UID
- `gs查询深渊` — 查询深渊
- `gs帮助` — 查看帮助

AI 在引导用户使用命令时，应使用正确的前缀格式，而非 `/绑定` 等斜杠命令。

## 改造的触发器清单

### 深渊相关
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_abyss` | 查询深渊 | 查询深渊、sy、深渊 |
| `genshinuid_poetry_abyss` | 查询幻想真境剧诗 | 幻想真境剧诗、新深渊、剧诗 |
| `genshinuid_hard_challenge` | 查询幽境危战 | 幽境危战、新新深渊、yjwz |
| `genshinuid_hard_challenge` | 幽境危战排行榜 | 幽境危战排行榜 |
| `genshinuid_xkdata` | 深渊概览 | 深渊概览、深渊统计 |
| `genshinuid_xkdata` | 深渊队伍 | 深渊队伍、深渊配队 |
| `genshinuid_xkdata` | 角色深渊详情 | 角色深渊详情 |

### 角色与面板
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_enka` | 查询角色面板 | 查询 |
| `genshinuid_enka` | 刷新面板 | 刷新面板、强制刷新 |
| `genshinuid_enka` | 角色橱窗 | 角色橱窗 |
| `genshinuid_enka` | 对比面板 | 对比面板 |
| `genshinuid_enka` | 保存面板 | 保存面板 |
| `genshinuid_enka` | 排名统计 | 排名统计 |
| `genshinuid_enka` | 排名列表 | 排名列表 |
| `genshinuid_enka` | 角色排行榜 | 角色排行榜 |
| `genshinuid_enka` | 角色排名 | 角色排名 |
| `genshinuid_enka` | 圣遗物排名 | 圣遗物排名 |
| `genshinuid_enka` | 圣遗物仓库 | 圣遗物仓库 |
| `genshinuid_enka` | 刷新圣遗物仓库 | 刷新圣遗物仓库 |
| `genshinuid_enka` | 切换api | 切换api |
| `genshinuid_enka` | 原图 | 原图 |
| `genshinuid_roleinfo` | 查询角色信息 | 查询、uid、UID |
| `genshinuid_roleinfo` | 角色列表 | 角色列表 |
| `genshinuid_roleinfo` | 注册时间 | 原神注册时间 |
| `genshinuid_count` | 毕业度统计 | 毕业度统计、练度统计 |

### 探索与收集
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_collection` | 查询完成度 | 查询完成度、wcd |
| `genshinuid_collection` | 查询收集 | 查询收集、sj |
| `genshinuid_collection` | 查询探索 | 查询探索、ts |

### 日常与便笺
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_resin` | 当前状态 | 当前状态 |
| `genshinuid_resin` | 实时便笺 | 每日、mr、便笺 |
| `genshinuid_resin` | 强制推送体力提醒 | 强制推送体力提醒 |
| `genshinuid_note` | 每月统计 | 每月统计 |
| `genshinuid_note` | 当前信息 | 当前信息、zj、札记 |
| `genshinuid_cale` | 个人日历 | 个人日历、日历 |
| `genshinuid_season_post` | 季报 | 季报 |

### 签到与米游币
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_signin` | 签到 | 签到 |
| `genshinuid_signin` | 全部重签 | 全部重签 |
| `genshinuid_mysbbscoin` | 开始获取米游币 | 开始获取米游币 |
| `genshinuid_mysbbscoin` | 全部重获取 | 全部重获取 |

### 抽卡记录
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_gachalog` | 抽卡记录 | 抽卡记录 |
| `genshinuid_gachalog` | 刷新抽卡记录 | 刷新抽卡记录 |
| `genshinuid_gachalog` | 全量刷新抽卡记录 | 全量刷新抽卡记录 |
| `genshinuid_gachalog` | 导出抽卡记录 | 导出抽卡记录 |
| `genshinuid_gachalog` | 从小助手导入 | 从小助手导入抽卡记录 |
| `genshinuid_gachalog` | 导出到小助手 | 导出抽卡记录到小助手 |
| `genshinuid_gachalog` | 导出链接 | 导出抽卡记录链接 |

### WIKI 查询
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_wikitext` | 原魔介绍 | 原魔介绍、查原魔 |
| `genshinuid_wikitext` | 食物介绍 | 食物介绍、查食物 |
| `genshinuid_wikitext` | 圣遗物介绍 | 圣遗物介绍、查圣遗物 |
| `genshinuid_wikitext` | 武器介绍 | 武器介绍、查武器 |
| `genshinuid_wikitext` | 角色天赋 | 角色天赋、查天赋 |
| `genshinuid_wikitext` | 角色介绍 | 角色介绍、查角色 |
| `genshinuid_wikitext` | 角色材料 | 角色材料 |
| `genshinuid_wikitext` | 武器材料 | 武器材料 |
| `genshinuid_wikitext` | 角色命座 | 角色命座、查命座 |

### 攻略与推荐
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_adv` | 角色推荐 | 用什么、能用啥 |
| `genshinuid_adv` | 武器推荐 | 能给谁、谁能用 |
| `genshinuid_guide` | 攻略 | 攻略、推荐 |
| `genshinuid_guide` | 参考面板 | 参考面板 |
| `genshinuid_guide` | 版本深渊 | 版本深渊、深渊阵容 |
| `genshinuid_guide` | 剧诗版本深渊 | 剧诗版本深渊 |
| `genshinuid_guide` | BBS攻略路线 | 路线 |

### 公告与活动
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_ann` | 原神公告 | 原神公告 |
| `genshinuid_ann` | 订阅原神公告 | 订阅原神公告 |
| `genshinuid_ann` | 取消订阅 | 取消订阅原神公告 |
| `genshinuid_ann` | 清除公告红点 | 清除公告红点 |
| `genshinuid_ann` | 自动清红 | 开启/关闭自动清红 |
| `genshinuid_eventlist` | 活动列表 | 活动列表 |
| `genshinuid_eventlist` | 卡池列表 | 卡池列表 |

### 兑换码
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_code` | 兑换码 | 兑换码 |
| `genshinuid_get_code` | 给我兑换码 | 给我一个兑换码 |

### 七圣召唤
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_gcg` | 七圣召唤 | 七圣召唤、qszh |
| `genshinuid_gcg` | 我的卡组 | 我的卡组 |

### 用户管理
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_user` | 绑定/切换/删除UID | 绑定uid、切换uid、删除uid |
| `genshinuid_user` | 绑定帮助 | ck帮助、绑定帮助 |

### 配置管理
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_config` | 配置 | 配置、原神配置 |
| `genshinuid_config` | 设置阈值 | 设置 |
| `genshinuid_config` | 开启/关闭功能 | 开启、关闭 |

### 其他功能
| 模块 | 触发器 | 关键词 |
|------|--------|--------|
| `genshinuid_help` | 帮助 | 帮助 |
| `genshinuid_map` | 切换地图 | 切换地图 |
| `genshinuid_map` | 查找资源点 | 哪里有、哪儿有 |
| `genshinuid_mys` | 原神任务 | 原神任务、任务详情 |
| `genshinuid_mys` | 抽表情 | 抽表情 |
| `genshinuid_mys` | 御神签 | 御神签 |
| `genshinuid_achievement` | 我的成就 | 我的成就、成就列表 |
| `genshinuid_achievement` | 查委托 | 查委托 |
| `genshinuid_achievement` | 查成就 | 查成就 |
| `genshinuid_dailycost` | 每日材料 | 每日材料、今日材料 |
| `genshinuid_etcimg` | 版本规划 | 版本规划、原石预估 |
| `genshinuid_etcimg` | 杂图 | 伤害乘区、血量表等 |
| `genshinuid_compute` | 我的背包 | 我的背包 |
| `genshinuid_returnlist` | 未复刻列表 | 未复刻、复刻列表 |
| `genshinuid_resource` | 下载全部资源 | 下载全部资源 |
| `genshinuid_check` | 清除缓存 | 清除缓存 |
| `genshinuid_data` | 导入v3数据 | 导入v3数据 |
| `genshinuid_data` | 重置core配置 | 重置core配置 |
| `genshinuid_update` | 更新记录 | 更新记录 |
| `genshinuid_update` | gs更新 | gs更新 |

## 技术实现细节

### MockBot 机制

AI 调用触发器时，框架会使用 `MockBot` 代理：
- `bot.send(str)` 的文本内容会被拦截并返回给 AI
- `bot.send(bytes)` 的图片数据会被暂存，AI 可通过 `send_trigger_images` 工具决定是否发送

### to_ai 注册机制

`to_ai` 参数会被框架的 `_register_trigger_as_ai_tool()` 函数处理：
1. 自动将触发器包装为 PydanticAI Tool
2. 注册到 `_TOOL_REGISTRY` 中
3. AI 系统可以根据用户意图自动选择合适的工具调用

## 注意事项

1. **图片类触发器**：大部分触发器返回的是图片（`bytes`），AI 调用时图片会被暂存而非直接返回文本。AI 会收到提示"已生成 N 张图片"，并可调用 `send_trigger_images` 工具发送。

2. **文字类触发器**：返回纯文本的触发器（如 `adv`、`resin_text`、`note_text`）的 `bot.send(str)` 会被 MockBot 自动拦截返回给 AI。

3. **向后兼容**：所有改造对普通用户完全透明，不影响现有功能。`to_ai` 参数不影响原有触发逻辑。

4. **命令前缀**：GenshinUID 使用 `gs` 前缀（如 `gs绑定uid`），不存在斜杠命令。

## 统计

- 改造触发器文件数：**30** 个
- 改造触发器总数：**97** 个
- 移除重复 AI 工具：**14** 个（原 `genshinuid_ai_func` 模块）

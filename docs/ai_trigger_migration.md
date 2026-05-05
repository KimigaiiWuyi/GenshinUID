# GenshinUID AI 触发器改造文档

## 改造概述

本次改造为 GenshinUID 插件的所有 100 个活跃触发器添加了 `to_ai` 参数和 `ai_return()` 数据注入，使触发器能被 AI 以 Tool Call 形式调用。

- **触发器总数**：100 个（分布在 35 个 `__init__.py` 文件中）
- **`to_ai` 覆盖率**：100%（100/100）
- **`ai_return` 注入文件数**：27 个（8 个触发器层 + 19 个渲染层）
- **未处理的触发器**：2 个（`genshinuid_topup` 和 `genshinuid_postdraw` 整体被注释掉）

---

## 一、触发器层改造（`to_ai` 描述规范化）

### 改进要点

1. **第一行**：简洁功能描述（18字以内，不加句号，标明所属游戏模块"原神"）
2. **空行分隔**：第一行与适用场景之间有空行
3. **适用场景**：覆盖用户的多种自然语言说法
4. **Args 部分**：明确参数格式、示例、注意事项
5. **on_fullmatch** 类型标注"无需参数，留空即可"
6. **on_suffix** 类型明确描述关键字**前面**的内容

### 各文件触发器清单

#### [`GenshinUID/genshinuid_abyss/__init__.py`](GenshinUID/genshinuid_abyss/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 查询深渊/sy/上期深渊等 | on_command | 查询原神深渊战斗信息 |

#### [`GenshinUID/genshinuid_achievement/__init__.py`](GenshinUID/genshinuid_achievement/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 我的成就/成就列表/成就一览 | on_command | 查询原神成就完成情况 |
| 查委托 | on_prefix | 查询原神每日委托完成情况 |
| 查成就 | on_prefix | 根据关键词搜索原神成就信息 |

#### [`GenshinUID/genshinuid_adv/__init__.py`](GenshinUID/genshinuid_adv/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 用什么/能用啥/怎么养 | on_suffix | 查询原神角色的武器和圣遗物推荐 |
| 能给谁/谁能用/给谁用 | on_suffix | 查询原神武器适合哪些角色 |

#### [`GenshinUID/genshinuid_ann/__init__.py`](GenshinUID/genshinuid_ann/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 原神公告 | on_command | 查看原神公告列表或指定公告详情 |
| 订阅原神公告 | on_fullmatch | 订阅原神公告推送 |
| 取消订阅原神公告等 | on_fullmatch | 取消订阅原神公告推送 |
| 取消原神公告红点等 | on_fullmatch | 清除原神公告的未读红点提示 |
| 开启自动清红/关闭自动清红 | on_fullmatch | 开启或关闭自动清除原神公告红点功能 |

#### [`GenshinUID/genshinuid_cale/__init__.py`](GenshinUID/genshinuid_cale/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 个人日历/日历等 | on_command | 查询原神个人日历（个人活动完成状态） |

#### [`GenshinUID/genshinuid_check/__init__.py`](GenshinUID/genshinuid_check/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 清除缓存 | on_fullmatch | 清除GenshinUID的缓存数据并备份数据库（管理员功能） |

#### [`GenshinUID/genshinuid_code/__init__.py`](GenshinUID/genshinuid_code/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 兑换码 | on_fullmatch | 获取原神最新前瞻直播兑换码 |

#### [`GenshinUID/genshinuid_collection/__init__.py`](GenshinUID/genshinuid_collection/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 查询完成度/wcd | on_command | 查询原神世界探索完成度总览 |
| 查询收集/sj/收集 | on_command | 查询原神收集物详情（神瞳、宝箱等） |
| 查询探索/ts | on_command | 查询原神各区域探索度详情 |

#### [`GenshinUID/genshinuid_compute/__init__.py`](GenshinUID/genshinuid_compute/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 我的背包/我的物品 | on_command | 查询原神背包物品列表 |

#### [`GenshinUID/genshinuid_config/__init__.py`](GenshinUID/genshinuid_config/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 配置/原神配置 | on_fullmatch | 查看当前用户的原神功能配置状态 |
| 设置 | on_prefix | 设置原神功能的阈值参数 |
| 开启/关闭 | on_prefix | 开启或关闭原神的各项推送和自动功能 |

#### [`GenshinUID/genshinuid_count/__init__.py`](GenshinUID/genshinuid_count/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 毕业度统计/练度统计 | on_command | 查询原神角色毕业度和练度统计 |

#### [`GenshinUID/genshinuid_dailycost/__init__.py`](GenshinUID/genshinuid_dailycost/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 每日材料/今日材料等 | on_command | 查看今日原神角色和武器突破所需材料 |

#### [`GenshinUID/genshinuid_data/__init__.py`](GenshinUID/genshinuid_data/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 导入v3数据 | on_fullmatch | 导入v3版本的旧数据到当前系统（管理员功能） |
| 重置core配置 | on_fullmatch | 重置GenshinUID的core配置到默认状态（管理员功能） |

#### [`GenshinUID/genshinuid_enka/__init__.py`](GenshinUID/genshinuid_enka/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 排名统计 | on_command | 查询原神角色排名统计数据 |
| 排名列表 | on_command | 查询原神角色排名列表 |
| 角色排行榜 | on_prefix | 查看指定角色的全服排行榜数据 |
| 角色排名 | on_prefix | 查询指定UID的某个角色在全服的排名 |
| 圣遗物排名/圣遗物排行榜 | on_command | 查看原神圣遗物排名排行榜 |
| 刷新全部圣遗物仓库 | on_fullmatch | 刷新所有用户的圣遗物仓库数据（管理员功能） |
| 刷新圣遗物仓库/强制刷新圣遗物仓库 | on_fullmatch | 刷新原神圣遗物仓库数据 |
| 圣遗物仓库 | on_command | 查看原神圣遗物仓库列表 |
| 原图 | on_fullmatch | 获取上一条消息中图片的原图 |
| 切换api | on_fullmatch | 切换面板查询使用的API源 |
| 查询 | on_prefix | 查询原神角色面板详情（武器、圣遗物、属性等） |
| 对比面板 | on_command | 对比多个原神角色面板配置 |
| 保存面板 | on_command | 保存当前原神角色面板为自定义名称 |
| 强制刷新/刷新面板等 | on_command | 刷新原神角色面板数据 |
| 角色橱窗 | on_command | 查看原神角色橱窗列表 |

#### [`GenshinUID/genshinuid_etcimg/__init__.py`](GenshinUID/genshinuid_etcimg/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 版本规划/原石预估 | on_command | 查看原神版本规划和原石预估图 |
| 伤害乘区/血量表等 | on_fullmatch | 查看原神怪物相关的参考数据图 |

#### [`GenshinUID/genshinuid_eventlist/__init__.py`](GenshinUID/genshinuid_eventlist/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 活动列表 | on_fullmatch | 查看原神当前正在进行的活动列表 |
| 卡池列表 | on_fullmatch | 查看原神当前和即将开放的卡池（祈愿）列表 |

#### [`GenshinUID/genshinuid_gachalog/__init__.py`](GenshinUID/genshinuid_gachalog/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 抽卡记录 | on_fullmatch | 查看原神抽卡记录 |
| 刷新抽卡记录/强制刷新抽卡记录 | on_fullmatch | 刷新原神抽卡记录数据 |
| 全量刷新抽卡记录 | on_fullmatch | 全量刷新原神抽卡记录（从头获取所有记录） |
| 导出抽卡记录 | on_fullmatch | 导出原神抽卡记录为UIGF格式文件 |
| 从小助手导入抽卡记录 | on_fullmatch | 从提瓦特小助手导入抽卡记录 |
| 导出抽卡记录到小助手 | on_fullmatch | 将抽卡记录导出到提瓦特小助手 |
| 导出抽卡记录链接/连接 | on_fullmatch | 获取原神抽卡记录的导出链接 |

#### [`GenshinUID/genshinuid_gcg/__init__.py`](GenshinUID/genshinuid_gcg/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 七圣召唤/qszh/七圣数据总览 | on_command | 查询原神七圣召唤数据总览 |
| 我的卡组/我的牌组 | on_command | 查询原神七圣召唤卡组详情 |

#### [`GenshinUID/genshinuid_get_code/__init__.py`](GenshinUID/genshinuid_get_code/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 给我一个兑换码/给我兑换码 | on_fullmatch | 获取一个可用的原神兑换码 |

#### [`GenshinUID/genshinuid_guide/__init__.py`](GenshinUID/genshinuid_guide/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 路线 | on_suffix | 查询原神材料的采集路线攻略 |
| 参考攻略/攻略/推荐 | on_prefix | 查询原神角色攻略图片 |
| 攻略/推荐 | on_suffix | 查询原神角色攻略图片 |
| 参考面板 | on_prefix | 查询原神角色参考面板图片 |
| 剧诗版本深渊/剧诗深渊阵容等 | on_command | 查看剧诗深渊（幻想真境剧诗）的版本信息和怪物阵容 |
| 版本深渊/深渊阵容等 | on_command | 查看指定版本的深渊怪物阵容和信息 |

#### [`GenshinUID/genshinuid_hard_challenge/__init__.py`](GenshinUID/genshinuid_hard_challenge/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 查询幽境危战/幽境危战等 | on_command | 查询原神幽境危战（三路深渊）战斗信息 |
| 幽境危战排行榜等 | on_fullmatch | 查看原神幽境危战（三路深渊）的排行榜数据 |

#### [`GenshinUID/genshinuid_help/__init__.py`](GenshinUID/genshinuid_help/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 帮助 | on_fullmatch | 获取GenshinUID插件的帮助信息和功能列表 |

#### [`GenshinUID/genshinuid_map/__init__.py`](GenshinUID/genshinuid_map/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 切换地图 | on_fullmatch | 切换原神资源点查询使用的地图 |
| 哪里有/哪儿有/哪有 | on_prefix | 查询原神中某种资源在地图上的分布位置 |

#### [`GenshinUID/genshinuid_mys/__init__.py`](GenshinUID/genshinuid_mys/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 原神任务/任务详情/qszh | on_prefix | 查询原神任务详情或区域任务列表 |
| 抽表情 | on_fullmatch | 随机抽取一个原神表情包 |
| 御神签 | on_fullmatch | 抽取今日原神御神签（每日运势） |

#### [`GenshinUID/genshinuid_mysbbscoin/__init__.py`](GenshinUID/genshinuid_mysbbscoin/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 开始获取米游币 | on_fullmatch | 自动获取米游币 |
| 全部重获取 | on_fullmatch | 重新获取所有用户的米游币（管理员功能） |

#### [`GenshinUID/genshinuid_note/__init__.py`](GenshinUID/genshinuid_note/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 每月统计 | on_fullmatch | 查询原神本月原石和莫拉收入统计 |
| 当前信息/zj/札记 | on_fullmatch | 查询原神当前实时便笺信息 |

#### [`GenshinUID/genshinuid_poetry_abyss/__init__.py`](GenshinUID/genshinuid_poetry_abyss/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 查询幻想真境剧诗/新深渊/剧诗等 | on_command | 查询原神幻想真境剧诗（新深渊）战斗信息 |

#### [`GenshinUID/genshinuid_resin/__init__.py`](GenshinUID/genshinuid_resin/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 当前状态 | on_fullmatch | 以文字形式查询原神当前状态（树脂、宝钱、派遣等） |
| 强制推送体力提醒 | on_fullmatch | 强制执行一次体力提醒推送（管理员功能） |
| 每日/mr/实时便笺等 | on_fullmatch | 以图片形式查询原神实时便笺信息 |

#### [`GenshinUID/genshinuid_resource/__init__.py`](GenshinUID/genshinuid_resource/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 下载全部资源 | on_fullmatch | 下载GenshinUID所需的全部资源文件（管理员功能） |

#### [`GenshinUID/genshinuid_returnlist/__init__.py`](GenshinUID/genshinuid_returnlist/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 未复刻/未复刻列表/复刻列表 | on_fullmatch | 查看原神角色和武器的未复刻天数列表 |

#### [`GenshinUID/genshinuid_roleinfo/__init__.py`](GenshinUID/genshinuid_roleinfo/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 原神注册时间/注册时间等 | on_command | 查询原神账号注册时间 |
| 查询/uid/UID | on_command | 查询原神角色信息面板 |
| 角色列表 | on_command | 查询原神全部角色列表 |

#### [`GenshinUID/genshinuid_season_post/__init__.py`](GenshinUID/genshinuid_season_post/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 季报 | on_fullmatch | 查询原神季度报告 |

#### [`GenshinUID/genshinuid_signin/__init__.py`](GenshinUID/genshinuid_signin/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 签到 | on_fullmatch | 执行米游社原神每日签到 |
| 全部重签 | on_fullmatch | 重新执行所有用户的米游社签到（管理员功能） |

#### [`GenshinUID/genshinuid_update/__init__.py`](GenshinUID/genshinuid_update/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 更新记录 | on_fullmatch | 查看GenshinUID插件的更新记录 |
| gs更新/gs强制更新等 | on_fullmatch | 执行GenshinUID插件更新（管理员功能） |

#### [`GenshinUID/genshinuid_user/__init__.py`](GenshinUID/genshinuid_user/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 绑定uid/切换uid/删除uid等 | on_command | 绑定、切换或删除原神UID |
| ck帮助/绑定帮助 | on_fullmatch | 获取原神Cookie绑定帮助信息 |

#### [`GenshinUID/genshinuid_wikitext/__init__.py`](GenshinUID/genshinuid_wikitext/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 原魔介绍/原魔资料/查原魔 | on_prefix | 查询原神原魔（怪物）的详细介绍 |
| 食物介绍/食物资料/查食物 | on_prefix | 查询原神食物的详细介绍 |
| 圣遗物介绍/圣遗物资料/查圣遗物 | on_prefix | 查询原神圣遗物套装的详细介绍 |
| 武器介绍/武器资料/查武器 | on_prefix | 查询原神武器的详细介绍和属性 |
| 角色天赋/查天赋 | on_prefix | 查询原神角色天赋的详细介绍 |
| 角色介绍/角色资料/查角色 | on_prefix | 查询原神角色的详细介绍和属性 |
| 角色材料 | on_prefix | 查询原神角色突破所需材料 |
| 武器材料 | on_prefix | 查询原神武器突破所需材料 |
| 角色命座/查命座 | on_prefix | 查询原神角色命座的详细介绍 |

#### [`GenshinUID/genshinuid_xkdata/__init__.py`](GenshinUID/genshinuid_xkdata/__init__.py)
| 触发器 | 类型 | to_ai |
|--------|------|-------|
| 深渊概览/深渊统计/深渊使用率 | on_fullmatch | 查看当前深渊的角色使用率概览统计图 |
| 深渊队伍/深渊队伍统计等 | on_fullmatch | 查看当前深渊的队伍推荐和组队统计图 |
| 角色深渊详情/角色深渊 | on_prefix | 查看指定角色的深渊使用详情数据 |

---

## 二、数据层改造（`ai_return` 注入）

### 注入原则

- `ai_return()` 在**数据已经拿到、图片还没生成时**调用
- 传递结构化的文本数据摘要，让 AI 能够"读懂"查询结果
- 用 `try/except` 包裹，错误只 `logger.warning`，不影响主流程
- 用户直接触发时 `ai_return()` 完全透明

### 触发器层注入（8 个文件）

这些文件中触发器返回纯文字结果，直接在触发器函数中注入：

| 文件 | 注入场景 | 提取的数据 |
|------|---------|-----------|
| [`genshinuid_adv/__init__.py`](GenshinUID/genshinuid_adv/__init__.py) | 角色推荐/武器推荐 | 文字推荐结果 |
| [`genshinuid_achievement/__init__.py`](GenshinUID/genshinuid_achievement/__init__.py) | 委托查询/成就搜索 | 文字搜索结果 |
| [`genshinuid_enka/__init__.py`](GenshinUID/genshinuid_enka/__init__.py) | 排名统计 | 排名文字结果 |
| [`genshinuid_mys/__init__.py`](GenshinUID/genshinuid_mys/__init__.py) | 任务详情/御神签 | 文字查询结果 |
| [`genshinuid_resin/__init__.py`](GenshinUID/genshinuid_resin/__init__.py) | 当前状态 | 树脂/宝钱/派遣文字状态 |
| [`genshinuid_roleinfo/__init__.py`](GenshinUID/genshinuid_roleinfo/__init__.py) | 注册时间 | 注册日期文字结果 |
| [`genshinuid_wikitext/__init__.py`](GenshinUID/genshinuid_wikitext/__init__.py) | 所有WIKI查询（9个触发器） | 文字版WIKI数据 |
| [`genshinuid_abyss/__init__.py`](GenshinUID/genshinuid_abyss/__init__.py) | 深渊查询 | 导入（深渊主要返回图片） |

### 渲染层注入（19 个文件）

这些文件是图片渲染函数，在数据获取后、图片生成前注入 `ai_return()`：

| 渲染文件 | 注入的数据 |
|---------|-----------|
| [`draw_char_count.py`](GenshinUID/genshinuid_count/draw_char_count.py) | 毕业度统计：评分分布（优秀/良好/一般）、TOP10角色详情（评分、天赋、词条、武器等级） |
| [`draw_new_collection_card.py`](GenshinUID/genshinuid_collection/draw_new_collection_card.py) | 世界探索：活跃天数、角色数、成就数、深渊、宝箱统计、各区域探索度（含供奉等级）、神瞳统计 |
| [`draw_collection_card.py`](GenshinUID/genshinuid_collection/draw_collection_card.py) | 收集/探索：活跃天数、总完成度、剩余原石、各项数据百分比 |
| [`get_my_pack.py`](GenshinUID/genshinuid_compute/get_my_pack.py) | 背包物品：缺少材料TOP10（含缺少数量）、拥有最多TOP10 |
| [`draw_daily_cost.py`](GenshinUID/genshinuid_dailycost/draw_daily_cost.py) | 每日材料：各秘境对应角色和武器（区分类型） |
| [`draw_cale_pic.py`](GenshinUID/genshinuid_cale/draw_cale_pic.py) | 个人日历：活动状态+剩余时间、未开始活动倒计时、奖励物品、卡池+剩余时间、武器卡池 |
| [`draw_gcginfo.py`](GenshinUID/genshinuid_gcg/draw_gcginfo.py) | 七圣召唤：等级、角色牌/行动牌收集数+百分比、展示卡牌名称 |
| [`draw_gcgdesk.py`](GenshinUID/genshinuid_gcg/draw_gcgdesk.py) | 卡组详情：角色牌、行动牌（含费用信息，展示前8张） |
| [`draw_note_card.py`](GenshinUID/genshinuid_note/draw_note_card.py) | 札记：今日/本月原石摩拉、上月对比、原石来源TOP5 |
| [`draw_roleinfo_card.py`](GenshinUID/genshinuid_roleinfo/draw_roleinfo_card.py) | 角色信息面板：活跃天数、角色数、成就数、深渊、宝箱总数、传送点、秘境、展示角色详情（等级/命座/好感/武器） |
| [`draw_teyvat_returnlist.py`](GenshinUID/genshinuid_returnlist/draw_teyvat_returnlist.py) | 未复刻排行：五星角色8个+四星角色5个+五星武器8个（含天数、上次UP版本、星级） |
| [`draw_teyvat_img.py`](GenshinUID/genshinuid_xkdata/draw_teyvat_img.py) | 深渊队伍推荐：TOP8队伍（含使用率、持有率、登场率） |
| [`draw_char_abyss.py`](GenshinUID/genshinuid_xkdata/draw_char_abyss.py) | 角色深渊统计：使用率、满星率、出场率、平均等级/命座、排名TOP5 |
| [`draw_abyss_card.py`](GenshinUID/genshinuid_abyss/draw_abyss_card.py) | 深渊信息：本期/上期标识、总星数、挑战次数、各层星数+通关时间、最强一击/最多击破/承受伤害 |
| [`draw_gachalogs.py`](GenshinUID/genshinuid_gachalog/draw_gachalogs.py) | 抽卡记录：各池总抽数/五星数/平均抽数/UP平均/已抽数/类型、最近出金记录（含抽数和UP标记）、UP记录、歪到列表 |
| [`draw_poetry_abyss.py`](GenshinUID/genshinuid_poetry_abyss/draw_poetry_abyss.py) | 幻想真境剧诗：本期/上期、难度、奖章、各关卡完成状态+塔罗标记、使用角色数 |
| [`draw_hard_challenge.py`](GenshinUID/genshinuid_hard_challenge/draw_hard_challenge.py) | 幽境危战：赛季时间、最高难度、总用时、各关卡怪物名称+最佳角色 |
| [`draw_season_post.py`](GenshinUID/genshinuid_season_post/draw_season_post.py) | 季度报告：摩拉/原石、锚点、区域探索度TOP5、活跃天数/角色数/成就数/深渊 |
| [`draw_role_rank.py`](GenshinUID/genshinuid_enka/draw_role_rank.py) | 角色排行榜：TOP10（含服务器区域）、百分比排名（超越X%玩家） |

---

## 三、未处理的触发器

以下 2 个触发器位于被注释掉的文件中，不需要处理：

| 文件 | 状态 |
|------|------|
| `genshinuid_topup/__init__.py` | 整个文件被 `'''` 注释掉 |
| `genshinuid_postdraw/__init__.py` | 整个文件被 `"""` 注释掉 |

---

## 四、不需要 `ai_return` 的触发器

以下触发器返回纯文字（`bot.send(str)`），MockBot 会自动拦截返回给 AI，无需额外 `ai_return`：

- 签到、全部重签（`genshinuid_signin`）
- 绑定uid、ck帮助（`genshinuid_user`）
- 配置、设置、开启/关闭（`genshinuid_config`）
- 原神公告、订阅/取消订阅、清红（`genshinuid_ann`）
- 更新记录、gs更新（`genshinuid_update`）
- 导入v3数据、重置core配置（`genshinuid_data`）
- 清除缓存（`genshinuid_check`）
- 下载全部资源（`genshinuid_resource`）
- 开始获取米游币、全部重获取（`genshinuid_mysbbscoin`）
- 给我一个兑换码（`genshinuid_get_code`）
- 兑换码（`genshinuid_code`）
- 切换地图（`genshinuid_map`）
- 刷新圣遗物仓库、保存面板、切换api（`genshinuid_enka`）
- 刷新抽卡记录、全量刷新、导出、导入（`genshinuid_gachalog`）
- 强制推送体力提醒（`genshinuid_resin`）
- 每月统计（`genshinuid_note`，返回文字）
- 帮助（`genshinuid_help`，返回图片但无结构化数据）
- 版本规划、怪物数据图（`genshinuid_etcimg`，返回静态图片）
- 活动列表、卡池列表（`genshinuid_eventlist`，返回图片但数据在渲染层深处）
- 资源点地图（`genshinuid_map`，返回图片但数据在渲染层深处）
- 抽表情（`genshinuid_mys`，返回随机图片）

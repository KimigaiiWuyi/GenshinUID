# 二、命令与触发器

> 返回 [SKILL.md](../SKILL.md)

触发器写在各 `genshinuid_*/__init__.py`。`to_ai` 写法见 [五、AI 集成](./05-ai-integration.md)。

## 2.1 选择触发器

| 场景 | 用 |
|------|----|
| 固定词、后面可跟参数（绑定 UID、查询体力） | `on_command` |
| 必须带参数（`查询胡桃`、`角色攻略雷电将军`） | `on_prefix` |
| 整句就是命令（`帮助`、`抽卡记录`） | `on_fullmatch` |
| 关键字在后面（`胡桃面板`） | `on_suffix` |

不要用 `on_keyword` 扫全消息。管理员命令设 `pm=1` 或 `pm=2`。

## 2.2 代表命令（均需前缀 `gs`）

| 命令 | SV | 模块 |
|------|----|------|
| `绑定uid` / `切换uid` / `删除uid` | 用户信息 | `genshinuid_user` |
| `ck帮助` | 绑定帮助 | `genshinuid_user` |
| `查询` / `查询<角色>` | 查询原神信息 / 面板查询 | `roleinfo` / `enka` |
| `刷新面板` / `强制刷新` | 面板查询 | `enka` |
| `mr` / 体力相关 | 查询体力 | `resin` |
| `深渊` / `上期深渊` | 查询深渊 | `abyss` |
| `抽卡记录` / `刷新抽卡记录` | 抽卡记录 | `gachalog` |
| `帮助` | gs帮助 | `help` |
| `签到` / `开启自动签到` | 原神签到 | `signin` |
| `开启体力推送` 等 | 原神配置 | `config` |

具体别名以各 `__init__.py` 元组为准，不要凭 README 猜。

## 2.3 加一条命令的步骤

1. 放到对应 `genshinuid_*` 子包，不要新起无前缀目录。
2. 已有 SV 就复用；新功能新 `SV("中文名")`。
3. 需要 UID：`uid = await get_uid(bot, ev)`，`None` 时 `UID_HINT`。
4. 用户也要能直接打：加 `to_ai="""..."""`（第一行含「原神」）。
5. 出图则在数据函数 `ai_return` 文本摘要。
6. 帮助图：改 `genshinuid_help/help.json`。

## 2.4 按钮

`GButton`（`utils/message.py`）自动带 `PREFIX`。发给 `bot.send_option`。

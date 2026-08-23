# 六、配置、订阅、启动、帮助

> 返回 [SKILL.md](../SKILL.md)

## 6.1 配置

```python
# genshinuid_config/gs_config.py
gsconfig = StringConfig("GenshinUID", CONFIG_PATH, CONIFG_DEFAULT)
```

- 文件：`data/GenshinUID/config.json`（`RESOURCE_PATH.CONFIG_PATH`）。
- 默认值：`config_default.py` 的 **`CONIFG_DEFAULT`**（缺字母 I）。改键名要同时改所有 `get_config("…")`。
- 类型：`GsBoolConfig` / `GsStrConfig` / `GsTimeRConfig` / `GsDictConfig` / `GsListConfig`。
- 用户命令：`genshinuid_config/__init__.py`（查看配置、设阈值、开关推送）。

重要键（完整列表看源码）：`SignTime`、`SchedSignin`、`SchedResinPush`、`SchedMhyBBSCoin`、`WidgetResin`、`EnableAkasha`、`EnableCharCardByMys`、`GachaLogOrder`、`PicWiki`、`OldPanle`。

## 6.2 数据库

本插件**不**定义 `table=True` 的 Bind。

- UID：框架 `GsBind`
- Cookie：框架 `GsUser`
- 推送状态：`gs_subscribe` 行，不是自建 Push 表

## 6.3 订阅（`gs_subscribe`）

任务名带 `[原神]`，例如：

- `[原神] 推送` 总开关
- `[原神] 体力` / `宝钱` / `派遣` / `质变仪` / `日常检查` / `活动提醒`
- `[原神] 自动清红`
- 签到 / 米游币走对应 Sched 配置 + subscribe

禁止 `for bot in gss.active_bot` 硬推群。管理员 `强制推送` 走已有 SV。

## 6.4 启动

`genshinuid_start/main.py`：

```python
@on_core_start
async def all_start():
    await download_Oceanid()
    await startup()              # 资源
    await create_all_char_card()
```

失败 `logger.exception`，不要吞掉后假装资源齐全。

## 6.5 帮助

`register_help("GenshinUID", f"{PREFIX}帮助", get_ICON())`。
帮助内容：`genshinuid_help/help.json` + `get_help.py` 出图。

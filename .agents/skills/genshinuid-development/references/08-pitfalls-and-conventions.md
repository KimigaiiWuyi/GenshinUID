# 八、坑点与代码规范

> 返回 [SKILL.md](../SKILL.md)

## 8.1 新代码红线

与 Core `AGENTS.md` §1 相同：禁止 `cast` / `Any` / 自身 `type: ignore` / `getattr`·`dict.get` 兜底 / 同步阻塞。
`#` 注释最多两行、每行 ≤88 字。行宽 120。

历史文件可以暂时脏。**你改动的函数**按新标准写。

唯一宽 `try/except`：`_ai_return_*`、解析 Enka/米游社 JSON、下载资源失败（打日志，不崩启动）。

## 8.2 本插件坑

1. **UID 位数**是 9。`insert_uid(..., 9)` 与 `get_uid` 的 `\d{9}` 必须一致。
2. **默认 `GsBind` 就是原神**。跨游戏插件才需要 `game_name`。
3. **展柜 12 人上限**。AI 文本工具无 CK 时必须写明。
4. **`CONIFG_DEFAULT` 拼写**。全局替换前先 grep 引用。
5. **`OldPanle` 拼写**同样是历史键名，配置里不要「修正」成 Panel。
6. **i18n**：改 `t("log.genshinuid.…")` 要改 `locales/{zh-cn,en,ja}/logs.json`。
7. **`tools/` 排除 ruff**：生成物可乱，但 effect 更新流程走 skill，不要手搓 200 个空键。
8. **不要**在启动钩子里加全量角色/深渊爬虫（会打米游社）。
9. **前缀缓存**：不要改 Core system prompt；本插件动态信息只进 `ai_return` / 工具返回。
10. **帮助列数** `help_column` 是字符串配置，读取后转 int。
11. **随机图 API** 失败要有面板底图兜底，不要抛到用户堆栈。

## 8.3 改完自查

- [ ] 前缀用 `PREFIX` / 触发器装饰器，不写死 `gs`
- [ ] 需要 UID 的命令处理了未绑定
- [ ] 出图命令有 `to_ai` 且数据层有 `ai_return`
- [ ] 新 `@ai_tools` 被 `genshinuid_ai_func/__init__.py` import，docstring 紧贴 def，有 covers/aliases
- [ ] 新素材路径进了 `RESOURCE_PATH.py`
- [ ] `ruff check GenshinUID`（不含 tools）

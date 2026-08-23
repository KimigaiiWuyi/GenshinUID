# 三、UID / Cookie / API

> 返回 [SKILL.md](../SKILL.md)

## 3.1 UID 绑定

`genshinuid_user` 调框架：

```python
await GsBind.insert_uid(qid, ev.bot_id, uid, ev.group_id, 9)
await GsBind.switch_uid_by_game(qid, ev.bot_id, uid)
await GsBind.delete_uid(qid, ev.bot_id, uid)
```

原神是 `GsBind` 默认游戏，**不要**传 `game_name="zzz"`。位数 `9`。

解析当前 UID：`utils/convert.py::get_uid`。

- 文本里的 9 位数字优先，并从 `ev.text` 剥掉。
- 否则 `GsBind.get_uid_by_game(user_id, bot_id)`。
- `@` 他人且不是 bot 自身 → 查被 @ 者。
- 顺带把 `group_id` 写回绑定记录（推送用）。

## 3.2 Cookie

战绩、便签、深渊、抽卡、签到依赖米游社 Cookie（及部分 Stoken）。
账号存在框架 `GsUser`，**不是**本插件的表。绑定流程见 `ck帮助`（`get_ck_help()`）。

无 Cookie：

- 面板仍可走 Enka 展柜缓存（最多 12 角色）。
- 树脂/深渊/全角色箱会失败，返回框架错误图或提示去绑 CK。

配置 `EnableCharCardByMys`：面板改走米游社，可能验证码。

## 3.3 API 客户端

| 客户端 | 路径 | 用途 |
|--------|------|------|
| `mys_api` | `utils/mys_api.py` | 米游社战绩（`_MysApi`） |
| Enka | `genshinuid_enka/to_data.py` | 展柜面板 |
| MiniGG | enka 切换 API | 国内面板镜像 |
| Hakush / Teyvat / CV | `utils/api/` | Wiki / 深渊库 / 攻略图 |

错误码：`int` 返回值走 `get_error_img` / `error_reply`，不要把 errno 当 JSON 往下传。

## 3.4 玩家缓存

`PLAYER_PATH / {uid} /`（见 `RESOURCE_PATH.py`）。刷新面板写入角色 JSON。
AI 用户工具读这些缓存；没有文件时提示 `gs强制刷新`。

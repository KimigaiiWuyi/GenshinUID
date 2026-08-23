# 七、渲染与资源路径

> 返回 [SKILL.md](../SKILL.md)

## 7.1 出图

本插件以 **PIL** 为主（各模块 `draw_*.py` + `texture2d/`）。
Wiki 可用图片版（配置 `PicWiki`）。不要无故引入 playwright。

公共脚：`utils/image/image_tools.py`、`utils/fonts/genshin_fonts.py`。
子模块素材放该模块 `texture2d/`（有的目录写成 `texture2D`，保持原样）。

## 7.2 路径单源

`utils/resource/RESOURCE_PATH.py`：

| 常量 | 含义 |
|------|------|
| `MAIN_PATH` | `get_res_path()/GenshinUID` |
| `CONFIG_PATH` | `config.json` |
| `RESOURCE_PATH` | 下载的游戏素材 |
| `PLAYER_PATH` | 面板缓存 |
| `WIKI_PATH` / `GUIDE_PATH` | Wiki / 攻略 |
| `CU_BG_PATH` / `CU_CHBG_PATH` | 自定义背景 |
| `CHAR_*` `WEAPON_PATH` `REL_PATH` | 角色/武器/圣遗物图 |
| `CHAR_DATA_PATH` 等 | RAG 用 JSON |

启动时 `init_dir()` 建目录。业务代码 import 常量，不要再 `get_res_path() / "GenshinUID" / ...`。

## 7.3 地图数据

`utils/map/data/`：`charList_{ver}.json`、`weaponList_*.json`、`char_alias.json` 等。
`ver` 与 `Genshin_version` 一致（如 `7.0.0`）。
`GS_MAP_PATH.py` 负责加载。改版本必须成套更新，不要只改 `version.py`。

## 7.4 资源下载

`genshinuid_resource`：`gs下载全部资源`（`pm=2`）。
实现：`utils/resource/download_all_resource.py` 等。不要在请求路径上同步阻塞下载。

import re
import json
import argparse
from io import BytesIO
from time import sleep
from typing import Any, Set, Dict, List, Tuple, Optional, Sequence
from pathlib import Path

import httpx
from PIL import Image

MAP_PATH = Path(__file__).parent.parent / "utils" / "map" / "data"
OUT_PATH = Path(__file__).parent

# yatta / ambr API & 静态资源
API_BASE = "https://gi.yatta.moe/api/v2"
ASSET_BASE = "https://gi.yatta.moe/assets/UI"
# 版本哈希，用于接口缓存控制；7.0 可用 70F0，也可留空
DEFAULT_VH = "70F0"
# 默认只拉该版本 changelog 中的更新；设为 None / "latest" 则取最新一版
DEFAULT_VERSION = "7.0"

suffix = "png"

# 角色资源模板：{} 填入 UI_AvatarIcon_ 后的英文 key，如 Alyosha / Odette
# 保存名特殊规则（见 resolve_char_save_name）：
#   UI_AvatarIcon_{en}.png      -> {角色ID}.png        例: 10000148.png
#   UI_Gacha_AvatarImg_{en}.png -> {角色中文名}.png    例: 阿罗夏.png
#   其余保持远端文件名
icon_list = [
    "Skill_E_{}_01." + suffix,
    "Skill_E_{}_02." + suffix,
    "Skill_S_{}_01." + suffix,
    "Skill_S_{}_02." + suffix,
    "UI_Talent_S_{}_01." + suffix,
    "UI_Talent_S_{}_02." + suffix,
    "UI_Talent_S_{}_03." + suffix,
    "UI_Talent_S_{}_04." + suffix,
    "UI_Talent_S_{}_05." + suffix,
    "UI_Talent_S_{}_06." + suffix,
    "UI_Talent_S_{}_07." + suffix,
    "UI_Talent_U_{}_01." + suffix,
    "UI_Talent_U_{}_02." + suffix,
    "UI_Talent_C_{}_01." + suffix,
    "UI_Talent_C_{}_02." + suffix,
    "UI_Gacha_AvatarImg_{}." + suffix,
    "UI_NameCardIcon_{}." + suffix,
    "UI_AvatarIcon_{}." + suffix,
    "UI_NameCardPic_{}_P." + suffix,
]

# 手动兜底：若 API 不可用，可临时填写
manual_char_list: List[str] = []
manual_weapon_ids: List[str] = []

is_download = True

_client: Optional[httpx.Client] = None


def get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(timeout=80, follow_redirects=True)
    return _client


def with_vh(url: str, vh: str = "") -> str:
    if not vh:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}vh={vh}"


def fetch_json(url: str, retries: int = 5) -> Any:
    last_err: Optional[Exception] = None
    for i in range(retries):
        try:
            resp = get_client().get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"请求失败({i + 1}/{retries}): {url} -> {e}")
            sleep(2 + i * 2)
    raise RuntimeError(f"无法获取 {url}: {last_err}")


def load_local_map(prefix: str) -> Dict[str, Any]:
    """优先读本地 utils/map/data 下最新版本列表，减少联网。"""
    files = sorted(MAP_PATH.glob(f"{prefix}_*.json"), reverse=True)
    for path in files:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and data:
                print(f"使用本地映射: {path.name} ({len(data)} 条)")
                return data
        except Exception as e:  # noqa: BLE001
            print(f"读取本地映射失败 {path}: {e}")
    return {}


def get_changelog(vh: str = DEFAULT_VH) -> Dict[str, Any]:
    url = with_vh(f"{API_BASE}/static/changelog", vh)
    print(f"获取 changelog: {url}")
    data = fetch_json(url)
    return data.get("data", data)


def parse_version_key(version: str) -> Tuple[int, ...]:
    nums = re.findall(r"\d+", version)
    return tuple(int(x) for x in nums) if nums else (0,)


def pick_changelog_entry(
    changelog: Dict[str, Any],
    version: Optional[str] = DEFAULT_VERSION,
) -> Tuple[str, Dict[str, Any]]:
    """
    选择 changelog 条目。
    version 为 None / 'latest' / '' 时取版本号最大的一条；
    否则按 version 字符串精确或前缀匹配（如 7.0 / 7.0.0）。
    """
    entries: List[Tuple[str, Dict[str, Any], Tuple[int, ...]]] = []
    for key, val in changelog.items():
        if not isinstance(val, dict):
            continue
        ver = str(val.get("version", key))
        entries.append((key, val, parse_version_key(ver)))

    if not entries:
        raise RuntimeError("changelog 为空")

    entries.sort(key=lambda x: x[2])

    if not version or str(version).lower() in {"latest", "new", "max"}:
        key, val, _ = entries[-1]
        return key, val

    target = str(version).strip()
    # 精确匹配 version 字段
    for key, val, _ in entries:
        if str(val.get("version", "")) == target or key == target:
            return key, val
    # 前缀匹配，如 7.0 匹配 7.0.0
    for key, val, _ in reversed(entries):
        ver = str(val.get("version", ""))
        if ver.startswith(target) or target.startswith(ver):
            return key, val

    available = ", ".join(f"{k}:{v.get('version')}" for k, v, _ in entries[-10:])
    raise RuntimeError(f"未找到版本 {target}，可用(末10条): {available}")


def collect_ids_from_entry(entry: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    items = entry.get("items") or {}
    avatars = [str(x) for x in items.get("avatar") or []]
    weapons = [str(x) for x in items.get("weapon") or []]
    return avatars, weapons


def get_avatar_items(vh: str = DEFAULT_VH) -> Dict[str, Any]:
    local = load_local_map("charList")
    if local:
        return local
    url = with_vh(f"{API_BASE}/chs/avatar", vh)
    print(f"获取角色列表: {url}")
    data = fetch_json(url)
    return data.get("data", data).get("items", {})


def get_weapon_items(vh: str = DEFAULT_VH) -> Dict[str, Any]:
    local = load_local_map("weaponList")
    if local:
        return local
    url = with_vh(f"{API_BASE}/chs/weapon", vh)
    print(f"获取武器列表: {url}")
    data = fetch_json(url)
    return data.get("data", data).get("items", {})


def find_item_by_id(items: Dict[str, Any], item_id: str) -> Optional[Dict[str, Any]]:
    """
    按 id 从 items 字典取值。
    key 统一按 str 比较，兼容 JSON 里 key 为数字字符串的情况。
    """
    sid = str(item_id)
    hit = items.get(sid)
    if isinstance(hit, dict):
        return hit
    for k, v in items.items():
        if not isinstance(v, dict):
            continue
        if str(k) == sid or str(v.get("id", "")) == sid:
            return v
    return None


def avatar_icon_key(info: Dict[str, Any]) -> Optional[str]:
    """从角色数据得到下载用英文 key（UI_AvatarIcon_Xxx -> Xxx）。"""
    icon = str(info.get("icon") or "")
    if icon.startswith("UI_AvatarIcon_"):
        key = icon[len("UI_AvatarIcon_") :]
    elif info.get("route"):
        # route 如 "Kamisato Ayaka" / "Alyosha"，技能资源一般用末段或专用 key
        key = str(info["route"]).split()[-1]
    else:
        return None
    # 旅行者资源不是常规 Skill_E_PlayerBoy 体系，跳过
    if key in {"PlayerBoy", "PlayerGirl"}:
        return None
    return key


def safe_filename(name: str) -> str:
    """去掉 Windows 非法文件名字符。"""
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


def weapon_save_name(info: Dict[str, Any]) -> str:
    """武器保存文件名：中文名.png。"""
    name = str(info.get("name") or info.get("id") or "unknown")
    return f"{safe_filename(name)}.png"


def resolve_char_save_name(
    remote_icon_name: str,
    char_id: str,
    char_name: str,
) -> str:
    """
    角色资源保存名规则：
    - UI_AvatarIcon_*.png      -> {角色ID}.png       例 UI_AvatarIcon_Alyosha.png -> 10000148.png
    - UI_Gacha_AvatarImg_*.png -> {角色中文名}.png   例 UI_Gacha_AvatarImg_Alyosha.png -> 阿罗夏.png
    - 其它资源保持远端文件名
    """
    base = remote_icon_name.split("/")[-1]
    stem = base.rsplit(".", 1)[0] if "." in base else base
    if stem.startswith("UI_AvatarIcon_"):
        return f"{char_id}.png"
    if stem.startswith("UI_Gacha_AvatarImg_"):
        return f"{safe_filename(char_name)}.png"
    return base if base.endswith(".png") else f"{stem}.png"


def weapon_icon_url(info: Dict[str, Any], vh: str = "") -> str:
    icon = str(info.get("icon") or "")
    if not icon:
        raise ValueError(f"武器缺少 icon 字段: {info}")
    if not icon.endswith((".png", ".webp")):
        icon = f"{icon}.png"
    url = f"{ASSET_BASE}/{icon}"
    return with_vh(url, vh) if vh else url


def download(icon_name: str, url: str, out_dir: Optional[Path] = None):
    icon_name = icon_name.split(".")[0] + ".png"
    path = (out_dir or OUT_PATH) / icon_name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"{icon_name}已经存在!，跳过！")
        return
    print(f"正在下载{icon_name}")
    print(url)
    while True:
        try:
            char_data = get_client().get(url)
            break
        except Exception:  # noqa: BLE001
            sleep(4)

    content_type = char_data.headers.get("Content-Type", "")
    if char_data.status_code != 200:
        print(f"{icon_name}不存在(status={char_data.status_code})，跳过！")
        return
    if "image/png" in content_type or url.lower().endswith(".png"):
        # 部分 CDN 不返回准确 content-type，用 magic 兜底
        if char_data.content[:8] == b"\x89PNG\r\n\x1a\n" or "image/png" in content_type:
            char_bytes = char_data.content
        elif char_data.content[:4] == b"RIFF" or "image/webp" in content_type:
            webp_image = BytesIO(char_data.content)
            img = Image.open(webp_image)
            png_bytes = BytesIO()
            img.save(png_bytes, "PNG")
            png_bytes.seek(0)
            char_bytes = png_bytes.read()
        else:
            # 尝试当 png 直接写（yatta 多数就是 png）
            if len(char_data.content) > 100 and b"<html" not in char_data.content[:200].lower():
                char_bytes = char_data.content
            else:
                print(f"{icon_name}不存在，跳过！ content-type={content_type}")
                return
    elif "image/webp" in content_type:
        webp_image = BytesIO(char_data.content)
        img = Image.open(webp_image)
        png_bytes = BytesIO()
        img.save(png_bytes, "PNG")
        png_bytes.seek(0)
        char_bytes = png_bytes.read()
    else:
        print(f"{icon_name}不存在，跳过！ content-type={content_type}")
        return

    with open(path, "wb") as handler:
        handler.write(char_bytes)
        print("下载成功！")


def download_char_icons(chars: Sequence[Dict[str, str]]):
    """
    chars: [{key, id, name}, ...]
      key  = 英文资源 key（Alyosha）
      id   = 角色 ID（10000148）
      name = 中文名（阿罗夏）
    """
    for char in chars:
        en_key = char["key"]
        char_id = char["id"]
        char_name = char["name"]
        print(f"==== 角色资源: {char_name} / {en_key} / {char_id} ====")
        for icon in icon_list:
            if icon.startswith("UI_NameCardPic"):
                _title = ASSET_BASE + "/namecard"
            else:
                _title = ASSET_BASE
            remote_name = icon.format(en_key)
            save_name = resolve_char_save_name(remote_name, char_id, char_name)
            url = f"{_title}/{remote_name}"
            if save_name != remote_name:
                print(f"{url}  ->  保存为 {save_name}")
            else:
                print(url)
            if is_download:
                download(save_name, url)


def download_weapon_icons(
    weapon_ids: Sequence[str],
    weapon_items: Dict[str, Any],
    vh: str = "",
    skip_skin: bool = False,
):
    for wid in weapon_ids:
        info = find_item_by_id(weapon_items, str(wid))
        if not info:
            print(f"武器 {wid} 不在列表中，跳过")
            continue
        if skip_skin and info.get("isWeaponSkin"):
            print(f"跳过武器皮肤: {info.get('name')} ({wid})")
            continue
        save_name = weapon_save_name(info)
        try:
            url = weapon_icon_url(info, vh=vh)
        except ValueError as e:
            print(e)
            continue
        print(f"==== 武器: {info.get('name')} ({wid}) icon={info.get('icon')} ====")
        print(url)
        if is_download:
            download(save_name, url)


def resolve_updated_chars(
    avatar_ids: Sequence[str],
    avatar_items: Dict[str, Any],
) -> List[Dict[str, str]]:
    """返回 [{key, id, name}, ...]，供下载与重命名使用。"""
    chars: List[Dict[str, str]] = []
    seen: Set[str] = set()
    for aid in avatar_ids:
        info = find_item_by_id(avatar_items, str(aid))
        if not info:
            print(f"角色 {aid} 不在列表中，跳过")
            continue
        key = avatar_icon_key(info)
        if not key:
            print(f"角色 {aid}({info.get('name')}) 无可用 icon key（可能是旅行者），跳过")
            continue
        # 旅行者等复合 id 保留原样；纯数字 id 用列表里的 id
        raw_id = info.get("id", aid)
        char_id = str(aid) if "-" in str(aid) else str(raw_id)
        char_name = str(info.get("name") or key)
        if key not in seen:
            seen.add(key)
            chars.append({"key": key, "id": char_id, "name": char_name})
            print(f"角色 {char_id} -> {char_name} / {key} (头像->{char_id}.png, 立绘->{char_name}.png)")
    return chars


def download_namecard_pic(start: int = 10000002):
    mapping_files = sorted(MAP_PATH.glob("enName2AvatarID_mapping_*.json"), reverse=True)
    if not mapping_files:
        print("未找到 enName2AvatarID_mapping，跳过 namecard 批量下载")
        return
    with open(mapping_files[0], encoding="utf-8") as f:
        enmap: Dict[str, str] = json.load(f)

    for _enname in enmap:
        en = _enname.split(" ")[-1]
        avatar_id = enmap[_enname]
        if int(avatar_id) < start:
            continue

        if en == "Jean":
            en = "Qin"
        elif en == "Baizhu":
            en = "Baizhuer"
        elif en == "Alhaitham":
            en = "Alhatham"
        elif en == "Jin":
            en = "Yunjin"
        elif en == "Miko":
            en = "Yae"
        elif en == "Heizou":
            en = "Heizo"
        elif en == "Amber":
            en = "Ambor"
        elif en == "Noelle":
            en = "Noel"
        elif en == "Yanfei":
            en = "Feiyan"
        elif en == "Shogun":
            en = "Shougun"
        elif en == "Lynette":
            en = "Linette"
        elif en == "Lyney":
            en = "Liney"
        elif en == "Tao":
            en = "Hutao"
        elif en == "Thoma":
            en = "Tohma"
        url = f"{ASSET_BASE}/UI_NameCardPic_{en}_P.{suffix}"
        download(f"{avatar_id}.{suffix}", url)


def main(
    version: Optional[str] = DEFAULT_VERSION,
    vh: str = DEFAULT_VH,
    do_char: bool = True,
    do_weapon: bool = True,
    skip_skin: bool = False,
    force_remote_list: bool = False,
):
    """
    1. 访问 changelog，取出该版本更新的 avatar / weapon
    2. 用 chs/avatar、chs/weapon（或本地 charList/weaponList）解析 icon
    3. 下载角色立绘/技能等 + 武器图标（中文名.png）
    """
    changelog = get_changelog(vh)
    key, entry = pick_changelog_entry(changelog, version)
    ver_name = entry.get("version", key)
    avatar_ids, weapon_ids = collect_ids_from_entry(entry)
    print(f"版本 {ver_name} (key={key})")
    print(f"  更新角色 IDs: {avatar_ids}")
    print(f"  更新武器 IDs: {weapon_ids}")

    if manual_char_list:
        print(f"附加手动角色: {manual_char_list}")
    if manual_weapon_ids:
        print(f"附加手动武器: {manual_weapon_ids}")
        weapon_ids = list(weapon_ids) + list(manual_weapon_ids)

    if do_char:
        if force_remote_list:
            url = with_vh(f"{API_BASE}/chs/avatar", vh)
            print(f"强制远程角色列表: {url}")
            avatar_items = fetch_json(url).get("data", {}).get("items", {})
        else:
            avatar_items = get_avatar_items(vh)
        chars = resolve_updated_chars(avatar_ids, avatar_items)
        # manual_char_list 可填英文 key；缺 id/名时仅作 key 兜底
        if manual_char_list:
            known = {c["key"] for c in chars}
            for c in manual_char_list:
                if c not in known:
                    chars.append({"key": c, "id": c, "name": c})
                    print(f"附加手动角色(仅 key，无重命名 id/名): {c}")
        if not chars:
            print("本版本无可用角色资源需要下载")
        else:
            print("将下载角色: " + ", ".join(f"{c['name']}({c['id']}/{c['key']})" for c in chars))
            download_char_icons(chars)

    if do_weapon:
        if force_remote_list:
            url = with_vh(f"{API_BASE}/chs/weapon", vh)
            print(f"强制远程武器列表: {url}")
            weapon_items = fetch_json(url).get("data", {}).get("items", {})
        else:
            weapon_items = get_weapon_items(vh)
        if not weapon_ids:
            print("本版本无武器更新")
        else:
            download_weapon_icons(weapon_ids, weapon_items, vh=vh, skip_skin=skip_skin)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="从 yatta changelog 自动下载更新角色资源与武器图标",
    )
    p.add_argument(
        "-v",
        "--version",
        default=DEFAULT_VERSION,
        help="游戏版本，如 7.0 / latest（默认 %(default)s）",
    )
    p.add_argument(
        "--vh",
        default=DEFAULT_VH,
        help="API vh 参数（默认 %(default)s）",
    )
    p.add_argument(
        "--char-only",
        action="store_true",
        help="只下载角色",
    )
    p.add_argument(
        "--weapon-only",
        action="store_true",
        help="只下载武器",
    )
    p.add_argument(
        "--skip-skin",
        action="store_true",
        help="跳过武器皮肤 (isWeaponSkin)",
    )
    p.add_argument(
        "--remote-list",
        action="store_true",
        help="强制走远程 avatar/weapon 列表，不用本地 map",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="只解析列表不下载",
    )
    p.add_argument(
        "--namecard",
        type=int,
        nargs="?",
        const=10000002,
        default=None,
        help="额外：按 avatarId 批量下载名片图（可传起始 id）",
    )
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    if args.dry_run:
        is_download = False

    if args.namecard is not None:
        download_namecard_pic(args.namecard)
    else:
        do_char = not args.weapon_only
        do_weapon = not args.char_only
        main(
            version=args.version,
            vh=args.vh,
            do_char=do_char,
            do_weapon=do_weapon,
            skip_skin=args.skip_skin,
            force_remote_list=args.remote_list,
        )

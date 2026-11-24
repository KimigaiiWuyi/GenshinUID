"""原神角色突破/升级材料离线计算器与采集地点索引。"""

from __future__ import annotations

import re
import json
import math
import asyncio
from typing import Mapping
from pathlib import Path
from dataclasses import dataclass

import aiohttp
from pydantic_ai import RunContext

from gsuid_core.ai_core.models import ToolContext
from gsuid_core.ai_core.register import ai_tools

from .user import CharBoxItem, _need_uid, collect_user_char_box
from ._common import as_int, as_str, region_zh
from ..utils.message import PREFIX
from ..utils.mys_api import mys_api
from ..utils.map.GS_MAP_PATH import monster2entry_data
from ..utils.map.name_covert import alias_to_char_name
from ..utils.resource.RESOURCE_PATH import CHAR_DATA_PATH, WIKI_DATA_CHAR

_CTX = ["原神", "Genshin", "游戏"]
_SEED_CHAR_DIR = Path(__file__).resolve().parents[1] / "tools" / "gs_data" / "char"
_SPLIT_RE = re.compile(r"[,，、;\s\n]+")
_BAG_QUERY_LIMIT = 50
_BAG_FETCH_ERRORS = (aiohttp.ClientError, TimeoutError, OSError)

# 原神角色 1~90 级累计经验精确表（源自 AvatarLevelExcelConfigData，Lv1→90 共 8,362,650 经验）
_CUMULATIVE_EXP: tuple[int, ...] = (
    0,
    1_000,
    2_325,
    4_025,
    6_175,
    8_800,
    11_950,
    15_675,
    20_025,
    25_025,
    30_725,
    37_175,
    44_400,
    52_450,
    61_375,
    71_200,
    81_950,
    93_675,
    106_400,
    120_175,
    135_050,
    151_850,
    169_850,
    189_100,
    209_650,
    231_525,
    254_775,
    279_425,
    305_525,
    333_100,
    362_200,
    392_850,
    425_100,
    458_975,
    494_525,
    531_775,
    570_750,
    611_500,
    654_075,
    698_500,
    744_800,
    795_425,
    848_125,
    902_900,
    959_800,
    1_018_875,
    1_080_150,
    1_143_675,
    1_209_475,
    1_277_600,
    1_348_075,
    1_424_575,
    1_503_625,
    1_585_275,
    1_669_550,
    1_756_500,
    1_846_150,
    1_938_550,
    2_033_725,
    2_131_725,
    2_232_600,
    2_341_550,
    2_453_600,
    2_568_775,
    2_687_100,
    2_808_625,
    2_933_400,
    3_061_475,
    3_192_875,
    3_327_650,
    3_465_825,
    3_614_525,
    3_766_900,
    3_922_975,
    4_082_800,
    4_246_400,
    4_413_825,
    4_585_125,
    4_760_350,
    4_939_525,
    5_122_700,
    5_338_925,
    5_581_950,
    5_855_050,
    6_161_850,
    6_506_450,
    6_893_400,
    7_327_825,
    7_815_450,
    8_362_650,
)
_ASCEND_BOUNDARY_LEVELS: frozenset[int] = frozenset({20, 40, 50, 60, 70, 80})

# 区域特产采集地点指引（结合地图命令「哪里有 <特产名>」可出精确点位图）
_SPECIALTY_LOCATIONS: dict[str, str] = {
    "钩钩果": "蒙德·奔狼领（密集）",
    "落落莓": "蒙德·望风山地 / 望风角",
    "塞西莉亚花": "蒙德·摘星崖（山顶集中）",
    "风车菊": "蒙德·风起地七天神像周边 / 风龙废墟",
    "慕风蘑菇": "蒙德·蒙德城 / 清泉镇 / 晨曦酒庄屋檐墙角",
    "小灯草": "蒙德·低语森林 / 奔狼领 / 达达乌帕谷",
    "嘟嘟莲": "蒙德·清泉镇湖畔 / 星落湖 / 晨曦酒庄水边",
    "蒲公英籽": "蒙德·蒙德城正门外两侧 / 晨曦酒庄周边（需风元素吹散）",
    "绝云椒椒": "璃月·轻策庄 / 绝云间 / 庆云顶",
    "夜泊石": "璃月·明蕴镇矿洞 / 层岩巨渊地上与地下矿区",
    "霓裳花": "璃月·璃月港玉京台 / 望舒客栈周边",
    "琉璃百合": "璃月·璃月港玉京台 / 轻策庄梯田",
    "清心": "璃月·绝云间 / 庆云顶 / 华光林高处山巅",
    "星螺": "璃月·瑶光滩 / 孤云阁海滩",
    "琉璃袋": "璃月·明蕴镇 / 无妄坡 / 绝云间峭壁",
    "石珀": "璃月·琥牢山 / 层岩巨渊 / 轻策庄岩壁",
    "清水玉": "璃月·沉玉谷（赤璋城垣 / 悬练山 / 灵濛山）",
    "鬼兜虫": "稻妻·鸣神大社山脚 / 踏鞴砂 / 九条阵屋树干",
    "绯樱绣球": "稻妻·鸣神岛（鸣神大社 / 影向山 / 镇守之森，需雷元素采集）",
    "晶化骨髓": "稻妻·八酝岛蛇骨矿洞 / 踏鞴砂蛇骨沿线",
    "血斛": "稻妻·九条阵屋 / 名椎滩 / 蛇神之首",
    "鸣草": "稻妻·踏鞴砂 / 蛇骨矿洞 / 影向山 / 清籁岛",
    "海灵芝": "稻妻·鸣神岛 / 神无冢 / 海祇岛 / 清籁岛近海浅滩",
    "珊瑚真珠": "稻妻·海祇岛珊瑚宫周边与渊下宫入口水池",
    "天云草实": "稻妻·清籁岛天云峠环湖（一对结两颗，效率极高）",
    "幽灯蕈": "稻妻·鹤观（知比山 / 千来神祠 / 逢岳之野）",
    "树王圣体菇": "须弥·无郁稠林 / 水天丛林树干与巨型菇盖",
    "帕蒂沙兰": "须弥·须弥城 / 禅那园 / 桓那兰那（现实态）",
    "月莲": "须弥·降诸魔山 / 维摩庄 / 离渡谷水面",
    "劫波莲": "须弥·维摩庄 / 水天丛林 / 降诸魔山瀑布悬崖",
    "赤念果": "须弥·沙漠仙人掌顶部（阿如村 / 饱饮之丘 / 丰饶绿洲）",
    "沙脂蛹": "须弥·千壑沙地（风蚀沙虫地下隧洞 / 亡者狭廊）",
    "悼灵花": "须弥·荒石苍漠（阻勒隘 / 铁穆山峡谷水边）",
    "万相石": "须弥·苍漠囿土地下矿道 / 锋刃林泽",
    "圣金虫": "须弥·大赤沙海（阿如村周边 / 丰饶绿洲 / 显圣厅地下）",
    "苍晶螺": "枫丹·赛洛海原 / 埃尔顿海沟 / 希望之路水下",
    "海露花": "枫丹·塔拉塔海谷 / 塞洛海原浅海（需水元素激活）",
    "柔灯铃": "枫丹·枫丹廷北郊 / 苍晶区（一株三朵）",
    "虹彩蔷薇": "枫丹·露景泉 / 枫丹廷西郊 / 厄里那斯",
    "幽光星星": "枫丹·黎翡区海滩与水下（芒索斯山东麓 / 梅洛彼得堡外）",
    "湖光铃兰": "枫丹·伊黎耶林区（湖中垂柳 / 优兰尼娅湖周边）",
    "子探测单元": "枫丹·枫丹动能工程科学研究院区废墟周边",
    "初露之源": "枫丹·莫尔泰区自家塔周围水下海贝",
    "浪沫羽鳃": "纳塔·流泉之众周边海岸与浮岛",
    "灼灼彩菊": "纳塔·圣火竞技场北侧 / 柴薪之丘 / 硫晶支脉",
    "青蜜莓": "纳塔·悬木人周边 / 祖遗庙宇 / 彩石顶（一株三颗）",
    "肉龙掌": "纳塔·回声之子周边 / 坚岩隘谷",
    "微光角菌": "纳塔·烟谜主周边 / 奥奇卡纳塔地下与山谷",
    "枯叶紫英": "纳塔·奥奇卡纳塔（旧城废墟周边密集）",
    "云岩裂叶": "纳塔·沃陆之邦 / 图兰大火山周边",
    "琉鳞石": "纳塔·安饶之野 / 圣山周边温泉岩壁",
    "便携轴承": "挪德卡莱·伦波岛 / 机械废墟与工坊周边",
    "霜盏花": "挪德卡莱·希汐岛 / 冻土林地",
    "月落银": "挪德卡莱·希汐岛沿岸与月光遗迹",
    "冬凌草": "挪德卡莱·高地雪坡与矿区边缘",
    "松珀香": "挪德卡莱·针叶林区树干与林间空地",
    "空羽蛾": "挪德卡莱·荒野与遗迹开阔地带",
    "妖精绿艾": "至冬·林地与郊野草丛",
    "析晶褶伞": "至冬·寒地洞穴与潮湿岩壁",
    "霜仙花": "至冬·雪原与冰湖沿岸",
    "植绒草": "至冬·苔原与高地草坡",
    "金蕨": "至冬·针叶林下与溪谷",
}

_EXTRA_BOSS_SOURCES: dict[str, str] = {
    "升扬样本·王族": "周本「门扉前的弈局」掉落",
    "升扬样本·战车": "周本「门扉前的弈局」掉落",
    "升扬样本·骑士": "周本「门扉前的弈局」掉落",
    "星与火的基石": "纳塔部族声望 / 主线任务获取（旅行者专用）",
}

_NON_REGION_TAGS: frozenset[str] = frozenset(
    {"MAINACTOR", "FATUI", "RANGER", "HVISION", "OMNI_SCOURGE", "NODKRAI_ZIBAI"}
)


@dataclass(frozen=True)
class PromoteTier:
    promote_level: int
    prev_max_level: int
    unlock_max_level: int
    coin_cost: int
    cost_items: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class CharAscendSpec:
    char_id: str
    name: str
    region_code: str
    region_zh: str
    tiers: tuple[PromoteTier, ...]
    item_names: Mapping[str, str]
    item_ranks: Mapping[str, int]
    talent_item_ids: tuple[str, ...]


@dataclass(frozen=True)
class MaterialMeta:
    item_id: str
    name: str
    rank: int
    category: str
    source_hint: str
    used_by: tuple[str, ...]


class _MaterialRegistry:
    """进程内只读缓存：按需一次扫描本地 139 角色 JSON 与 monster2entry_data。"""

    def __init__(self) -> None:
        self._loaded: bool = False
        self.chars_by_id: dict[str, CharAscendSpec] = {}
        self.chars_by_name: dict[str, CharAscendSpec] = {}
        self.materials_by_id: dict[str, MaterialMeta] = {}
        self.materials_by_name: dict[str, MaterialMeta] = {}
        self._drop_monsters: dict[str, list[str]] = {}

    def ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._build_monster_drop_map()
        self._load_all_chars()
        self._loaded = True

    def _build_monster_drop_map(self) -> None:
        drop_sets: dict[str, set[str]] = {}
        for entry in monster2entry_data.values():
            if not isinstance(entry, dict):
                continue
            mname = as_str(entry["name"]) if "name" in entry else ""
            reward = entry["reward"] if "reward" in entry else None
            if not mname or not isinstance(reward, dict):
                continue
            for item_id in reward:
                key = str(item_id)
                if key not in drop_sets:
                    drop_sets[key] = set()
                drop_sets[key].add(mname)
        for item_id, names in drop_sets.items():
            self._drop_monsters[item_id] = sorted(names)

    def _load_all_chars(self) -> None:
        item_names: dict[str, str] = {}
        item_ranks: dict[str, int] = {}
        item_users: dict[str, list[str]] = {}
        item_regions: dict[str, list[str]] = {}

        # 按优先级合并：运行时 wiki 缓存 / CHAR_DATA_PATH 覆盖仓库内置种子，确保新版本自动生效
        dirs: list[Path] = [_SEED_CHAR_DIR]
        if CHAR_DATA_PATH.is_dir():
            dirs.append(CHAR_DATA_PATH)
        if WIKI_DATA_CHAR.is_dir():
            dirs.append(WIKI_DATA_CHAR)

        raw_files: dict[str, Path] = {}
        for folder in dirs:
            if not folder.is_dir():
                continue
            for path in folder.glob("*.json"):
                raw_files[path.stem] = path

        for stem, path in sorted(raw_files.items()):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if not isinstance(raw, dict):
                continue
            spec = _parse_char_ascend(stem, raw)
            if spec is None:
                continue
            self.chars_by_id[spec.char_id] = spec
            if spec.name not in self.chars_by_name or "-" not in spec.char_id:
                self.chars_by_name[spec.name] = spec

            used_ids: set[str] = set()
            for tier in spec.tiers:
                for iid, _cnt in tier.cost_items:
                    used_ids.add(iid)
            for iid in spec.talent_item_ids:
                used_ids.add(iid)

            for iid, iname in spec.item_names.items():
                # 跳过历史导出偶发数字哈希，保留有效中文名
                if iid not in item_names or (item_names[iid].isdigit() and not iname.isdigit()):
                    item_names[iid] = iname
                if iid in spec.item_ranks:
                    item_ranks[iid] = spec.item_ranks[iid]

            for iid in used_ids:
                if iid not in item_users:
                    item_users[iid] = []
                if spec.name not in item_users[iid]:
                    item_users[iid].append(spec.name)
                if spec.region_code and spec.region_code not in _NON_REGION_TAGS:
                    if iid not in item_regions:
                        item_regions[iid] = []
                    if spec.region_zh not in item_regions[iid]:
                        item_regions[iid].append(spec.region_zh)

        for iid, iname in item_names.items():
            rank = item_ranks[iid] if iid in item_ranks else 1
            cat = _classify_item(iid, rank)
            hint = _resolve_source_hint(
                iid,
                iname,
                cat,
                self._drop_monsters[iid] if iid in self._drop_monsters else [],
                item_regions[iid] if iid in item_regions else [],
            )
            users = tuple(sorted(item_users[iid])) if iid in item_users else ()
            meta = MaterialMeta(
                item_id=iid,
                name=iname,
                rank=rank,
                category=cat,
                source_hint=hint,
                used_by=users,
            )
            self.materials_by_id[iid] = meta
            self.materials_by_name[iname] = meta


_REGISTRY = _MaterialRegistry()


def _parse_char_ascend(stem: str, raw: Mapping[str, object]) -> CharAscendSpec | None:
    name = as_str(raw["name"]) if "name" in raw else ""
    if not name or name.startswith("奇偶"):
        return None
    cid = str(raw["id"]) if "id" in raw else stem
    if "-" in stem:
        cid = stem
    region_code = as_str(raw["region"]) if "region" in raw else ""
    upgrade = raw["upgrade"] if "upgrade" in raw and isinstance(raw["upgrade"], dict) else None
    if upgrade is None or "promote" not in upgrade or not isinstance(upgrade["promote"], list):
        return None

    item_names: dict[str, str] = {}
    item_ranks: dict[str, int] = {}
    items_raw = raw["items"] if "items" in raw and isinstance(raw["items"], dict) else {}
    for kid, entry in items_raw.items():
        if not isinstance(entry, dict):
            continue
        iname = as_str(entry["name"]) if "name" in entry else str(kid)
        item_names[str(kid)] = iname
        item_ranks[str(kid)] = as_int(entry["rank"]) if "rank" in entry else 1

    tiers: list[PromoteTier] = []
    prev_max = 20
    for p in upgrade["promote"]:
        if not isinstance(p, dict):
            continue
        plevel = as_int(p["promoteLevel"]) if "promoteLevel" in p else 0
        umax = as_int(p["unlockMaxLevel"]) if "unlockMaxLevel" in p else prev_max
        if plevel == 0:
            prev_max = umax or 20
            continue
        coin = as_int(p["coinCost"]) if "coinCost" in p else 0
        costs_raw = p["costItems"] if "costItems" in p and isinstance(p["costItems"], dict) else {}
        cost_pairs: list[tuple[str, int]] = []
        for kid, cnt in costs_raw.items():
            n = as_int(cnt)
            if n > 0:
                cost_pairs.append((str(kid), n))
        tiers.append(
            PromoteTier(
                promote_level=plevel,
                prev_max_level=prev_max,
                unlock_max_level=umax,
                coin_cost=coin,
                cost_items=tuple(cost_pairs),
            )
        )
        prev_max = umax

    talent_ids: set[str] = set()
    talent_raw = raw["talent"] if "talent" in raw and isinstance(raw["talent"], dict) else {}
    for skill in talent_raw.values():
        if not isinstance(skill, dict) or "promote" not in skill or not isinstance(skill["promote"], dict):
            continue
        for lv_info in skill["promote"].values():
            if not isinstance(lv_info, dict):
                continue
            citems = lv_info["costItems"] if "costItems" in lv_info and isinstance(lv_info["costItems"], dict) else {}
            for kid in citems:
                talent_ids.add(str(kid))

    return CharAscendSpec(
        char_id=cid,
        name=name,
        region_code=region_code,
        region_zh=region_zh(region_code) if region_code else "提瓦特",
        tiers=tuple(tiers),
        item_names=item_names,
        item_ranks=item_ranks,
        talent_item_ids=tuple(sorted(talent_ids)),
    )


def _classify_item(item_id: str, rank: int) -> str:
    if item_id.startswith(("100", "101")):
        return "区域特产"
    if item_id.startswith("113"):
        return "周本素材" if rank >= 5 else "世界Boss素材"
    if item_id.startswith("1041"):
        return "元素突破晶石"
    if item_id.startswith("1043"):
        return "天赋书"
    if item_id.startswith("112"):
        return "怪物掉落"
    return "其他素材"


def _resolve_source_hint(
    item_id: str,
    name: str,
    category: str,
    monsters: list[str],
    regions: list[str],
) -> str:
    if name in _SPECIALTY_LOCATIONS:
        return f"{_SPECIALTY_LOCATIONS[name]}（可用「哪里有 {name}」查点位图）"
    if name in _EXTRA_BOSS_SOURCES:
        return _EXTRA_BOSS_SOURCES[name]
    if category == "区域特产":
        reg = "/".join(regions[:2]) if regions else "提瓦特"
        return f"{reg}区域特产（可用「哪里有 {name}」查点位图）"
    if category in ("世界Boss素材", "周本素材"):
        if monsters:
            shown = " / ".join(monsters[:3])
            prefix = "周本" if category == "周本素材" else "世界Boss"
            return f"{prefix}「{shown}」掉落"
        return "对应世界Boss/周本掉落"
    if category == "怪物掉落":
        if monsters:
            shown = "、".join(monsters[:4])
            more = f"等{len(monsters)}种怪物" if len(monsters) > 4 else ""
            return f"击杀 {shown}{more} 掉落（高阶可合成台 3:1 合成）"
        return "野外普通/精英怪掉落（高阶可合成台 3:1 合成）"
    if category == "元素突破晶石":
        return "对应元素世界Boss/周本/每日委托获取，也可用嬗变之尘在合成台转换"
    if category == "天赋书":
        return "对应地区天赋秘境按周几轮换刷取（周日全开）"
    return f"道具ID {item_id}"


def _cumulative_exp(level: int) -> int:
    lv = max(1, min(90, level))
    return _CUMULATIVE_EXP[lv - 1]


def _resolve_spec_for_box_item(item: CharBoxItem) -> CharAscendSpec | None:
    _REGISTRY.ensure_loaded()
    if item.char_id and item.char_id in _REGISTRY.chars_by_id:
        return _REGISTRY.chars_by_id[item.char_id]
    if item.name in _REGISTRY.chars_by_name:
        return _REGISTRY.chars_by_name[item.name]
    if item.name == "旅行者":
        for candidate in ("10000007-anemo", "10000005-anemo"):
            if candidate in _REGISTRY.chars_by_id:
                return _REGISTRY.chars_by_id[candidate]
    return None


async def _try_fetch_bag_inventory(
    uid: str,
    targets: list[tuple[CharBoxItem, int]],
) -> dict[str, int] | None:
    """尝试调用米游社养成计算器拿到玩家当前背包库存（只扣已有，不依赖其总缺口）。"""
    from ..genshinuid_compute.utils import char_id_to_compute_dict

    coros = [
        char_id_to_compute_dict(
            item.char_id,
            current_level=max(1, min(target_lv - 1, item.level)),
            target_level=target_lv,
            skill1_current_level=1,
            skill1_target_level=1,
            skill2_current_level=1,
            skill2_target_level=1,
            skill3_current_level=1,
            skill3_target_level=1,
            weapon_id=0,
        )
        for item, target_lv in targets[:_BAG_QUERY_LIMIT]
        if item.char_id and item.char_id.isdigit()
    ]
    if not coros:
        return None
    raw_entries = await asyncio.gather(*coros)
    payload: list[dict[str, object]] = [entry for entry in raw_entries if isinstance(entry, dict)]
    if not payload:
        return None
    try:
        resp = await mys_api.get_batch_compute_info(uid, payload)
    except _BAG_FETCH_ERRORS:
        return None
    if not isinstance(resp, dict) or "overall_consume" not in resp:
        return None
    consume = resp["overall_consume"]
    if not isinstance(consume, list):
        return None
    bag: dict[str, int] = {}
    for row in consume:
        if not isinstance(row, dict) or "id" not in row or "num" not in row or "lack_num" not in row:
            continue
        iid = str(row["id"])
        have = max(0, as_int(row["num"]) - as_int(row["lack_num"]))
        bag[iid] = have
    return bag


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain="原神养成计算",
    covers=[
        "统计未满90级角色数量",
        "计算角色升到90级缺多少突破材料",
        "汇总未满级角色所需特产Boss素材经验书摩拉",
        "哪些材料要去哪个地方采",
    ],
    aliases=["原神·升级材料计算", "原神·90级突破缺口", "原神·养成材料统计"],
)
async def calc_genshin_char_ascension_gaps(
    ctx: RunContext[ToolContext],
    uid: str = "",
    target_level: int = 90,
    char_names: str = "",
    deduct_bag: bool = True,
    include_sources: bool = True,
) -> str:
    """一次性离线计算用户未满级角色升级到目标等级（默认90级）的全部材料缺口与采集地点。

    问「还有多少角色没90级 / 升90级都缺多少材料 / 哪些材料去哪采 / 拉某几个角色要多少材料」时优先直接调本工具。
    纯本地计算全部角色突破表、经验书、摩拉，并自动附带特产采集区、世界Boss名与掉落怪；
    已绑 Cookie 时可同时扣减米游社养成计算器里的背包现有库存。

    Args:
        uid: 9 到 10 位原神 UID。留空则用当前用户默认绑定。
        target_level: 目标等级（20~90），默认 90。
        char_names: 可选，只计算指定角色（逗号/顿号/空格分隔，支持简称）。留空则统计全箱未达 target_level 的角色。
        deduct_bag: 是否尝试读取米游社背包扣减现有库存，默认 True（无 Cookie 或接口失败自动退回总需求）。
        include_sources: 是否附带每种材料的采集地区 / Boss / 掉落怪说明，默认 True。
    """
    target, err = await _need_uid(ctx, uid)
    if err:
        return err
    goal_lv = max(20, min(90, int(target_level)))
    source, box = await collect_user_char_box(target)
    if not box:
        return (
            f"UID {target} 暂无角色箱数据。[source=none complete=false]\n"
            f"绑定 Cookie 可读全角色箱；未绑 Cookie 时请先 `{PREFIX}强制刷新` 拉取展柜缓存。"
        )

    _REGISTRY.ensure_loaded()
    filter_names: set[str] = set()
    if char_names.strip():
        for raw_name in _SPLIT_RE.split(char_names.strip()):
            token = raw_name.strip()
            if not token:
                continue
            resolved = await alias_to_char_name(token)
            filter_names.add(resolved)
            filter_names.add(token)

    at_or_above: list[CharBoxItem] = []
    below: list[CharBoxItem] = []
    for item in box:
        if filter_names and item.name not in filter_names:
            continue
        if item.level >= goal_lv:
            at_or_above.append(item)
        else:
            below.append(item)

    if filter_names and not below and not at_or_above:
        return f"UID {target} 的角色箱中未找到指定角色：{char_names}"
    if not below:
        scope_tag = "complete=true" if source == "mys_index" else "complete=false"
        return (
            f"UID {target} [{source} {scope_tag}]：所选 {len(at_or_above)} 名角色均已达到 Lv{goal_lv}，"
            "无升级突破材料缺口。"
        )

    below.sort(key=lambda c: (-c.level, -c.rarity, c.name))

    bag: dict[str, int] | None = None
    if deduct_bag and source == "mys_index":
        bag = await _try_fetch_bag_inventory(target, [(c, goal_lv) for c in below])

    totals_by_id: dict[str, int] = {}
    item_char_refs: dict[str, list[str]] = {}
    total_exp = 0
    total_ascend_mora = 0
    boundary_chars: list[str] = []
    missing_specs: list[str] = []
    per_char_rows: list[str] = []

    for item in below:
        cur_lv = max(1, item.level)
        if cur_lv in _ASCEND_BOUNDARY_LEVELS:
            boundary_chars.append(f"{item.name}(Lv{cur_lv})")
        exp_need = max(0, _cumulative_exp(goal_lv) - _cumulative_exp(cur_lv))
        total_exp += exp_need
        spec = _resolve_spec_for_box_item(item)
        if spec is None:
            missing_specs.append(item.name)
            per_char_rows.append(f"| {item.name} | Lv{cur_lv} | (缺本地图鉴数据) | - | - |")
            continue

        char_spec_parts: list[str] = []
        char_boss_parts: list[str] = []
        char_mob_parts: list[str] = []
        char_totals: dict[str, int] = {}
        for tier in spec.tiers:
            if tier.prev_max_level < goal_lv and cur_lv <= tier.prev_max_level:
                total_ascend_mora += tier.coin_cost
                for iid, cnt in tier.cost_items:
                    totals_by_id[iid] = (totals_by_id[iid] if iid in totals_by_id else 0) + cnt
                    char_totals[iid] = (char_totals[iid] if iid in char_totals else 0) + cnt
                    if iid not in item_char_refs:
                        item_char_refs[iid] = []
                    if item.name not in item_char_refs[iid]:
                        item_char_refs[iid].append(item.name)

        for iid, cnt in char_totals.items():
            meta = _REGISTRY.materials_by_id[iid] if iid in _REGISTRY.materials_by_id else None
            iname = meta.name if meta is not None else (spec.item_names[iid] if iid in spec.item_names else iid)
            cat = meta.category if meta is not None else _classify_item(iid, 1)
            piece = f"{iname}×{cnt}"
            if cat == "区域特产":
                char_spec_parts.append(piece)
            elif cat in ("世界Boss素材", "周本素材"):
                char_boss_parts.append(piece)
            elif cat == "怪物掉落":
                char_mob_parts.append(piece)

        per_char_rows.append(
            f"| {item.name} | Lv{cur_lv} | {'、'.join(char_spec_parts) or '无(仅经验)'} | "
            f"{'、'.join(char_boss_parts) or '无'} | {'、'.join(char_mob_parts) or '无'} |"
        )

    level_mora = total_exp // 5
    total_mora = total_ascend_mora + level_mora
    heros_wit = math.ceil(total_exp / 20_000)

    complete_flag = "complete=true" if source == "mys_index" else "complete=false"
    if bag is not None:
        bag_flag = (
            f"已扣减米游社背包库存（按前 {_BAG_QUERY_LIMIT} 名未满级角色回查，其余材料按总需求计）"
            if len(below) > _BAG_QUERY_LIMIT
            else "已扣减米游社背包现有库存"
        )
    else:
        bag_flag = "未扣减背包库存（按当前等级→目标等级总需求计）"
    lines: list[str] = [
        f"UID {target} 升至 Lv{goal_lv} 材料缺口统计 [source={source} {complete_flag}]",
        f"总览：共 {len(box)} 名角色｜已满 Lv{goal_lv}：{len(at_or_above)} 名｜未满 Lv{goal_lv}：{len(below)} 名",
        f"库存口径：{bag_flag}",
    ]
    if source != "mys_index":
        lines.append(f"⚠️ 当前为展柜缓存而非全角色箱，绑定 Cookie 或 `{PREFIX}刷新面板` 可获取全箱。")
    if boundary_chars:
        shown_b = "、".join(boundary_chars[:12])
        more_b = f" 等{len(boundary_chars)}人" if len(boundary_chars) > 12 else ""
        lines.append(
            f"注：接口不含当前突破星级，处于 20/40/50/60/70/80 级边界的角色（{shown_b}{more_b}）"
            "默认按未突破计入下一阶突破材料。"
        )
    if missing_specs:
        lines.append(f"注：以下角色缺少本地图鉴突破表未计入材料：{', '.join(missing_specs)}")

    # 经验与摩拉总计
    wit_have = bag["104003"] if bag is not None and "104003" in bag else None
    mora_have = bag["202"] if bag is not None and "202" in bag else None
    wit_line = f"大英雄的经验：需 {heros_wit:,} 本（总经验 {total_exp:,}）"
    if wit_have is not None:
        wit_line += f"｜背包已有 {wit_have:,} 本｜净缺 {max(0, heros_wit - wit_have):,} 本"
    mora_line = f"摩拉：共需 {total_mora:,}（升级 {level_mora:,} + 突破 {total_ascend_mora:,}）"
    if mora_have is not None:
        mora_line += f"｜背包已有 {mora_have:,}｜净缺 {max(0, total_mora - mora_have):,}"
    lines.extend(["", "## 1. 经验与摩拉总计", f"- {wit_line}", f"- {mora_line}"])

    # 按材料大类汇总
    grouped: dict[str, list[tuple[str, int, int | None, MaterialMeta | None]]] = {
        "区域特产": [],
        "世界Boss素材": [],
        "怪物掉落": [],
        "元素突破晶石": [],
        "其他素材": [],
    }
    for iid, need in totals_by_id.items():
        meta = _REGISTRY.materials_by_id[iid] if iid in _REGISTRY.materials_by_id else None
        cat = meta.category if meta is not None else _classify_item(iid, 1)
        bucket = cat if cat in grouped else "其他素材"
        have = bag[iid] if bag is not None and iid in bag else None
        grouped[bucket].append((iid, need, have, meta))

    def _emit_group(title: str, key: str, *, show_resin: bool = False) -> None:
        entries = grouped[key]
        if not entries:
            return
        entries.sort(key=lambda e: (-((max(0, e[1] - e[2])) if e[2] is not None else e[1]), -e[1], e[0]))
        lines.extend(["", f"## {title}（共 {len(entries)} 种）"])
        for iid, need, have, meta in entries:
            iname = meta.name if meta is not None else iid
            users = item_char_refs[iid] if iid in item_char_refs else []
            user_str = "、".join(users[:5]) + (f"等{len(users)}人" if len(users) > 5 else "")
            if have is not None:
                lack = max(0, need - have)
                qty_s = f"需 {need}｜已有 {have}｜净缺 {lack}"
                eff = lack
            else:
                qty_s = f"共需 {need}"
                eff = need
            resin_s = ""
            if show_resin and eff > 0:
                runs = math.ceil(eff / 2.5)
                resin_s = f"（约打 {runs} 次 / {runs * 40} 树脂）"
            src_s = f"｜来源：{meta.source_hint}" if include_sources and meta is not None else ""
            lines.append(f"- **{iname}**：{qty_s}{resin_s}（用者：{user_str}）{src_s}")

    _emit_group("2. 区域特产汇总与采集地", "区域特产")
    _emit_group("3. 世界Boss突破素材汇总", "世界Boss素材", show_resin=True)
    _emit_group("4. 怪物掉落素材汇总", "怪物掉落")
    _emit_group("5. 元素突破晶石汇总", "元素突破晶石")
    _emit_group("6. 其他突破素材", "其他素材")

    lines.extend(
        [
            "",
            f"## 7. 未满 Lv{goal_lv} 角色明细（共 {len(below)} 名，按当前等级从高到低）",
            "| 角色 | 当前等级 | 缺口特产 | 缺口Boss素材 | 缺口怪物素材 |",
            "|---|---|---|---|---|",
            *per_char_rows,
        ]
    )
    return "\n".join(lines)


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain="原神资料库",
    covers=[
        "原神材料在哪采",
        "特产采集地点",
        "世界Boss掉落对应表",
        "怪物掉落来源",
        "角色需要哪些突破和天赋材料",
    ],
    aliases=["原神·材料产地", "原神·采集地点查询", "原神·素材来源"],
)
async def get_genshin_material_sources(
    ctx: RunContext[ToolContext],
    material_names: str,
) -> str:
    """批量查询原神突破材料/特产/Boss素材/怪物掉落的采集地点与掉落来源，也可直接传角色名查其全部养成材料。

    纯本地离线毫秒级查询，无需逐个查知识库或网页搜索。若需某特产的精确地图标点图，可继续调用「哪里有 <特产名>」。

    Args:
        material_names: 材料名或角色名（逗号/顿号/空格分隔），如 "绯樱绣球、清心、恒常机关之心" 或 "神里绫华"。
    """
    _ = ctx
    raw = material_names.strip()
    if not raw:
        return "请提供至少一个材料名或角色名。"
    _REGISTRY.ensure_loaded()
    tokens = [tok.strip() for tok in _SPLIT_RE.split(raw) if tok.strip()]
    blocks: list[str] = []
    seen_out: set[str] = set()

    for token in tokens[:30]:
        if token in _REGISTRY.materials_by_name:
            meta = _REGISTRY.materials_by_name[token]
            if meta.item_id in seen_out:
                continue
            seen_out.add(meta.item_id)
            users = "、".join(meta.used_by[:8]) + (f" 等{len(meta.used_by)}人" if len(meta.used_by) > 8 else "")
            blocks.append(
                f"- **{meta.name}**（{meta.category}）：{meta.source_hint}" + (f"｜需求角色：{users}" if users else "")
            )
            continue

        # 尝试按角色名/别名展开该角色的全部突破与天赋材料
        resolved_char = await alias_to_char_name(token)
        if resolved_char in _REGISTRY.chars_by_name:
            spec = _REGISTRY.chars_by_name[resolved_char]
            if f"char:{spec.name}" in seen_out:
                continue
            seen_out.add(f"char:{spec.name}")
            mat_lines: list[str] = [f"### {spec.name}（{spec.region_zh}）养成材料与来源"]
            char_ids: list[str] = []
            for tier in spec.tiers:
                for iid, _cnt in tier.cost_items:
                    if iid not in char_ids:
                        char_ids.append(iid)
            for iid in spec.talent_item_ids:
                if iid not in char_ids:
                    char_ids.append(iid)
            for iid in char_ids:
                if iid not in _REGISTRY.materials_by_id:
                    continue
                meta = _REGISTRY.materials_by_id[iid]
                if meta.category == "元素突破晶石" and meta.rank != 5:
                    continue
                if meta.category == "天赋书" and meta.rank != 4:
                    continue
                mat_lines.append(f"  - {meta.name}（{meta.category}）：{meta.source_hint}")
            blocks.append("\n".join(mat_lines))
            continue

        # 子串模糊匹配（如「刀镡」「史莱姆」「琉璃」）
        fuzzy = [m for name, m in _REGISTRY.materials_by_name.items() if token in name]
        if fuzzy:
            for meta in fuzzy[:6]:
                if meta.item_id in seen_out:
                    continue
                seen_out.add(meta.item_id)
                users = "、".join(meta.used_by[:6]) + (f" 等{len(meta.used_by)}人" if len(meta.used_by) > 6 else "")
                blocks.append(
                    f"- **{meta.name}**（{meta.category}）：{meta.source_hint}"
                    + (f"｜需求角色：{users}" if users else "")
                )
        else:
            blocks.append(
                f"- **{token}**：未在本地角色突破/天赋材料索引中命中，可核对名称或用「哪里有 {token}」查地图。"
            )

    return "\n".join(blocks)


def search_local_materials_text(query: str, limit: int = 4) -> list[str]:
    """供 kb.py 在 Qdrant 离线时按词面降级检索材料来源。"""
    _REGISTRY.ensure_loaded()
    q = query.strip()
    if not q:
        return []
    hits: list[MaterialMeta] = []
    seen: set[str] = set()
    for token in _SPLIT_RE.split(q):
        tok = token.strip()
        if len(tok) < 2:
            continue
        for name, meta in _REGISTRY.materials_by_name.items():
            if meta.item_id in seen:
                continue
            if tok == name or tok in name or name in q:
                seen.add(meta.item_id)
                hits.append(meta)
                if len(hits) >= limit:
                    break
        if len(hits) >= limit:
            break
    out: list[str] = []
    for meta in hits:
        users = "、".join(meta.used_by[:8])
        out.append(
            f"### {meta.name}（本地材料索引·{meta.category}）\n"
            f"获取途径：{meta.source_hint}\n" + (f"需求角色：{users}" if users else "")
        )
    return out

from typing import Any, Dict, List, Tuple, Union, Literal, Optional
from urllib.parse import quote, unquote

from aiohttp import TCPConnector, ClientSession, ContentTypeError

from gsuid_core.i18n import t
from gsuid_core.logger import logger

from .api import (
    DATA_API,
    MAIN_API,
    RANK_API,
    SORT_API,
    BUILDS_API,
    REFRESH_API,
    STYGIAN_API,
    BUILD_LB_API,
    HASH_ROW_API,
    ARTI_SORT_API,
    GLOBAL_LB_API,
    DAMAGE_DIST_API,
    LEADERBOARD_API,
    SUBSTAT_PRIORITY_API,
)
from .models import (
    GlobalRankRow,
    BuildLeaderboardRow,
    SubstatPriorityItem,
    SubstatPriorityBoard,
    DamageDistributionBoard,
)
from .ttl_cache import CV_CACHE_TTL_SEC, TtlMemo
from .global_ranks import parse_global_ranks_payload
from .substat_priority import (
    parse_substat_priority_payload,
    compute_substat_priority_boards,
)
from .build_leaderboards import (
    extract_build_md5,
    list_visible_leaderboards,
    parse_build_leaderboards_payload,
)
from .damage_distribution import (
    board_calculation_id,
    find_damage_distribution,
    list_visible_distributions,
    parse_damage_distribution_payload,
)

_SUBSTAT_CACHE: TtlMemo[list[SubstatPriorityItem]] = TtlMemo(CV_CACHE_TTL_SEC)
_LEADERBOARD_CACHE: TtlMemo[list[BuildLeaderboardRow]] = TtlMemo(CV_CACHE_TTL_SEC)
_MD5_CACHE: TtlMemo[str] = TtlMemo(CV_CACHE_TTL_SEC)
_DMG_CACHE: TtlMemo[list[DamageDistributionBoard]] = TtlMemo(CV_CACHE_TTL_SEC)
_GLOBAL_CACHE: TtlMemo[list[GlobalRankRow]] = TtlMemo(CV_CACHE_TTL_SEC)

SUBSTAT_MAP = {
    "双爆": "critValue",
    "百分比攻击力": "substats.ATK%",
    "百分比血量": "substats.HP%",
    "百分比防御": "substats.DEF%",
    "固定攻击力": "substats.Flat ATK",
    "固定血量": "substats.Flat HP",
    "固定生命": "substats.Flat HP",
    "固定防御力": "substats.Flat DEF",
    "元素精通": "substats.Elemental Mastery",
    "元素充能效率": "substats.Energy Recharge",
    "暴击率": "substats.Crit RATE",
    "暴击伤害": "substats.Crit DMG",
}


class _CvApi:
    ssl_verify = True
    _HEADER = {
        "User-Agent": "GsCore / GenshinUID / 6.2.0",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=self.ssl_verify))
        self.sessionID = None

    async def get_artifacts_list(
        self,
        sort_by: Union[
            Literal[
                "critValue",
                "substats.Flat ATK",
                "substats.Flat HP",
                "substats.Flat DEF",
                "substats.ATK%",
                "substats.HP%",
                "substats.DEF%",
                "substats.Elemental Mastery",
                "substats.Energy Recharge",
                "substats.Crit RATE",
                "substats.Crit DMG",
            ],
            str,
            None,
        ] = "critValue",
    ) -> Optional[List[Dict]]:
        if sort_by is None or not sort_by:
            sort_by = "critValue"
        if not sort_by.startswith(("c", "s")):
            for i in SUBSTAT_MAP:
                if sort_by in i:
                    sort_by = SUBSTAT_MAP[i]
                    break
            else:
                return None
        raw_data = await self._cv_request(
            ARTI_SORT_API.format(sort_by),
            "GET",
            self._HEADER,
        )
        if isinstance(raw_data, Dict) and "data" in raw_data:
            if raw_data["data"]:
                return raw_data["data"]
            else:
                return None

    async def get_leaderboard_id_list(self, char_id: str) -> Optional[List[Dict]]:
        raw_data = await self._cv_request(
            LEADERBOARD_API.format(char_id),
            "GET",
            self._HEADER,
        )
        if isinstance(raw_data, Dict) and "data" in raw_data:
            if raw_data["data"]:
                return raw_data["data"]
            else:
                return None

    async def get_calculation_info(self, char_id: str) -> Optional[Tuple[str, int]]:
        raw_data = await self.get_leaderboard_id_list(char_id)
        if raw_data is not None:
            return (
                raw_data[0]["weapons"][0]["calculationId"],
                raw_data[0]["count"],
            )

    async def get_sort_list(
        self,
        char_id: str,
        calculation_id: Optional[str] = None,
        combo: Optional[Union[str, int, float]] = None,
    ) -> Optional[Tuple[List[Dict], int]]:
        count = 0
        if calculation_id is None:
            _raw_data = await self.get_calculation_info(char_id)
            if _raw_data is not None:
                calculation_id, count = _raw_data
        else:
            lb_data = await self.get_leaderboard_id_list(char_id)
            if lb_data:
                for i in lb_data:
                    for g in i["weapons"]:
                        if g["calculationId"] == calculation_id:
                            count = i["count"]
                            break

        if count == 0:
            return None

        extra = ""
        if combo:
            extra += f"&p=lt%7C{combo}"
        else:
            extra = "&p="

        url = SORT_API.format(calculation_id) + extra
        logger.debug(t("log.genshinuid.akasha_url_url_9d8655", url=url))
        raw_data = await self._cv_request(
            url,
            "GET",
            self._HEADER,
        )
        if isinstance(raw_data, Dict) and "data" in raw_data:
            return raw_data["data"], count

    async def get_session_id(self) -> str:
        async with self.session.get(MAIN_API) as resp:
            cookies = resp.cookies
            cookies_dict = dict(cookies)
            sid = cookies_dict.get("connect.sid", None)
            if sid is not None:
                sid = sid.value
            else:
                sid = "NVybrjSdSZISA0JRuKFoZIndoCfDWdA2"
            sid = unquote(str(sid))
            sessionID = sid.split(".")[0].split(":")[-1]
            self.sessionID = sessionID
            return sessionID

    async def get_base_data(self, uid: str) -> Union[Dict, int]:
        sessionID = await self.get_session_id()
        return await self._cv_request(DATA_API.format(uid), "GET", self._HEADER, {"sessionID": sessionID})

    async def get_refresh_data(self, uid: str) -> Union[Dict, int]:
        return await self._cv_request(
            REFRESH_API.format(uid),
            "GET",
            self._HEADER,
            {"sessionID": self.sessionID},
        )

    async def get_rank_data(self, uid: str) -> Union[Tuple[Dict, Dict], int]:
        await self.get_base_data(uid)
        await self.get_refresh_data(uid)
        data1 = await self._cv_request(RANK_API.format(uid), "GET", self._HEADER)
        data2 = await self._cv_request(BUILDS_API.format(uid), "GET", self._HEADER)
        await self.session.close()
        if isinstance(data1, int):
            return data1
        if isinstance(data2, int):
            return data2
        return data1, data2

    async def get_stygian_rank_data(self):
        data = await self._cv_request(STYGIAN_API, "GET", self._HEADER)
        if isinstance(data, int):
            return data
        row = await self._cv_request(
            HASH_ROW_API + data["totalRowsHash"],
            "GET",
            self._HEADER,
        )

        if isinstance(row, int):
            count: int = 2999999
        else:
            count = row["totalRows"]

        return data, count

    async def get_substat_priority(self, uid: str, md5: str) -> list[SubstatPriorityItem] | int:
        """请求某套配装在各 Akasha 榜上的副词条优先级。

        对应 ``GET /api/substatPriority/{uid}/{md5}``。
        每条榜的 ``substats`` 是「当前面板再加一发五星满幅」后的模拟榜分。
        相同 ``uid`` + ``md5`` 缓存一小时，并发相同请求合并为一次 HTTP。
        失败返回 errno（与其它 CV 方法一致），失败不进缓存。
        """

        async def fetch() -> list[SubstatPriorityItem] | int:
            url = SUBSTAT_PRIORITY_API.format(quote(uid, safe=""), quote(md5, safe=""))
            raw = await self._cv_request(url, "GET", self._HEADER)
            if isinstance(raw, int):
                return raw
            parsed = parse_substat_priority_payload(raw)
            if parsed is None:
                return -1
            return parsed

        return await _SUBSTAT_CACHE.get(f"{uid}:{md5}", fetch)

    async def get_substat_priority_boards(
        self,
        uid: str,
        md5: str,
        *,
        include_hidden: bool = False,
    ) -> list[SubstatPriorityBoard] | int:
        """请求并计算 ``% gain over base`` / 名次变化。

        公式：``pct = 100 * result / Base.result - 100``。
        与角色卡 ``Show substat priority`` 表同一套数；跟玩家当前配装有关。
        走 ``get_substat_priority`` 的一小时缓存。
        """
        items = await self.get_substat_priority(uid, md5)
        if isinstance(items, int):
            return items
        return compute_substat_priority_boards(items, include_hidden=include_hidden)

    async def get_build_leaderboards(self, uid: str, md5: str) -> list[BuildLeaderboardRow] | int:
        """请求某套配装在各队伍榜上的名次 / 伤害分。

        对应 ``GET /api/leaderboards/{uid}/{md5}?variant=profilePage``。
        即角色卡 ``Show leaderboards`` 表；跟当前配装有关，不是全服固定值。
        含 ``hidden`` 的榜，未按名次排序。
        相同 ``uid`` + ``md5`` 缓存一小时，并发相同请求合并为一次 HTTP。
        """

        async def fetch() -> list[BuildLeaderboardRow] | int:
            url = BUILD_LB_API.format(quote(uid, safe=""), quote(md5, safe=""))
            raw = await self._cv_request(
                url,
                "GET",
                self._HEADER,
                {"variant": "profilePage"},
            )
            if isinstance(raw, int):
                return raw
            parsed = parse_build_leaderboards_payload(raw)
            if parsed is None:
                return -1
            return parsed

        return await _LEADERBOARD_CACHE.get(f"{uid}:{md5}", fetch)

    async def get_visible_leaderboards(
        self,
        uid: str,
        md5: str,
        *,
        include_hidden: bool = False,
    ) -> list[BuildLeaderboardRow] | int:
        """请求并排成角色卡 ``calculation-list`` 同款表。

        丢掉 ``hidden``（除非 ``include_hidden``），再按 ``ranking`` 升序。
        ``top_pct`` 对应页面 ``top N%``。走 ``get_build_leaderboards`` 的一小时缓存。
        """
        rows = await self.get_build_leaderboards(uid, md5)
        if isinstance(rows, int):
            return rows
        return list_visible_leaderboards(rows, include_hidden=include_hidden)

    async def get_build_md5(self, uid: str, character_id: str) -> str | int:
        """从 ``/api/builds?uid=`` 取某角色当前配装 md5。

        优先 ``type == current``。相同 ``uid`` + ``characterId`` 缓存一小时。
        """

        async def fetch() -> str | int:
            raw = await self._cv_request(BUILDS_API.format(uid), "GET", self._HEADER)
            if isinstance(raw, int):
                return raw
            md5 = extract_build_md5(raw, character_id)
            if md5 is None:
                return -1
            return md5

        return await _MD5_CACHE.get(f"{uid}:{character_id}", fetch)

    async def get_damage_distribution(
        self,
        uid: str,
        md5: str,
        calculation_id: str,
    ) -> list[DamageDistributionBoard] | int:
        """请求某套配装在各队伍榜上的伤害拆分。

        对应 ``GET /api/damageDistribution/{calculationId}/{uid}/{md5}``。
        ``calculationId`` 会截到前 10 位。一次返回该角色全部榜。
        缓存键是 ``uid`` + ``md5``（换榜不重复打），并发相同请求合并。
        失败返回 errno，失败不进缓存。
        """
        calc_id = board_calculation_id(calculation_id)
        if not calc_id:
            return -1

        async def fetch() -> list[DamageDistributionBoard] | int:
            url = DAMAGE_DIST_API.format(
                quote(calc_id, safe=""),
                quote(uid, safe=""),
                quote(md5, safe=""),
            )
            raw = await self._cv_request(url, "GET", self._HEADER)
            if isinstance(raw, int):
                return raw
            parsed = parse_damage_distribution_payload(raw)
            if parsed is None:
                return -1
            return parsed

        return await _DMG_CACHE.get(f"{uid}:{md5}", fetch)

    async def get_global_ranks(
        self,
        calculation_id: str,
        out_of: int,
        *,
        size: int = 20,
    ) -> list[GlobalRankRow] | int:
        """请求某队伍榜的全服名次表，与 ``gs角色排名`` 同一接口。

        ``GET /api/leaderboards?sort=calculation.result&calculationId=``。
        ``calculationId`` 截到前 10 位。失败返回 errno，失败不进缓存。
        """
        calc_id = board_calculation_id(calculation_id)
        if not calc_id or out_of <= 0 or size <= 0:
            return -1

        async def fetch() -> list[GlobalRankRow] | int:
            url = GLOBAL_LB_API.format(quote(calc_id, safe=""), size)
            raw = await self._cv_request(url, "GET", self._HEADER)
            if isinstance(raw, int):
                return raw
            parsed = parse_global_ranks_payload(raw, out_of)
            if parsed is None:
                return -1
            return parsed

        return await _GLOBAL_CACHE.get(f"{calc_id}:{out_of}:{size}", fetch)

    async def get_damage_distribution_board(
        self,
        uid: str,
        md5: str,
        calculation_id: str,
        *,
        include_hidden: bool = False,
    ) -> DamageDistributionBoard | int:
        """请求并取出当前高亮榜那一条拆分（含 ``% of Result``）。

        走 ``get_damage_distribution`` 的一小时缓存。找不到对应榜返回 -1。
        """
        boards = await self.get_damage_distribution(uid, md5, calculation_id)
        if isinstance(boards, int):
            return boards
        visible = list_visible_distributions(boards, include_hidden=include_hidden)
        found = find_damage_distribution(visible, calculation_id)
        if found is None:
            return -1
        return found

    async def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict, int]:
        """GET 一个 Akasha JSON。给刷新落盘用，不走解析缓存。"""
        return await self._cv_request(url, "GET", self._HEADER, params)

    async def close(self):
        # 调用session对象的close方法关闭会话
        await self.session.close()

    async def _cv_request(
        self,
        url: str,
        method: Literal["GET", "POST"] = "GET",
        header: Dict[str, Any] = _HEADER,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict, int]:
        logger.debug(t("log.genshinuid.akasha_url_url_9d8655_1", url=url))
        logger.debug(t("log.genshinuid.akasha_header_header_7422a5", header=header))

        async with self.session.request(
            method,
            url=url,
            headers=header,
            params=params,
            json=data,
            timeout=300,  # type: ignore
        ) as resp:
            try:
                raw_data = await resp.json()
            except ContentTypeError:
                _raw_data = await resp.text()
                raw_data = {"retcode": -999, "data": _raw_data}
            logger.debug(raw_data)
            return raw_data

from __future__ import annotations

import sys
import asyncio
import importlib.util
from types import ModuleType
from typing import Dict, List, Tuple, Literal, Optional
from pathlib import Path

import pytest

from gsuid_core.utils.database.models import GsUser

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_BBS_DIR = _PLUGIN_ROOT / "GenshinUID" / "genshinuid_mysbbscoin"
_BBS_FILE = _BBS_DIR / "get_mihoyo_bbs_coin.py"


def _load_bbs_module() -> ModuleType:
    pkg_name = "GenshinUID.genshinuid_mysbbscoin"
    mod_name = f"{pkg_name}.get_mihoyo_bbs_coin"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    injected_pkg = False
    if pkg_name not in sys.modules:
        pkg = ModuleType(pkg_name)
        pkg.__path__ = [str(_BBS_DIR)]
        pkg.__package__ = pkg_name
        sys.modules[pkg_name] = pkg
        injected_pkg = True
    try:
        spec = importlib.util.spec_from_file_location(mod_name, _BBS_FILE)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = pkg_name
        spec.loader.exec_module(mod)
        return mod
    finally:
        if injected_pkg:
            sys.modules.pop(pkg_name, None)


_bbs_mod = _load_bbs_module()
MihoyoBBSCoin = _bbs_mod.MihoyoBBSCoin
mihoyobbs_List = _bbs_mod.mihoyobbs_List


def test_get_tasks_list_auto_upgrades_hyp_stoken_and_persists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_stoken = "stuid=10000001;stoken=v2_fake_hyp_token;mid=fake_mid_0001"
    new_stoken = "stuid=10000001;stoken=v2_fake_bbs_token;mid=fake_mid_0001"
    coin = MihoyoBBSCoin(
        stoken=old_stoken,
        device_id="a" * 32,
        device_fp="0123456789abc",
        device_info="OnePlus/IN2020/14/5",
        uid="100000001",
        mys_id="10000001",
    )

    assert coin.headers["x-rpc-device_name"] == "OnePlus IN2020"
    assert coin.headers["x-rpc-device_model"] == "IN2020"
    assert coin.headers["x-rpc-sys_version"] == "14"
    assert coin.headers["x-rpc-verify_key"] == "bll8iq97cem8"
    assert coin.headers["Host"] == "bbs-api.miyoushe.com"
    assert coin.headers["x-rpc-device_fp"] == "0123456789abc"

    seen_cookies: List[str] = []
    upgrade_calls: List[Tuple[str, str, Optional[str], Optional[str], Optional[str]]] = []
    db_updates: List[Tuple[Dict[str, str], Dict[str, str]]] = []

    async def fake_request(
        method: Literal["GET", "POST"],
        url: str,
        header: Dict[str, str],
        data: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        cookie = header["Cookie"]
        seen_cookies.append(cookie)
        if cookie == old_stoken:
            return {"retcode": -100, "message": "登录失效，请重新登录", "data": None}
        return {
            "retcode": 0,
            "message": "OK",
            "data": {
                "can_get_points": 30,
                "already_received_points": 20,
                "total_points": 1234,
                "states": [
                    {"mission_id": 58, "is_get_award": False, "happened_times": 0},
                    {"mission_id": 59, "is_get_award": False, "happened_times": 2},
                    {"mission_id": 60, "is_get_award": True, "happened_times": 5},
                    {"mission_id": 61, "is_get_award": False, "happened_times": 0},
                ],
            },
        }

    async def fake_exchange(
        stoken: str,
        mys_id: str,
        full_sk: str = "",
        device_id: Optional[str] = None,
        device_fp: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> Dict[str, str]:
        upgrade_calls.append((mys_id, full_sk, device_id, device_fp, device_info))
        return {
            "stoken": "v2_fake_bbs_token",
            "uid": "10000001",
            "mid": "fake_mid_0001",
            "app_cookie": new_stoken,
        }

    async def fake_update_by_xx(by: Dict[str, str], **kwargs: str) -> int:
        db_updates.append((by, kwargs))
        return 0

    monkeypatch.setattr(coin, "_request", fake_request)
    monkeypatch.setattr(
        _bbs_mod.mys_api,
        "exchange_hyp_stoken_to_bbs_stoken",
        fake_exchange,
        raising=False,
    )
    monkeypatch.setattr(GsUser, "update_data_by_xx", fake_update_by_xx)

    res = asyncio.run(coin.get_tasks_list())

    assert res == "今日完成情况!"
    assert coin._abort_msg is None
    assert seen_cookies == [old_stoken, new_stoken]
    assert upgrade_calls == [
        ("10000001", old_stoken, "a" * 32, "0123456789abc", "OnePlus/IN2020/14/5"),
    ]
    assert coin.stoken == new_stoken
    assert coin.headers["Cookie"] == new_stoken
    assert db_updates == [({"mys_id": "10000001"}, {"stoken": new_stoken})]
    assert coin.Today_getcoins == 30
    assert coin.Today_have_getcoins == 20
    assert coin.Have_coins == 1234
    assert coin.Task_do["bbs_Sign"] is False
    assert coin.Task_do["bbs_Read_posts"] is False
    assert coin.Task_do["bbs_Read_posts_num"] == 5
    assert coin.Task_do["bbs_Like_posts"] is True
    assert coin.Task_do["bbs_Share"] is False


def test_task_run_aborts_cleanly_when_stoken_upgrade_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coin = MihoyoBBSCoin(
        stoken="stuid=10000001;stoken=v2_expired;mid=fake_mid_0001",
        device_id="b" * 32,
        uid="100000001",
        mys_id="10000001",
    )

    upgrade_attempts = 0
    list_called = False

    async def fake_request(
        method: Literal["GET", "POST"],
        url: str,
        header: Dict[str, str],
        data: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        return {"retcode": -100, "message": "登录失效，请重新登录", "data": None}

    async def fake_exchange(
        stoken: str,
        mys_id: str,
        full_sk: str = "",
        device_id: Optional[str] = None,
        device_fp: Optional[str] = None,
        device_info: Optional[str] = None,
    ) -> int:
        nonlocal upgrade_attempts
        upgrade_attempts += 1
        return -100

    async def fake_get_list() -> List[List[str]]:
        nonlocal list_called
        list_called = True
        return []

    monkeypatch.setattr(coin, "_request", fake_request)
    monkeypatch.setattr(coin, "get_list", fake_get_list)
    monkeypatch.setattr(
        _bbs_mod.mys_api,
        "exchange_hyp_stoken_to_bbs_stoken",
        fake_exchange,
        raising=False,
    )

    result = asyncio.run(coin.task_run())

    assert "失效" in result
    assert coin._abort_msg == result
    assert upgrade_attempts == 1
    assert list_called is False


def test_load_mihoyo_bbs_list_includes_all_forums() -> None:
    coin = MihoyoBBSCoin(
        stoken="stuid=10000001;stoken=v2_fake_bbs_token;mid=fake_mid_0001",
        device_id="c" * 32,
    )
    asyncio.run(coin.load_mihoyo_bbs_list_use())

    ids = [item["id"] for item in coin.mihoyobbs_List_Use]
    assert ids == [item["id"] for item in mihoyobbs_List]
    assert "10" in ids

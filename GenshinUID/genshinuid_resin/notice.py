import datetime
from typing import Dict, List, Tuple, Union, Sequence

from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.segment import MessageSegment
from gsuid_core.subscribe import gs_subscribe
from gsuid_core.utils.api.mys.models import WidgetResin, DailyNoteData
from gsuid_core.utils.database.models import Subscribe

from ..utils.message import PREFIX
from ..utils.mys_api import mys_api
from ..genshinuid_config.gs_config import gsconfig

MR_NOTICE = f"\n✅可发送[{PREFIX}mr]或者[{PREFIX}每日]来查看更多信息！\n"

NOTICE = {
    "coin": "💰 你的洞天宝钱快满啦！",
    "resin": "🌜 你的树脂/体力快满啦！",
    "go": "👨‍🏭 你有派遣奖励即将可领取！",
    "transform": "⌛ 你的质变仪即将可使用！",
    "daily": "🚑️ 你的日常任务还没有完成！",
}

NOTICE_MAP = {
    "coin": "洞天宝钱",
    "resin": "树脂/体力",
    "go": "派遣",
    "transform": "质变仪",
    "daily": "日常任务",
}


async def _to_dict(data: Sequence[Subscribe]) -> Dict[str, List[Subscribe]]:
    result: Dict[str, List[Subscribe]] = {}
    for item in data:
        if str(item.uid) not in result:
            result[str(item.uid)] = []
        result[str(item.uid)].append(item)
    return result


async def send_notice_list():
    datas = await gs_subscribe.get_subscribe("[原神] 推送")
    coin_datas = await gs_subscribe.get_subscribe("[原神] 宝钱")
    resin_datas = await gs_subscribe.get_subscribe("[原神] 体力")
    go_datas = await gs_subscribe.get_subscribe("[原神] 派遣")
    transform_datas = await gs_subscribe.get_subscribe("[原神] 质变仪")
    daily_datas = await gs_subscribe.get_subscribe("[原神] 日常检查")

    datas = await _to_dict(datas)
    coin_datas = await _to_dict(coin_datas)
    resin_datas = await _to_dict(resin_datas)
    go_datas = await _to_dict(go_datas)
    transform_datas = await _to_dict(transform_datas)
    daily_datas = await _to_dict(daily_datas)

    for uid in datas:
        # data = datas[uid]
        if uid:
            # 请求小组件源 或是战绩源
            use_widget = gsconfig.get_config("WidgetResin").data
            if use_widget:
                raw_data = await mys_api.get_widget_resin_data(uid)
            else:
                raw_data = await mys_api.get_daily_data(uid)

            if isinstance(raw_data, int):
                logger.error(t("log.genshinuid.uid_raw_data_aee7d6", uid=uid, raw_data=raw_data))
                continue

            for mode in NOTICE:
                if datetime.datetime.now().hour > 2 and mode == "daily":
                    logger.info(t("log.genshinuid.uid_392e14", uid=uid))
                    continue

                _datas: Dict[str, List[Subscribe]] = locals()[f"{mode}_datas"]
                logger.debug(t("log.genshinuid.datas_4b0d0f", _datas=_datas))

                if uid in _datas:
                    _data_list = _datas[uid]
                    for _data in _data_list:
                        mg = _data.extra_message or "0"
                        res = await check(
                            mode,
                            raw_data,
                            int(mg),
                        )
                        if res[0]:
                            if mode == "daily":
                                mlist = [
                                    f"🚨 原神推送提醒 - UID{uid}",
                                    NOTICE[mode],
                                    MR_NOTICE,
                                ]
                            else:
                                mlist = [
                                    f"🚨 原神推送提醒 - UID{uid}",
                                    NOTICE[mode],
                                    f"当前{NOTICE_MAP[mode]}值为: {res[1]}",
                                    f"你设置的阈值为: {_data.extra_message}",
                                    MR_NOTICE,
                                ]
                            user_id = _data.user_id
                            msg = [MessageSegment.at(user_id), "\n", "\n".join(mlist)]
                            await _data.send(msg)


async def check(
    mode: str,
    data: Union[DailyNoteData, WidgetResin],
    limit: int,
) -> Tuple[bool, int]:
    if mode == "coin":
        if data["current_home_coin"] >= limit:
            return True, data["current_home_coin"]
        elif data["current_home_coin"] >= data["max_home_coin"]:
            return True, data["current_home_coin"]
        else:
            return False, data["current_home_coin"]
    if mode == "resin":
        if data["current_resin"] >= limit:
            return True, data["current_resin"]
        elif data["current_resin"] >= data["max_resin"]:
            return True, data["current_resin"]
        else:
            return False, data["current_resin"]
    if mode == "go":
        for i in data["expeditions"]:
            if i["status"] == "Ongoing":
                if "remained_time" in i and int(i["remained_time"]) <= limit * 60:
                    return True, int(i["remained_time"])
            else:
                return True, 0
        return False, 0
    if mode == "transform":
        if "transformer" in data:
            if data["transformer"]["obtained"]:
                time = data["transformer"]["recovery_time"]
                time_min = (time["Day"] * 24 + time["Hour"]) * 60 + time["Minute"]
                if time_min <= limit:
                    return True, time_min
            return False, 0
        else:
            logger.warning(t("log.genshinuid.msg_d30a1a"))
            return False, 0
    if mode == "daily":
        if not data["is_extra_task_reward_received"]:
            return True, 0
    return False, 0

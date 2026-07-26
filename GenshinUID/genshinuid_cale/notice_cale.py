from typing import List

from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.segment import MessageSegment
from gsuid_core.subscribe import gs_subscribe
from gsuid_core.utils.api.mys.models import Act

from ..utils.message import PREFIX
from ..utils.mys_api import mys_api


async def notice_cale():
    datas = await gs_subscribe.get_subscribe("[原神] 推送")
    active_datas = await gs_subscribe.get_subscribe("[原神] 活动提醒")

    datas = await gs_subscribe._to_dict(datas)
    active_datas = await gs_subscribe._to_dict(active_datas)

    for uid in datas:
        if uid and uid in active_datas:
            data = await mys_api.get_calendar_data(uid)
            if isinstance(data, int):
                logger.error(t("log.genshinuid.uid_data_d7c9c9", uid=uid, data=data))
                continue

            act_list: List[Act] = []
            if "selected_act_list" in data:
                act_list += data["selected_act_list"]

            if "act_list" in data:
                act_list += data["act_list"]

            if "fixed_act_list" in data:
                act_list += data["fixed_act_list"]

            for act in act_list:
                if act["status"] == 2 and act["countdown_seconds"] <= 172810 and not act["is_finished"]:
                    for _sub in active_datas[uid]:
                        t = ""
                        if act["type"] == "ActTypeHardChallengeSub":
                            t = f"差{act['y'] - act['x']}"

                        if act["type"] == "ActTypeExplore" and "explore_detail" in act and act["explore_detail"]:
                            ed = act["explore_detail"]
                            t = f"{ed['explore_percent']}%"

                        mlist = [
                            f"🚨 活动推送提醒 - UID{uid}",
                            f"当前{act['name']}活动快要结束了!",
                            f"你当前进度：未完成！{t}",
                            f"还剩下{act['countdown_seconds'] // 60}分钟, 活动即将结束！",
                            f"你可以发送 {PREFIX}日历 查看活动详情！",
                        ]
                        user_id = _sub.user_id
                        msg = [MessageSegment.at(user_id), "\n", "\n".join(mlist)]
                        await _sub.send(msg)

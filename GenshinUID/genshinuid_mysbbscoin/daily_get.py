from gsuid_core.subscribe import gs_subscribe
from gsuid_core.utils.database.models import GsUser

from .get_mihoyo_bbs_coin import MihoyoBBSCoin
from ..genshinuid_config.gs_config import gsconfig


async def coin_task(uid: str):
    stoken = await GsUser.get_user_attr_by_uid(uid, "stoken")
    if stoken:
        im = await mihoyo_coin(stoken)
    else:
        im = "失败, 未绑定stoken，无法获取米游币!"
    return im


async def all_daily_mihoyo_bbs_coin():
    datas = await gs_subscribe.get_subscribe("[原神] 自动米游币")
    priv_result, group_result = await gs_subscribe.muti_task(datas, coin_task, "uid")

    if gsconfig.get_config("MhyBBSCoinReport").data:
        for _, data in priv_result.items():
            im = "\n".join(data["im"])
            event = data["event"]
            await event.send(im)

    if gsconfig.get_config("MhyBBSCoinReportGroup").data:
        for _, data in group_result.items():
            im = "✅ 今日自动获取米游币已完成！\n"
            im += f"📝 本群共获取成功{data['success']}人，共获取失败{data['fail']}人。"
            event = data["event"]
            await event.send(im)


async def mihoyo_coin(stoken: str):
    get_coin = MihoyoBBSCoin(stoken)
    im = await get_coin.task_run()
    return im

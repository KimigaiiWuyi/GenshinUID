import random
import asyncio
from copy import deepcopy

from gsuid_core.gss import gss
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.database.models import GsUser
from gsuid_core.utils.plugins_config.gs_config import core_plugins_config

from ..utils.mys_api import mys_api

private_msg_list = {}
group_msg_list = {}
already = 0


# 签到函数
async def sign_in(uid: str) -> str:
    logger.info(t("log.genshinuid.uid_ee7732", uid=uid))
    # 获得签到信息
    sign_info = await mys_api.get_sign_info(uid)
    # 初步校验数据
    if isinstance(sign_info, int):
        return await sign_error(uid, sign_info)
    # 检测是否已签到
    if sign_info["is_sign"]:
        logger.info(t("log.genshinuid.uid_52af1e", uid=uid))
        global already
        already += 1
        day_of_month = int(sign_info["today"].split("-")[-1])
        signed_count = int(sign_info["total_sign_day"])
        sign_missed = day_of_month - signed_count
        return f"今日已签到！本月漏签次数：{sign_missed}"

    # 实际进行签到
    Header = {}
    for index in range(4):
        # 进行一次签到
        sign_data = await mys_api.mys_sign(uid=uid, header=Header)
        # 检测数据
        if isinstance(sign_data, int):
            return await sign_error(uid, sign_data)
        if "risk_code" in sign_data:
            # 出现校验码
            if sign_data["risk_code"] == 375:
                if core_plugins_config.get_config("CaptchaPass").data:
                    gt = sign_data["gt"]
                    ch = sign_data["challenge"]
                    vl, ch = await mys_api._pass(gt, ch, Header)
                    if vl:
                        delay = 1
                        Header["x-rpc-challenge"] = ch
                        Header["x-rpc-validate"] = vl
                        Header["x-rpc-seccode"] = f"{vl}|jordan"
                        logger.info(t("log.genshinuid.uid_delay_047f39", uid=uid, delay=delay))
                        await asyncio.sleep(delay)
                    else:
                        delay = 605 + random.randint(1, 120)
                        logger.info(t("log.genshinuid.uid_delay_bb3983", uid=uid, delay=delay))
                        await asyncio.sleep(delay)
                    continue
                else:
                    logger.info(t("log.genshinuid.msg_185139"))
                return "签到失败...出现验证码!"
            # 成功签到!
            else:
                if index == 0:
                    logger.info(t("log.genshinuid.uid_0e4f10", uid=uid))
                else:
                    logger.info(t("log.genshinuid.uid_index_07cd35", uid=uid, index=index))
                break
        elif (int(str(uid)[0]) > 5) and (sign_data["code"] == "ok"):
            # 国际服签到无risk_code字段
            logger.info(t("log.genshinuid.uid_6944d8", uid=uid))
            break
        else:
            # 重试超过阈值
            logger.warning(t("log.genshinuid.msg_dac6af"))
            return "签到失败...出现验证码!\n请过段时间使用[签到]或由管理员[全部重签]或手动至米游社进行签到！"
    # 签到失败
    else:
        im = "签到失败!"
        logger.warning(t("log.genshinuid.uid_im_270690", uid=uid, im=im))
        return im
    # 获取签到列表
    sign_list = await mys_api.get_sign_list(uid)
    new_sign_info = await mys_api.get_sign_info(uid)

    if isinstance(sign_list, int):
        return await sign_error(uid, sign_list)
    elif isinstance(new_sign_info, int):
        return await sign_error(uid, new_sign_info)

    # 获取签到奖励物品，拿旧的总签到天数 + 1 为新的签到天数，再 -1 即为今日奖励物品的下标
    getitem = sign_list["awards"][int(sign_info["total_sign_day"]) + 1 - 1]
    get_im = f"本次签到获得{getitem['name']}x{getitem['cnt']}"
    day_of_month = int(new_sign_info["today"].split("-")[-1])
    signed_count = int(new_sign_info["total_sign_day"])
    sign_missed = day_of_month - signed_count
    if new_sign_info["is_sign"]:
        mes_im = "签到成功"
    else:
        mes_im = "签到失败..."
        sign_missed -= 1
    sign_missed = sign_info.get("sign_cnt_missed") or sign_missed
    im = f"{mes_im}!\n{get_im}\n本月漏签次数：{sign_missed}"
    logger.info(t("log.genshinuid.uid_mes_im_sign_missed_595ec2", uid=uid, mes_im=mes_im, sign_missed=sign_missed))
    return im


async def sign_error(uid: str, retcode: int) -> str:
    error_msg = get_error(retcode)
    logger.warning(t("log.genshinuid.uid_retcode_error_msg_002bbc", uid=uid, retcode=retcode, error_msg=error_msg))
    if retcode == 10001 or retcode == -100:
        ck = await GsUser.get_user_cookie_by_uid(uid)
        if ck:
            await GsUser.update_data_by_uid_without_bot_id(uid, status="error")
    return f"签到失败!{error_msg}"


async def single_daily_sign(bot_id: str, uid: str, gid: str, qid: str):
    im = await sign_in(uid)
    if gid == "on":
        if qid not in private_msg_list:
            private_msg_list[qid] = []
        private_msg_list[qid].append({"bot_id": bot_id, "uid": uid, "msg": im})
    else:
        # 向群消息推送列表添加这个群
        if gid not in group_msg_list:
            group_msg_list[gid] = {
                "bot_id": bot_id,
                "success": 0,
                "failed": 0,
                "push_message": "",
            }
        if im.startswith(("签到失败", "网络有点忙", "OK", "ok")):
            message = f"[CQ:at,qq={qid}] {im}"
            group_msg_list[gid]["failed"] += 1
            group_msg_list[gid]["push_message"] += "\n" + message
        else:
            group_msg_list[gid]["success"] += 1


async def daily_sign():
    global already
    tasks = []
    for BOT_ID in gss.active_bot:
        user_list = await GsUser.get_all_user()
        uid_list = [user.uid for user in user_list if user.sign_switch != "off" and not user.status and user.uid]
        logger.info(t("log.genshinuid.uid_uid_list_ae3264", uid_list=uid_list))
        for user in user_list:
            if user.sign_switch != "off" and not user.status and user.uid:
                tasks.append(single_daily_sign(user.bot_id, user.uid, user.sign_switch, user.user_id))
            if len(tasks) >= 1:
                await asyncio.gather(*tasks)
                if already >= 1:
                    delay = 1
                else:
                    delay = 50 + random.randint(3, 45)
                logger.info(t("log.genshinuid.p0_delay_fba95c", p0=len(tasks), delay=delay))
                tasks.clear()
                already = 0
                await asyncio.sleep(delay)
    await asyncio.gather(*tasks)
    tasks.clear()
    result = {
        "private_msg_list": deepcopy(private_msg_list),
        "group_msg_list": deepcopy(group_msg_list),
    }
    private_msg_list.clear()
    group_msg_list.clear()
    logger.info(result)
    return result

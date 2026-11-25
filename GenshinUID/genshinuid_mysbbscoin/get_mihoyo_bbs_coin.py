import json
import random
import asyncio
from copy import deepcopy
from typing import Dict, Literal, Optional

import httpx
from httpx import AsyncClient

from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.utils.api.mys.api import (
    BBS_LIKE,
    BBS_LIST,
    BBS_SIGN,
    BBS_SHARE,
    BBS_TASKS,
    BBS_DETAIL,
)
from gsuid_core.utils.api.mys.tools import (
    random_hex,
    mys_version,
    random_text,
    get_ds_token,
    get_web_ds_token,
)

from ..utils.mys_api import mys_api

mihoyobbs_List = [
    {
        "id": "1",
        "forumId": "1",
        "name": "崩坏3",
        "url": "https://bbs.mihoyo.com/bh3/",
    },
    {
        "id": "2",
        "forumId": "26",
        "name": "原神",
        "url": "https://bbs.mihoyo.com/ys/",
    },
    {
        "id": "3",
        "forumId": "30",
        "name": "崩坏2",
        "url": "https://bbs.mihoyo.com/bh2/",
    },
    {
        "id": "4",
        "forumId": "37",
        "name": "未定事件簿",
        "url": "https://bbs.mihoyo.com/wd/",
    },
    {
        "id": "5",
        "forumId": "34",
        "name": "大别野",
        "url": "https://bbs.mihoyo.com/dby/",
    },
    {
        "id": "6",
        "forumId": "52",
        "name": "崩坏：星穹铁道",
        "url": "https://bbs.mihoyo.com/sr/",
    },
    {
        "id": "8",
        "forumId": "57",
        "name": "绝区零",
        "url": "https://bbs.mihoyo.com/zzz/",
    },
    {
        "id": "9",
        "forumId": "948",
        "name": "崩坏：因缘精灵",
        "url": "https://bbs.mihoyo.com/hna/",
    },
    {
        "id": "10",
        "forumId": "950",
        "name": "星布谷地",
        "url": "https://bbs.mihoyo.com/planet/",
    },
]


class MihoyoBBSCoin:
    def __init__(
        self,
        stoken: str,
        device_id: Optional[str] = None,
        device_fp: Optional[str] = None,
    ):
        self.postsList = []
        self.headers: Dict[str, str] = {
            "DS": get_web_ds_token(),
            "Cookie": stoken,
            "x-rpc-client_type": "2",
            "x-rpc-app_version": mys_version,
            "x-rpc-sys_version": "14",
            "x-rpc-channel": "miyousheluodi",
            "x-rpc-device_id": device_id or random_hex(32),
            "x-rpc-device_name": random_text(random.randint(1, 10)),
            "x-rpc-device_model": "Mi 10",
            "x-rpc-verify_key": "bll8iq97cem8",
            "x-rpc-csm_source": "myself",
            "Referer": "https://app.mihoyo.com",
            "User-Agent": "okhttp/4.9.3",
        }
        if device_fp:
            self.headers["x-rpc-device_fp"] = device_fp
        self.Task_do = {
            "bbs_Sign": False,
            "bbs_Read_posts": False,
            "bbs_Read_posts_num": 7,
            "bbs_Like_posts": False,
            "bbs_Like_posts_num": 10,
            "bbs_Share": False,
        }
        self.mihoyobbs_List_Use = []
        self.Today_getcoins = 0
        self.Today_have_getcoins = 0  # 这个变量以后可能会用上, 先留着了
        self.Have_coins = 0
        self._abort_msg: Optional[str] = None

    async def task_run(self):
        self._abort_msg = None
        await self.load_mihoyo_bbs_list_use()
        start = await self.get_tasks_list()
        if self._abort_msg:
            return self._abort_msg
        if (
            self.Task_do["bbs_Sign"]
            and self.Task_do["bbs_Read_posts"]
            and self.Task_do["bbs_Like_posts"]
            and self.Task_do["bbs_Share"]
        ):
            return "\n".join(
                [
                    start,
                    "SignM已经完成过了~",
                    "ReadM已经完成过了~",
                    "LikeM任务已经完成过了~",
                    "ShareM已经完成过了~",
                ]
            )
        self.postsList = await self.get_list()
        read = await self.read_posts()
        share = await self.share_post()
        like = await self.like_posts()
        sign = await self.signing()
        if start and sign and read and like and share:
            return "\n".join([start, sign, read, like, share])
        return "失败, 米游社币任务执行出错了~"

    async def load_mihoyo_bbs_list_use(self):
        self.mihoyobbs_List_Use = []
        for i in range(1, 10):
            for k in mihoyobbs_List:
                if i == int(k["id"]):
                    self.mihoyobbs_List_Use.append(k)

    # 获取任务列表, 用来判断做了哪些任务
    async def get_tasks_list(self):
        logger.info(t("log.genshinuid.msg_8a612f"))
        data = await self._request(
            "GET",
            BBS_TASKS.get(),
            self.headers,
        )
        retcode = data.get("retcode")
        msg = str(data.get("message", ""))
        if retcode == -100 or "err" in msg.lower():
            logger.error(t("log.genshinuid.cookie_cookie_f6e063"))
            self._abort_msg = "失败, 你的Cookies/Stoken已失效，请重新扫码登录。"
            return self._abort_msg
        task_data = data.get("data")
        if retcode != 0 or not isinstance(task_data, dict):
            self._abort_msg = f"失败, 获取米游币任务列表出错(retcode={retcode}): {msg}"
            return self._abort_msg

        self.Today_getcoins = int(task_data.get("can_get_points", 0))
        self.Today_have_getcoins = int(task_data.get("already_received_points", 0))
        self.Have_coins = int(task_data.get("total_points", 0))
        # 如果当日可获取米游币数量为0直接判断全部任务都完成了
        if self.Today_getcoins == 0:
            self.Task_do["bbs_Sign"] = True
            self.Task_do["bbs_Read_posts"] = True
            self.Task_do["bbs_Like_posts"] = True
            self.Task_do["bbs_Share"] = True
        else:
            states = task_data.get("states") or []
            # 如果第0个大于或等于62则直接判定任务没做
            if states and states[0]["mission_id"] >= 62:
                logger.info(t("log.genshinuid.p0_04807b", p0=self.Today_getcoins))
            else:
                logger.info(t("log.genshinuid.p0_e523b0", p0=self.Today_getcoins))
                for i in states:
                    # 58是讨论区签到
                    if i["mission_id"] == 58:
                        if i["is_get_award"]:
                            self.Task_do["bbs_Sign"] = True
                    # 59是看帖子
                    elif i["mission_id"] == 59:
                        if i["is_get_award"]:
                            self.Task_do["bbs_Read_posts"] = True
                        else:
                            self.Task_do["bbs_Read_posts_num"] = max(
                                0,
                                self.Task_do["bbs_Read_posts_num"] - i["happened_times"],
                            )
                    # 60是给帖子点赞
                    elif i["mission_id"] == 60:
                        if i["is_get_award"]:
                            self.Task_do["bbs_Like_posts"] = True
                        else:
                            self.Task_do["bbs_Like_posts_num"] = max(
                                0,
                                self.Task_do["bbs_Like_posts_num"] - i["happened_times"],
                            )
                    # 61是分享帖子
                    elif i["mission_id"] == 61:
                        if i["is_get_award"]:
                            self.Task_do["bbs_Share"] = True
                            # 分享帖子是最后一个日常任务，后面均为一次性任务
                            break
        return "今日完成情况!"

    # 获取要帖子列表
    async def get_list(self) -> list:
        temp_list = []
        logger.info(t("log.genshinuid.msg_603dcf"))
        data = await self._request(
            "GET",
            BBS_LIST.format(self.mihoyobbs_List_Use[0]["forumId"]),
            self.headers,
        )
        list_data = data.get("data")
        if data.get("retcode") != 0 or not isinstance(list_data, dict):
            return temp_list
        posts = list_data.get("list") or []
        limit = min(10, len(posts))

        for n in range(limit):
            temp_list.append(
                [
                    posts[n]["post"]["post_id"],
                    posts[n]["post"]["subject"],
                ]
            )

        logger.info(t("log.genshinuid.bbs_posts_got", count=len(temp_list)))
        return temp_list

    # 进行签到操作
    async def signing(self):
        if self.Task_do["bbs_Sign"]:
            return "SignM已经完成过了~"
        logger.info(t("log.genshinuid.msg_0005c2"))
        header = deepcopy(self.headers)
        ok_count = 0
        for i in self.mihoyobbs_List_Use:
            data = await self._request(
                "POST",
                BBS_SIGN.get(),
                header,
                {"gids": int(i["id"])},
            )
            retcode = data.get("retcode", -1)
            msg = str(data.get("message", ""))
            if retcode == -100:
                logger.error(t("log.genshinuid.cookie_cookie_f6e063"))
                return "SignM:失败(登录失效)"
            if retcode in (0, 1008) and "err" not in msg.lower():
                ok_count += 1
                await asyncio.sleep(random.randint(2, 8))
            else:
                logger.warning(t("log.genshinuid.game_id_p0_d62c87", p0=i["id"]))
                await asyncio.sleep(random.randint(9, 30))
        return "SignM:完成!" if ok_count > 0 else "SignM:失败!"

    # 看帖子
    async def read_posts(self):
        if self.Task_do["bbs_Read_posts"]:
            return "ReadM已经完成过了~"
        if not self.postsList:
            return "ReadM:失败(未获取到帖子列表)"
        logger.info(t("log.genshinuid.msg_cc41b8"))
        num_ok = 0
        count = min(self.Task_do["bbs_Read_posts_num"], len(self.postsList))
        for i in range(count):
            data = await self._request(
                "GET",
                BBS_DETAIL.format(self.postsList[i][0]),
                self.headers,
            )
            if data.get("retcode") == -100:
                return "ReadM:失败(登录失效)"
            if data.get("retcode") == 0 or data.get("message") == "OK":
                num_ok += 1
            await asyncio.sleep(random.randint(4, 13))
        return "ReadM:成功!Read:{}!".format(str(num_ok))

    # 点赞
    async def like_posts(self):
        if self.Task_do["bbs_Like_posts"]:
            return "LikeM任务已经完成过了~"
        if not self.postsList:
            return "LikeM:失败(未获取到帖子列表)"
        logger.info(t("log.genshinuid.msg_bec7e3"))
        num_ok = 0
        num_cancel = 0
        count = min(self.Task_do["bbs_Like_posts_num"], len(self.postsList))
        for i in range(count):
            data = await self._request(
                "POST",
                BBS_LIKE.get(),
                self.headers,
                {
                    "post_id": self.postsList[i][0],
                    "is_cancel": False,
                },
            )
            if data.get("retcode") == -100:
                return "LikeM:失败(登录失效)"
            if data.get("retcode") == 0 or data.get("message") == "OK":
                num_ok += 1
            await asyncio.sleep(random.randint(4, 13))
            data = await self._request(
                "POST",
                BBS_LIKE.get(),
                self.headers,
                {
                    "post_id": self.postsList[i][0],
                    "is_cancel": True,
                },
            )
            if data.get("retcode") == -100:
                return "LikeM:失败(登录失效)"
            if data.get("retcode") == 0 or data.get("message") == "OK":
                num_cancel += 1
            await asyncio.sleep(random.randint(4, 13))
        return f"LikeM:完成!like:{num_ok}, dislike:{num_cancel}!"

    # 分享操作
    async def share_post(self):
        if self.Task_do["bbs_Share"]:
            return "ShareM已经完成过了~"
        if not self.postsList:
            return "ShareM:失败(未获取到帖子列表)"
        logger.info(t("log.genshinuid.msg_45c37c"))
        for _ in range(4):
            data = await self._request(
                "GET",
                BBS_SHARE.format(self.postsList[0][0]),
                self.headers,
            )
            if data.get("retcode") == -100:
                return "ShareM:失败(登录失效)"
            if data.get("retcode") == 0 or data.get("message") == "OK":
                return "ShareM:完成!"
            await asyncio.sleep(random.randint(4, 13))
        return "ShareM:失败!"

    async def _request(
        self,
        method: Literal["GET", "POST"],
        url: str,
        header: Dict[str, str],
        data: Optional[Dict] = None,
    ) -> Dict:
        payload = data if data is not None else {}
        res_data: Dict = {"retcode": -999, "message": "请求未返回数据"}
        for attempt in range(2):
            if BBS_SIGN.get() in url:
                header["DS"] = get_ds_token("", payload, "22")
            else:
                header["DS"] = get_web_ds_token()
            data_str = json.dumps(payload) if method == "POST" else None
            try:
                async with AsyncClient(timeout=15.0) as client:
                    logger.trace(method, url, data_str, header)
                    req = await client.request(
                        method=method,
                        url=url,
                        content=data_str,
                        headers=header,
                    )
                    res_data = req.json()
                    logger.debug(res_data)
            except (httpx.HTTPError, ValueError) as exc:
                res_data = {"retcode": -999, "message": f"网络请求失败: {exc}"}
                if attempt == 0:
                    await asyncio.sleep(1)
                    continue
                break
            if res_data.get("retcode") == 1034:
                challenge = await mys_api._upass(deepcopy(header), True)
                if challenge:
                    header["x-rpc-challenge"] = challenge
                continue
            break
        return res_data

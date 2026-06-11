import asyncio
from copy import deepcopy
from base64 import b64encode
from typing import Any, Dict, List, Tuple, Union, Optional
from pathlib import Path
from collections import OrderedDict

import aiofiles
from nonebot import (
    on,
    require,
    on_notice,
    get_driver,
    on_message,
    on_request,
    on_fullmatch,
)
from nonebot.log import logger
from nonebot.plugin import PluginMetadata
from nonebot.matcher import Matcher
from nonebot.adapters import Bot
from nonebot.permission import SUPERUSER
from websockets.exceptions import ConnectionClosed
from nonebot.internal.adapter import Event

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler  # noqa:E402

from .client import GsClient, driver  # noqa:E402
from .models import Message, MessageReceive  # noqa:E402

get_message = on_message(priority=0, block=False)
get_notice = on_notice(priority=0, block=False)
get_meta = on_notice(priority=0, block=False)
get_meta_request = on_request(priority=0, block=False)
get_tn = on("inline")
connect_core = on_fullmatch(
    ("连接core", "链接core"),
    permission=SUPERUSER,
    block=True,
)

__plugin_meta__ = PluginMetadata(
    name="GenshinUID",
    description="SayuCore连接器, 支持大部分适配器的全功能插件",
    usage="支持大部分适配器连接SayuCore",
    type="application",
    homepage="https://docs.sayu-bot.com",
    supported_adapters=None,
)

# 与 [gsuid-core] 的唯一 WS 连接实例; 连接生命周期(connect/重连/心跳)均在本模块管理,
# 故全局持有于此, client.py 内的发送/回执路径一律通过 GsClient 自身的 self 访问,
# 不跨模块共享该全局, 避免 init <-> client 的循环依赖与变量重绑定不同步问题.
gsclient: Optional[GsClient] = None
connect_lock = asyncio.Lock()
command_start = deepcopy(driver.config.command_start)
command_start.discard("")
msg_id_cache = OrderedDict()

if hasattr(driver.config, "gsuid_core_repeat"):
    is_repeat = True
else:
    is_repeat = False

driver = get_driver()

if hasattr(driver.config, "gsuid_core_reply_img"):
    is_reply_img = driver.config.gsuid_core_reply_img
else:
    is_reply_img = True


async def file_to_base64(file_path: Path):
    # 读取文件内容
    async with aiofiles.open(str(file_path), "rb") as file:
        file_content = await file.read()

    # 将文件内容转换为base64编码
    base64_encoded = b64encode(file_content)

    # 将base64编码的字节转换为字符串
    base64_string = base64_encoded.decode("utf-8")

    return base64_string


@get_tn.handle()
@get_notice.handle()
async def get_notice_message(bot: Bot, ev: Event):
    if gsclient is None:
        return await connect()
    try:
        await gsclient.ws.ping()
    except ConnectionClosed:
        return await connect()
    raw_data = ev.dict()
    logger.debug(raw_data)

    try:
        user_id = str(ev.get_user_id())
    except ValueError:
        user_id = "未知"

    group_id = None
    sp_user_type = None
    sp_bot_id = None
    self_id = str(bot.self_id)
    sender = {}
    msg_id = ""
    pm = 6

    if await SUPERUSER(bot, ev):
        pm = 1

    if "group_id" in raw_data:
        group_id = str(raw_data["group_id"])

    if "user_id" in raw_data:
        user_id = str(raw_data["user_id"])

    if sp_bot_id:
        bot_id = sp_bot_id
    else:
        bot_id = ev.__class__.__module__.split(".")[2]

    user_type = "group" if group_id else "direct"

    if bot.adapter.get_name() == "OneBot V11":
        if "notice_type" in raw_data and raw_data["notice_type"] in [
            "group_upload",
            "offline_file",
        ]:
            if "url" in raw_data["file"]:
                val = raw_data["file"]["url"]
            elif "id" in raw_data["file"]:
                if raw_data["file"]["size"] <= 1024 * 1024 * 4:
                    val_data = await bot.call_api(
                        "get_file",
                        file_id=raw_data["file"]["id"],
                    )
                    if "base64" in val_data and val_data["base64"]:
                        val = val_data["base64"]
                    else:
                        path = Path(val_data["file"])
                        val = await file_to_base64(path)
            else:
                logger.debug(raw_data)
                logger.warning("[文件上传] 不支持的协议端")
                return

            name = raw_data["file"]["name"]
            message = [Message("file", f"{name}|{val}")]
            # onebot_v11
        else:
            return
    elif bot.adapter.get_name() == "Milky":
        from nonebot.adapters.milky.bot import Bot
        from nonebot.adapters.milky.event import (
            GroupFileUploadEvent,
            FriendFileUploadEvent,
        )

        assert isinstance(bot, Bot)

        if isinstance(ev, GroupFileUploadEvent):
            file_id = ev.data.file_id
            file_link = await bot.get_group_file_download_url(group_id=ev.data.group_id, file_id=file_id)
            message = [Message("file", file_link)]
            user_id = str(ev.data.user_id)
            group_id = str(ev.data.group_id)
            user_type = "group"
        elif isinstance(ev, FriendFileUploadEvent):
            file_id = ev.data.file_id
            file_link = await bot.get_private_file_download_url(
                user_id=ev.data.user_id,
                file_id=file_id,
                file_hash=ev.data.file_hash,
            )
            user_id = str(ev.data.user_id)
            group_id = None
            message = [Message("file", file_link)]
            user_type = "direct"
        else:
            return
    elif bot.adapter.get_name() == "Heybox":
        from nonebot.adapters.heybox.event import UserIMMessageEvent

        if isinstance(ev, UserIMMessageEvent):
            user_id = str(ev.user_id)
            group_id = f"{ev.channel_id}-{ev.room_id}"
            msg_id = ev.im_seq
            bot_id = "heybox"
            message = [Message("text", ev.msg)]
            user_type = "group"
        else:
            return
    elif bot.adapter.get_name() == "Telegram":
        from nonebot.adapters.telegram.event import CallbackQueryEvent

        if isinstance(ev, CallbackQueryEvent):
            if ev.from_.is_bot:
                return

            user_id = str(ev.from_.id)
            msg_id = str(ev.id)
            sender = ev.from_.dict()
            if ev.message:
                if ev.message.chat.type == "private":
                    user_type = "direct"
                else:
                    user_type = "group"
                    group_id = str(ev.message.chat.id)
                message = [Message("text", ev.data)]
            else:
                logger.debug("[gsuid] 不支持该 Telegram 事件...")
                return
        else:
            logger.debug("[gsuid] 不支持该 Telegram 事件...")
            return
    elif bot.adapter.get_name() == "Discord":
        from nonebot.adapters.discord import MessageComponentInteractionEvent
        from nonebot.adapters.discord.api import (
            ChannelType,
            InteractionResponse,
            InteractionCallbackType,
            is_not_unset,
        )

        sender = {}
        if isinstance(ev, MessageComponentInteractionEvent):
            user_type = "direct" if is_not_unset(ev.channel) and ev.channel.type == ChannelType.DM else "group"
            msg_id = str(ev.id)
            group_id = str(ev.channel_id)
            message = [Message("text", ev.data.custom_id)]
            if user_type == "direct":
                nickname = ev.user.username  # type: ignore
                avatar = ev.user.avatar  # type: ignore
                user_id = str(ev.user.id)  # type: ignore
            else:
                nickname = ev.member.user.username  # type: ignore
                avatar = ev.member.user.avatar  # type: ignore
                user_id = str(ev.member.user.id)  # type: ignore
            sender = {
                "nickname": nickname,
                "avatar": f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}",
            }
            await bot.call_api(
                "create_interaction_response",
                interaction_id=ev.id,
                interaction_token=ev.token,
                response=InteractionResponse(type=InteractionCallbackType.PONG),
            )
        else:
            logger.debug("[gsuid] 不支持该 Discord 事件...")
            return
    elif bot.adapter.get_name() == "QQ":
        from nonebot.adapters.qq.bot import Bot
        from nonebot.adapters.qq.event import InteractionCreateEvent

        assert isinstance(bot, Bot), "仅适用于 QQ 机器人"

        sender = {}
        if isinstance(ev, InteractionCreateEvent):
            if ev.scene == "guild":
                sp_bot_id = "qqguild"
                user_type = "group"
                group_id = str(ev.channel_id)
                msg_id = str(ev.data.resolved.message_id)
            else:
                sp_bot_id = "qqgroup"

                if ev.scene == "group":
                    sender = {"avatar": f"https://q.qlogo.cn/qqapp/{self_id}/{str(ev.group_member_openid)}/0"}
                    user_type = "group"
                    group_id = str(ev.group_openid)
                    user_id = str(ev.group_member_openid)
                else:
                    user_type = "direct"
                    user_id = str(ev.user_openid)

                if user_id in msg_id_cache:
                    msg_id = msg_id_cache[user_id]
                else:
                    msg_id = str(ev.id)

                if len(msg_id_cache) >= 300:
                    oldest_key = next(iter(msg_id_cache))
                    del msg_id_cache[oldest_key]

                # tx暂不支持
                # msg_id = str(ev.id)

            message = [Message("text", ev.data.resolved.button_data)]

            await bot.put_interaction(interaction_id=ev.id, code=0)
        else:
            logger.debug("[gsuid] 不支持该 QQ 事件...")
            return
    else:
        return
    msg = MessageReceive(
        bot_id=sp_bot_id if sp_bot_id else bot_id,
        bot_self_id=self_id,
        user_type=sp_user_type if sp_user_type else user_type,
        group_id=group_id,
        user_id=user_id,
        sender=sender,
        content=message,
        msg_id=msg_id,
        user_pm=pm,
    )
    logger.info(f"【发送】[gsuid-core]: {msg.bot_id}")
    await gsclient._input(msg)


@get_message.handle()
async def get_all_message(bot: Bot, ev: Event):
    if gsclient is None:
        return await connect()

    try:
        await gsclient.ws.ping()
    except ConnectionClosed:
        return await connect()

    # 通用字段获取
    group_id = None
    user_id = ev.get_user_id()
    messages = ev.get_message()
    logger.debug(ev)

    self_id = str(bot.self_id)
    message: List[Message] = []
    sp_bot_id: Optional[str] = None

    pm = 6
    msg_id = ""

    # qqguild
    sender = {}
    if bot.adapter.get_name() == "QQ":
        sp_bot_id = "qqguild"
        from nonebot.adapters.qq.event import (
            GuildMessageEvent,
            C2CMessageCreateEvent,
            GroupMessageCreateEvent,
            DirectMessageCreateEvent,
            GroupAtMessageCreateEvent,
        )

        # 私聊
        if isinstance(ev, DirectMessageCreateEvent):
            user_type = "direct"
            group_id = str(ev.guild_id)
            msg_id = ev.id
            sender = ev.author.dict()
            sender["nickname"] = ev.author.username
        elif isinstance(ev, GroupAtMessageCreateEvent):
            sp_bot_id = "qqgroup"
            user_type = "group"
            group_id = str(ev.group_openid)
            msg_id = ev.id
            sender = ev.author.dict()
            sender = {
                "avatar": f"https://q.qlogo.cn/qqapp/{self_id}/{str(user_id)}/0",
            }
            msg_id_cache[user_id] = msg_id
        elif isinstance(ev, GroupMessageCreateEvent):
            sp_bot_id = "qqgroup"
            user_type = "group"
            group_id = str(ev.group_openid)
            msg_id = ev.id
            sender = ev.author.dict()
            # 如果需要，可以像 GroupAtMessageCreateEvent 一样构造头像 URL
            sender = {
                "avatar": f"https://q.qlogo.cn/qqapp/{self_id}/{str(ev.author.member_openid)}/0",
            }
            msg_id_cache[user_id] = msg_id
        elif isinstance(ev, C2CMessageCreateEvent):
            sp_bot_id = "qqgroup"
            user_type = "direct"
            group_id = None
            msg_id = ev.id
            sender = ev.author.dict()
            try:
                sender["nickname"] = f"QQ用户{ev.author.user_openid[:4]}"
            except:  # noqa: E722, B001
                sender["nickname"] = "QQ用户"
            msg_id_cache[user_id] = msg_id
        # 群聊
        elif isinstance(ev, GuildMessageEvent):
            user_type = "group"
            group_id = str(ev.channel_id)
            sender = ev.author.dict()
            if ev.member and ev.member.roles:
                if 4 in ev.member.roles:
                    pm = 2
                elif 2 in ev.member.roles:
                    pm = 3
                elif 5 in ev.member.roles:
                    pm = 5
            msg_id = ev.id
        else:
            logger.debug("[gsuid] 不支持该 QQ Guild 事件...")
            return

        if (
            hasattr(ev, "message_reference") and ev.message_reference  # type: ignore
        ):
            reply_msg_id = ev.message_reference.message_id  # type: ignore
            message.append(Message("reply", reply_msg_id))

        if hasattr(ev, "reply") and ev.reply:
            logger.debug(f"reply_obj:{ev.reply}")
            for att in getattr(ev.reply, "attachments") or []:
                if att.url:
                    message.append(Message("image", att.url))
    # telegram
    elif bot.adapter.get_name() == "Telegram":
        from nonebot.adapters.telegram.event import (
            GroupMessageEvent,
            PrivateMessageEvent,
        )

        if isinstance(ev, GroupMessageEvent) or isinstance(ev, PrivateMessageEvent):
            if ev.from_.is_bot:
                return

            user_id = str(ev.from_.id)
            msg_id = str(ev.message_id)
            sender = ev.from_.dict()
            if isinstance(ev, GroupMessageEvent):
                user_type = "group"
                group_id = str(ev.chat.id)
            else:
                user_type = "direct"
        else:
            logger.debug("[gsuid] 不支持该 Telegram 事件...")
            return
    elif bot.adapter.get_name() == "Heybox":
        from nonebot.adapters.heybox.event import UserIMMessageEvent

        if isinstance(ev, UserIMMessageEvent):
            user_id = str(ev.user_id)
            group_id = f"{ev.channel_id}-{ev.room_id}"
            msg_id = ev.im_seq
            bot_id = "heybox"
            print(ev.msg)
            print(ev.get_message())
            message = [Message("text", ev.msg)]
            user_type = "group"
            print(ev.__dict__)
            sender = {
                "name": ev.nickname,
            }
        else:
            return
    # onebot
    elif bot.adapter.get_name() == "OneBot V11":
        from nonebot.adapters.onebot.v11.event import (
            GroupMessageEvent,
            PrivateMessageEvent,
        )

        if isinstance(ev, GroupMessageEvent) or isinstance(ev, PrivateMessageEvent):
            messages = ev.original_message
            msg_id = str(ev.message_id)
            if ev.sender.role == "owner":
                pm = 2
            elif ev.sender.role == "admin":
                pm = 3

            sender = ev.sender.dict(exclude_none=True)
            sender["avatar"] = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"

            if isinstance(ev, GroupMessageEvent):
                user_type = "group"
                group_id = str(ev.group_id)
            else:
                user_type = "direct"

            if hasattr(ev, "reply") and ev.reply and is_reply_img:
                for seg in ev.reply.message:
                    if seg.type == "image" and seg.data:
                        message.append(Message("image", seg.data["url"]))
        else:
            logger.debug("[gsuid] 不支持该 onebotv11 事件...")
            return
    elif bot.adapter.get_name() == "Feishu":
        from nonebot.adapters.feishu.event import GroupMessageEvent as FGM, PrivateMessageEvent as FPM

        if isinstance(ev, FGM) or isinstance(ev, FPM):
            for feishu_msg in messages:
                if "image_key" in feishu_msg.data:
                    feishu_msg.data["url"] = feishu_msg.data["image_key"]
            user_id = ev.get_user_id()
            msg_id = ev.message_id
            sender = {}
            if isinstance(ev, FGM):
                user_type = "group"
                group_id = ev.event.message.chat_id
            else:
                user_type = "direct"
        else:
            logger.debug("[gsuid] 不支持该 Feishu 事件...")
            return
    elif bot.adapter.get_name() == "Milky":
        from nonebot.adapters.milky.event import (
            GroupMessageEvent,
            FriendMessageEvent,
        )

        if isinstance(ev, GroupMessageEvent) or isinstance(ev, FriendMessageEvent):
            sender = {
                "name": ev.data.sender.nickname,
                "nickname": ev.data.sender.nickname,
                "avatar": f"http://q1.qlogo.cn/g?b=qq&nk={ev.data.sender.user_id}&s=640",
            }
            if isinstance(ev, GroupMessageEvent):
                user_id = ev.get_user_id()
                msg_id = str(ev.message_id)
                user_type = "group"
                group_id = str(ev.data.peer_id)
            elif isinstance(ev, FriendMessageEvent):
                user_id = ev.get_user_id()
                msg_id = str(ev.message_id)
                user_type = "direct"
                group_id = None
    # OneBot V12 (仅在 ComWechatClient 测试)
    elif bot.adapter.get_name() == "OneBot V12":
        from nonebot.adapters.onebot.v12.event import (
            GroupMessageEvent,
            PrivateMessageEvent,
        )

        # v12msgid = raw_data['id']  # V12的消息id
        # self = raw_data['self']  # 返回 platform='xxx' user_id='wxid_xxxxx'
        # platform = self.platform  # 机器人平台
        # V12还支持频道等其他平台，速速Pr！
        sender = {}
        if isinstance(ev, GroupMessageEvent) or isinstance(ev, PrivateMessageEvent):
            messages = ev.original_message
            msg_id = ev.message_id
            sp_bot_id = "onebot_v12"

            if "[文件]" in ev.alt_message:
                file_id = messages[0].data.get("file_id")
                logger.info("[OB12文件ID]", file_id)
                if file_id and file_id in messages[0].data.values():
                    data = await get_file(bot, file_id)
                    logger.info("[OB12文件]", data)
                    name = data["name"]
                    path = data["path"]
                    message.append(await convert_file(path, name))

            if isinstance(ev, GroupMessageEvent):
                user_type = "group"
                group_id = ev.group_id
            else:
                user_type = "direct"
        else:
            logger.debug("[gsuid] 不支持该 onebotv12 事件...")
            return
    elif bot.adapter.get_name() == "Discord":
        from nonebot.adapters.discord import (
            GuildMessageCreateEvent,
            DirectMessageCreateEvent,
        )

        sender = {}
        if isinstance(ev, GuildMessageCreateEvent):
            user_type = "group"
            msg_id = str(ev.message_id)
            group_id = str(int(ev.channel_id))
            sender = {
                "nickname": ev.author.username,
                "avatar": f"https://cdn.discordapp.com/avatars/{user_id}/{ev.author.avatar}",
            }
        elif isinstance(ev, DirectMessageCreateEvent):
            msg_id = str(ev.message_id)
            user_type = "direct"
            group_id = str(int(ev.channel_id))
            sender = {
                "nickname": ev.author.username,
                "avatar": f"https://cdn.discordapp.com/avatars/{user_id}/{ev.author.avatar}",
            }
        else:
            logger.debug("[gsuid] 不支持该 Discord 事件...")
            return

        # 处理 Discord 消息中的附件
        if ev.attachments:
            from nonebot.adapters.discord.api import UNSET
            from nonebot.adapters.discord.utils import model_dump

            message.extend(
                Message(
                    (
                        "image"
                        if (content_type := dc_attachment.content_type) is not UNSET and "image" in content_type
                        else "attachment"
                    ),
                    model_dump(dc_attachment, exclude_unset=True),
                )
                for dc_attachment in ev.attachments
            )
    else:
        logger.debug(f"[gsuid] 不支持该 {bot.adapter.get_name()} 事件...")
        return

    if sp_bot_id:
        bot_id = sp_bot_id
    else:
        bot_id = messages.__class__.__module__.split(".")[2]

    # 确认超管权限
    if await SUPERUSER(bot, ev):
        pm = 1

    # 如果有at提及，增加AT
    if ev.is_tome():
        message.append(Message("at", self_id))

    # 处理消息
    for index, _msg in enumerate(messages):
        message = await convert_message(_msg, message, index, bot)

    if not message:
        return

    logger.debug(f"[转换消息段] {message}")
    msg = MessageReceive(
        bot_id=bot_id,
        bot_self_id=self_id,
        user_type=user_type,
        group_id=group_id,
        user_id=user_id,
        sender=sender,
        content=message,
        msg_id=msg_id if msg_id else "",
        user_pm=pm,
    )
    logger.info(f"【发送】[gsuid-core]: {msg.bot_id}")
    await gsclient._input(msg)


def _ob11_event_to_meta(raw_data: Dict[str, Any]) -> Optional[Tuple[str, Dict[str, Any]]]:
    """将 OneBot V11 的通知/请求事件映射为 (meta事件名, data) 元组.

    返回 None 表示该事件无需作为 meta 事件上报(交由其他处理器或忽略).
    事件名与 data 字段遵循 gsuid_core 的 meta 命名约定.
    """
    post_type = raw_data.get("post_type")
    if post_type == "notice":
        ntype = raw_data.get("notice_type")
        if ntype == "group_increase":
            return "user_join_group", {
                "user_id": str(raw_data.get("user_id", "")),
                "group_id": str(raw_data.get("group_id", "")),
                "operator_id": str(raw_data.get("operator_id", "")),
                "sub_type": raw_data.get("sub_type", ""),
            }
        elif ntype == "group_decrease":
            return "user_exit_group", {
                "user_id": str(raw_data.get("user_id", "")),
                "group_id": str(raw_data.get("group_id", "")),
                "operator_id": str(raw_data.get("operator_id", "")),
                "sub_type": raw_data.get("sub_type", ""),
            }
        elif ntype == "group_admin":
            return "group_admin_change", {
                "user_id": str(raw_data.get("user_id", "")),
                "group_id": str(raw_data.get("group_id", "")),
                "sub_type": raw_data.get("sub_type", ""),
            }
        elif ntype == "group_ban":
            return "group_ban", {
                "user_id": str(raw_data.get("user_id", "")),
                "group_id": str(raw_data.get("group_id", "")),
                "operator_id": str(raw_data.get("operator_id", "")),
                "duration": raw_data.get("duration", 0),
                "sub_type": raw_data.get("sub_type", ""),
            }
        elif ntype == "group_recall":
            return "group_recall", {
                "user_id": str(raw_data.get("user_id", "")),
                "group_id": str(raw_data.get("group_id", "")),
                "operator_id": str(raw_data.get("operator_id", "")),
                "message_id": str(raw_data.get("message_id", "")),
            }
        elif ntype == "friend_recall":
            return "friend_recall", {
                "user_id": str(raw_data.get("user_id", "")),
                "message_id": str(raw_data.get("message_id", "")),
            }
        elif ntype == "friend_add":
            return "friend_add", {
                "user_id": str(raw_data.get("user_id", "")),
            }
        elif ntype == "notify" and raw_data.get("sub_type") == "poke":
            data = {
                "user_id": str(raw_data.get("user_id", "")),
                "target_id": str(raw_data.get("target_id", "")),
            }
            if raw_data.get("group_id") is not None:
                data["group_id"] = str(raw_data["group_id"])
            return "poke", data
        return None
    elif post_type == "request":
        rtype = raw_data.get("request_type")
        if rtype == "friend":
            return "friend_request", {
                "user_id": str(raw_data.get("user_id", "")),
                "comment": raw_data.get("comment", ""),
                "flag": raw_data.get("flag", ""),
            }
        elif rtype == "group":
            return "group_request", {
                "user_id": str(raw_data.get("user_id", "")),
                "group_id": str(raw_data.get("group_id", "")),
                "comment": raw_data.get("comment", ""),
                "flag": raw_data.get("flag", ""),
                "sub_type": raw_data.get("sub_type", ""),
            }
        return None
    return None


@get_meta_request.handle()
@get_meta.handle()
async def get_meta_message(bot: Bot, ev: Event):
    """监听平台元事件(进退群/禁言/撤回/戳一戳/加好友/加群申请等),

    转换为 content=[Message('meta-<事件名>', data)] 的 MessageReceive 上报 core,
    由 core 的 on_meta 触发器分发. 当前仅实现 OneBot V11(参考适配器),
    其它适配器未映射时静默忽略, 不影响既有行为.
    """
    if gsclient is None:
        return await connect()
    try:
        await gsclient.ws.ping()
    except ConnectionClosed:
        return await connect()

    if bot.adapter.get_name() != "OneBot V11":
        return

    raw_data = ev.dict()
    meta = _ob11_event_to_meta(raw_data)
    if meta is None:
        return
    event_name, data = meta

    self_id = str(bot.self_id)
    bot_id = ev.__class__.__module__.split(".")[2]
    group_id = data.get("group_id") or None
    user_id = data.get("user_id") or ""
    user_type = "group" if group_id else "direct"

    pm = 6
    if await SUPERUSER(bot, ev):
        pm = 1

    msg = MessageReceive(
        bot_id=bot_id,
        bot_self_id=self_id,
        user_type=user_type,
        group_id=group_id,
        user_id=user_id,
        sender={},
        content=[Message(f"meta-{event_name}", data)],
        msg_id="",
        user_pm=pm,
    )
    logger.info(f"【发送】[gsuid-core][Meta]: {event_name}")
    await gsclient._input(msg)


@connect_core.handle()
async def send_connect_msg(matcher: Matcher):
    await connect()
    await matcher.send("链接成功！")


@driver.on_bot_connect
async def start_client():
    if gsclient is None:
        await connect()


async def connect():
    global gsclient

    async with connect_lock:
        if gsclient is not None:
            return
        try:
            await asyncio.sleep(2)
            gsclient = await GsClient().async_connect()

            await gsclient.start()

        except ConnectionRefusedError:
            gsclient = None
            logger.error("Core服务器连接失败...请稍后使用[启动core]命令启动...")


@scheduler.scheduled_job("cron", second="*/10")
async def repeat_connect():
    if is_repeat:
        global gsclient
        if gsclient is None:
            await connect()
        else:
            try:
                await gsclient.ws.ensure_open()
            except ConnectionClosed:
                return await connect()
        return


async def convert_message(
    _msg: Any,
    message: List[Message],
    index: int,
    bot: Bot,
):
    if _msg.type == "text":
        data: str = _msg.data["text"]

        if index == 0 or index == 1:
            for word in command_start:
                _data = data.strip()
                if _data.startswith(word):
                    data = _data[len(word) :]  # noqa:E203
                    break
        message.append(Message("text", data))
    elif _msg.type == "file":
        if "file_id" in _msg.data:
            name = _msg.data.get("file")
            if float(_msg.data.get("file_size") or _msg.data.get("size")) <= 1024 * 1024 * 4:
                val_data = await bot.call_api(
                    "get_file",
                    file_id=_msg.data.get("file_id"),
                )
                if "base64" in val_data and val_data["base64"]:
                    val = val_data["base64"]
                else:
                    path = Path(val_data["file"])
                    val = await file_to_base64(path)
                message.append(Message("file", f"{name}|{val}"))
    elif _msg.type == "image":
        file_id = _msg.data.get("file_id")
        if file_id in _msg.data.values():
            message.append(Message("image", _msg.data["file_id"]))
            logger.debug("[OB12图片]", _msg.data["file_id"])
        elif "path" in _msg.data:
            message.append(Message("image", _msg.data["path"]))
        elif "file" in _msg.data and "url" not in _msg.data:
            message.append(Message("image", _msg.data["file"]))
        else:
            message.append(Message("image", _msg.data["url"]))
    elif _msg.type == "at":
        message.append(Message("at", _msg.data["qq"]))
    elif _msg.type == "reply":
        message_id = _msg.data.get("message_id")
        if message_id in _msg.data.values():
            message.append(Message("reply", _msg.data["message_id"]))
        else:
            message.append(Message("reply", _msg.data["id"]))
    elif _msg.type == "mention_user":
        message.append(Message("at", str(_msg.data["user_id"])))  # discord给的整数值，需要转换成字符串
    elif _msg.type == "mention":
        if "user_id" in _msg.data:
            message.append(Message("at", _msg.data["user_id"]))
    return message


# 读取文件为base64
async def convert_file(content: Union[Path, str, bytes], file_name: str) -> Message:
    if isinstance(content, Path):
        async with aiofiles.open(str(content), "rb") as fp:
            file = await fp.read()
    elif isinstance(content, bytes):
        file = content
    else:
        async with aiofiles.open(content, "rb") as fp:
            file = await fp.read()
    return Message(
        type="file",
        data=f"{file_name}|{b64encode(file).decode()}",
    )


# 获取文件
async def get_file(bot: Bot, file_id: str):
    data = await bot.call_api(
        api="get_file",
        file_id=f"{file_id}",
        type="path",
    )
    return data

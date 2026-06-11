import asyncio
from typing import Dict, List, Union, Optional
from asyncio import CancelledError

import websockets.client
from msgspec import json as msgjson
from nonebot import get_bot, get_bots, get_driver
from nonebot.log import logger
from nonebot.adapters import Bot
from websockets.exceptions import ConnectionClosedError

from .models import Message as GsMessage, MessageSend, MessageReceive
from .send_utils import (
    Milky_send,
    del_msg,
    group_send,
    guild_send,
    feishu_send,
    heybox_send,
    onebot_send,
    discord_send,
    telegram_send,
    onebot_v12_send,
)

bots: Dict[str, str] = {}
driver = get_driver()

if hasattr(driver.config, "gsuid_core_botid"):
    BOT_ID = str(driver.config.gsuid_core_botid)
else:
    BOT_ID = "NoneBot2"

if hasattr(driver.config, "gsuid_core_host"):
    HOST = driver.config.gsuid_core_host
else:
    HOST = "localhost"

if hasattr(driver.config, "gsuid_core_port"):
    PORT = driver.config.gsuid_core_port
else:
    PORT = "8765"

if hasattr(driver.config, "gsuid_core_ws_token"):
    WS_TOKEN = driver.config.gsuid_core_ws_token
else:
    WS_TOKEN = ""


def _get_bot(bot_id: str) -> Bot:
    if "v12" in bot_id:
        bot_id = "onebotv12"
    elif "qqguild" in bot_id:
        bot_id = "qq"
    # bots: Dict[str, str] 以适配器名称为键、bot_self_id为值的字典
    _refresh_bots()
    if bot_id not in bots:
        for _bot_id in bots.keys():
            if bot_id in _bot_id:
                bot_id = _bot_id
                break
        else:
            logger.warning("未获取到正确的Bot实例,将使用默认Bot...")
            logger.warning(f"当前bot_id: {bot_id}, bots: {bots}")
            return get_bot()
    bot_real_id = bots[bot_id]
    bot = get_bot(bot_real_id)
    return bot


def _refresh_bots():
    global bots
    _bots = get_bots()
    for bot_real_id in _bots:
        bot = _bots[bot_real_id]
        bot_id = bot.type.lower().replace(" ", "")
        bots[bot_id] = bot_real_id


class GsClient:
    _instance = None

    @classmethod
    async def async_connect(cls, IP: str = HOST, PORT: Union[str, int] = PORT):
        self = GsClient()
        cls.is_alive = True
        cls.ws_url = f"ws://{IP}:{PORT}/ws/{BOT_ID}"
        if WS_TOKEN:
            cls.ws_url += f"?token={WS_TOKEN}"
        logger.info(f"Bot_ID: {BOT_ID}连接至[gsuid-core]: {self.ws_url}...")
        cls.ws = await websockets.client.connect(  # type: ignore
            cls.ws_url,
            max_size=2**26,
            open_timeout=60,
            ping_timeout=60,
        )
        logger.success(f"与[gsuid-core]成功连接! Bot_ID: {BOT_ID}")
        cls.msg_list = asyncio.queues.Queue()
        cls.pending = []
        return self

    def __new__(cls, *args, **kwargs):
        # 判断sv是否已经被初始化
        if cls._instance is None:
            cls._instance = super(GsClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    async def recv_msg(self):
        try:
            await asyncio.sleep(5)
            _refresh_bots()
            async for message in self.ws:
                try:
                    _bots = get_bots()
                    msg = msgjson.decode(message, type=MessageSend)
                    logger.info(f"【接收】[gsuid-core]: {msg.bot_id} - {msg.target_type} - {msg.target_id}")
                    bot_list = []

                    # 解析消息
                    if msg.bot_id == "NoneBot2":
                        if msg.content:
                            _data = msg.content[0]
                            if _data.type and _data.type.startswith("log"):
                                _type = _data.type.split("_")[-1].lower()
                                getattr(logger, _type)(_data.data)
                        continue

                    if msg.bot_self_id in _bots:
                        bot_list.append(_bots[msg.bot_self_id])
                    elif not msg.bot_self_id:
                        bot_list.append(_get_bot(msg.bot_id))
                    else:
                        continue

                    # 撤回控制包(单段 excute_delete_message): 短路到平台撤回 API,
                    # 不当普通消息发送, 避免非 onebot 平台误发空消息
                    if msg.content and len(msg.content) == 1 and msg.content[0].type == "excute_delete_message":
                        _del_data = msg.content[0].data
                        _mid = _del_data.get("message_id") if isinstance(_del_data, dict) else None
                        if _mid is not None:
                            for bot in bot_list:
                                await del_msg(
                                    bot,
                                    msg.bot_id,
                                    str(_mid),
                                    msg.target_id,
                                    msg.target_type,
                                )
                        continue

                    content = ""
                    image: Optional[str] = None
                    record: Optional[str] = None
                    node = []
                    file = ""
                    at_list = []
                    group_id = ""
                    markdown = ""
                    video = ""
                    buttons = []
                    template_buttons = ""
                    template_markdown = {}

                    if msg.content:
                        for _c in msg.content:
                            if _c.data:
                                if _c.type == "text":
                                    content += _c.data
                                elif _c.type == "image":
                                    image = _c.data
                                elif _c.type == "node":
                                    node = _c.data
                                elif _c.type == "file":
                                    file = _c.data
                                elif _c.type == "at":
                                    at_list.append(_c.data)
                                elif _c.type == "record":
                                    record = _c.data
                                elif _c.type == "group":
                                    group_id = _c.data
                                elif _c.type == "markdown":
                                    markdown = _c.data
                                elif _c.type == "buttons":
                                    buttons = _c.data
                                elif _c.type == "template_markdown":
                                    template_markdown = _c.data
                                elif _c.type == "template_buttons":
                                    template_buttons = _c.data
                                elif _c.type == "video":
                                    video = _c.data
                    else:
                        pass

                    # 根据bot_id字段发送消息

                    # 平台真实出站消息id; 仅当 send 函数回传时非空
                    # 一帧被平台展开为多条消息时为 List[str]
                    recall_id: Optional[Union[str, List[str]]] = None

                    try:
                        for bot in bot_list:
                            # OneBot v11
                            if msg.bot_id == "onebot":
                                recall_id = await onebot_send(
                                    bot,
                                    msg.content,
                                    msg.target_id,
                                    msg.target_type,
                                )
                            # OneBot v12
                            elif msg.bot_id == "onebot_v12":
                                recall_id = await onebot_v12_send(
                                    bot,
                                    content,
                                    image,
                                    node,
                                    file,
                                    at_list,
                                    record,
                                    msg.target_id,
                                    msg.target_type,
                                )
                            elif msg.bot_id == "heybox":
                                recall_id = await heybox_send(
                                    bot,
                                    content,
                                    image,
                                    node,
                                    file,
                                    at_list,
                                    record,
                                    msg.target_id,
                                    msg.target_type,
                                    msg.msg_id,
                                )
                            # 频道
                            elif msg.bot_id == "qqguild":
                                recall_id = await guild_send(
                                    bot,
                                    content,
                                    image,
                                    node,
                                    at_list,
                                    markdown,
                                    buttons,
                                    template_markdown,
                                    template_buttons,
                                    msg.target_id,
                                    msg.target_type,
                                    msg.msg_id,
                                    group_id,
                                )
                            elif msg.bot_id == "telegram":
                                recall_id = await telegram_send(
                                    bot,
                                    content,
                                    image,
                                    file,
                                    node,
                                    buttons,
                                    record,
                                    video,
                                    msg.target_id,
                                )
                            elif msg.bot_id == "qqgroup":
                                recall_id = await group_send(
                                    bot,
                                    content,
                                    image,
                                    node,
                                    markdown,
                                    buttons,
                                    template_markdown,
                                    template_buttons,
                                    msg.target_id,
                                    msg.target_type,
                                    msg.msg_id,
                                )
                            elif msg.bot_id == "milky":
                                recall_id = await Milky_send(
                                    bot,
                                    content,
                                    image,
                                    file,
                                    node,
                                    at_list,
                                    record,
                                    video,
                                    msg.target_id,
                                    msg.target_type,
                                )
                            elif msg.bot_id == "feishu":
                                recall_id = await feishu_send(
                                    bot,
                                    content,
                                    image,
                                    file,
                                    node,
                                    at_list,
                                    record,
                                    msg.target_id,
                                    msg.target_type,
                                )
                            elif msg.bot_id == "discord":
                                recall_id = await discord_send(
                                    bot,
                                    content,
                                    image,
                                    node,
                                    at_list,
                                    markdown,
                                    buttons,
                                    record,
                                    video,
                                    msg.target_id,
                                    msg.target_type,
                                    group_id,
                                )
                    finally:
                        # 只要 core 要求回执(echo 非空)就回执, 即便没拿到 id(返回
                        # None/空list)或发送中途异常: 让 core 立即结算该帧, 避免
                        # 空等 RECALL_WAIT_TIMEOUT 或连续零回执被误判为不支持回执
                        if msg.echo:
                            await self._send_recall_receipt(msg, recall_id)

                except Exception as e:
                    logger.exception(e)
        except CancelledError:
            logger.warning(f"与[gsuid-core]断开连接! Bot_ID: {BOT_ID}")
        except KeyboardInterrupt:
            logger.warning(f"与[gsuid-core]断开连接! Bot_ID: {BOT_ID}")
        except RuntimeError as e:
            logger.error(e)
        except ConnectionClosedError:
            for task in self.pending:
                task.cancel()
            logger.warning(f"与[gsuid-core]断开连接! Bot_ID: {BOT_ID}")
            for _ in range(30):
                await asyncio.sleep(5)
                try:
                    await self.async_connect()
                    await self.start()
                    break
                except:  # noqa
                    logger.debug("自动连接core服务器失败...五秒后重新连接...")

    async def _input(self, msg: MessageReceive):
        await self.msg_list.put(msg)

    async def _send_recall_receipt(
        self,
        msg: MessageSend,
        recall_id: Optional[Union[str, List[str]]],
    ):
        """回传 recall_message_id 回执.

        复用上行 MessageReceive 通道, content 仅含单段 recall_message_id,
        data 自带 echo(原样回传供 core 关联)与 id(平台真实出站消息id).
        id 为 None 表示本帧未拿到平台消息id(core 会结算该帧但不计入返回);
        id 为 list 表示一帧被平台展开为多条消息, core 会 flatten 进扁平结果.
        """
        receipt = MessageReceive(
            bot_id=msg.bot_id,
            bot_self_id=msg.bot_self_id,
            user_id="",
            content=[
                GsMessage(
                    type="recall_message_id",
                    data={"echo": msg.echo, "id": recall_id},
                )
            ],
        )
        await self._input(receipt)

    async def send_msg(self):
        try:
            while True:
                msg: MessageReceive = await self.msg_list.get()
                msg_send = msgjson.encode(msg)
                await self.ws.send(msg_send)
        except CancelledError:
            logger.warning(f"与[gsuid-core]断开连接! Bot_ID: {BOT_ID}")

    async def start(self):
        recv_task = asyncio.create_task(self.recv_msg())
        send_task = asyncio.create_task(self.send_msg())
        _, self.pending = await asyncio.wait(
            [recv_task, send_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

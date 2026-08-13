import asyncio
from typing import Any
from asyncio import CancelledError

from msgspec import json as msgjson
from nonebot import get_bots, get_driver
from nonebot.log import logger
from nonebot.adapters import Bot
from websockets.exceptions import ConnectionClosedError
from websockets.asyncio.client import ClientConnection, connect

from .send import (
    send_gs,
    is_log_packet,
    is_delete_packet,
    handle_log_packet,
    handle_delete_packet,
)
from .config import gs_config
from .models import Message as GsMessage, MessageSend, MessageReceive
from .identity import resolve_bot

driver = get_driver()


def _pick_bots(msg: MessageSend) -> list[Bot]:
    bots = get_bots()
    if msg.bot_self_id and msg.bot_self_id in bots:
        return [bots[msg.bot_self_id]]
    if not msg.bot_self_id:
        found = resolve_bot(msg.bot_id, msg.bot_self_id)
        if found is not None:
            return [found]
    return []


class GsClient:
    _instance: "GsClient | None" = None
    is_alive: bool
    ws_url: str
    ws: ClientConnection
    msg_list: asyncio.Queue[MessageReceive]
    pending: set[asyncio.Task[Any]]

    @classmethod
    async def async_connect(cls) -> "GsClient":
        cfg = gs_config()
        self = GsClient()
        cls.is_alive = True
        cls.ws_url = f"ws://{cfg.gsuid_core_host}:{cfg.gsuid_core_port}/ws/{cfg.gsuid_core_botid}"
        if cfg.gsuid_core_ws_token:
            cls.ws_url += f"?token={cfg.gsuid_core_ws_token}"
        logger.info(f"Bot_ID: {cfg.gsuid_core_botid}连接至[gsuid-core]: {cls.ws_url}...")
        cls.ws = await connect(
            cls.ws_url,
            max_size=2**26,
            open_timeout=60,
            ping_timeout=60,
        )
        logger.success(f"与[gsuid-core]成功连接! Bot_ID: {cfg.gsuid_core_botid}")
        cls.msg_list = asyncio.Queue()
        cls.pending = set()
        return self

    def __new__(cls, *args: object, **kwargs: object) -> "GsClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def recv_msg(self) -> None:
        cfg = gs_config()
        try:
            await asyncio.sleep(5)
            async for message in self.ws:
                try:
                    msg = msgjson.decode(message, type=MessageSend)
                    logger.info(f"【接收】[gsuid-core]: {msg.bot_id} - {msg.target_type} - {msg.target_id}")
                    if is_log_packet(msg, cfg.gsuid_core_botid):
                        handle_log_packet(msg)
                        continue
                    bot_list = _pick_bots(msg)
                    if not bot_list:
                        continue
                    if is_delete_packet(msg.content):
                        for bot in bot_list:
                            await handle_delete_packet(bot, msg)
                        continue
                    recall_id: str | list[str] | None = None
                    try:
                        for bot in bot_list:
                            recall_id = await send_gs(bot, msg)
                    finally:
                        if msg.echo:
                            await self._send_recall_receipt(msg, recall_id)
                except Exception as exc:
                    logger.exception(exc)
        except CancelledError:
            logger.warning(f"与[gsuid-core]断开连接! Bot_ID: {cfg.gsuid_core_botid}")
        except KeyboardInterrupt:
            logger.warning(f"与[gsuid-core]断开连接! Bot_ID: {cfg.gsuid_core_botid}")
        except RuntimeError as exc:
            logger.error(exc)
        except ConnectionClosedError:
            for task in self.pending:
                task.cancel()
            logger.warning(f"与[gsuid-core]断开连接! Bot_ID: {cfg.gsuid_core_botid}")
            for _ in range(30):
                await asyncio.sleep(5)
                try:
                    await self.async_connect()
                    await self.start()
                    break
                except OSError:
                    logger.debug("自动连接core服务器失败...五秒后重新连接...")

    async def _input(self, msg: MessageReceive) -> None:
        await self.msg_list.put(msg)

    async def _send_recall_receipt(
        self,
        msg: MessageSend,
        recall_id: str | list[str] | None,
    ) -> None:
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

    async def send_msg(self) -> None:
        try:
            while True:
                msg = await self.msg_list.get()
                await self.ws.send(msgjson.encode(msg))
        except CancelledError:
            logger.warning(f"与[gsuid-core]断开连接! Bot_ID: {gs_config().gsuid_core_botid}")

    async def start(self) -> None:
        recv_task = asyncio.create_task(self.recv_msg())
        send_task = asyncio.create_task(self.send_msg())
        _, self.pending = await asyncio.wait(
            [recv_task, send_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

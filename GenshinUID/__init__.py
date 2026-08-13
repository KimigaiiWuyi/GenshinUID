import asyncio

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
require("nonebot_plugin_alconna")

from nonebot_plugin_apscheduler import scheduler  # noqa: E402
from nonebot_plugin_alconna.uniseg import (  # noqa: E402
    Target,
    UniMessage,
    get_target,
    get_message_id,
)
from nonebot_plugin_alconna.uniseg.constraint import (  # noqa: E402
    SerializeFailed,
)

from .client import GsClient  # noqa: E402
from .config import PluginConfig, gs_config  # noqa: E402
from .extras import handle_notice  # noqa: E402
from .receive import build_message_receive  # noqa: E402
from .meta_event import build_meta_receive  # noqa: E402

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
    description="SayuCore连接器, 基于 Alconna UniMessage 的多适配器桥",
    usage="支持大部分适配器连接SayuCore",
    type="application",
    homepage="https://docs.sayu-bot.com",
    config=PluginConfig,
    supported_adapters=None,
)

gsclient: GsClient | None = None
connect_lock = asyncio.Lock()
driver = get_driver()


async def _ensure_client() -> GsClient | None:
    global gsclient
    if gsclient is None:
        await connect()
        return gsclient
    try:
        await gsclient.ws.ping()
    except ConnectionClosed:
        gsclient = None
        await connect()
    return gsclient


@get_tn.handle()
@get_notice.handle()
async def get_notice_message(bot: Bot, ev: Event) -> None:
    client = await _ensure_client()
    if client is None:
        return
    msg = await handle_notice(bot, ev)
    if msg is None:
        return
    logger.info(f"【发送】[gsuid-core]: {msg.bot_id}")
    await client._input(msg)


def _uni_from_event(bot: Bot, ev: Event) -> tuple[UniMessage, Target, str]:
    """优先 Alconna of/get_target/get_message_id; Console 无 uniseg 时走构造器."""
    raw = ev.get_message()
    try:
        uni = UniMessage.of(raw, bot=bot)
    except SerializeFailed:
        uni = UniMessage(raw.extract_plain_text())
    try:
        target = get_target(ev, bot)
        msg_id = get_message_id(ev, bot)
        return uni, target, msg_id
    except (SerializeFailed, NotImplementedError):
        return (
            uni,
            Target(
                ev.get_user_id(),
                private=True,
                adapter=bot.adapter.get_name(),
                self_id=str(bot.self_id),
            ),
            "",
        )


@get_message.handle()
async def get_all_message(bot: Bot, ev: Event) -> None:
    client = await _ensure_client()
    if client is None:
        return
    uni, target, msg_id = _uni_from_event(bot, ev)
    try:
        uni = await uni.attach_reply(ev, bot)
    except SerializeFailed:
        pass
    packed = await build_message_receive(bot, ev, uni, target, msg_id)
    if packed is None:
        return
    logger.debug(f"[转换消息段] {packed.content}")
    logger.info(f"【发送】[gsuid-core]: {packed.bot_id}")
    await client._input(packed)


@get_meta_request.handle()
@get_meta.handle()
async def get_meta_message(bot: Bot, ev: Event) -> None:
    client = await _ensure_client()
    if client is None:
        return
    pm = 1 if await SUPERUSER(bot, ev) else 6
    msg = build_meta_receive(bot, ev, pm)
    if msg is None:
        return
    event_name = msg.content[0].type
    logger.info(f"【发送】[gsuid-core][Meta]: {event_name}")
    await client._input(msg)


@connect_core.handle()
async def send_connect_msg(matcher: Matcher) -> None:
    await connect()
    await matcher.send("链接成功！")


@driver.on_startup
async def start_client() -> None:
    logger.info("GenshinUID startup: 准备连接 core")
    if gsclient is None:
        await connect()


@driver.on_shutdown
async def stop_client() -> None:
    global gsclient
    if gsclient is None:
        return
    for task in gsclient.pending:
        if not task.done():
            task.cancel()
    await gsclient.ws.close()
    gsclient = None
    logger.info("已断开与 gsuid-core 的连接")


async def connect() -> None:
    global gsclient
    async with connect_lock:
        if gsclient is not None:
            return
        try:
            logger.info("正在连接 gsuid-core...")
            gsclient = await GsClient().async_connect()
            asyncio.create_task(gsclient.start())
            logger.success("gsuid-core 收发协程已启动")
        except ConnectionRefusedError:
            gsclient = None
            logger.error("Core服务器连接失败...请稍后使用[启动core]命令启动...")
        except Exception as exc:
            gsclient = None
            logger.exception(exc)


@scheduler.scheduled_job("cron", second="*/10")
async def repeat_connect() -> None:
    if not gs_config().gsuid_core_repeat:
        return
    global gsclient
    if gsclient is None:
        await connect()
        return
    try:
        await gsclient.ws.ping()
    except ConnectionClosed:
        gsclient = None
        await connect()

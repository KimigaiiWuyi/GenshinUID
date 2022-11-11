import asyncio
import threading
from typing import Union

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from ..utils.exception.handle_exception import handle_exception
from ..utils.download_resource.download_all_resource import (
    download_all_resource,
)

download_resource = on_command('下载全部资源', rule=FullCommand())


@download_resource.handle()
@handle_exception('下载全部资源', '资源下载错误')
@register_menu(
    '下载全部资源',
    '下载全部资源',
    '手动下载插件运行所需的资源',
    trigger_method='管理员指令',
    detail_des=(
        '介绍：\n'
        '手动下载插件正常运行所需的资源（一般每次启动会自动检查并下载）\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>下载全部资源</ft>'
    ),
)
async def send_download_resource_msg(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
):
    if not await SUPERUSER(bot, event):
        return
    await matcher.send('正在开始下载~可能需要较久的时间!')
    im = await download_all_resource()
    await matcher.finish(im)


async def startup():
    logger.info('[资源文件下载] 正在检查与下载缺失的资源文件，可能需要较长时间，请稍等')
    logger.info(f'[资源文件下载] {await download_all_resource()}')


threading.Thread(target=lambda: asyncio.run(startup()), daemon=True).start()

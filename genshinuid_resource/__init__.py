import threading

from ..all_import import *  # noqa: F403, F401
from ..utils.download_resource.download_all_resource import (
    download_all_resource,
)


@sv.on_fullmatch('下载全部资源')
async def send_download_resource_msg(bot: HoshinoBot, ev: CQEvent):
    if ev.sender:
        qid = ev.sender['user_id']
    else:
        return
    if qid not in bot.config.SUPERUSERS:
        return
    await bot.send(ev, '正在开始下载~可能需要较久的时间!')
    im = await download_all_resource()
    await bot.send(ev, im)


async def startup():
    logger.info('[资源文件下载] 正在检查与下载缺失的资源文件，可能需要较长时间，请稍等')
    logger.info(f'[资源文件下载] {await download_all_resource()}')


threading.Thread(target=lambda: asyncio.run(startup()), daemon=True).start()

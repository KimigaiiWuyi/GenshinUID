import asyncio

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from .get_lots_data import get_lots_msg
from .get_meme_card import get_meme_img
from .get_mys_data import get_region_task, get_task_detail

sv_find_task = SV('查询游戏攻略')
sv_fun = SV('娱乐功能')


@sv_find_task.on_prefix(('原神任务', '任务详情', 'qszh'))
async def send_task_adv(bot: Bot, ev: Event):
    if ev.text in ['须弥', '层岩', '海岛']:
        im = await get_region_task(ev.text)
        for i in im:
            mes = [MessageSegment.text(_msg) for _msg in i]
            await bot.send(MessageSegment.node(mes))
            await asyncio.sleep(1)
        return
    else:
        im = await get_task_detail(ev.text)
        await bot.send(im)


@sv_fun.on_fullmatch(('抽表情'))
async def send_meme_card(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[抽表情]')
    await bot.send(await get_meme_img())


@sv_fun.on_fullmatch(('御神签'))
async def send_lots_data(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[御神签]')
    await bot.send(await get_lots_msg(ev.user_id))

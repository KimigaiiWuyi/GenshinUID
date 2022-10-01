import asyncio

from ..all_import import *
from .get_meme_card import get_meme_img
from .get_mys_data import get_region_task, get_task_detail


@sv.on_rex('(原神任务|任务|任务详情|任务攻略)( )?([\u4e00-\u9fa5]+)( )?')
async def send_task_adv(bot: HoshinoBot, ev: CQEvent):
    args = ev['match'].groups()
    if str(args[2]) in ['须弥', '层岩', '海岛']:
        im = await get_region_task(str(args[2]))
        for i in im:
            await hoshino_bot.send_group_forward_msg(
                group_id=ev.group_id, messages=i
            )
            await asyncio.sleep(1)
        return
    else:
        im = await get_task_detail(str(args[2]))
        await bot.send(ev, im)


@sv.on_fullmatch('抽表情')
async def send_meme_card(bot: HoshinoBot, ev: CQEvent):
    logger.info('开始执行[抽表情]')
    img = await get_meme_img()
    img = await convert_img(img)
    await bot.send(ev, img)

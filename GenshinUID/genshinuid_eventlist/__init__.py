from ..all_import import *  # noqa: F401, F403
from .draw_event_img import IMG_PATH, save_draw_event_img


@sv.scheduled_job('cron', hour='2')
async def draw_event():
    await save_draw_event_img()


@sv.on_fullmatch('活动列表')
async def send_events(bot: HoshinoBot, ev: CQEvent):
    while True:
        if IMG_PATH.exists():
            im = await convert_img(IMG_PATH)
            break
        else:
            await save_draw_event_img()
    await bot.send(ev, im)

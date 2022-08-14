from ..all_import import *  # noqa: F401, F403
from .draw_event_img import IMG_PATH, save_draw_event_img

get_event = on_command('活动列表', priority=priority)
scheduler = require('nonebot_plugin_apscheduler').scheduler


@scheduler.scheduled_job('cron', hour='2')
async def draw_event():
    await save_draw_event_img()


@get_event.handle()
@handle_exception('活动')
async def send_events(matcher: Matcher, args: Message = CommandArg()):
    if args:
        return
    while True:
        if IMG_PATH.exists():
            with open(IMG_PATH, 'rb') as f:
                im = MessageSegment.image(f.read())
            break
        else:
            await save_draw_event_img()
    await matcher.finish(im)

from nonebot.matcher import Matcher
from nonebot import require, on_command
from nonebot.adapters.onebot.v11 import MessageSegment

from ..config import priority
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from .draw_event_img import IMG_PATH, save_draw_event_img
from ..utils.exception.handle_exception import handle_exception

get_event = on_command('活动列表', priority=priority, rule=FullCommand())
scheduler = require('nonebot_plugin_apscheduler').scheduler


@scheduler.scheduled_job('cron', hour='2')
async def draw_event():
    await save_draw_event_img()


@get_event.handle()
@handle_exception('活动')
@register_menu(
    '活动列表',
    '活动列表',
    '查询当前版本活动日程表',
    detail_des=('指令：' '<ft color=(238,120,0)>活动列表</ft>\n' ' \n' '查询当前版本活动日程表'),
)
async def send_events(matcher: Matcher):
    while True:
        if IMG_PATH.exists():
            with open(IMG_PATH, 'rb') as f:
                im = MessageSegment.image(f.read())
            break
        else:
            await save_draw_event_img()
    await matcher.finish(im)

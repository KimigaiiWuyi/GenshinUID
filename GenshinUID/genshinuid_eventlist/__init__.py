from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.onebot.v11 import MessageSegment

from ..config import priority
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from .draw_event_img import get_event_img, get_all_event_img
from ..utils.exception.handle_exception import handle_exception

get_event = on_command('活动列表', priority=priority, rule=FullCommand())
get_gacha = on_command('卡池列表', priority=priority, rule=FullCommand())


@scheduler.scheduled_job('cron', hour='2')
async def draw_event():
    await get_all_event_img()


@get_event.handle()
@handle_exception('活动')
@register_menu(
    '活动列表',
    '活动列表',
    '查询当前版本活动日程表',
    detail_des=(
        '介绍：\n'
        '查询当前版本活动日程表\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>活动列表</ft>'
    ),
)
async def send_events(matcher: Matcher):
    img = await get_event_img('EVENT')
    await matcher.finish(MessageSegment.image(img))


@get_gacha.handle()
@handle_exception('活动')
@register_menu(
    '卡池列表',
    '卡池列表',
    '查询当前版本卡池列表',
    detail_des=(
        '介绍：\n'
        '查询当前版本卡池列表\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>卡池列表</ft>'
    ),
)
async def send_gachas(matcher: Matcher):
    img = await get_event_img('GACHA')
    await matcher.finish(MessageSegment.image(img))

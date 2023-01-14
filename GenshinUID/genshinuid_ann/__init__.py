import base64

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot import get_bot, require, on_command
from nonebot.adapters.ntchat.message import Message
from nonebot.adapters.ntchat import (
    MessageEvent,
    MessageSegment,
    TextMessageEvent,
)

from .util import black_ids
from ..config import priority
from .main import ann, consume_remind
from ..utils.nonebot2.rule import FullCommand
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..genshinuid_config.default_config import string_config
from ..utils.exception.handle_exception import handle_exception
from .ann_card import sub_ann, unsub_ann, ann_list_card, ann_detail_card

require('nonebot_plugin_apscheduler')
from nonebot_plugin_apscheduler import scheduler

update_ann_scheduler = scheduler
get_ann_info = on_command('原神公告', priority=priority)
reg_ann = on_command(
    '订阅原神公告', priority=priority, rule=FullCommand(), permission=SUPERUSER
)
unreg_ann = on_command(
    '取消订阅原神公告',
    aliases={'取消原神公告', '退订原神公告'},
    priority=priority,
    rule=FullCommand(),
    permission=SUPERUSER,
)
consume_ann = on_command('清除原神公告红点', priority=priority, rule=FullCommand())


@get_ann_info.handle()
@handle_exception('原神公告', '获取/发送原神公告失败')
async def send_ann_pic(
    matcher: Matcher,
    args: Message = CommandArg(),
):
    ann_id = str(args).replace(' ', '').replace('#', '')

    if not ann_id:
        img = await ann_list_card()
        await matcher.finish(MessageSegment.image(img))

    if not ann_id.isdigit():
        raise Exception("公告ID不正确")

    img = await ann_detail_card(int(ann_id))
    await matcher.finish(MessageSegment.image(img))


@reg_ann.handle()
@handle_exception('设置原神公告', '设置原神公告失败')
async def send_reg_ann(
    event: TextMessageEvent,
    matcher: Matcher,
):
    await matcher.finish(sub_ann(event.room_wxid))


@unreg_ann.handle()
@handle_exception('取消原神公告', '取消设置原神公告失败')
async def send_unreg_ann(
    event: TextMessageEvent,
    matcher: Matcher,
):
    await matcher.finish(unsub_ann(event.room_wxid))


@consume_ann.handle()
@handle_exception('取消原神公告红点', '取消红点失败')
async def send_consume_ann(
    event: MessageEvent,
    matcher: Matcher,
):
    qid = event.from_wxid
    uid = await select_db(qid, mode='uid')
    uid = str(uid)
    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)
    await matcher.finish(await consume_remind(uid))


@update_ann_scheduler.scheduled_job('cron', minute=10)
async def check_ann():
    await check_ann_state()


async def check_ann_state():
    logger.info('[原神公告] 定时任务: 原神公告查询..')
    ids = string_config.get_config('Ann_Ids')
    sub_list = string_config.get_config('Ann_Groups')
    if not sub_list:
        logger.info('没有群订阅, 取消获取数据')
        return
    if not ids:
        ids = await ann().get_ann_ids()
        if not ids:
            raise Exception('获取原神公告ID列表错误,请检查接口')
        string_config.set_config('Ann_Ids', ids)
        logger.info('初始成功, 将在下个轮询中更新.')
        return
    new_ids = await ann().get_ann_ids()

    new_ann = set(ids) ^ set(new_ids)
    if not new_ann:
        logger.info('[原神公告] 没有最新公告')
        return

    for ann_id in new_ann:
        if ann_id in black_ids:
            continue
        try:
            img = await ann_detail_card(ann_id)
            logger.info('[原神公告] 推送完毕, 更新数据库')
            string_config.set_config('Ann_Ids', new_ids)
            for group in sub_list:
                bot = get_bot()
                b64img = base64.b64encode(img)
                await bot.call_api(
                    api='send_image',
                    to_wxid=str(group),
                    file_path="base64://" + b64img.decode(),
                )
        except Exception as e:
            logger.exception(e)

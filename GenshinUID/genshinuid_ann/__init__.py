import random
import asyncio

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.gss import gss
from gsuid_core.models import Event
from gsuid_core.aps import scheduler
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import UID_HINT

from .util import black_ids
from ..utils.convert import get_uid
from .main import ann, consume_remind
from ..utils.image.convert import convert_img
from ..genshinuid_config.gs_config import gsconfig
from .ann_card import sub_ann, unsub_ann, ann_list_card, ann_detail_card

sv_ann = SV('原神公告')
sv_ann_sub = SV('原神公告订阅', pm=2)
sv_ann_hint = SV('原神公告红点')


@sv_ann.on_command(('原神公告'))
async def ann_(bot: Bot, ev: Event):
    ann_id = ev.text
    if not ann_id:
        img = await ann_list_card()
        img = await convert_img(img)
        return await bot.send(img)

    if not ann_id.isdigit():
        raise Exception('公告ID不正确')

    img = await ann_detail_card(int(ann_id))
    img = await convert_img(img)
    await bot.send(img)


@sv_ann_sub.on_fullmatch('订阅原神公告')
async def sub_ann_(bot: Bot, ev: Event):
    if ev.group_id is None:
        return await bot.send('请在群聊中订阅')
    await bot.send(sub_ann(bot.bot_id, ev.group_id))


@sv_ann_sub.on_fullmatch(('取消订阅原神公告', '取消原神公告', '退订原神公告'))
async def unsub_ann_(bot: Bot, ev: Event):
    if ev.group_id is None:
        return await bot.send('请在群聊中取消订阅')
    await bot.send(unsub_ann(bot.bot_id, ev.group_id))


@sv_ann_hint.on_fullmatch(('取消原神公告红点', '清除原神公告红点'))
async def consume_remind_(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    else:
        await bot.send(await consume_remind(uid))


@scheduler.scheduled_job('cron', minute=10)
async def check_ann():
    await check_ann_state()


async def check_ann_state():
    logger.info('[原神公告] 定时任务: 原神公告查询..')
    ids = gsconfig.get_config('Ann_Ids').data
    sub_list = gsconfig.get_config('Ann_Groups').data

    if not sub_list:
        logger.info('没有群订阅, 取消获取数据')
        return

    if not ids:
        ids = await ann().get_ann_ids()
        if not ids:
            raise Exception('获取原神公告ID列表错误,请检查接口')
        gsconfig.set_config('Ann_Ids', ids)
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
            img = await convert_img(img)
            for bot_id in sub_list:
                try:
                    for BOT_ID in gss.active_bot:
                        bot = gss.active_bot[BOT_ID]
                        for group_id in sub_list[bot_id]:
                            await bot.target_send(
                                img, 'group', group_id, bot_id, '', ''
                            )
                            await asyncio.sleep(random.uniform(1, 3))
                except Exception as e:
                    logger.exception(e)
        except Exception as e:
            logger.exception(str(e))

    logger.info('[原神公告] 推送完毕, 更新数据库')
    gsconfig.set_config('Ann_Ids', new_ids)

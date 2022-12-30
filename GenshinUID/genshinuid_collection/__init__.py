import re

from hoshino.typing import CQEvent, HoshinoBot

from ..base import sv, logger
from ..utils.data_convert.get_uid import get_uid
from ..utils.message.error_reply import UID_HINT
from ..utils.message.error_reply import *  # noqa: F403,F401
from ..utils.draw_image_tools.send_image_tool import convert_img
from .draw_collection_card import draw_explora_img, draw_collection_img


@sv.on_prefix(('查询收集', '收集', 'sj'))
async def send_collection_info(bot: HoshinoBot, ev: CQEvent):
    raw_mes = ev.message.extract_plain_text().replace(' ', '')
    logger.info('开始执行[查询收集信息]')
    at = re.search(r'\[CQ:at,qq=(\d*)]', raw_mes)

    if at:
        qid = int(at.group(1))
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return

    uid = await get_uid(qid, raw_mes)
    logger.info('[查询收集信息]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await bot.send(ev, UID_HINT)

    im = await draw_collection_img(qid, uid)
    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')


@sv.on_prefix(('查询探索', '探索', 'ts'))
async def send_explora_info(bot: HoshinoBot, ev: CQEvent):
    raw_mes = ev.message.extract_plain_text().replace(' ', '')
    logger.info('开始执行[查询探索信息]')
    at = re.search(r'\[CQ:at,qq=(\d*)]', raw_mes)

    if at:
        qid = int(at.group(1))
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return

    uid = await get_uid(qid, raw_mes)
    logger.info('[查询探索信息]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await bot.send(ev, UID_HINT)

    im = await draw_explora_img(qid, uid)
    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')

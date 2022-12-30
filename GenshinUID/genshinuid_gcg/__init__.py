import re

from hoshino.typing import CQEvent, HoshinoBot

from ..base import sv, logger
from .draw_gcginfo import draw_gcg_info
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..utils.draw_image_tools.send_image_tool import convert_img


@sv.on_prefix(('七圣召唤', '七圣', '召唤'))
async def send_gcg_pic(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        raw_mes = ev.message.extract_plain_text().replace(' ', '')
    else:
        return

    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))
    logger.info('开始执行[七圣召唤]')

    if at:
        qid = int(at.group(1))
    else:
        qid = int(ev.sender['user_id'])
    logger.info('[七圣召唤]QQ: {}'.format(qid))

    # 获取uid
    uid = re.findall(r'\d+', raw_mes)
    if uid:
        uid = uid[0]
    else:
        uid = await select_db(qid, mode='uid')
        uid = str(uid)

    logger.info('[七圣召唤]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await bot.send(ev, UID_HINT)

    im = await draw_gcg_info(uid)

    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')

import re
import random
import asyncio
from typing import Tuple

from hoshino.typing import CQEvent, HoshinoBot

from ..base import sv, logger
from .get_enka_img import draw_enka_img
from .draw_char_rank import draw_cahrcard_list
from ..utils.message.error_reply import UID_HINT
from ..utils.enka_api.get_enka_data import switch_api
from ..utils.enka_api.enka_to_card import enka_to_card
from ..utils.enka_api.enka_to_data import enka_to_data
from ..utils.download_resource.RESOURCE_PATH import TEMP_PATH
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.db_operation.db_operation import select_db, get_all_uid

AUTO_REFRESH = False


@sv.on_fullmatch('切换api')
async def send_change_api_info(bot: HoshinoBot, ev: CQEvent):
    print(ev)
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return

    if qid not in bot.config.SUPERUSERS:
        return

    im = await switch_api()
    await bot.send(ev, im)


@sv.on_rex(r'^(\[CQ:reply,id=[0-9]+\])?( )?(\[CQ:at,qq=[0-9]+\])?( )?原图')
async def send_original_pic(bot: HoshinoBot, ev: CQEvent):
    for msg in ev.message:
        if msg['type'] == 'reply':
            msg_id = msg['data']['id']
            path = TEMP_PATH / f'{msg_id}.jpg'
            if path.exists():
                logger.info('[原图]访问图片: {}'.format(path))
                with open(path, 'rb') as f:
                    im = await convert_img(f.read())
                    await bot.send(ev, im)


@sv.on_rex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(uid|查询|mys)([0-9]+)?'
    r'([\u4e00-\u9fa5]+)'
    r'(\[CQ:at,qq=[0-9]+\])?( )?',
)
async def send_char_info(bot: HoshinoBot, ev: CQEvent):
    args = ev['match'].groups()
    if args[4] is None:
        return
    # 获取角色名
    msg = ''.join(re.findall('[\u4e00-\u9fa5]', args[4]))
    logger.info('开始执行[查询角色面板]')
    logger.info('[查询角色面板]参数: {}'.format(args))
    # 获取角色名
    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))
    image = re.search(r'\[CQ:image,file=(.*),url=(.*)]', str(ev.message))

    img = None
    if image:
        img = image.group(2)
    if at:
        qid = int(at.group(1))
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return
    logger.info('[查询角色面板]QQ: {}'.format(qid))

    # 获取uid
    if args[3] is None:
        uid = await select_db(qid, mode='uid')
        uid = str(uid)
    else:
        uid = args[3]
    logger.info('[查询角色面板]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await bot.send(ev, UID_HINT)

    im = await draw_enka_img(msg, uid, img)

    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, Tuple):
        img = await convert_img(im[0])
        req = await bot.send(ev, img)
        msg_id = req['message_id']
        if im[1]:
            with open(TEMP_PATH / f'{msg_id}.jpg', 'wb') as f:
                f.write(im[1])
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')


async def refresh_char_data():
    """
    :说明:
      刷新全部绑定uid的角色展柜面板进入本地缓存。
    """
    uid_list = await get_all_uid()
    t = 0
    for uid in uid_list:
        try:
            im = await enka_to_data(uid)
            logger.info(im)
            t += 1
            await asyncio.sleep(35 + random.randint(1, 20))
        except Exception:
            logger.exception(f'{uid}刷新失败！')
            logger.error(f'{uid}刷新失败！本次自动刷新结束！')
            return f'执行失败从{uid}！共刷新{str(t)}个角色！'
    else:
        logger.info(f'共刷新{str(t)}个角色！')
        return f'执行成功！共刷新{str(t)}个角色！'


@sv.scheduled_job('cron', hour='4')
async def daily_refresh_charData():
    global AUTO_REFRESH
    if AUTO_REFRESH:
        await refresh_char_data()


@sv.on_prefix('强制刷新')
async def send_card_info(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return

    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))

    if at:
        qid = int(at.group(1))
        message = message.replace(str(at), '')
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return

    uid = re.findall(r'\d+', message)  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))

    if len(uid) >= 1:
        uid = uid[0]
    else:
        if m == '全部数据':
            if qid in bot.config.SUPERUSERS:
                await bot.send(ev, '开始刷新全部数据，这可能需要相当长的一段时间！！')
                im = await refresh_char_data()
                await bot.send(ev, str(im))
                return
            else:
                return
        else:
            uid = await select_db(qid, mode='uid')
            uid = str(uid)
            if '未找到绑定的UID' in uid:
                await bot.send(ev, UID_HINT)
                return
    im = await enka_to_card(uid)

    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')


@sv.on_prefix('毕业度统计')
async def send_charcard_list(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return

    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))

    if at:
        qid = int(at.group(1))
        message = message.replace(str(at), '')
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return

    # 获取uid
    uid = re.findall(r'\d+', message)
    if uid:
        uid = uid[0]
    else:
        uid = await select_db(qid, mode='uid')

    im = await draw_cahrcard_list(str(uid), qid)

    logger.info(f'UID{uid}获取角色数据成功！')
    if isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, str(im))

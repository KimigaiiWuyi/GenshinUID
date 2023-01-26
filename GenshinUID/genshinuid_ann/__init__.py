import random
import asyncio

from nonebot import get_bot
from hoshino import Service, priv

from ..base import logger
from .util import black_ids
from .main import ann, consume_remind
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..genshinuid_config.default_config import string_config
from ..utils.draw_image_tools.send_image_tool import convert_img
from .ann_card import sub_ann, unsub_ann, ann_list_card, ann_detail_card

sv_help = '''
原神公告
原神公告#ID
'''.strip()

sv = Service(
    name='原神公告',  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=True,  # 默认启用
    # bundle = '娱乐', #分组归类
    help_=sv_help,  # 帮助说明
)

prefix = '原神'


@sv.on_prefix((f'{prefix}公告#', f'{prefix}公告'))
async def ann_(bot, ev):
    ann_id = ev.message.extract_plain_text().strip()
    if not ann_id:
        img = await ann_list_card()
        img = await convert_img(img)
        await bot.send(ev, img, at_sender=True)
        return

    if not ann_id.isdigit():
        raise Exception("公告ID不正确")
    try:
        img = await ann_detail_card(int(ann_id))
        img = await convert_img(img)
        await bot.send(ev, img, at_sender=True)
    except Exception as e:
        await bot.finish(ev, str(e))


@sv.on_fullmatch(f'订阅{prefix}公告')
async def sub_ann_(bot, ev):
    if not priv.check_priv(ev, priv.ADMIN):
        raise Exception("你没有权限开启原神公告推送")
    try:
        await bot.send(ev, sub_ann(ev.group_id))
    except Exception as e:
        await bot.finish(ev, str(e))


@sv.on_fullmatch((f'取消订阅{prefix}公告', f'取消{prefix}公告', f'退订{prefix}公告'))
async def unsub_ann_(bot, ev):
    if not priv.check_priv(ev, priv.ADMIN):
        raise Exception("你没有权限取消原神公告推送")
    try:
        await bot.send(ev, unsub_ann(ev.group_id))
    except Exception as e:
        await bot.finish(ev, str(e))


@sv.on_fullmatch(f'取消{prefix}公告红点')
async def consume_remind_(bot, ev):
    try:
        qid = int(ev.sender['user_id'])
        uid = await select_db(qid, mode='uid')
        uid = str(uid)
        if '未找到绑定的UID' in uid:
            await bot.send(ev, UID_HINT)
            return
        await bot.send(ev, await consume_remind(uid), at_sender=True)
    except Exception as e:
        await bot.finish(ev, str(e))


@sv.scheduled_job('cron', minute=10)
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
            img = await convert_img(img)
            bot = get_bot()
            for group in sub_list:
                try:
                    await bot.send_group_msg(group_id=group, message=img)
                    await asyncio.sleep(random.uniform(1, 3))
                except Exception as e:
                    logger.exception(e)
        except Exception as e:
            logger.exception(str(e))

    logger.info('[原神公告] 推送完毕, 更新数据库')
    string_config.set_config('Ann_Ids', new_ids)

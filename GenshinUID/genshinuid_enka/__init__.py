import re
import json
import random
import asyncio
from typing import Union

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import require, on_command
from nonebot.permission import SUPERUSER
from nonebot.params import Depends, CommandArg
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageSegment,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from ..config import priority
from ..genshinuid_meta import register_menu
from ..utils.enka_api.get_enka_data import switch_api
from ..utils.enka_api.enka_to_data import enka_to_data
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.message.error_reply import UID_HINT, CHAR_HINT
from .draw_char_card import draw_char_img, draw_cahrcard_list
from ..utils.alias.alias_to_char_name import alias_to_char_name
from ..utils.download_resource.RESOURCE_PATH import PLAYER_PATH
from ..utils.exception.handle_exception import handle_exception
from ..utils.db_operation.db_operation import select_db, get_all_uid

refresh = on_command('强制刷新')
change_api = on_command('切换api')
get_charcard_list = on_command('毕业度统计')
get_char_info = on_command(
    '查询',
    priority=priority,
)

AUTO_REFRESH = False
refresh_scheduler = require('nonebot_plugin_apscheduler').scheduler


@change_api.handle()
@handle_exception('切换api')
async def send_change_api_info(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Message = CommandArg(),
):
    if args or not await SUPERUSER(bot, event):
        return

    im = await switch_api()
    await matcher.finish(im)


@get_char_info.handle()
@handle_exception('查询角色面板')
@register_menu(
    '查询角色面板',
    '查询(@某人)角色名',
    '查询你的或者指定人的已缓存展柜角色的面板',
    detail_des=(
        '指令：'
        '<ft color=(238,120,0)>[查询</ft>'
        '<ft color=(125,125,125)>(@某人)</ft>'
        '<ft color=(238,120,0)>/uidxxx/mysxxx]</ft>'
        '<ft color=(238,120,0)>角色名</ft>\n'
        ' \n'
        '可以用来查看你的或者指定人的已缓存展柜角色的面板\n'
        '支持部分角色别名\n'
        ' \n'
        '示例：\n'
        '<ft color=(238,120,0)>查询宵宫</ft>；\n'
        '<ft color=(238,120,0)>查询</ft><ft color=(0,148,200)>@无疑Wuyi</ft>'
        ' <ft color=(238,120,0)>公子</ft>'
    ),
)
async def send_char_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Message = CommandArg(),
    custom: ImageAndAt = Depends(),
):
    if args is None:
        return
    logger.info('开始执行[查询角色面板]')
    raw_mes = args.extract_plain_text().strip()
    at = custom.get_first_at()
    img = custom.get_first_image()

    if at:
        qid = at
    else:
        qid = event.user_id
    logger.info('[查询角色面板]QQ: {}'.format(qid))

    # 获取uid
    uid = re.findall(r'\d+', raw_mes)
    if uid:
        uid = uid[0]
    else:
        uid = await select_db(qid, mode='uid')
        uid = str(uid)
    logger.info('[查询角色面板]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)

    # 获取角色名
    char_name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))

    player_path = PLAYER_PATH / str(uid)
    if char_name == '展柜角色':
        char_file_list = player_path.glob('*')
        char_list = []
        for i in char_file_list:
            file_name = i.name
            if '\u4e00' <= file_name[0] <= '\u9fff':
                char_list.append(file_name.split('.')[0])
        char_list_str = ','.join(char_list)
        await matcher.finish(f'UID{uid}当前缓存角色:{char_list_str}', at_sender=True)
    else:
        if '旅行者' in char_name:
            char_name = '旅行者'
        else:
            char_name = await alias_to_char_name(char_name)
        char_path = player_path / f'{char_name}.json'
        if char_path.exists():
            with open(char_path, 'r', encoding='utf8') as fp:
                char_data = json.load(fp)
        else:
            await matcher.finish(CHAR_HINT.format(char_name), at_sender=True)

    im = await draw_char_img(char_data, img)

    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')


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


@refresh_scheduler.scheduled_job('cron', hour='4')
async def daily_refresh_charData():
    global AUTO_REFRESH
    if AUTO_REFRESH:
        await refresh_char_data()


@refresh.handle()
@handle_exception('强制刷新')
@register_menu(
    '刷新展柜缓存',
    '强制刷新',
    '强制刷新你的或者指定人缓存的角色展柜数据',
    detail_des=(
        '指令：'
        '<ft color=(238,120,0)>强制刷新</ft>'
        '<ft color=(125,125,125)>(uid/全部数据)</ft>\n'
        ' \n'
        '用于强制刷新你的或者指定人缓存的角色展柜数据\n'
        '当刷新全部数据时需要机器人管理员权限\n'
        ' \n'
        '示例：\n'
        '<ft color=(238,120,0)>强制刷新</ft>；\n'
        '<ft color=(238,120,0)>强制刷新123456789</ft>；\n'
        '<ft color=(238,120,0)>强制刷新全部数据</ft>'
    ),
)
async def send_card_info(
    bot: Bot,
    matcher: Matcher,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    args: Message = CommandArg(),
):
    message = args.extract_plain_text().strip().replace(' ', '')
    uid = re.findall(r'\d+', message)  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    qid = int(event.sender.user_id)  # type: ignore

    if len(uid) >= 1:
        uid = uid[0]
    else:
        if m == '全部数据':
            if await SUPERUSER(bot, event):
                await matcher.send('开始刷新全部数据，这可能需要相当长的一段时间！！')
                im = await refresh_char_data()
                await matcher.finish(str(im))
            else:
                return
        else:
            uid = await select_db(qid, mode='uid')
            uid = str(uid)
            if not uid:
                await matcher.finish(UID_HINT)
    im = await enka_to_data(uid)
    logger.info(f'UID{uid}获取角色数据成功！')
    await matcher.finish(str(im))


@get_charcard_list.handle()
@handle_exception('毕业度统计')
@register_menu(
    '毕业度统计',
    '毕业度统计',
    '查看你或指定人已缓存的展柜角色毕业度',
    detail_des=(
        '指令：'
        '<ft color=(238,120,0)>毕业度统计</ft>'
        '<ft color=(125,125,125)>(@某人)</ft>\n'
        ' \n'
        '可以查看你或指定人已缓存的所有展柜角色毕业度\n'
        ' \n'
        '示例：\n'
        '<ft color=(238,120,0)>毕业度统计</ft>；\n'
        '<ft color=(238,120,0)>毕业度统计</ft><ft color=(0,148,200)>@无疑Wuyi</ft>'
    ),
)
async def send_charcard_list(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Message = CommandArg(),
    custom: ImageAndAt = Depends(),
):

    message = args.extract_plain_text().strip().replace(' ', '')
    limit = re.findall(r'\d+', message)  # str
    if len(limit) >= 1:
        limit = int(limit[0])
    else:
        limit = 24
    at = custom.get_first_at()
    if at:
        uid = await select_db(at, mode='uid')
        message = message.replace(str(at), '')
    else:
        uid = await select_db(
            int(event.sender.user_id), mode='uid'  # type: ignore
        )
    im = await draw_cahrcard_list(str(uid), limit)

    logger.info(f'UID{uid}获取角色数据成功！')
    if isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish(str(im))

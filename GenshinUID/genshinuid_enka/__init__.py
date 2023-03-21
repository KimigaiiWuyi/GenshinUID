import re
import random
import asyncio
from typing import Tuple, Union

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.params import Depends, CommandArg
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageSegment,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from ..config import priority
from .get_enka_img import draw_enka_img
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from .draw_char_rank import draw_cahrcard_list
from ..utils.message.error_reply import UID_HINT
from ..utils.enka_api.get_enka_data import switch_api
from ..utils.enka_api.enka_to_card import enka_to_card
from ..utils.enka_api.enka_to_data import enka_to_data
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.download_resource.RESOURCE_PATH import TEMP_PATH
from ..utils.exception.handle_exception import handle_exception
from ..utils.db_operation.db_operation import select_db, get_all_uid

refresh = on_command('强制刷新')
original_pic = on_command('原图', rule=FullCommand())
change_api = on_command('切换api')
get_charcard_list = on_command('毕业度统计')
get_char_info = on_command(
    '查询',
    priority=priority,
)

AUTO_REFRESH = False
refresh_scheduler = scheduler


@change_api.handle()
@handle_exception('切换api')
@register_menu(
    '切换API',
    '切换api',
    '切换获取角色面板时使用的API',
    detail_des=(
        '介绍：\n'
        '切换获取角色面板时使用的Enka Network API\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>切换api</ft>'
    ),
)
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


@original_pic.handle()
@handle_exception('原图')
@register_menu(
    '查看面板原图',
    '原图',
    '查看角色面板中原随机图',
    trigger_method='回复+指令',
    detail_des=(
        '介绍：\n'
        '查看开启随机图功能时角色面板中角色位置的原图，需要回复要查看原图的面板图片消息\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>原图</ft>'
    ),
)
async def send_original_pic(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
):
    if event.reply:
        msg_id = event.reply.message_id
        path = TEMP_PATH / f'{msg_id}.jpg'
        if path.exists():
            logger.info('[原图]访问图片: {}'.format(path))
            with open(path, 'rb') as f:
                await matcher.finish(MessageSegment.image(f.read()))


@get_char_info.handle()
@handle_exception('查询角色面板')
@register_menu(
    '查询角色面板',
    '查询(@某人)角色名',
    '查询你的或者指定人的已缓存展柜角色的面板',
    detail_des=(
        '介绍：\n'
        '可以用来查看你的或者指定人的已缓存展柜角色的面板\n'
        '支持部分角色别名\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>{查询</ft>'
        '<ft color=(125,125,125)>(@某人)</ft>'
        '<ft color=(238,120,0)>|uid</ft><ft color=(0,148,200)>xx</ft>'
        '<ft color=(238,120,0)>|mys</ft><ft color=(0,148,200)>xx</ft>'
        '<ft color=(238,120,0)>}</ft>'
        '<ft color=(0,148,200)>[角色名]</ft>\n'
        '后面可以跟 '
        '<ft color=(238,120,0)>换</ft>'
        '<ft color=(125,125,125)>(精{一|二|三|四|五})</ft>'
        '<ft color=(0,148,200)>[武器名]</ft> '
        '来更换展示的武器\n'
        '可以跟 '
        '<ft color=(125,125,125)>(成长)</ft><ft color=(238,120,0)>曲线</ft> '
        '来查询该角色成长曲线\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>查询宵宫</ft>\n'
        '- <ft color=(238,120,0)>查询绫华换精五雾切</ft>\n'
        '- <ft color=(238,120,0)>查询一斗成长曲线</ft>\n'
        '- <ft color=(238,120,0)>查询</ft><ft color=(0,123,67)>@无疑Wuyi</ft>'
        ' <ft color=(238,120,0)>公子</ft>'
    ),
)
@register_menu(
    '查询展柜角色',
    '查询展柜角色',
    '查询插件已缓存的展柜角色列表',
    detail_des=(
        '介绍：\n'
        '查询插件当前已缓存的展柜角色列表\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>查询展柜角色</ft>'
    ),
)
async def send_char_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Message = CommandArg(),
    custom: ImageAndAt = Depends(),
):
    raw_mes = args.extract_plain_text().strip()
    name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
    if not name:
        return

    logger.info('开始执行[查询角色面板]')
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

    im = await draw_enka_img(raw_mes, uid, img)

    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, Tuple):
        req = await matcher.send(MessageSegment.image(im[0]))
        msg_id = req['message_id']
        if im[1]:
            with open(TEMP_PATH / f'{msg_id}.jpg', 'wb') as f:
                f.write(im[1])
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
    custom: ImageAndAt = Depends(),
):
    message = args.extract_plain_text().strip().replace(' ', '')
    uid = re.findall(r'\d+', message)  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    qid = event.user_id
    at = custom.get_first_at()
    if at:
        qid = at

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
    im = await enka_to_card(uid)

    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')


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
    raw_mes = args.extract_plain_text().strip()
    qid = event.user_id
    at = custom.get_first_at()
    if at:
        qid = at

    # 获取uid
    uid = re.findall(r'\d+', raw_mes)
    if uid:
        uid = uid[0]
    else:
        uid = await select_db(qid, mode='uid')
        uid = str(uid)

    im = await draw_cahrcard_list(str(uid), qid)

    logger.info(f'UID{uid}获取角色数据成功！')
    if isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish(str(im))

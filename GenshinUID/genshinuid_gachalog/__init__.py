import os
import asyncio

from nonebot.log import logger
from nonebot.rule import is_type
from nonebot.matcher import Matcher
from nonebot import get_bot, on_command, on_message
from nonebot.adapters.ntchat.permission import GROUP
from nonebot.adapters.ntchat import (
    MessageSegment,
    FileMessageEvent,
    TextMessageEvent,
)

from .get_gachalogs import save_gachalogs
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from .draw_gachalogs import draw_gachalogs_img
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..utils.exception.handle_exception import handle_exception
from .export_and_import import export_gachalogs, import_gachalogs

get_gacha_log = on_command('刷新抽卡记录', aliases={'强制刷新抽卡记录'}, rule=FullCommand())
get_gacha_log_card = on_command('抽卡记录', rule=FullCommand())
import_gacha_log = on_message(block=False, rule=(is_type(FileMessageEvent)))
export_gacha_log = on_command('导出抽卡记录', rule=FullCommand(), permission=GROUP)


@export_gacha_log.handle()
@handle_exception('导出抽卡记录')
@register_menu(
    '导出抽卡记录',
    '导出抽卡记录',
    '导出符合UIGF规范的抽卡记录',
    trigger_method='群聊指令',
    detail_des=(
        '介绍：\n'
        '导出UIGF格式规范的json格式抽卡记录上传到群文件\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>导出抽卡记录</ft>'
    ),
)
async def export_gacha_log_info(
    event: TextMessageEvent,
    matcher: Matcher,
):
    logger.info('开始执行[导出抽卡记录]')
    qid = event.from_wxid
    gid = event.room_wxid
    uid = await select_db(qid, mode='uid')
    bot = get_bot()
    if not isinstance(uid, str) or '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)
    raw_data = await export_gachalogs(uid)
    if raw_data['retcode'] == 'ok':
        await bot.call_api(
            'send_file',
            to_wxid=gid,
            file_path=raw_data['url'],
        )
        logger.info(f'[导出抽卡记录] UID{uid}成功!')
        await matcher.finish('上传成功!')
    else:
        logger.warning(f'[导出抽卡记录] UID{uid}失败!')
        await matcher.finish('导出抽卡记录失败!')


@import_gacha_log.handle()
@handle_exception('导入抽卡记录')
@register_menu(
    '导入抽卡记录',
    'json格式文件',
    '导入符合UIGF规范的抽卡记录',
    trigger_method='私聊离线文件',
    detail_des=(
        '介绍：\n'
        '导入UIGF格式规范的json格式抽卡记录到插件本地缓存\n'
        ' \n'
        '触发方式：\n'
        '- <ft color=(238,120,0)>私聊发送json格式的离线文件</ft>'
    ),
)
async def import_gacha_log_info(event: FileMessageEvent, matcher: Matcher):
    await asyncio.sleep(2)  # 等待下载文件，避免占用
    # 检测文件是否存在并小于8MB
    if (
        os.path.exists(event.file)
        and os.path.getsize(event.file) <= 8 * 1024 * 1024
        and event.file_name.endswith(".json")
    ):
        uid = await select_db(event.from_wxid, mode='uid')
        if not isinstance(uid, str) or '未找到绑定的UID' in uid:
            await matcher.finish(UID_HINT)
        logger.info('开始执行[导入抽卡记录]')
        im = await import_gachalogs(event.file, uid)
        await matcher.finish(im)
    else:
        await matcher.finish()


@get_gacha_log_card.handle()
@handle_exception('抽卡记录')
@register_menu(
    '查询抽卡记录',
    '抽卡记录',
    '查询你的原神抽卡记录',
    detail_des=(
        '介绍：\n'
        '查询你的原神抽卡记录\n'
        '需要<ft color=(238,120,0)>绑定Stoken</ft>\n'
        ' \n'
        '指令：\n'
        '<ft color=(238,120,0)>抽卡记录</ft>'
    ),
)
async def send_gacha_log_card_info(
    event: TextMessageEvent,
    matcher: Matcher,
):
    logger.info('开始执行[抽卡记录]')

    uid = await select_db(event.from_wxid, mode='uid')
    if isinstance(uid, str):
        im = await draw_gachalogs_img(uid, event.from_wxid)  # type: ignore
        if isinstance(im, bytes):
            await matcher.finish(MessageSegment.image(im))
        else:
            await matcher.finish(im)
    else:
        await matcher.finish(UID_HINT)


@get_gacha_log.handle()
@handle_exception('刷新抽卡记录')
@register_menu(
    '刷新抽卡记录',
    '刷新抽卡记录',
    '刷新你的原神抽卡记录本地缓存',
    detail_des=(
        '介绍：\n'
        '刷新你的原神抽卡记录本地缓存\n'
        '需要<ft color=(238,120,0)>绑定Stoken</ft>\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>刷新抽卡记录</ft>'
    ),
)
async def send_daily_info(
    event: TextMessageEvent,
    matcher: Matcher,
):
    logger.info('开始执行[刷新抽卡记录]')
    wxid_list = []
    wxid_list.append(event.from_wxid)
    uid = await select_db(event.from_wxid, mode='uid')
    if isinstance(uid, str):
        is_force = False
        if event.msg.startswith('强制'):
            is_force = True
        tip = '正在刷新抽卡记录，请耐心等待，不要重复发送命令。'
        await matcher.send(
            MessageSegment.room_at_msg(content=tip, at_list=wxid_list)
        )
        im = await save_gachalogs(uid, None, is_force)
        await matcher.finish(im)
    else:
        await matcher.finish(UID_HINT)

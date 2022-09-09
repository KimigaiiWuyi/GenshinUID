from typing import Union

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import get_bot, on_notice, on_command
from nonebot.adapters.onebot.v11 import (
    NoticeEvent,
    MessageSegment,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from .get_gachalogs import save_gachalogs
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from .draw_gachalogs import draw_gachalogs_img
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..utils.exception.handle_exception import handle_exception
from .export_and_import import export_gachalogs, import_gachalogs

get_gacha_log = on_command('刷新抽卡记录', rule=FullCommand())
get_gacha_log_card = on_command('抽卡记录', rule=FullCommand())
import_gacha_log = on_notice()
export_gacha_log = on_command('导出抽卡记录', rule=FullCommand())


@export_gacha_log.handle()
@handle_exception('导出抽卡记录')
async def export_gacha_log_info(
    event: GroupMessageEvent,
    matcher: Matcher,
):

    logger.info('开始执行[导出抽卡记录]')
    qid = event.user_id
    gid = event.group_id
    uid = await select_db(qid, mode='uid')
    bot = get_bot()
    if not isinstance(uid, str) or '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)
    raw_data = await export_gachalogs(uid)
    if raw_data['retcode'] == 'ok':
        await bot.call_api(
            'upload_group_file',
            group_id=gid,
            name=raw_data['name'],
            file=raw_data['url'],
        )
        logger.info(f'[导出抽卡记录] UID{uid}成功!')
        await matcher.finish('上传成功!')
    else:
        logger.warning(f'[导出抽卡记录] UID{uid}失败!')
        await matcher.finish('导出抽卡记录失败!')


@import_gacha_log.handle()
@handle_exception('导入抽卡记录')
async def import_gacha_log_info(event: NoticeEvent, matcher: Matcher):
    args = event.dict()
    if args['notice_type'] != 'offline_file':
        await matcher.finish()
    url = args['file']['url']
    name: str = args['file']['name']
    if not name.endswith('.json'):
        return
    qid = args['user_id']
    uid = await select_db(qid, mode='uid')
    if not isinstance(uid, str) or '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)
    logger.info('开始执行[导入抽卡记录]')
    im = await import_gachalogs(url, uid)
    await matcher.finish(im)


@get_gacha_log_card.handle()
@handle_exception('抽卡记录')
@register_menu(
    '查询抽卡记录',
    '抽卡记录',
    '查询你的原神抽卡记录',
    detail_des=(
        '指令：'
        '<ft color=(238,120,0)>抽卡记录</ft>\n'
        ' \n'
        '查询你的原神抽卡记录\n'
        '需要<ft color=(238,120,0)>绑定Stoken</ft>'
    ),
)
async def send_gacha_log_card_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
):
    logger.info('开始执行[抽卡记录]')

    uid = await select_db(event.user_id, mode='uid')
    if isinstance(uid, str):
        im = await draw_gachalogs_img(uid)
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
        '指令：'
        '<ft color=(238,120,0)>刷新抽卡记录</ft>\n'
        ' \n'
        '刷新你的原神抽卡记录本地缓存\n'
        '需要<ft color=(238,120,0)>绑定Stoken</ft>'
    ),
)
async def send_daily_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
):
    logger.info('开始执行[刷新抽卡记录]')
    uid = await select_db(event.user_id, mode='uid')
    if isinstance(uid, str):
        im = await save_gachalogs(uid)
        await matcher.finish(im)
    else:
        await matcher.finish(UID_HINT)

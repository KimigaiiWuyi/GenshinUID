from .get_gachalogs import save_gachalogs
from ..all_import import *  # noqa: F403,F401
from .draw_gachalogs import draw_gachalogs_img
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.message.error_reply import *  # noqa: F403,F401
from .export_and_import import export_gachalogs, import_gachalogs


@sv.on_notice()
async def import_gacha_log_info(session: NoticeSession):
    ev = session.event
    if ev['notice_type'] != 'offline_file':
        return
    url = ev['file']['url']
    name: str = ev['file']['name']
    if not name.endswith('.json'):
        return
    qid = ev['user_id']
    uid = await select_db(qid, mode='uid')
    if not isinstance(uid, str) or '未找到绑定的UID' in uid:
        await session.send(UID_HINT)
        return
    logger.info('开始执行[导入抽卡记录]')
    im = await import_gachalogs(url, uid)
    await session.send(im, at_sender=True)


@sv.on_fullmatch('导出抽卡记录')
async def export_gacha_log_info(bot: HoshinoBot, ev: CQEvent):
    logger.info('开始执行[导出抽卡记录]')
    qid = int(ev.sender['user_id'])
    gid = int(ev.group_id)
    uid = await select_db(qid, mode='uid')
    bot = get_bot()
    if not isinstance(uid, str) or '未找到绑定的UID' in uid:
        await bot.send(ev, UID_HINT)
        return
    raw_data = await export_gachalogs(uid)
    if raw_data['retcode'] == 'ok':
        await bot.call_action(
            action='upload_group_file',
            group_id=gid,
            name=raw_data['name'],
            file=raw_data['url'],
        )
        logger.info(f'[导出抽卡记录] UID{uid}成功!')
        await bot.send(ev, '上传成功!')
    else:
        logger.warning(f'[导出抽卡记录] UID{uid}失败!')
        await bot.send(ev, '导出抽卡记录失败!')


@sv.on_fullmatch('抽卡记录')
async def send_gacha_log_card_info(bot: HoshinoBot, ev: CQEvent):
    logger.info('开始执行[抽卡记录]')
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return
    uid = await select_db(qid, mode='uid')

    if isinstance(uid, str):
        im = await draw_gachalogs_img(uid)
        if isinstance(im, bytes):
            im = await convert_img(im)
            await bot.send(ev, im)
        else:
            await bot.send(ev, im)
    else:
        await bot.send(ev, UID_HINT)


@sv.on_fullmatch('刷新抽卡记录')
async def send_daily_info(bot: HoshinoBot, ev: CQEvent):
    logger.info('开始执行[刷新抽卡记录]')
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return
    uid = await select_db(qid, mode='uid')
    if isinstance(uid, str):
        im = await save_gachalogs(uid)
        await bot.send(ev, im)
    else:
        await bot.send(ev, UID_HINT)

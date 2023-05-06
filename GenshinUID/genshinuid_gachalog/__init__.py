from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.utils.error_reply import UID_HINT

from ..utils.convert import get_uid
from ..utils.database import get_sqla
from .get_gachalogs import save_gachalogs
from .draw_gachalogs import draw_gachalogs_img
from .export_and_import import export_gachalogs, import_gachalogs
from .lelaer_tools import (
    get_gachaurl,
    get_lelaer_gachalog,
    export_gachalog_to_lelaer,
)

sv_gacha_log = SV('抽卡记录')
sv_refresh_gacha_log = SV('刷新抽卡记录')
sv_export_gacha_log = SV('导出抽卡记录')
sv_import_gacha_log = SV('导入抽卡记录', area='DIRECT')
sv_import_lelaer_gachalog = SV('从小助手导入抽卡记录')
sv_export_lelaer_gachalog = SV('导出抽卡记录到小助手')
sv_export_gachalogurl = SV('导出抽卡记录链接', area='DIRECT')


@sv_import_gacha_log.on_file('json')
async def send_import_gacha_info(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    if ev.file and ev.file_type:
        await bot.send('正在尝试导入抽卡记录中，请耐心等待……')
        return await bot.send(
            await import_gachalogs(ev.file, ev.file_type, uid)
        )
    else:
        return await bot.send('导入抽卡记录异常...')


@sv_gacha_log.on_fullmatch(('抽卡记录'))
async def send_gacha_log_card_info(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[抽卡记录]')
    uid, user_id = await get_uid(bot, ev, True)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_gachalogs_img(uid, user_id)
    await bot.send(im)


@sv_refresh_gacha_log.on_fullmatch(('刷新抽卡记录', '强制刷新抽卡记录'))
async def send_refresh_gacha_info(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[刷新抽卡记录]')
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    is_force = False
    if ev.command.startswith('强制'):
        await bot.logger.info('[WARNING]本次为强制刷新')
        is_force = True
    await bot.send(f'UID{uid}开始执行[刷新抽卡记录],需要一定时间...请勿重复触发！')
    im = await save_gachalogs(uid, None, is_force)
    await bot.send(im)


@sv_export_gacha_log.on_fullmatch(('导出抽卡记录'))
async def send_export_gacha_info(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[导出抽卡记录]')
    sqla = get_sqla(ev.bot_id)
    uid = await sqla.get_bind_uid(ev.user_id)
    if uid is None:
        return await bot.send(UID_HINT)
    export = await export_gachalogs(uid)
    if export['retcode'] == 'ok':
        file_name = export['name']
        file_path = export['url']
        return await bot.send(MessageSegment.file(file_path, file_name))
    else:
        return await bot.send('导出抽卡记录失败...')


@sv_import_lelaer_gachalog.on_fullmatch(('从小助手导入抽卡记录'))
async def import_lelaer_gachalog(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[从小助手导入抽卡记录]')
    sqla = get_sqla(ev.bot_id)
    uid = await sqla.get_bind_uid(ev.user_id)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await get_lelaer_gachalog(uid)
    await bot.send(im)


@sv_export_lelaer_gachalog.on_fullmatch(('导出抽卡记录到小助手'))
async def export_to_lelaer_gachalog(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[导出抽卡记录到小助手]')
    sqla = get_sqla(ev.bot_id)
    uid = await sqla.get_bind_uid(ev.user_id)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await export_gachalog_to_lelaer(uid)
    await bot.send(im)


@sv_export_gachalogurl.on_fullmatch(('导出抽卡记录链接', '导出抽卡记录连接'))
async def export_gachalogurl(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[导出抽卡记录链接]')
    sqla = get_sqla(ev.bot_id)
    uid = await sqla.get_bind_uid(ev.user_id)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await get_gachaurl(uid)
    await bot.send(MessageSegment.node([MessageSegment.text(im)]))

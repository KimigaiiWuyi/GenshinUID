from .get_gachalogs import save_gachalogs
from ..all_import import *  # noqa: F403,F401
from .draw_gachalogs import draw_gachalogs_img
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.message.error_reply import *  # noqa: F403,F401
from ..utils.mhy_api.get_mhy_data import get_gacha_log_by_authkey


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

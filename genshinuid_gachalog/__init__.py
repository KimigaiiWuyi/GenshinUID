from .get_gachalogs import save_gachalogs
from ..all_import import *  # noqa: F403,F401
from .draw_gachalogs import draw_gachalogs_img
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.message.error_reply import *  # noqa: F403,F401
from ..utils.mhy_api.get_mhy_data import get_gacha_log_by_authkey

get_gacha_log = on_command('刷新抽卡记录')
get_gacha_log_card = on_command('抽卡记录')


@get_gacha_log_card.handle()
@handle_exception('抽卡记录')
async def send_gacha_log_card_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    custom: ImageAndAt = Depends(),
    args: Tuple[Any, ...] = CommandArg(),
):
    logger.info('开始执行[抽卡记录]')
    if args:
        return
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
async def send_daily_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    custom: ImageAndAt = Depends(),
    args: Tuple[Any, ...] = CommandArg(),
):
    logger.info('开始执行[刷新抽卡记录]')
    if args:
        return
    uid = await select_db(event.user_id, mode='uid')
    if isinstance(uid, str):
        im = await save_gachalogs(uid)
        await matcher.finish(im)
    else:
        await matcher.finish(UID_HINT)

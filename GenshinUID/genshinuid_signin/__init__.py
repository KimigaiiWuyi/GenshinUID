from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.aps import scheduler
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import UID_HINT
from gsuid_core.utils.database.models import GsBind
from gsuid_core.utils.sign.sign import sign_in, daily_sign
from gsuid_core.utils.boardcast.send_msg import send_board_cast_msg

from ..genshinuid_config.gs_config import gsconfig

SIGN_TIME = gsconfig.get_config('SignTime').data
IS_REPORT = gsconfig.get_config('PrivateSignReport').data

sv_sign = SV('原神签到')
sv_sign_config = SV('原神签到管理', pm=2)


# 每日零点半执行米游社原神签到
@scheduler.scheduled_job('cron', hour=SIGN_TIME[0], minute=SIGN_TIME[1])
async def sign_at_night():
    if gsconfig.get_config('SchedSignin').data:
        await send_daily_sign()


# 群聊内 签到 功能
@sv_sign.on_fullmatch('签到')
async def get_sign_func(bot: Bot, ev: Event):
    await bot.logger.info('[原神] [签到]QQ号: {}'.format(ev.user_id))
    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[原神] [签到]UID: {}'.format(uid))
    await bot.send(await sign_in(uid, 'gs'))


@sv_sign_config.on_fullmatch('全部重签')
async def recheck(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[全部重签]')
    await bot.send('[原神] [全部重签] 已开始执行...')
    await send_daily_sign()
    await bot.send('[原神] [全部重签] 执行完成！')


async def send_daily_sign():
    logger.info('[原神] 开始执行[每日全部签到]')
    # 执行签到 并获得推送消息
    result = await daily_sign('gs')
    if not IS_REPORT:
        result['private_msg_dict'] = {}
    await send_board_cast_msg(result)
    logger.info('[原神] [每日全部签到]群聊推送完成')

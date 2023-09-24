from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.aps import scheduler
from gsuid_core.utils.error_reply import UID_HINT
from gsuid_core.utils.database.models import GsBind

from .get_draw import post_my_draw
from .daily_check_draw import daily_get_draw
from ..genshinuid_config.gs_config import gsconfig

sv_post_my_draw = SV('留影叙佳期')
sv_post_my_draw_admin = SV('自动留影叙佳期', pm=1)

DRAW_TIME = gsconfig.get_config('GetDrawTaskTime').data


# 群聊内 每月统计 功能
@sv_post_my_draw.on_fullmatch(('留影叙佳期', '原神画片'))
async def send_postdraw_data(bot: Bot, ev: Event):
    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return UID_HINT
    await bot.send(await post_my_draw(uid))


@sv_post_my_draw_admin.on_fullmatch(('强制进行自动留影叙佳期'))
async def send_all_postdraw_data(bot: Bot, ev: Event):
    await daily_get_draw()


# 执行自动留影叙佳期
@scheduler.scheduled_job('cron', hour=DRAW_TIME[0], minute=DRAW_TIME[1])
async def postdraw_sign_at_night():
    if gsconfig.get_config('SchedGetDraw').data:
        await daily_get_draw()

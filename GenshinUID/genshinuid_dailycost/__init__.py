from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.aps import scheduler
from gsuid_core.logger import logger

from .draw_daily_cost import draw_daily_cost_img

sv_daily_cost = SV('查询每日材料')


@sv_daily_cost.on_command(('每日材料', '今日材料', '每日素材', '今日素材'), block=True)
async def send_collection_info(bot: Bot, ev: Event):
    logger.info('开始执行[每日材料]')
    im = await draw_daily_cost_img()
    await bot.send(im)


# 每日四点出头执行刷新材料图
@scheduler.scheduled_job('cron', hour=4, minute=1)
async def refresh_daily_cost():
    await draw_daily_cost_img(True)

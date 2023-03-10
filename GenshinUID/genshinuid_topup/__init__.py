from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .gs_topup import topup_


@SV('原神充值').on_fullmatch(('gsrc', '原神充值'))
async def send_qrcode_login(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[原神充值]')
    goods_id = int(ev.text) if ev.text.isdigit() else None
    if goods_id is None:
        return await bot.send('请输入正确的商品编号(1~6), 例如原神充值6!')
    await topup_(bot, ev.bot_id, ev.user_id, ev.group_id, ev.text)

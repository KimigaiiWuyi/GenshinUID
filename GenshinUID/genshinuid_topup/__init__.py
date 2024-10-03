from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .gs_topup import GOODS, topup_
from ..genshinuid_config.gs_config import gsconfig

sv_topup = SV('原神充值')

INPUTTIP = '''请输入正确的商品编号(0~6), 如:原神充值6
也可以直接输入物品名称或价格，如:原神充值月卡 | pay648'''


@sv_topup.on_command(('原神充值', 'pay'))
async def send_qrcode_login(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[原神充值]')
    value = ev.text
    for _k in ['微信', 'wx', 'ali', 'pay', 'zfb', '支付', '支付宝']:
        value = value.replace(_k, '')

    # 判断支付方式
    if '微信' in ev.text or 'wx' in ev.text:
        method = 'weixin'
    elif '支付宝' in ev.text or 'zfb' in ev.text:
        method = 'alipay'
    else:
        if gsconfig.get_config('DefaultPayWX').data:
            method = 'weixin'
        else:
            method = 'alipay'

    # 输入物品别名识别
    goods_id = None
    for gId, gData in GOODS.items():
        if (value.isdigit() and int(value) == gId) or (
            value in gData['aliases']
        ):
            goods_id = gId
            break

    if goods_id is None:
        return await bot.send(INPUTTIP)

    if ev.group_id is None:
        gid = 'direct'
    else:
        gid = ev.group_id

    await topup_(bot, ev.bot_id, ev.user_id, gid, goods_id, method)

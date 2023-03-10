import io
import base64
import asyncio
import traceback

import qrcode
from gsuid_core.bot import Bot
from nonebot.log import logger
from qrcode import ERROR_CORRECT_L
from gsuid_core.segment import MessageSegment

from ..utils.mys_api import mys_api
from ..utils.database import get_sqla
from ..utils.error_reply import get_error
from ..gsuid_utils.api.mys.models import MysOrder

disnote = '''免责声明:
该充值接口由米游社提供,不对充值结果负责。
请在充值前仔细阅读米哈游的充值条款。
'''


def get_qrcode_base64(url: str):
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    img_byte = io.BytesIO()
    img.save(img_byte, format='PNG')  # type:ignore
    img_byte = img_byte.getvalue()
    return base64.b64encode(img_byte).decode()


async def refresh(order: MysOrder, uid: str) -> str:
    times = 0
    while True:
        await asyncio.sleep(5)
        order_status = await mys_api.check_order(order, uid)
        if isinstance(order_status, int):
            return get_error(order_status)
        if order_status['status'] != 900:
            pass
        else:
            return '支付成功'
        times += 1
        if times > 60:
            return '支付超时'


async def topup_(
    bot: Bot, bot_id: str, user_id: str, group_id: str, goods_id: int
):
    sqla = get_sqla(bot_id)
    uid = await sqla.get_bind_uid(user_id)
    if uid is None:
        return await bot.send('未绑定米游社账号')
    fetchgoods_data = await mys_api.get_fetchgoods()
    if isinstance(fetchgoods_data, int):
        return await bot.send(get_error(fetchgoods_data))
    if goods_id < len(fetchgoods_data):
        goods_data = fetchgoods_data[goods_id]
    else:
        return await bot.send('商品不存在,最大为' + str(len(fetchgoods_data) - 1))
    order = await mys_api.topup(uid, goods_data)
    if isinstance(order, int):
        logger.warning(f'[充值] {group_id} {user_id} 出错！')
        return await bot.send(get_error(order))
    try:
        im = []
        b64_data = get_qrcode_base64(order['encode_order'])
        qrc = MessageSegment.image(b64_data)
        im.append(MessageSegment.text(f'充值uid：{uid}'))
        im.append(
            MessageSegment.text(
                f'商品名称：{goods_data["goods_name"]}×{goods_data["goods_unit"]}'
                if int(goods_data['goods_unit']) > 0
                else goods_data['goods_name']
            ),
        )
        im.append(MessageSegment.text(f'商品价格：{int(order["amount"])/100}'))
        im.append(MessageSegment.text(f'订单号：{order["order_no"]}'))
        im.append(MessageSegment.text(disnote))
        im.append(MessageSegment.text(qrc))
        return await bot.send(MessageSegment.node(im))
    except Exception:
        traceback.print_exc()
        logger.warning(f'[充值] {group_id} 图片发送失败')
    return await bot.send(await refresh(order, uid))

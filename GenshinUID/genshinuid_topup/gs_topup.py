import io
import base64
import asyncio
import traceback
from typing import Literal
from time import strftime, localtime

import qrcode
from gsuid_core.bot import Bot
from qrcode import ERROR_CORRECT_L
from gsuid_core.logger import logger
from gsuid_core.segment import MessageSegment

from ..utils.mys_api import mys_api
from ..utils.database import get_sqla
from ..utils.error_reply import get_error
from .draw_topup_img import draw_wx, draw_ali
from ..gsuid_utils.api.mys.models import MysOrder

disnote = '''免责声明:
该充值接口由米游社提供,不对充值结果负责。
请在充值前仔细阅读米哈游的充值条款。'''

GOODS = {
    0: {
        'title': '创世结晶×60',
        'aliases': ['创世结晶x60', '结晶×60', '结晶x60', '创世结晶60', '结晶60'],
    },
    1: {
        'title': '创世结晶×300',
        'aliases': ['创世结晶x300', '结晶×300', '结晶x300', '创世结晶300', '结晶300', '30'],
    },
    2: {
        'title': '创世结晶×980',
        'aliases': ['创世结晶x980', '结晶×980', '结晶x980', '创世结晶980', '结晶980', '98'],
    },
    3: {
        'title': '创世结晶×1980',
        'aliases': [
            '创世结晶x1980',
            '结晶×1980',
            '结晶x1980',
            '创世结晶1980',
            '结晶1980',
            '198',
        ],
    },
    4: {
        'title': '创世结晶×3280',
        'aliases': [
            '创世结晶x3280',
            '结晶×3280',
            '结晶x3280',
            '创世结晶3280',
            '结晶3280',
            '328',
        ],
    },
    5: {
        'title': '创世结晶×6480',
        'aliases': [
            '创世结晶x6480',
            '结晶×6480',
            '结晶x6480',
            '创世结晶6480',
            '结晶6480',
            '648',
        ],
    },
    6: {
        'title': '空月祝福',
        'aliases': ['空月', '祝福', '月卡', '小月卡'],
    },
}


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


async def refresh(order: MysOrder, uid: str, order_id: str) -> str:
    times = 0
    while True:
        await asyncio.sleep(5)
        order_status = await mys_api.check_order(order, uid)
        if isinstance(order_status, int):
            return get_error(order_status)
        if order_status['status'] != 900:
            pass
        else:
            return f'UID{uid}支付成功, 订单号{order_id}'
        times += 1
        if times > 60:
            return f'UID{uid}支付超时, 订单号{order_id}'


async def topup_(
    bot: Bot,
    bot_id: str,
    user_id: str,
    group_id: str,
    goods_id: int,
    method: Literal['weixin', 'alipay'],
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
    order = await mys_api.topup(uid, goods_data, method)
    if isinstance(order, int):
        logger.warning(f'[充值] {group_id} {user_id} 出错！')
        return await bot.send(get_error(order))
    try:
        b64_data = get_qrcode_base64(order['encode_order'])
        img_b64decode = base64.b64decode(b64_data)
        qrimage = io.BytesIO(img_b64decode)  # 二维码
        item_icon_url = goods_data['goods_icon']  # 图标
        item_id = goods_data['goods_id']  # 商品内部id
        item_pay_url = order['encode_order']  # 支付链接
        item_name_full = (
            f"{goods_data['goods_name']}×{goods_data['goods_unit']}"
        )
        # 物品名字(非月卡)
        item_name = (
            item_name_full
            if int(goods_data['goods_unit']) > 0
            else goods_data["goods_name"]
        )
        # 物品名字
        item_price: str = order["currency"] + str(
            int(order["amount"]) / 100
        )  # 价格
        item_order_no = order['order_no']  # 订单号
        item_create_time = order['create_time']  # 创建时间
        timestamp = strftime(
            '%Y-%m-%d %H:%M:%S', localtime(int(item_create_time))
        )  # 年月日时间

        if method == 'alipay':
            img_data = await draw_ali(
                uid,
                item_name,
                item_price,
                item_order_no,
                qrimage,
                item_icon_url,
                item_create_time,
                item_id,
            )
            await bot.send(img_data)
        else:
            img_data = await draw_wx(
                uid,
                item_name,
                item_price,
                item_order_no,
                qrimage,
                item_icon_url,
                item_create_time,
                item_id,
            )
            msg_text = f'【{item_name}】\nUID: {uid}\n时间: {timestamp}'
            msg_text2 = msg_text + f'\n\n{item_pay_url}\n\n{disnote}'
            msg_node = []
            msg_node.append(MessageSegment.text(msg_text2))
            msg_node.append(MessageSegment.image(img_data))
            await bot.send(MessageSegment.node(msg_node))
    except Exception:
        traceback.print_exc()
        logger.warning(f'[充值] {group_id} 图片发送失败')
    return await bot.send(await refresh(order, uid, order['order_no']))

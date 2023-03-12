import io
import base64
import asyncio
import traceback
from typing import List, NoReturn

import qrcode
from nonebot.log import logger
from nonebot.matcher import Matcher
from qrcode.constants import ERROR_CORRECT_L
from nonebot.adapters.ntchat import MessageSegment

from .draw_topup_img import draw_wx, draw_ali
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..utils.mhy_api.get_mhy_data import topup, checkorder, fetchgoods

disnote = '''免责声明：该充值接口由米游社提供，不对充值结果负责。
请在充值前仔细阅读米哈游的充值条款。'''

GOODS = {
    0: {
        "title": "创世结晶×60",
        "aliases": ["创世结晶x60", "结晶×60", "结晶x60", "创世结晶60", "结晶60"],
    },
    1: {
        "title": "创世结晶×300",
        "aliases": ["创世结晶x300", "结晶×300", "结晶x300", "创世结晶300", "结晶300", "30"],
    },
    2: {
        "title": "创世结晶×980",
        "aliases": ["创世结晶x980", "结晶×980", "结晶x980", "创世结晶980", "结晶980", "98"],
    },
    3: {
        "title": "创世结晶×1980",
        "aliases": [
            "创世结晶x1980",
            "结晶×1980",
            "结晶x1980",
            "创世结晶1980",
            "结晶1980",
            "198",
        ],
    },
    4: {
        "title": "创世结晶×3280",
        "aliases": [
            "创世结晶x3280",
            "结晶×3280",
            "结晶x3280",
            "创世结晶3280",
            "结晶3280",
            "328",
        ],
    },
    5: {
        "title": "创世结晶×6480",
        "aliases": [
            "创世结晶x6480",
            "结晶×6480",
            "结晶x6480",
            "创世结晶6480",
            "结晶6480",
            "648",
        ],
    },
    6: {
        "title": "空月祝福",
        "aliases": ["空月", "祝福", "月卡", "小月卡"],
    },
}


def get_qrcode_base64(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_byte = io.BytesIO()
    img.save(img_byte, format="PNG")  # type: ignore
    img_byte = img_byte.getvalue()
    return base64.b64encode(img_byte).decode()


async def refresh(order, uid, oid):
    times = 0
    while True:
        await asyncio.sleep(5)
        order_status = await checkorder(order, uid)
        if order_status != 900:
            pass
        else:
            return "{$@}" + f"支付成功！\nUID:{uid}\n订单号:{oid}"
        times += 1
        if times > 60:
            return "{$@}" + f"支付超时！\nUID:{uid}\n订单号:{oid}"


async def topup_(matcher: Matcher, qid, group_id, goods_id, method):
    async def send_group_msg(msg: str, at_list: List) -> NoReturn:
        await matcher.finish(
            MessageSegment.room_at_msg(content=msg, at_list=at_list)
        )

    wxid_list = []
    wxid_list.append(qid)
    uid = await select_db(qid, mode="uid")
    if uid is None:
        await send_group_msg("{$@}" + UID_HINT, wxid_list)
    fetchgoods_data = await fetchgoods()
    try:
        goods_data = fetchgoods_data[goods_id]
    except Exception as e:
        logger.warning(f'[充值]错误 {e}')
        await send_group_msg(
            "{$@}商品不存在,最大为" + str(len(fetchgoods_data) - 1), wxid_list
        )
    try:
        order = await topup(uid, goods_data, method)
    except Exception as e:
        logger.warning(f"[充值] {group_id} {qid} 错误：{e}")
        await send_group_msg("{$@}出错了,可能是Cookie过期或接口出错。", wxid_list)
    try:
        b64_data = get_qrcode_base64(order["encode_order"])
        img_b64decode = base64.b64decode(b64_data)
        qrimage = io.BytesIO(img_b64decode)  # 二维码
        item_icon_url: str = goods_data['goods_icon']  # 图标
        item_id: str = goods_data['goods_id']  # 商品内部id
        item_pay_url: str = order['encode_order']  # 支付链接
        item_name_full = (
            f"{goods_data['goods_name']}×{str(goods_data['goods_unit'])}"
        )
        # 物品名字(非月卡)
        item_name: str = (
            item_name_full
            if int(goods_data['goods_unit']) > 0
            else goods_data["goods_name"]
        )
        # 物品名字
        item_price: str = order["currency"] + str(
            int(order["amount"]) / 100
        )  # 价格
        item_order_no: str = order['order_no']  # 订单号
        item_create_time: int = order['create_time']  # 创建时间

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
            return MessageSegment.image(img_data)
        else:
            img_data = await draw_wx(
                uid,
                item_name,
                item_price,
                item_order_no,
                item_icon_url,
                item_create_time,
                item_id,
            )
            msg_text = '{$@}' + f' UID：{uid}\n{item_name}\n{item_create_time}'
            msg_text2 = msg_text + f'\n\nZF：{item_pay_url}\n\n{disnote}'
            at_msg = MessageSegment.room_at_msg(
                content=msg_text2, at_list=wxid_list
            )
            return MessageSegment.image(img_data) + at_msg

    except Exception as e:
        traceback.print_exc()
        logger.warning(f"[充值] {group_id} 图片发送失败: {e}")
    await send_group_msg(
        await refresh(order, uid, order['order_no']), wxid_list
    )

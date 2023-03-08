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

from ..utils.db_operation.db_operation import select_db
from ..utils.mhy_api.get_mhy_data import topup, checkorder, fetchgoods

disnote = '''免责声明:
该充值接口由米游社提供,不对充值结果负责。
请在充值前仔细阅读米哈游的充值条款。
'''


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


async def refresh(order, uid):
    times = 0
    while True:
        await asyncio.sleep(5)
        order_status = await checkorder(order, uid)
        if order_status != 900:
            pass
        else:
            return "支付成功"
        times += 1
        if times > 60:
            return "支付超时"


async def topup_(matcher: Matcher, qid, group_id, goods_id):
    async def send_group_msg(msg: str, at_list: List) -> NoReturn:
        await matcher.finish(
            MessageSegment.room_at_msg(content=msg, at_list=at_list)
        )

    wxid_list = []
    wxid_list.append(qid)
    uid = await select_db(qid, mode="uid")
    if uid is None:
        await send_group_msg("未绑定米游社账号", wxid_list)
    fetchgoods_data = await fetchgoods()
    try:
        goods_data = fetchgoods_data[goods_id]
    except Exception:
        await send_group_msg(
            "商品不存在,最大为" + str(len(fetchgoods_data) - 1), wxid_list
        )
    try:
        order = await topup(uid, goods_data)
    except Exception:
        logger.warning(f"[充值] {group_id} {qid}")
        await send_group_msg("出错了,可能是cookie过期或接口出错", wxid_list)
    try:
        b64_data = get_qrcode_base64(order["encode_order"])
        qrc = f'[CQ:image,file=base64://{b64_data}]'
        await matcher.send(f"充值uid：{uid}")
        await matcher.send(
            f"商品名称：{goods_data['goods_name']}×{str(goods_data['goods_unit'])}"
            if int(goods_data['goods_unit']) > 0
            else goods_data["goods_name"],
        )
        await matcher.send(f'商品价格：{int(order["amount"])/100}')
        await matcher.send(f"订单号：{order['order_no']}")
        await matcher.send(disnote)
        await matcher.send(qrc)
    except Exception:
        traceback.print_exc()
        logger.warning(f"[充值] {group_id} 图片发送失败")
    await send_group_msg(await refresh(order, uid), wxid_list)

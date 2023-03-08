import io
import base64
import asyncio
import traceback

import qrcode
from nonebot.log import logger

from ..utils.message.send_msg import send_forward_msg
from ..utils.db_operation.db_operation import select_db
from ..utils.mhy_api.get_mhy_data import topup, checkorder, fetchgoods

disnote = '''免责声明:
该充值接口由米游社提供,不对充值结果负责。
请在充值前仔细阅读米哈游的充值条款。
'''


def get_qrcode_base64(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_byte = io.BytesIO()
    img.save(img_byte, format="PNG")
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


async def topup_(bot, qid, group_id, goods_id):
    async def send_group_msg(msg: str):
        await bot.call_action(
            action='send_group_msg',
            group_id=group_id,
            message=msg,
        )
        return ""

    uid = await select_db(qid, mode="uid")
    if uid is None:
        await send_group_msg("未绑定米游社账号")
        return
    fetchgoods_data = await fetchgoods()
    try:
        goods_data = fetchgoods_data[goods_id]
    except Exception:
        await send_group_msg("商品不存在,最大为" + str(len(fetchgoods_data) - 1))
        return
    try:
        order = await topup(uid, goods_data)
    except Exception:
        await send_group_msg("出错了,可能是cookie过期或接口出错")
        logger.warn(f"[充值] {group_id} {qid}")
        return
    try:
        im = []
        b64_data = get_qrcode_base64(order["encode_order"])
        qrc = f'[CQ:image,file=base64://{b64_data}]'
        im.append(f"充值uid：{uid}")
        im.append(
            f"商品名称：{goods_data['goods_name']}×{str(goods_data['goods_unit'])}"
            if int(goods_data['goods_unit']) > 0
            else goods_data["goods_name"],
        )
        im.append(f'商品价格：{int(order["amount"])/100}')
        im.append(f"订单号：{order['order_no']}")
        im.append(disnote)
        im.append(qrc)
        await send_forward_msg(bot, group_id, "小助手", str(qid), im)
    except Exception:
        traceback.print_exc()
        logger.warn(f"[充值] {group_id} 图片发送失败")
    await send_group_msg(await refresh(order, uid))

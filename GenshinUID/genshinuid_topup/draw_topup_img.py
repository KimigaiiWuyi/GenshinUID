from io import BytesIO
from typing import Literal
from time import strftime, localtime

from PIL import Image, ImageDraw

from ..utils.image.image_tools import get_pic
from ..utils.fonts.genshin_fonts import gs_font_12, gs_font_15, gs_font_25


async def draw_pay_img(
    uid: str,
    item_info: str,
    item_price: str,
    item_order_no: str,
    qrcode: BytesIO,
    item_icon: str,
    item_create_time: str,
    item_id: str,
    type: Literal['微信', '支付宝'],
):
    '''充值图片绘制'''
    itemImg = await get_pic(item_icon)
    left, top = 0, 0
    if type == '支付宝':
        themeColor = '#1678ff'
        res = Image.new('RGBA', (450, 530), themeColor)
    else:
        themeColor = '#29ac66'
        res = Image.new('RGBA', (450, 200), themeColor)
        left = (450 - 370) / 2  # (图片宽度 - 矩形宽度) / 2
        top = (200 - 130) / 2  # (图片高度 - 矩形高度) / 2
    warning = 20 if item_id == 'ys_chn_blessofmoon_tier5' else 0
    drawer = ImageDraw.Draw(res)
    resample = getattr(Image, 'Resampling', Image).LANCZOS

    if type == '支付宝':
        # 头部矩形背景
        drawer.rectangle(
            (75, 50 - warning, 375 - 1, 150 - warning), fill='#E5F9FF', width=0
        )
        # 商品图片
        item = itemImg.resize((90, 90), resample=resample)
        res.paste(item, (80, 55 - warning), item)
        # 二维码图片
        qrcode_img = Image.open(qrcode)
        qrcode_img = qrcode_img.resize((300, 300), resample=resample)
        res.paste(qrcode_img, (75, 150 + warning), qrcode_img)
        # 商品名称
        drawer.text(
            (
                int(175 + (195 - gs_font_25.getlength(item_info)) / 2),
                int(
                    70 - warning + (30 - gs_font_25.getbbox(item_info)[-1]) / 2
                ),
            ),
            item_info,
            fill='#000000',
            font=gs_font_25,
        )
        # 价格
        drawer.text(
            (
                int(175 + (195 - gs_font_25.getlength(item_price)) / 2),
                int(
                    105
                    - warning
                    + (30 - gs_font_25.getbbox(item_price)[-1]) / 2
                ),
            ),
            item_price,
            fill='#000000',
            font=gs_font_25,
        )
        # 商品充值 UID
        drawer.text(
            (
                int((460 - gs_font_15.getlength(f'充值到 UID{uid}')) / 2),
                int(
                    155
                    + warning
                    + (20 - gs_font_15.getbbox(f'充值到 UID{uid}')[-1]) / 2
                ),
            ),
            f'充值到 UID{uid}',
            fill='#333333',
            font=gs_font_15,
        )
        # 月卡相关商品警告
        if warning:
            # 首部矩形背景
            drawer.rectangle((75, 130, 375 - 1, 170), fill='#eeeeee', width=0)
            # 转换警告文字
            warning_text = '特殊情况将直接返还 330 创世结晶'
            drawer.text(
                (
                    int((450 - gs_font_15.getlength(warning_text)) / 2),
                    int(130 + (40 - gs_font_15.getbbox(warning_text)[-1]) / 2),
                ),
                warning_text,
                fill='#ff5652',
                font=gs_font_15,
            )
        # 图片生成时间
        timestamp = strftime(
            '%Y-%m-%d %H:%M:%S', localtime(int(item_create_time))
        )
        drawer.text(
            (
                int((460 - gs_font_15.getlength(timestamp)) / 2),
                425 + warning,
            ),
            timestamp,
            fill='#1678ff',
            font=gs_font_15,
        )
        # 账单信息
        ticket = f'{type}账单编号 {item_order_no}'
        high = 455 if warning else 460
        drawer.text(
            (
                int((450 - gs_font_15.getlength(ticket)) / 2),
                high + warning,
            ),
            ticket,
            fill='#ffffff',
            font=gs_font_15,
        )
        # 免责声明
        drawer.text(
            (
                int(
                    (
                        410
                        - gs_font_15.getlength(
                            '免责声明：该充值接口由米游社提供，不对充值结果负责。\n请在充值前仔细阅读米哈游的充值条款。'
                        )
                        / 2
                    )
                ),
                490 + warning / 3,
            ),
            '免责声明：该充值接口由米游社提供，不对充值结果负责。\n          请在充值前仔细阅读米哈游的充值条款。',
            fill='#FFA500',
            font=gs_font_12,
        )
    else:
        # 微信
        drawer.rectangle(
            (left, top - warning, left + 370, top + 130 - warning),
            fill='#E5F9FF',
            width=0,
        )
        item = itemImg.resize((110, 110), resample=resample)
        res.paste(item, (55, 50 - warning), item)
        # 商品名称
        drawer.text(
            (
                int(175 + (215 - gs_font_25.getlength(item_info)) / 2),
                int(
                    50 - warning + (30 - gs_font_25.getbbox(item_info)[-1]) / 2
                ),
            ),
            item_info,
            fill='#000000',
            font=gs_font_25,
        )
        # 商品价格
        drawer.text(
            (
                int(180 + (195 - gs_font_25.getlength(item_price)) / 2),
                int(
                    80
                    - warning
                    + (30 - gs_font_25.getbbox(item_price)[-1]) / 2
                ),
            ),
            item_price,
            fill='#000000',
            font=gs_font_25,
        )
        # 商品充值 UID
        drawer.text(
            (
                int(185 + (195 - gs_font_15.getlength(f'充值到 UID{uid}')) / 2),
                int(
                    120
                    - warning
                    + (20 - gs_font_15.getbbox(f'充值到 UID{uid}')[-1]) / 2
                ),
            ),
            f'充值到 UID{uid}',
            fill='#333333',
            font=gs_font_15,
        )
        # 月卡相关商品警告
        if warning:
            # 首部矩形背景
            drawer.rectangle(
                (left, top + 110, left + 370, top + 130),
                fill="#eeeeee",
                width=0,
            )
            # 转换警告文字
            warning_text = '特殊情况将直接返还 330 创世结晶'
            drawer.text(
                (
                    int((450 - gs_font_15.getlength(warning_text)) / 2),
                    int(135 + (40 - gs_font_15.getbbox(warning_text)[-1]) / 2),
                ),
                warning_text,
                fill='#ff5652',
                font=gs_font_15,
            )
        # 图片生成时间
        timestamp = strftime(
            '%Y-%m-%d %H:%M:%S', localtime(int(item_create_time))
        )
        drawer.text(
            (
                int(185 + (195 - gs_font_15.getlength(timestamp)) / 2),
                140 - warning,
            ),
            timestamp,
            fill='#29ac66',
            font=gs_font_15,
        )
        # 账单信息
        ticket = f'{type}账单编号 {item_order_no}'
        drawer.text(
            (
                int((450 - gs_font_15.getlength(ticket)) / 2),
                170,
            ),
            ticket,
            fill='#ffffff',
            font=gs_font_15,
        )

    buf = BytesIO()
    res.convert('RGB').save(buf, format='PNG')
    return buf.getvalue()


# 支付宝充值图片绘制
async def draw_ali(
    uid: str,
    item_info: str,
    item_price: str,
    item_order_no: str,
    qrcode: BytesIO,
    item_icon: str,
    item_create_time: str,
    item_id: str,
) -> bytes:
    return await draw_pay_img(
        uid,
        item_info,
        item_price,
        item_order_no,
        qrcode,
        item_icon,
        item_create_time,
        item_id,
        '支付宝',
    )


# 微信充值图片绘制
async def draw_wx(
    uid: str,
    item_info: str,
    item_price: str,
    item_order_no: str,
    qrcode: BytesIO,
    item_icon: str,
    item_create_time: str,
    item_id: str,
) -> bytes:
    return await draw_pay_img(
        uid,
        item_info,
        item_price,
        item_order_no,
        qrcode,
        item_icon,
        item_create_time,
        item_id,
        '微信',
    )

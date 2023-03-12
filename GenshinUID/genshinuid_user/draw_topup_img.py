from io import BytesIO
from time import strftime, localtime

from httpx import AsyncClient
from PIL import Image, ImageDraw, ImageFont

from ..utils.genshin_fonts.genshin_fonts import FONT_ORIGIN_PATH


def font(size: int) -> ImageFont.FreeTypeFont:
    """Pillow 绘制字体设置"""
    return ImageFont.truetype(str(FONT_ORIGIN_PATH), size=size)

# 支付宝充值图片绘制
async def draw_ali(
    uid, 
    item_info: str, 
    item_price: str, 
    item_order_no: str, 
    qrcode, 
    item_icon: str, 
    item_create_time: int,
    item_id: str
) -> bytes:
    #    itemId: str, item: Image.Image, qrcode: Image.Image, info: Dict[str, str]
    """充值图片绘制"""
    async with AsyncClient() as client:
        _img = await client.get(item_icon, timeout=10.0)
        itemImg = Image.open(BytesIO(_img.content)).convert("RGBA")

    themeColor = "#1678ff"
    warning = 20 if item_id == 'ys_chn_blessofmoon_tier5' else 0
    res = Image.new("RGBA", (450, 530), themeColor)
    drawer = ImageDraw.Draw(res)
    resample = getattr(Image, "Resampling", Image).LANCZOS

    # 头部矩形背景
    drawer.rectangle((75, 50 - warning, 375 - 1, 150 -
                     warning), fill="#E5F9FF", width=0)
    # 商品图片
    item = itemImg.resize((90, 90), resample=resample)
    res.paste(item, (80, 55 - warning), item)
    # 二维码图片
    qrcode = Image.open(qrcode)
    qrcode = qrcode.resize((300, 300), resample=resample)
    res.paste(qrcode, (75, 150 + warning), qrcode)
    # 商品名称
    drawer.text(
        (
            int(175 + (195 - font(25).getlength(item_info)) / 2),
            int(70 - warning + (30 - font(25).getbbox(item_info)[-1]) / 2),
        ),
        item_info,
        fill="#000000",
        font=font(25),
    )
    # 价格
    drawer.text(
        (
            int(175 + (195 - font(25).getlength(item_price)) / 2),
            int(105 - warning + (30 - font(25).getbbox(item_price)[-1]) / 2),
        ),
        item_price,
        fill="#000000",
        font=font(25),
    )
    # 商品充值 UID
    drawer.text(
        (
            int((460 - font(15).getlength(f"充值到 UID{uid}")) / 2),
            int(155 + warning +
                (20 - font(15).getbbox(f"充值到 UID{uid}")[-1]) / 2),
        ),
        f"充值到 UID{uid}",
        fill="#333333",
        font=font(15),
    )
    # 月卡相关商品警告
    if warning:
        # 首部矩形背景
        drawer.rectangle((75, 130, 375 - 1, 170), fill="#eeeeee", width=0)
        # 转换警告文字
        warning_text = f"特殊情况将直接返还 330 创世结晶"
        drawer.text(
            (
                int((450 - font(15).getlength(warning_text)) / 2),
                int(130 + (40 - font(15).getbbox(warning_text)[-1]) / 2),
            ),
            warning_text,
            fill="#ff5652",
            font=font(15),
        )
    # 图片生成时间
    timestamp = strftime("%Y-%m-%d %H:%M:%S", localtime(int(item_create_time)))
    drawer.text(
        (int((460 - font(15).getlength(timestamp)) / 2), 425 + warning),
        timestamp,
        fill="#1678ff",
        font=font(15),
    )
    # 账单信息
    ticket = f"支付宝账单编号 {item_order_no}"
    drawer.text(
        (int((450 - font(15).getlength(ticket)) / 2), 460 + warning),
        ticket,
        fill="#ffffff",
        font=font(15),
    )
    # 免责声明
    drawer.text(
        (int((410 - font(15).getlength("免责声明：该充值接口由米游社提供，不对充值结果负责。\n请在充值前仔细阅读米哈游的充值条款。") / 2)), 
        490 + warning
    ),
    "免责声明：该充值接口由米游社提供，不对充值结果负责。\n          请在充值前仔细阅读米哈游的充值条款。",
    fill="#FFA500",
    font=font(12),
    )
    buf = BytesIO()
    res.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()

# 微信充值图片绘制
async def draw_wx(
    uid, 
    item_info: str, 
    item_price: str, 
    item_order_no: str, 
    item_icon: str, 
    item_create_time: int,
    item_id: str
) -> bytes:
    """充值图片绘制"""
    async with AsyncClient() as client:
        _img = await client.get(item_icon, timeout=10.0)
        itemImg = Image.open(BytesIO(_img.content)).convert("RGBA")


    themeColor = "#29ac66"
    warning = 20 if item_id == 'ys_chn_blessofmoon_tier5' else 0
    res = Image.new("RGBA", (450, 200), themeColor)
    drawer = ImageDraw.Draw(res)
    resample = getattr(Image, "Resampling", Image).LANCZOS
    left = (450 - 370) / 2  # (图片宽度 - 矩形宽度) / 2
    top = (200 - 130) / 2  # (图片高度 - 矩形高度) / 2
    # 头部矩形背景
    drawer.rectangle((left, top - warning, left + 370, top + 130 - warning),  # 使用新的左上角和右下角的坐标
                     fill="#E5F9FF",  # 保留原有的填充色
                     width=0,  # 保留原有的边框宽度
                     )

    # 商品图片
    item = itemImg.resize((110, 110), resample=resample)
    res.paste(item, (55, 50 - warning), item)
    # 商品名称
    drawer.text(
        (
            int(175 + (215 - font(25).getlength(item_info)) / 2),
            int(50 - warning + (30 - font(25).getbbox(item_info)[-1]) / 2),
        ),
        item_info,
        fill="#000000",
        font=font(25),
    )
    # 价格
    drawer.text(
        (
            int(180 + (195 - font(25).getlength(item_price)) / 2),
            int(80 - warning + (30 - font(25).getbbox(item_price)[-1]) / 2),
        ),
        item_price,
        fill="#000000",
        font=font(25),
    )
    # 商品充值 UID
    drawer.text(
        (
            int(185 + (195 - font(15).getlength(f"充值到 UID{uid}")) / 2),
            int(120 - warning +
                (20 - font(15).getbbox(f"充值到 UID{uid}")[-1]) / 2),
        ),
        f"充值到 UID{uid}",
        fill="#000000",
        font=font(15),
    )
    # 图片生成时间
    timestamp = strftime("%Y-%m-%d %H:%M:%S", localtime(int(item_create_time)))
    drawer.text(
        (int(185 + (195 - font(15).getlength(timestamp)) / 2), 140 - warning),
        timestamp,
        fill="#29ac66",
        font=font(15),
    )
    if warning:
        # 首部矩形背景
        drawer.rectangle((left, top + 110, left + 370,
                         top + 130), fill="#eeeeee", width=0)
        # 转换警告文字
        warning_text = f"特殊情况将直接返还 330 创世结晶"
        drawer.text(
            (
                int((450 - font(15).getlength(warning_text)) / 2),
                int(135 + (40 - font(15).getbbox(warning_text)[-1]) / 2),
            ),
            warning_text,
            fill="#ff5652",
            font=font(15),
        )
    # 账单信息
    ticket = f"微信支付账单编号 {item_order_no}"
    drawer.text(
        (int((450 - font(15).getlength(ticket)) / 2), 170),
        ticket,
        fill="#ffffff",
        font=font(15),
    )
    buf = BytesIO()
    res.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()

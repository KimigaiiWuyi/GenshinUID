from pathlib import Path

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.message_models import Button

from ..version import Genshin_version
from ..utils.image.convert import convert_img

PRIMOGEMS_DATA_PATH = Path(__file__).parent / 'primogems_data'
IMG_PATH = Path(__file__).parent / 'img_data'

sv_primogems_data = SV('版本规划')
sv_etc_img = SV('杂图')


@sv_primogems_data.on_command(('版本规划', '原石预估'))
async def send_primogems_data(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[图片][版本规划]')
    if ev.text:
        path = PRIMOGEMS_DATA_PATH / f'{ev.text}.png'
        if path.exists():
            img = f'{ev.text}.png'
        else:
            return
    else:
        img = f'{Genshin_version[:3]}.png'
    primogems_img = PRIMOGEMS_DATA_PATH / img
    await bot.logger.info('[图片][版本规划]访问图片: {}'.format(img))
    primogems_img = await convert_img(primogems_img)
    a = Button('📄版本规划4.3', '版本规划4.3')
    b = Button('🔔今日材料', '今日材料')
    await bot.send_option(primogems_img, [a, b])


@sv_etc_img.on_fullmatch(
    (
        '伤害乘区',
        '血量表',
        '抗性表',
        '血量排行',
        '深渊血量排行',
    )
)
async def send_img_data(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[图片][杂图]')
    img = IMG_PATH / f'{ev.command}.jpg'
    if img.exists():
        a = Button('👾怪物血量表', '血量表')
        b = Button('👾怪物抗性表', '抗性表')
        c = Button('👾怪物血量排行', '血量排行')
        d = Button('🤖伤害乘区', '伤害乘区')
        await bot.send_option(await convert_img(img), [a, b, c, d])
    else:
        return

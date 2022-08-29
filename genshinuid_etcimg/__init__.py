from pathlib import Path

from ..all_import import *

PRIMOGEMS_DATA_PATH = Path(__file__).parent / 'primogems_data'
IMG_PATH = Path(__file__).parent / 'img_data'
version = ['3.0', '2.8']


@sv.on_rex(r'(版本规划|原石预估)(\S+)?')
async def send_primogems_data(bot: HoshinoBot, ev: CQEvent):
    args = ev['match'].groups()
    logger.info('开始执行[图片][版本规划]')
    logger.info('[图片][版本规划]参数: {}'.format(args))
    if args[1]:
        if str(args[1]) in version:
            img = f'{args[1]}.png'
        else:
            return
    else:
        img = f'{version[0]}.png'
    primogems_img = PRIMOGEMS_DATA_PATH / img
    logger.info('[图片][版本规划]访问图片: {}'.format(img))
    primogems_img = await convert_img(primogems_img)
    await bot.send(ev, primogems_img)


@sv.on_rex(r'(查询)?(伤害乘区|血量表|抗性表)')
async def send_img_data(bot: HoshinoBot, ev: CQEvent):
    args = ev['match'].groups()
    logger.info('开始执行[图片][杂图]')
    logger.info('[图片][杂图]参数: {}'.format(args))
    img = IMG_PATH / f'{args[1]}.jpg'
    if img.exists():
        img = await convert_img(img)
        await bot.send(ev, img)
    else:
        return

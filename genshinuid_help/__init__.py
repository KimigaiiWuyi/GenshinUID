from ..all_import import *  # noqa: F403,F401

HELP_IMG = Path(__file__).parent / 'help.png'


@sv.on_fullmatch('gs帮助')
async def send_guide_pic(bot, ev):
    logger.info('获得gs帮助图片成功！')
    img = await convert_img(HELP_IMG)
    await bot.send(ev, img)

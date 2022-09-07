from ..all_import import *  # noqa: F403,F401

HELP_IMG = Path(__file__).parent / 'help.png'


@sv.on_fullmatch('gs帮助', 'genshin帮助', 'ys帮助', '原神帮助')
async def send_guide_pic(bot, ev):
    img = await convert_img(HELP_IMG)
    logger.info('获得gs帮助图片成功！')
    await bot.send(ev, img)

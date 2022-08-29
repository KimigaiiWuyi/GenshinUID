from .get_adv import char_adv, weapon_adv
from ..all_import import *  # noqa: F401, F403


@sv.on_rex(r'([\u4e00-\u9fa5]+)(用什么|能用啥|怎么养)')
async def send_char_adv(bot: HoshinoBot, ev: CQEvent):
    name = await alias_to_char_name(str(ev['match'].group(1)))
    im = await char_adv(name)
    await bot.send(ev, im)


@sv.on_rex(r'([\u4e00-\u9fa5]+)(能给谁|给谁用|要给谁|谁能用)')
async def send_weapon_adv(bot: HoshinoBot, ev: CQEvent):
    name = await alias_to_char_name(str(ev['match'].group(1)))
    im = await weapon_adv(name)
    await bot.send(ev, im)

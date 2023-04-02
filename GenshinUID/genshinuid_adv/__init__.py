from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .get_adv import char_adv, weapon_adv

sv_adv_text = SV('文字推荐')


@sv_adv_text.on_suffix(('用什么', '能用啥', '怎么养'))
async def send_char_adv(bot: Bot, ev: Event):
    await bot.send(await char_adv(ev.text))


@sv_adv_text.on_suffix(('能给谁', '谁能用', '给谁用'))
async def send_weapon_adv(bot: Bot, ev: Event):
    await bot.send(await weapon_adv(ev.text))

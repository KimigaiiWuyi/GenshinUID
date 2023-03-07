import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from .get_wiki_text import (
    char_wiki,
    foods_wiki,
    talent_wiki,
    weapon_wiki,
    enemies_wiki,
    artifacts_wiki,
    char_costs_wiki,
    char_stats_wiki,
    weapon_costs_wiki,
    weapon_stats_wiki,
    constellation_wiki,
)


@SV('原神WIKI文字版').on_prefix(('原魔介绍', '原魔资料'))
async def send_enemies(bot: Bot, ev: Event):
    await bot.send(await enemies_wiki(ev.text))


@SV('原神WIKI文字版').on_prefix(('食物介绍', '食物资料'))
async def send_food(bot: Bot, ev: Event):
    await bot.send(await foods_wiki(ev.text))


@SV('原神WIKI文字版').on_prefix(('圣遗物介绍', '圣遗物资料'))
async def send_artifacts(bot: Bot, ev: Event):
    await bot.send(await artifacts_wiki(ev.text))


@SV('原神WIKI文字版').on_prefix(('武器介绍', '武器资料'))
async def send_weapon(bot: Bot, ev: Event):
    name = ''.join(re.findall('[\u4e00-\u9fa5]', ev.text))
    level = re.findall(r'\d+', ev.text)
    if len(level) == 1:
        im = await weapon_stats_wiki(name, int(level[0]))
    else:
        im = await weapon_wiki(name)
    await bot.send(im)


@SV('原神WIKI文字版').on_prefix(('角色天赋'))
async def send_talents(bot: Bot, ev: Event):
    name = ''.join(re.findall('[\u4e00-\u9fa5]', ev.text))
    num = re.findall(r'\d+', ev.text)
    if len(num) == 1:
        im = await talent_wiki(name, int(num[0]))
        if isinstance(im, list):
            return await bot.send(MessageSegment.node(im))
    else:
        im = '参数不正确。'
    await bot.send(im)


@SV('原神WIKI文字版').on_prefix(('角色介绍', '角色资料'))
async def send_char(bot: Bot, ev: Event):
    name = ''.join(re.findall('[\u4e00-\u9fa5]', ev.text))
    level = re.findall(r'\d+', ev.text)
    if len(level) == 1:
        im = await char_stats_wiki(name, int(level[0]))
    else:
        im = await char_wiki(name)
    await bot.send(im)


@SV('原神WIKI文字版').on_prefix(('角色材料'))
async def send_char_cost(bot: Bot, ev: Event):
    im = await char_costs_wiki(ev.text)
    await bot.send(im)


@SV('原神WIKI文字版').on_prefix(('武器材料'))
async def send_weapon_cost(bot: Bot, ev: Event):
    im = await weapon_costs_wiki(ev.text)
    await bot.send(im)


@SV('原神WIKI文字版').on_prefix(('角色命座'))
async def send_polar(bot: Bot, ev: Event):
    num = int(re.findall(r'\d+', ev.text)[0])
    m = ''.join(re.findall('[\u4e00-\u9fa5]', ev.text))
    if num <= 0 or num > 6:
        return await bot.send('你家{}有{}命？'.format(m, num))
    im = await constellation_wiki(m, num)
    await bot.send(im)

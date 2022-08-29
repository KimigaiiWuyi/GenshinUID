import re

from ..all_import import *  # noqa: F401, F403
from .get_wiki_text import (
    char_wiki,
    audio_wiki,
    foods_wiki,
    weapon_wiki,
    enemies_wiki,
    artifacts_wiki,
)


@sv.on_prefix('语音')
async def send_audio(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return
    if message == '':
        return

    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    im = await audio_wiki(name, message)
    if name == '列表':
        await bot.send(ev, MessageSegment.image(im))
    else:
        if isinstance(im, str):
            await bot.send(ev, im)
        else:
            await bot.send(ev, MessageSegment.record(im))


@sv.on_prefix('原魔')
async def send_enemies(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return
    if message == '':
        return

    im = await enemies_wiki(message)
    await bot.send(ev, im)


@sv.on_prefix('食物')
async def send_food(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return
    if message == '':
        return

    im = await foods_wiki(message)
    await bot.send(ev, im)


@sv.on_prefix('圣遗物')
async def send_artifacts(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return
    if message == '':
        return

    im = await artifacts_wiki(message)
    await bot.send(ev, im)


@sv.on_prefix('武器')
async def send_weapon(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return
    if message == '':
        return

    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    level = re.findall(r'\d+', message)
    if len(level) == 1:
        im = await weapon_wiki(name, level=level[0])
    else:
        im = await weapon_wiki(name)
    await bot.send(ev, im)


@sv.on_prefix('天赋')
async def send_talents(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return
    if message == '':
        return

    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    num = re.findall(r'\d+', message)
    if len(num) == 1:
        im = await char_wiki(name, 'talents', num[0])
        if isinstance(im, list):
            await hoshino_bot.send_group_forward_msg(
                group_id=ev.group_id, messages=im
            )
            return
    else:
        im = '参数不正确。'
    await bot.send(ev, im)


@sv.on_prefix('角色')
async def send_char(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return
    if message == '':
        return

    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    level = re.findall(r'\d+', message)
    if len(level) == 1:
        im = await char_wiki(name, 'char', level=level[0])
    else:
        im = await char_wiki(name)
    await bot.send(ev, im)


@sv.on_prefix('材料')
async def send_cost(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return
    if message == '':
        return

    im = await char_wiki(message, 'costs')
    await bot.send(ev, im)


@sv.on_prefix('命座')
async def send_polar(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return
    if message == '':
        return

    num = int(re.findall(r'\d+', message)[0])  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    if num <= 0 or num > 6:
        await bot.send(ev, '你家{}有{}命？'.format(m, num))
        return
    im = await char_wiki(m, 'constellations', num)
    await bot.send(ev, im)

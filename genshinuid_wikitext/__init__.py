from ..all_import import *  # noqa: F401, F403
from .get_wiki_text import (
    char_wiki,
    audio_wiki,
    foods_wiki,
    weapon_wiki,
    enemies_wiki,
    artifacts_wiki,
)

get_weapon = on_command('武器', priority=priority)
get_char = on_command('角色', priority=priority)
get_cost = on_command('材料', priority=priority)
get_polar = on_command('命座', priority=priority)
get_talents = on_command('天赋', priority=priority)
get_enemies = on_command('原魔', priority=priority)
get_audio = on_command('语音', priority=priority)
get_artifacts = on_command('圣遗物', priority=priority)
get_food = on_command('食物', priority=priority)


@get_audio.handle()
@handle_exception('语音', '语音发送失败，可能是FFmpeg环境未配置。')
async def send_audio(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    im = await audio_wiki(name, message)
    if name == '列表':
        await matcher.finish(MessageSegment.image(im))
    else:
        if isinstance(im, str):
            await matcher.finish(im)
        else:
            await matcher.finish(MessageSegment.record(im))


@get_enemies.handle()
@handle_exception('怪物')
async def send_enemies(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await enemies_wiki(message)
    await matcher.finish(im)


@get_food.handle()
@handle_exception('食物')
async def send_food(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await foods_wiki(message)
    await matcher.finish(im)


@get_artifacts.handle()
@handle_exception('圣遗物')
async def send_artifacts(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await artifacts_wiki(message)
    await matcher.finish(im)


@get_weapon.handle()
@handle_exception('武器')
async def send_weapon(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    level = re.findall(r'\d+', message)
    if len(level) == 1:
        im = await weapon_wiki(name, level=level[0])
    else:
        im = await weapon_wiki(name)
    await matcher.finish(im)


@get_talents.handle()
@handle_exception('天赋')
async def send_talents(
    bot: Bot,
    event: GroupMessageEvent,
    matcher: Matcher,
    args: Message = CommandArg(),
):
    message = args.extract_plain_text().strip().replace(' ', '')
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    num = re.findall(r'\d+', message)
    if len(num) == 1:
        im = await char_wiki(name, 'talents', num[0])
        if isinstance(im, list):
            await bot.call_api(
                'send_group_forward_msg', group_id=event.group_id, messages=im
            )
            await matcher.finish()
            return
    else:
        im = '参数不正确。'
    await matcher.finish(im)


@get_char.handle()
@handle_exception('角色')
async def send_char(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    level = re.findall(r'\d+', message)
    if len(level) == 1:
        im = await char_wiki(name, 'char', level=level[0])
    else:
        im = await char_wiki(name)
    await matcher.finish(im)


@get_cost.handle()
@handle_exception('材料')
async def send_cost(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await char_wiki(message, 'costs')
    await matcher.finish(im)


@get_polar.handle()
@handle_exception('命座')
async def send_polar(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    num = int(re.findall(r'\d+', message)[0])  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    if num <= 0 or num > 6:
        await get_polar.finish('你家{}有{}命？'.format(m, num))
        return
    im = await char_wiki(m, 'constellations', num)
    await matcher.finish(im)

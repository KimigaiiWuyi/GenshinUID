import re

from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.adapters.ntchat.message import Message

from ..config import priority
from ..genshinuid_meta import register_menu
from ..utils.exception.handle_exception import handle_exception
from .get_wiki_text import (
    char_wiki,
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

# 语音暂时不支持
'''
@get_audio.handle()
@handle_exception('语音', '语音发送失败，可能是FFmpeg环境未配置。')
@register_menu(
    '角色语音',
    '语音[ID]',
    '获取角色语音',
    detail_des=(
        '介绍：\n'
        '获取角色语音\n'
        '获取语言ID列表请使用指令 <ft color=(238,120,0)>语音列表</ft>\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>语音{列表|</ft>'
        '<ft color=(0,148,200)>[语音ID]</ft>'
        '<ft color=(238,120,0)>}</ft>'
    ),
)
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
'''


@get_enemies.handle()
@handle_exception('怪物')
@register_menu(
    '怪物图鉴',
    '怪物xx',
    '获取怪物Wiki',
    detail_des=(
        '介绍：\n'
        '获取怪物Wiki\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>怪物</ft><ft color=(0,148,200)>[怪物名称]</ft>'
    ),
)
async def send_enemies(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await enemies_wiki(message)
    await matcher.finish(im)


@get_food.handle()
@handle_exception('食物')
@register_menu(
    '食物图鉴',
    '食物xx',
    '获取食物Wiki',
    detail_des=(
        '介绍：\n'
        '获取食物Wiki\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>食物</ft><ft color=(0,148,200)>[食物名称]</ft>'
    ),
)
async def send_food(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await foods_wiki(message)
    await matcher.finish(im)


@get_artifacts.handle()
@handle_exception('圣遗物')
@register_menu(
    '圣遗物图鉴',
    '圣遗物xx',
    '获取怪物Wiki',
    detail_des=(
        '介绍：\n'
        '获取圣遗物Wiki\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>圣遗物</ft><ft color=(0,148,200)>[圣遗物名称]</ft>'
    ),
)
async def send_artifacts(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await artifacts_wiki(message)
    await matcher.finish(im)


@get_weapon.handle()
@handle_exception('武器')
@register_menu(
    '武器图鉴',
    '武器xx',
    '获取武器Wiki',
    detail_des=(
        '介绍：\n'
        '获取武器Wiki\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>武器</ft><ft color=(0,148,200)>[武器名称]</ft>'
        '<ft color=(125,125,125)>(级数)</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>武器雾切</ft>\n'
        '- <ft color=(238,120,0)>武器无工之剑90</ft>'
    ),
)
async def send_weapon(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    level = re.findall(r'\d+', message)
    if len(level) == 1:
        im = await weapon_wiki(name, level=level[0])
    else:
        im = await weapon_wiki(name)
    await matcher.finish(im)


# 天赋暂时不支持
'''
@get_talents.handle()
@handle_exception('天赋')
@register_menu(
    '天赋效果',
    '天赋[角色][天赋序号]',
    '查询角色天赋技能效果',
    detail_des=(
        '介绍：\n'
        '查询角色天赋技能效果\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>天赋</ft>'
        '<ft color=(0,148,200)>[角色名称][天赋序号]</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>天赋绫华2</ft>'
    ),
)
async def send_talents(
    bot: Bot,
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
    else:
        im = '参数不正确。'
    await matcher.finish(im)
'''


@get_char.handle()
@handle_exception('角色')
@register_menu(
    '角色图鉴',
    '角色xx',
    '获取角色Wiki',
    detail_des=(
        '介绍：\n'
        '获取角色Wiki\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>角色</ft><ft color=(0,148,200)>[角色名称]</ft>'
        '<ft color=(125,125,125)>(等级)</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>角色可莉</ft>\n'
        '- <ft color=(238,120,0)>角色可莉90</ft>'
    ),
)
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
@register_menu(
    '材料图鉴',
    '材料xx',
    '获取材料Wiki',
    detail_des=(
        '介绍：\n'
        '获取材料Wiki\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>材料</ft><ft color=(0,148,200)>[材料名称]</ft>'
    ),
)
async def send_cost(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await char_wiki(message, 'costs')
    await matcher.finish(im)


@get_polar.handle()
@handle_exception('命座')
@register_menu(
    '角色命座图鉴',
    '命座[角色][等级]',
    '获取角色命座Wiki',
    detail_des=(
        '介绍：\n'
        '获取角色命座Wiki\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>命座</ft>'
        '<ft color=(0,148,200)>[角色名称][命座等级]</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>命座胡桃1</ft>'
    ),
)
async def send_polar(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    num = int(re.findall(r'\d+', message)[0])  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    if num <= 0 or num > 6:
        await get_polar.finish('你家{}有{}命？'.format(m, num))
        return
    im = await char_wiki(m, 'constellations', num)
    await matcher.finish(im)

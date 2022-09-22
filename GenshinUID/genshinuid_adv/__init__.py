from typing import Any, Tuple

from nonebot import on_regex
from nonebot.matcher import Matcher
from nonebot.params import RegexGroup

from ..config import priority
from .get_adv import char_adv, weapon_adv
from ..genshinuid_meta import register_menu
from ..utils.alias.alias_to_char_name import alias_to_char_name
from ..utils.exception.handle_exception import handle_exception

get_char_adv = on_regex('([\u4e00-\u9fa5]+)(用什么|能用啥|怎么养)', priority=priority)
get_weapon_adv = on_regex(
    '([\u4e00-\u9fa5]+)(能给谁|给谁用|要给谁|谁能用)', priority=priority
)


@get_char_adv.handle()
@handle_exception('建议')
@register_menu(
    '角色配置推荐',
    'xx用什么',
    '查询角色武器/圣遗物推荐配置',
    detail_des=(
        '指令：'
        '<ft color=(238,120,0)>[角色名][用什么/能用啥/怎么养]</ft>\n'
        ' \n'
        '可以查询某角色的武器/圣遗物推荐配置\n'
        '支持部分角色别名\n'
        ' \n'
        '示例：\n'
        '<ft color=(238,120,0)>钟离用什么</ft>；\n'
        '<ft color=(238,120,0)>公子怎么养</ft>'
    ),
)
async def send_char_adv(
    matcher: Matcher, args: Tuple[Any, ...] = RegexGroup()
):
    name = await alias_to_char_name(str(args[0]))
    im = await char_adv(name)
    await matcher.finish(im)


@get_weapon_adv.handle()
@handle_exception('建议')
@register_menu(
    '装备适用角色',
    'xx能给谁',
    '查询某武器/圣遗物能给谁用',
    detail_des=(
        '指令：'
        '<ft color=(238,120,0)>[角色名][能给谁/给谁用/要给谁/谁能用]</ft>\n'
        ' \n'
        '可以通过武器/圣遗物名反查适用的角色\n'
        '支持部分别名\n'
        ' \n'
        '示例：\n'
        '<ft color=(238,120,0)>四风原典能给谁</ft>；\n'
        '<ft color=(238,120,0)>千岩给谁用</ft>'
    ),
)
async def send_weapon_adv(
    matcher: Matcher, args: Tuple[Any, ...] = RegexGroup()
):
    name = await alias_to_char_name(str(args[0]))
    im = await weapon_adv(name)
    await matcher.finish(im)

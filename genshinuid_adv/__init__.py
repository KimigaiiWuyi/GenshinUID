from typing import Any, Tuple

from nonebot import on_regex
from nonebot.matcher import Matcher
from nonebot.params import RegexGroup

from ..config import priority

from .get_adv import char_adv, weapon_adv
from ..utils.alias.alias_to_char_name import alias_to_char_name
from ..utils.exception.handle_exception import handle_exception

get_char_adv = on_regex('([\u4e00-\u9fa5]+)(用什么|能用啥|怎么养)', priority=priority)
get_weapon_adv = on_regex(
    '([\u4e00-\u9fa5]+)(能给谁|给谁用|要给谁|谁能用)', priority=priority
)


@get_char_adv.handle()
@handle_exception('建议')
async def send_char_adv(
    matcher: Matcher, args: Tuple[Any, ...] = RegexGroup()
):
    name = await alias_to_char_name(str(args[0]))
    im = await char_adv(name)
    await matcher.finish(im)


@get_weapon_adv.handle()
@handle_exception('建议')
async def send_weapon_adv(
    matcher: Matcher, args: Tuple[Any, ...] = RegexGroup()
):
    name = await alias_to_char_name(str(args[0]))
    im = await weapon_adv(name)
    await matcher.finish(im)

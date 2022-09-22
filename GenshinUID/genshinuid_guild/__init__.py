from typing import List

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.message import event_preprocessor
from nonebot.adapters.qqguild.message import Text
from nonebot.adapters.qqguild.api.model import Guild
from nonebot.adapters.qqguild import Bot, MessageEvent

from ..utils.nonebot2.rule import FullCommand
from ..utils.exception.handle_exception import handle_exception

guild_detail = on_command('频道统计', block=True, rule=FullCommand())


@event_preprocessor
async def _(event: MessageEvent):
    msg = event.get_message().extract_content()
    msg = msg.replace(' ', '').replace('/', '')
    r_msg = None
    new_msg = []
    for i in event._message:  # type: ignore
        if isinstance(i, Text):
            i.data['text'] = msg

    if r_msg:
        new_msg.insert(0, r_msg)
        event._message = new_msg

    if event.content:
        event.content = event.content.replace(' ', '').replace('/', '')


@guild_detail.handle()
@handle_exception('频道统计')
async def send_create_map_msg(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
):
    if not await SUPERUSER(bot, event):
        return
    logger.info('[频道统计]正在执行...')
    await matcher.send('频道统计正在执行...可能需要较长时间!')
    # 最后的计数
    ALL_MEMBER = 0

    # 开始分页
    after = None
    # 频道列表
    guild_list = []
    while True:
        new_guild_list: List[Guild] = await bot.call_api(
            'guilds', before=None, after=after, limit=None
        )
        for guild in new_guild_list:
            if guild.member_count:
                ALL_MEMBER += guild.member_count
            after = guild.id
        guild_list.extend(new_guild_list)
        logger.info(f'当前页gid={after}')
        if new_guild_list == []:
            break
    im = f'当前Bot加入频道数{len(guild_list)}, 总人数为{ALL_MEMBER}'
    await matcher.finish(im)

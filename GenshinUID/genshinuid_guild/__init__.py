import asyncio
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
            if '毕业都统计' in i.data['text']:
                i.data['text'].replace('都', '度')

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

    # 初始化最后的计数
    ALL_MEMBER = 0
    HIDE = 0

    # 开始分页
    after = None
    # 初始化频道列表
    guild_list = []
    # 开始循环
    while True:
        # 本次获取的频道列表
        new_guild_list: List[Guild] = await bot.call_api(
            'guilds', before=None, after=after, limit=None
        )
        # 遍历频道列表
        for guild in new_guild_list:
            # 如果该频道人数展示
            if guild.member_count:
                # 总人数加上该频道的人数
                ALL_MEMBER += guild.member_count
            else:
                HIDE += 1
                logger.info(f'频道{guild.id}隐藏频道人数信息，已跳过计算...')
            # 重新设定拉取值
            after = guild.id
        # 把本次拉取的频道列表 合并到总频道列表
        guild_list.extend(new_guild_list)
        logger.info(f'当前页gid={after}')
        # 如果已经拉取不到频道了，就退出循环
        if new_guild_list == []:
            break
        await asyncio.sleep(0.5)
    im = f'当前Bot加入频道数{len(guild_list)}\n总人数为{ALL_MEMBER}\n隐藏人数频道数量{HIDE}！'
    await matcher.finish(im)

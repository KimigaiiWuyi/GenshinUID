from nonebot.rule import Rule
from nonebot.adapters.qqguild import Message
from nonebot.params import Depends, CommandArg


async def full_command(arg: Message = CommandArg()) -> bool:
    return not bool(str(arg))


def FullCommand() -> Rule:
    return Rule(full_command)


def FullCommandDepend():
    return Depends(full_command)

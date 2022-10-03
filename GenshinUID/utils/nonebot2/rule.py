from nonebot.rule import Rule
from nonebot.params import Depends, CommandArg
from nonebot.adapters.onebot.v11 import Message


async def full_command(arg: Message = CommandArg()) -> bool:
    return not bool(str(arg))


def FullCommand() -> Rule:
    return Rule(full_command)


def FullCommandDepend():
    return Depends(full_command)

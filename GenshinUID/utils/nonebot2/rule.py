from nonebot.rule import Rule
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message


def FullCommand() -> Rule:
    async def dependency(arg: Message = CommandArg()) -> bool:
        return not bool(str(arg))

    return Rule(dependency)

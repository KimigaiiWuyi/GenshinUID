from functools import wraps
from typing import Optional

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.exception import FinishedException
from nonebot.adapters.onebot.v11 import ActionFailed


def handle_exception(
    name: str, log_msg: Optional[str] = None, fail_msg: Optional[str] = None
):
    """
    :说明:
      捕获命令执行过程中发生的异常并回报。
    :参数:
      * ``name: str``: 项目的名称。
      * ``log_msg: str = None``: 自定义捕获异常后在日志中留存的信息。留空则使用默认信息。
      * ``fail_msg: str = None``: 自定义捕获异常后向用户回报的信息，仅在提供自定义日志信息时有效。
                                  开头带@则艾特用户。留空则与日志信息相同。
    """

    def wrapper(func):
        @wraps(func)
        async def inner(
            log_msg: Optional[str] = log_msg,
            fail_msg: Optional[str] = fail_msg,
            **kwargs,
        ):
            matcher: Matcher = kwargs['matcher']
            try:
                await func(**kwargs)
            except ActionFailed as e:
                # 此为bot本身由于风控或网络问题发不出消息，并非代码本身出问题
                await matcher.send(f'发送消息失败{e.info["wording"]}')
                logger.exception(f'发送{name}消息失败')
            except FinishedException:
                # `finish` 会抛出此异常，应予以抛出而不处理
                raise
            except Exception as e:
                # 如果e内包含敏感信息，应在此处进行处理
                if 'SQL' in str(e):
                    e = '数据库操作失败!可能正在[校验全部Cookies]\n敏感信息已抹去...请等待一段时间后重试!'
                # 代码本身出问题
                if log_msg:
                    if not fail_msg:
                        fail_msg = log_msg
                    if fail_msg[0] == '@':
                        await matcher.send(
                            f'{fail_msg[1:]}\n错误信息为{e}', at_sender=True
                        )
                    else:
                        await matcher.send(f'{fail_msg}\n错误信息为{e}')
                    if log_msg[0] == '@':
                        log_msg = log_msg[1:]
                    logger.exception(log_msg)
                else:
                    await matcher.send(f'发生错误 {e}，请检查后台输出。')
                    logger.exception(f'获取{name}信息错误')

        return inner

    return wrapper

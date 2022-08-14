import asyncio

from ..all_import import *  # noqa: F403, F401
from ..utils.db_operation.db_cache_and_check import check_db, check_stoken_db
from ..utils.download_resource.download_all_resource import (
    download_all_resource,
)

check = on_command('校验全部Cookies')
check_stoken = on_command('校验全部Stoken')
download_resource = on_command('下载全部资源')


@download_resource.handle()
@handle_exception('下载全部资源', '资源下载错误')
async def send_download_resource_msg(
    matcher: Matcher, args: Message = CommandArg()
):
    if args:
        return
    await matcher.send('正在开始下载~可能需要较久的时间!')
    im = await download_all_resource()
    await matcher.finish(im)


# 群聊内 校验Cookies 是否正常的功能，不正常自动删掉
@check.handle()
@handle_exception('Cookie校验', 'Cookie校验错误')
async def send_check_cookie(
    bot: Bot, matcher: Matcher, args: Message = CommandArg()
):
    if args:
        await matcher.finish()
    raw_mes = await check_db()
    im = raw_mes[0]
    await matcher.send(im)
    for i in raw_mes[1]:
        await bot.call_api(
            api='send_private_msg',
            **{
                'user_id': i[0],
                'message': (
                    '您绑定的Cookies（uid{}）已失效，以下功能将会受到影响：\n'
                    '查看完整信息列表\n查看深渊配队\n自动签到/当前状态/每月统计\n'
                    '请及时重新绑定Cookies并重新开关相应功能。'
                ).format(i[1]),
            },
        )
        await asyncio.sleep(3 + random.randint(1, 3))
    await matcher.finish()


# 群聊内 校验Stoken 是否正常的功能，不正常自动删掉
@check_stoken.handle()
@handle_exception('Stoken校验', 'Stoken校验错误')
async def send_check_stoken(
    bot: Bot, matcher: Matcher, args: Message = CommandArg()
):
    if args:
        await matcher.finish()
    raw_mes = await check_stoken_db()
    im = raw_mes[0]
    await matcher.send(im)
    for i in raw_mes[1]:
        await bot.call_api(
            api='send_private_msg',
            **{
                'user_id': i[0],
                'message': (
                    '您绑定的Stoken（uid{}）已失效，以下功能将会受到影响：\n'
                    'gs开启自动米游币，开始获取米游币。\n'
                    '重新添加后需要重新开启自动米游币。'
                ).format(i[1]),
            },
        )
        await asyncio.sleep(3 + random.randint(1, 3))

    await matcher.finish()

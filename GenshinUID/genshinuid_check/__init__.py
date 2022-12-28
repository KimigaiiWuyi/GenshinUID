import random
import asyncio

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.ntchat import Bot, TextMessageEvent

from .backup_data import data_backup
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from ..utils.exception.handle_exception import handle_exception
from ..utils.db_operation.db_cache_and_check import check_db, check_stoken_db
from ..utils.db_operation.db_operation import delete_cookies, get_all_push_list
from ..utils.message.get_cqhttp_data import (
    get_all_friend_list,
    get_group_member_list,
)

backup = on_command('gs清除缓存', rule=FullCommand())
check = on_command('校验全部Cookies', rule=FullCommand())
check_stoken = on_command('校验全部Stoken', rule=FullCommand())
remove_invalid_user = on_command('清除无效用户', rule=FullCommand())

backup_scheduler = scheduler


@backup_scheduler.scheduled_job('cron', hour=0)
async def daily_refresh_charData():
    await data_backup()


@backup.handle()
@handle_exception('清除缓存', '清除缓存错误')
@register_menu(
    '清除缓存',
    '清除缓存',
    '清除插件产生的缓存数据',
    trigger_method='超级用户指令',
    detail_des=(
        '介绍：\n'
        '备份一份插件数据库后清除插件产生的文件与数据库缓存\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>清除缓存</ft>'
    ),
)
async def send_backup_msg(
    bot: Bot,
    event: TextMessageEvent,
    matcher: Matcher,
):
    if not await SUPERUSER(bot, event):
        return
    await data_backup()
    await matcher.finish('操作成功完成!')


@remove_invalid_user.handle()
@handle_exception('清除无效用户', '清除无效用户错误')
@register_menu(
    '清除无效用户',
    '清除无效用户',
    '清除非好友或非推送群成员的数据',
    trigger_method='超级用户指令',
    detail_des=(
        '介绍：\n'
        '从数据库中删除掉 开启了私聊推送但不是Bot好友的用户 '
        '以及 开启了群聊推送但不在推送目标群的用户 的数据\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>清除无效用户</ft>'
    ),
)
async def send_remove_invalid_user_msg(
    bot: Bot,
    event: TextMessageEvent,
    matcher: Matcher,
):
    if not await SUPERUSER(bot, event):
        return
    im_list = []
    invalid_user = {}
    invalid_uid_list = []
    user_list = await get_all_push_list()
    friend_list = await get_all_friend_list(bot)
    for user in user_list:
        if user['StatusA'] == 'on':
            if user['QID'] not in friend_list:
                invalid_user['qid'] = user['UID']
                invalid_uid_list.append(user['UID'])
        else:
            group_member_list = await get_group_member_list(
                bot, int(user['StatusA'])
            )
            if user['QID'] not in group_member_list:
                invalid_user['qid'] = user['UID']
                invalid_uid_list.append(user['UID'])
    for uid in invalid_uid_list:
        im_list.append(await delete_cookies(str(uid)))
        logger.warning(f'无效UID已被删除: {uid}')
    await matcher.finish(f'已清理失效用户{len(im_list)}个!')


# 群聊内 校验Cookies 是否正常的功能，不正常自动删掉
@check.handle()
@handle_exception('Cookie校验', 'Cookie校验错误')
@register_menu(
    '校验全部Cookies',
    '校验全部Cookies',
    '校验数据库内所有Cookies是否正常',
    detail_des=(
        '介绍：\n'
        '校验数据库内所有Cookies是否正常，不正常的会自动删除\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>校验全部Cookies</ft>\n'
        '注意<ft color=(238,120,0)>Cookies</ft>的'
        '<ft color=(238,120,0)>C</ft>为大写'
    ),
)
async def send_check_cookie(bot: Bot, matcher: Matcher):
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
@register_menu(
    '校验全部Stoken',
    '校验全部Stoken',
    '校验数据库内所有Stoken是否正常',
    detail_des=(
        '介绍：\n'
        '校验数据库内所有Stoken是否正常，不正常的会自动删除\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>校验全部Stoken</ft>\n'
        '注意<ft color=(238,120,0)>Stoken</ft>的<ft color=(238,120,0)>S</ft>为大写'
    ),
)
async def send_check_stoken(bot: Bot, matcher: Matcher):
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

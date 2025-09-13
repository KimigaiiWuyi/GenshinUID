import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import CK_HINT
from gsuid_core.subscribe import Subscribe, gs_subscribe
from gsuid_core.utils.database.models import GsBind, GsUser

from ..utils.message import UID_HINT
from ..utils.message import PREFIX as P
from .draw_config_card import draw_config_img

sv_self_config = SV('原神配置')

PRIV_MAP = {
    '宝钱': 2000,
    '体力': 100,
    '派遣': 300,
    '质变仪': 1000,
    '自动签到': None,
    '自动米游币': None,
    '推送': None,
}


@sv_self_config.on_fullmatch(('配置', '原神配置'))
async def send_config_card(bot: Bot, ev: Event):
    logger.info('开始执行[gs配置]')
    im = await draw_config_img(ev.bot_id)
    await bot.send(im)


@sv_self_config.on_prefix(('设置'))
async def send_config_ev(bot: Bot, ev: Event):
    logger.info('开始执行[设置阈值信息]')

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)
    cookie = await GsUser.get_user_cookie_by_uid(uid)
    if cookie is None:
        return await bot.send(CK_HINT)

    config_name = ''.join(
        re.findall('[\u4e00-\u9fa5]', ev.text.replace('阈值', ''))
    )

    value = re.findall(r'\d+', ev.text)
    value = value[0] if value else None

    if value is None:
        return await bot.send(
            f'🔨 [原神服务]\n❌ 请输入正确的阈值数字...\n🚩 例如: {P}设置体力阈值200'
        )

    logger.info(f'[设置阈值信息] func: {config_name}, value: {value}')

    if config_name not in PRIV_MAP or (
        config_name in PRIV_MAP and PRIV_MAP[config_name] is None
    ):
        return await bot.send(
            f'🔨 [原神服务]\n❌ 请输入正确的功能名称...\n🚩 例如: {P}设置体力阈值200'
        )

    datas = await gs_subscribe.get_subscribe(
        f'[原神] {config_name}',
        ev.user_id,
        ev.bot_id,
        ev.user_type,
    )

    if datas:
        if len(datas) > 1:
            logger.warning(
                f'[设置阈值信息] {ev.user_id} 存在多个订阅, {datas}'
            )

        data = datas[0]
        await gs_subscribe.update_subscribe_message(
            'single',
            data.task_name,
            ev,
            extra_message=str(value),
        )
        im = f'🔨 [原神服务]\n✅ 已为[UID{uid}]设置{config_name}为{value}!'
    else:
        im = '🔨 [原神服务]\n❌ 请先开启功能...\n🚩 例如: {P}开启体力推送'

    await bot.send(im)


# 开启 自动签到 和 推送树脂提醒 功能
@sv_self_config.on_prefix(('开启', '关闭'))
async def open_switch_func(bot: Bot, ev: Event):
    user_id = ev.user_id
    config_name = ev.text
    if config_name.startswith(('体力', '宝钱', '派遣', '质变仪')):
        config_name = config_name.replace('推送', '')

    if config_name not in PRIV_MAP:
        return await bot.send(
            f'🔨 [原神服务]\n❌ 请输入正确的功能名称...\n🚩 例如: {P}开启自动签到'
        )

    logger.info(
        f'[原神服务] [{user_id}]尝试[{ev.command[2:]}]了[{ev.text}]功能'
    )

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)
    cookie = await GsUser.get_user_cookie_by_uid(uid)
    if cookie is None:
        return await bot.send(CK_HINT)

    c_name = f'[原神] {config_name}'

    if '开启' in ev.command:
        im = f'🔨 [原神服务]\n✅ 已为[UID{uid}]开启{config_name}功能。'

        if PRIV_MAP[config_name] is None and await gs_subscribe.get_subscribe(
            c_name, uid=uid
        ):
            await Subscribe.update_data_by_data(
                {
                    'task_name': c_name,
                    'uid': uid,
                },
                {
                    'user_id': ev.user_id,
                    'bot_id': ev.bot_id,
                    'group_id': ev.group_id,
                    'bot_self_id': ev.bot_self_id,
                    'user_type': ev.user_type,
                    'WS_BOT_ID': ev.WS_BOT_ID,
                },
            )
        else:
            await gs_subscribe.add_subscribe(
                'single',
                c_name,
                ev,
                extra_message=PRIV_MAP[config_name],
                uid=uid,
            )

        if PRIV_MAP[config_name]:
            im += f'\n🔧 并设置了触发阈值为{PRIV_MAP[config_name]}!'
            if not await gs_subscribe.get_subscribe('[原神] 推送', uid=uid):
                im += '\n⚠ 警告: 由于未打开推送总开关, 所以此项设置可能无效！'
                im += f'如需打开总开关, 请发送命令开启推送: {P}开启推送！'
        if config_name == '推送':
            resin = await gs_subscribe.get_subscribe('[原神] 体力', uid=uid)
            coin = await gs_subscribe.get_subscribe('[原神] 宝钱', uid=uid)
            go = await gs_subscribe.get_subscribe('[原神] 派遣', uid=uid)
            trans = await gs_subscribe.get_subscribe('[原神] 质变仪', uid=uid)

            im += f'\n✅ 如需关闭请发送命令: {P}关闭推送\n💚 该项为总开关, 你开可以单独开启体力、宝钱、派遣、质变仪的推送。'
            im += '\n🔖 【当前推送设置状态】'
            if resin:
                im += f'\n✅ 体力推送 (阈值: {resin[0].extra_message})'
            else:
                im += f'\n❌ 体力推送 (可发送{P}开启体力推送)'
            if coin:
                im += f'\n✅ 宝钱推送 (阈值: {coin[0].extra_message})'
            else:
                im += f'\n❌ 宝钱推送 (可发送{P}开启宝钱推送)'
            if go:
                im += f'\n✅ 派遣推送 (阈值: {go[0].extra_message})'
            else:
                im += f'\n❌ 派遣推送 (可发送{P}开启派遣推送)'
            if trans:
                im += f'\n✅ 质变仪推送 (阈值: {trans[0].extra_message})'
            else:
                im += f'\n❌ 质变仪推送 (可发送{P}开启质变仪推送)'
    else:
        data = await gs_subscribe.get_subscribe(
            c_name,
            ev.user_id,
            ev.bot_id,
            ev.user_type,
        )
        if data:
            await gs_subscribe.delete_subscribe(
                'single',
                c_name,
                ev,
                uid=uid,
            )
            im = f'🔨 [原神服务]\n✅ 已为[UID{uid}]关闭{config_name}功能。'
        else:
            im = f'🔨 [原神服务]\n❌ 未找到[UID{uid}]的{config_name}功能配置, 该功能可能未开启。'

    await bot.send(im)

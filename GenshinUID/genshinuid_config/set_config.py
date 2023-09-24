from typing import Optional

from gsuid_core.logger import logger
from gsuid_core.utils.database.models import GsPush, GsUser

from .gs_config import gsconfig
from .config_default import CONIFG_DEFAULT

PUSH_MAP = {
    '宝钱': 'coin',
    '体力': 'resin',
    '派遣': 'go',
    '质变仪': 'transform',
}
PRIV_MAP = {
    '自动签到': 'sign',
    '自动米游币': 'bbs',
    '推送': 'push',
    '自动留影叙佳期': 'draw',
}


async def set_push_value(bot_id: str, func: str, uid: str, value: int):
    if func in PUSH_MAP:
        status = PUSH_MAP[func]
    else:
        return '该配置项不存在!'
    logger.info('[设置推送阈值]func: {}, value: {}'.format(status, value))
    if (
        await GsPush.update_data_by_uid(
            uid, bot_id, None, **{f'{status}_value': value}
        )
        == 0
    ):
        return f'设置成功!\n当前{func}推送阈值:{value}'
    else:
        return '设置失败!\n请检查参数是否正确!'


async def set_config_func(
    bot_id: str,
    config_name: str = '',
    uid: str = '0',
    user_id: str = '',
    option: str = '0',
    query: Optional[bool] = None,
    is_admin: bool = False,
):
    # 这里将传入的中文config_name转换为英文status
    for _name in CONIFG_DEFAULT:
        config = CONIFG_DEFAULT[_name]
        if config.title == config_name and isinstance(config.data, bool):
            name = _name
            break
    else:
        logger.info(
            f'uid: {uid}, option: {option}, config_name: {config_name}'
        )
        if config_name in PRIV_MAP:
            # 执行设置
            await GsUser.update_data_by_uid(
                uid,
                bot_id,
                None,
                **{
                    f'{PRIV_MAP[config_name]}_switch': option,
                },
            )
        elif config_name.replace('推送', '') in PUSH_MAP:
            await GsUser.update_data_by_uid(
                uid,
                bot_id,
                None,
                **{
                    f'{PUSH_MAP[config_name.replace("推送", "")]}_push': option,
                },
            )
        else:
            return '该配置项不存在!'

        if option == 'on':
            succeed_msg = '开启至私聊消息!'
        elif option == 'off':
            succeed_msg = '关闭!'
        else:
            succeed_msg = f'开启至群{option}'
        return f'{config_name}已{succeed_msg}'

    if is_admin:
        logger.info(f'config_name:{config_name},query:{query}')
        # 执行设置
        if query is not None:
            gsconfig.set_config(name, query)
            im = '成功设置{}为{}。'.format(config_name, '开' if query else '关')
        else:
            im = '未传入参数query!'
    else:
        im = '只有管理员才能设置群服务。'
    return im

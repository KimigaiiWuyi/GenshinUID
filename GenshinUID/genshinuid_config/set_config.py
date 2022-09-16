from typing import Optional

from nonebot.log import logger

from ..utils.message.error_reply import CK_HINT
from ..utils.db_operation.db_operation import (
    open_push,
    config_check,
    update_push_value,
    update_push_status,
)

SWITCH_MAP = {
    '自动签到': 'StatusB',
    '推送': 'StatusA',
    '自动米游币': 'StatusC',
    '米游币推送': 'MhyBBSCoinReport',
    '简洁签到报告': 'SignReportSimple',
    '私聊报告': 'PrivateReport',
    '随机图': 'RandomPic',
    '定时签到': 'SchedSignin',
    '定时米游币': 'SchedMhyBBSCoin',
    '催命模式': 'CrazyNotice',
    '网页控制台': 'OpenWeb',
}

PUSH_MAP = {
    '宝钱': 'Coin',
    '体力': 'Resin',
    '派遣': 'Go',
    '质变仪': 'Transform',
}

HINT_MAP = {
    '米游币推送': '\n该选项不会影响到实际米游币获取\n*【管理员命令全局生效】',
    '简洁签到报告': '\n该选项将减少每日群内签到报告的字数\n*【管理员命令全局生效】',
}
SWITCH_STR = ''
PUSH_STR = ''
for switch in SWITCH_MAP:
    SWITCH_STR += '\n' + switch

for push in PUSH_MAP:
    PUSH_STR += '\n' + push


async def set_push_value(func: str, uid: str, value: int):
    if func in PUSH_MAP:
        status = PUSH_MAP[func]
    else:
        return f'该配置项不存在!\n当前推送配置:{PUSH_STR}'
    logger.info('[设置推送阈值]func: {}, value: {}'.format(status, value))
    if await update_push_value(int(uid), status, int(value)):
        return f'设置成功!\n当前{func}推送阈值:{value}'
    else:
        return '设置失败!\n请检查参数是否正确!'


async def set_config_func(
    config_name: str = '',
    uid: str = '0',
    qid: Optional[str] = None,
    option: str = '0',
    query: Optional[str] = None,
    is_admin: bool = False,
):
    """
    :说明:
      设置配置项
      如果config_name为私人服务, 例如['自动签到', '推送', '自动米游币'],
      则需要传入uid, qid和option
      ---
      如果config_name为群服务, 例如['米游币推送', '简洁签到报告'],
      则需要传入query即可
    :参数:
      * config_name (str): 设置的参数名。
      * uid (str): 用户id。
      * qid (str): 群id。
      * option (str): 'off'(关闭), 'on'(开启), '群号'(开启至群聊推送)。
      * query (str): 'CLOSED', 'OPEN'。
      * is_admin (bool): 是否为管理员。
    :返回:
      * im: 设置消息。
    """
    # 这里将传入的中文config_name转换为英文status
    if config_name in SWITCH_MAP:
        status = SWITCH_MAP[config_name]
    elif config_name in PUSH_MAP:
        status = PUSH_MAP[config_name]
    else:
        return f'该配置项不存在!\n当前配置项:{SWITCH_STR}\n当前推送配置:{PUSH_STR}'

    # 这里判断是否是私人服务
    if config_name in ['自动签到', '推送', '自动米游币']:
        logger.info(
            f'uid: {uid}, qid: {qid}, option: {option}, config_name: {status}'
        )
        # 执行设置
        if await open_push(uid, qid, option, status):
            if option == 'on':
                succeed_msg = '开启至私聊消息!'
            elif option == 'off':
                succeed_msg = '关闭!'
            else:
                succeed_msg = f'开启至{option}'
            im = f'{config_name}已{succeed_msg}'
        else:
            im = '设置失败, 可能是未绑定Coookie或者Cookie已过期。\n' + CK_HINT
    elif config_name in PUSH_MAP:
        logger.info('[设置推送信息]func: {}'.format(config_name))
        if await update_push_status(int(uid), status, option):
            return f'设置{config_name}成功, 状态为{option}!\n'
        else:
            return f'设置{config_name}失败, '
    # 这里判断是否是群服务
    else:
        if is_admin:
            logger.info(f'config_name:{status},query:{query}')
            # 执行设置
            if query:
                if await config_check(status, query):
                    im = '成功设置{}为{}。'.format(config_name, query)
                    if config_name in HINT_MAP:
                        im += HINT_MAP[config_name]
                else:
                    im = '设置失败!'
            else:
                im = '未传入参数query!'
        else:
            im = '只有管理员才能设置群服务。'
    return im

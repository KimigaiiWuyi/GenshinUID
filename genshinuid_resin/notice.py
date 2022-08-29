from typing import List

from nonebot.log import logger

from ..utils.mhy_api.get_mhy_data import get_daily_data
from ..utils.db_operation.db_operation import (
    get_push_data,
    update_is_pushed,
    get_all_push_list,
)

MR_NOTICE = '\n可发送[mr]或者[每日]来查看更多信息!'

NOTICE = {
    'Coin': f'你的洞天宝钱快满啦!{MR_NOTICE}',
    'Resin': f'你的树脂/体力快满啦!{MR_NOTICE}',
    'Go': f'你有派遣信息即将可收取!{MR_NOTICE}',
    'Transform': f'你的质变仪即将可使用!{MR_NOTICE}',
}


async def get_notice_list() -> List[dict]:
    uid_list = await get_all_push_list()
    private_msg_list = {}
    group_msg_list = {}
    for item in uid_list:
        uid = str(item['UID'])
        qid = str(item['QID'])
        raw_data = await get_daily_data(uid)
        if raw_data['retcode'] != 0:
            logger.error(f'[推送提醒]获取{uid}的数据失败!')
            continue
        raw_data = raw_data['data']
        push_data = await get_push_data(int(uid))
        private_msg_list, group_msg_list = await all_check(
            raw_data,
            push_data,
            private_msg_list,
            group_msg_list,
            qid,
            int(uid),
        )
    return [private_msg_list, group_msg_list]


async def all_check(
    raw_data: dict,
    push_data: dict,
    private_msg_list: dict,
    group_msg_list: dict,
    qid: str,
    uid: int,
) -> List[dict]:
    for mode in ['Coin', 'Resin', 'Go', 'Transform']:
        # 检查条件
        if push_data[f'{mode}IsPush'] == 'on':
            if not await check(mode, raw_data, push_data[f'{mode}Value']):
                await update_is_pushed(uid, mode, 'off')
            continue
        if await check(mode, raw_data, push_data[f'{mode}Value']):
            if push_data[f'{mode}Push'] == 'on':
                # 初始化
                if qid not in private_msg_list:
                    private_msg_list[qid] = ''
                # 添加私聊信息
                private_msg_list[qid] += NOTICE[mode]
                await update_is_pushed(uid, mode, 'on')
            elif push_data[f'{mode}Push'] == 'off':
                pass
            else:
                # 初始化
                if push_data[f'{mode}Push'] not in group_msg_list:
                    group_msg_list[push_data[f'{mode}Push']] = ''
                # 添加群聊信息
                group_msg_list[
                    push_data[f'{mode}Push']
                ] += f'[CQ:at,qq={qid}]{NOTICE[mode]}'
                await update_is_pushed(uid, mode, 'on')
    return [private_msg_list, group_msg_list]


async def check(mode: str, data: dict, limit: int) -> bool:
    if mode == 'Coin':
        if data['current_home_coin'] >= limit:
            return True
        elif data['current_home_coin'] >= data['max_home_coin']:
            return True
        else:
            return False
    if mode == 'Resin':
        if data['current_resin'] >= limit:
            return True
        elif data['current_resin'] >= data['max_resin']:
            return True
        else:
            return False
    if mode == 'Go':
        for i in data['expeditions']:
            if i['status'] == 'Ongoing':
                if int(i['remained_time']) <= limit * 60:
                    return True
            else:
                return True
        return False
    if mode == 'Transform':
        if data['transformer']['obtained']:
            time: dict = data['transformer']['recovery_time']
            time_min = (time['Day'] * 24 + time['Hour']) * 60 + time['Minute']
            if time_min <= limit:
                return True
        return False
    return False

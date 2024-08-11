from typing import Dict, List, Union

from gsuid_core.gss import gss
from gsuid_core.logger import logger
from gsuid_core.utils.api.mys.models import DailyNoteData
from gsuid_core.utils.database.models import GsPush, GsUser

from ..utils.mys_api import mys_api
from ..genshinuid_config.gs_config import gsconfig

MR_NOTICE = '\n✅可发送[mr]或者[每日]来查看更多信息！\n'

NOTICE = {
    'coin': '你的洞天宝钱快满啦！',
    'resin': '你的树脂/体力快满啦！',
    'go': '你有派遣奖励即将可领取！',
    'transform': '你的质变仪即将可使用！',
}


async def get_notice_list() -> Dict[str, Dict[str, Dict]]:
    msg_dict = {}
    for bot_id in gss.active_bot:
        user_list: List[GsUser] = await GsUser.get_all_push_user_list()
        for user in user_list:
            if user.uid is None:
                continue
            raw_data = await mys_api.get_daily_data(user.uid)
            if isinstance(raw_data, int):
                logger.error(
                    f'[推送提醒] 获取{user.uid}的数据失败!错误代码为: {raw_data}'
                )
                continue
            push_data = await GsPush.select_data_by_uid(user.uid)
            if push_data is None:
                continue

            msg_dict = await all_check(
                user.bot_id,
                raw_data,
                push_data.__dict__,
                msg_dict,
                user.user_id,
                user.uid,
            )
    return msg_dict


async def all_check(
    bot_id: str,
    raw_data: DailyNoteData,
    push_data: Dict,
    msg_dict: Dict[str, Dict[str, Dict]],
    user_id: str,
    uid: str,
) -> Dict[str, Dict[str, Dict]]:
    for mode in NOTICE.keys():
        # 检查条件
        if push_data[f'{mode}_is_push'] == 'on':
            if not gsconfig.get_config('CrazyNotice').data:
                if not await check(mode, raw_data, push_data[f'{mode}_value']):
                    await GsPush.update_data_by_uid(
                        uid, bot_id, None, **{f'{mode}_is_push': 'off'}
                    )
            continue
        # 准备推送
        _check = await check(mode, raw_data, push_data[f'{mode}_value'])
        if _check:
            if push_data[f'{mode}_push'] == 'off':
                pass
            # on 推送到私聊
            else:
                notice = NOTICE[mode]
                if isinstance(_check, int):
                    notice += f'（当前值: {_check}）'
                # 初始化
                if bot_id not in msg_dict:
                    msg_dict[bot_id] = {'direct': {}, 'group': {}}

                if push_data[f'{mode}_push'] == 'on':
                    # 添加私聊信息
                    if user_id not in msg_dict[bot_id]['direct']:
                        msg_dict[bot_id]['direct'][user_id] = notice
                    else:
                        msg_dict[bot_id]['direct'][user_id] += notice
                    await GsPush.update_data_by_uid(
                        uid, bot_id, None, **{f'{mode}_is_push': 'on'}
                    )
                # 群号推送到群聊
                else:
                    # 初始化
                    gid = push_data[f'{mode}_push']
                    if gid not in msg_dict[bot_id]['group']:
                        msg_dict[bot_id]['group'][gid] = {}

                    if user_id not in msg_dict[bot_id]['group'][gid]:
                        msg_dict[bot_id]['group'][gid][user_id] = notice
                    else:
                        msg_dict[bot_id]['group'][gid][user_id] += notice
                    await GsPush.update_data_by_uid(
                        uid, bot_id, None, **{f'{mode}_is_push': 'on'}
                    )
    return msg_dict


async def check(
    mode: str, data: DailyNoteData, limit: int
) -> Union[bool, int]:
    if mode == 'coin':
        if data['current_home_coin'] >= limit:
            return data['current_home_coin']
        elif data['current_home_coin'] >= data['max_home_coin']:
            return data['current_home_coin']
        else:
            return False
    if mode == 'resin':
        if data['current_resin'] >= limit:
            return data['current_resin']
        elif data['current_resin'] >= data['max_resin']:
            return data['current_resin']
        else:
            return False
    if mode == 'go':
        for i in data['expeditions']:
            if i['status'] == 'Ongoing':
                if int(i['remained_time']) <= limit * 60:
                    return True
            else:
                return True
        return False
    if mode == 'transform':
        if data['transformer']['obtained']:
            time = data['transformer']['recovery_time']
            time_min = (time['Day'] * 24 + time['Hour']) * 60 + time['Minute']
            if time_min <= limit:
                return True
        return False
    return False
    return False

from typing import Dict, List, Union

from gsuid_core.gss import gss
from gsuid_core.logger import logger
from gsuid_core.utils.api.mys.models import DailyNoteData
from gsuid_core.utils.database.models import GsPush, GsUser

from ..utils.message import PREFIX
from ..utils.mys_api import mys_api
from ..utils.api.mys.models import WidgetResin
from ..genshinuid_config.gs_config import gsconfig

MR_NOTICE = f'\n✅可发送[{PREFIX}mr]或者[{PREFIX}每日]来查看更多信息！\n'

NOTICE = {
    'coin': '💰你的洞天宝钱快满啦！',
    'resin': '🌜你的树脂/体力快满啦！',
    'go': '👨‍🏭你有派遣奖励即将可领取！',
    'transform': '⌛你的质变仪即将可使用！',
}


async def get_notice_list() -> Dict[str, Dict[str, Dict]]:
    msg_dict = {}
    for bot_id in gss.active_bot:
        user_list: List[GsUser] = await GsUser.get_all_push_user_list()
        for user in user_list:
            if user.uid is None:
                continue

            # 请求小组件源 或是战绩源
            use_widget = gsconfig.get_config('WidgetResin').data
            if use_widget:
                raw_data = await mys_api.get_widget_resin_data(user.uid)
            else:
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
    raw_data: Union[DailyNoteData, WidgetResin],
    push_data: Dict,
    msg_dict: Dict[str, Dict[str, Dict]],
    user_id: str,
    uid: str,
) -> Dict[str, Dict[str, Dict]]:
    for mode in NOTICE.keys():
        _check = await check(
            mode,
            raw_data,
            push_data[f'{mode}_value'],
        )

        # 检查条件
        if push_data[f'{mode}_is_push'] == 'on':
            if not gsconfig.get_config('CrazyNotice').data:
                if not _check:
                    await GsPush.update_data_by_uid(
                        uid, bot_id, None, **{f'{mode}_is_push': 'off'}
                    )
            continue

        # 准备推送
        if _check:
            if push_data[f'{mode}_push'] == 'off':
                pass
            else:
                notice = NOTICE[mode]
                if isinstance(_check, int):
                    notice += f'（当前值: {_check}）'

                # 初始化
                if bot_id not in msg_dict:
                    msg_dict[bot_id] = {'direct': {}, 'group': {}}
                    direct_data = msg_dict[bot_id]['direct']
                    group_data = msg_dict[bot_id]['group']

                # on 推送到私聊
                if push_data[f'{mode}_push'] == 'on':
                    # 添加私聊信息
                    if user_id not in direct_data:
                        direct_data[user_id] = notice
                    else:
                        direct_data[user_id] += notice
                # 群号推送到群聊
                else:
                    # 初始化
                    gid = push_data[f'{mode}_push']
                    if gid not in group_data:
                        group_data[gid] = {}

                    if user_id not in group_data[gid]:
                        group_data[gid][user_id] = notice
                    else:
                        group_data[gid][user_id] += notice

                await GsPush.update_data_by_uid(
                    uid, bot_id, None, **{f'{mode}_is_push': 'on'}
                )
    return msg_dict


async def check(
    mode: str,
    data: Union[DailyNoteData, WidgetResin],
    limit: int,
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
                if (
                    'remained_time' in i
                    and int(i['remained_time']) <= limit * 60
                ):
                    return True
            else:
                return True
        return False
    if mode == 'transform':
        if 'transformer' in data:
            if data['transformer']['obtained']:
                time = data['transformer']['recovery_time']
                time_min = (time['Day'] * 24 + time['Hour']) * 60 + time[
                    'Minute'
                ]
                if time_min <= limit:
                    return True
            return False
        else:
            logger.warning('[推送提醒] 小组件源不存在质变仪数据...')
            return False
    return False

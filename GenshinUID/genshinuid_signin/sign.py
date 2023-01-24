import random
import asyncio
from copy import deepcopy

from nonebot.log import logger

from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import config_check, get_all_signin_list
from ..utils.mhy_api.get_mhy_data import (
    _pass,
    get_sign_info,
    get_sign_list,
    mihoyo_bbs_sign,
)

private_msg_list = {}
group_msg_list = {}
already = 0


# 签到函数
async def sign_in(uid) -> str:
    if '未找到绑定的UID' in uid:
        return UID_HINT
    logger.info(f'[签到] {uid} 开始执行签到')
    # 获得签到信息
    sign_info = await get_sign_info(uid)
    # 初步校验数据
    if sign_info and 'data' in sign_info and sign_info['data']:
        sign_info = sign_info['data']
    else:
        logger.warning(f'[签到] {uid} 出错, 请检查Cookies是否过期！')
        return '签到失败...请检查Cookies是否过期！'
    # 检测是否已签到
    if sign_info['is_sign']:
        logger.info(f'[签到] {uid} 该用户今日已签到,跳过...')
        global already
        already += 1
        day_of_month = int(sign_info['today'].split('-')[-1])
        signed_count = int(sign_info['total_sign_day'])
        sign_missed = day_of_month - signed_count
        return f'今日已签到！本月漏签次数：{sign_missed}'

    # 实际进行签到
    Header = {}
    for index in range(4):
        # 进行一次签到
        sign_data = await mihoyo_bbs_sign(uid=uid, Header=Header)
        logger.info(sign_data)
        # 检测数据
        if sign_data and 'data' in sign_data and sign_data['data']:
            if 'risk_code' in sign_data['data']:
                # 出现校验码
                if sign_data['data']['risk_code'] == 375:
                    if await config_check('CaptchaPass'):
                        gt = sign_data['data']['gt']
                        ch = sign_data['data']['challenge']
                        vl, ch = await _pass(gt, ch, Header)
                        if vl:
                            delay = 1
                            Header['x-rpc-challenge'] = ch
                            Header['x-rpc-validate'] = vl
                            Header['x-rpc-seccode'] = f'{vl}|jordan'
                            logger.info(f'[签到] {uid} 已获取验证码, 等待时间{delay}秒')
                            await asyncio.sleep(delay)
                        else:
                            delay = 605 + random.randint(1, 120)
                            logger.info(f'[签到] {uid} 未获取验证码,等待{delay}秒后重试...')
                            await asyncio.sleep(delay)
                        continue
                    else:
                        logger.info('配置文件暂未开启[跳过无感验证],结束本次任务...')
                    return '签到失败...出现验证码!'
                # 成功签到!
                else:
                    if index == 0:
                        logger.info(f'[签到] {uid} 该用户无校验码!')
                    else:
                        logger.info(f'[签到] [无感验证] {uid} 该用户重试 {index} 次验证成功!')
                    break
            elif (int(str(uid)[0]) > 5) and (
                sign_data['data']['code'] == 'ok'
            ):
                # 国际服签到无risk_code字段
                logger.info(f'[国际服签到] {uid} 签到成功!')
                break
            else:
                # 重试超过阈值
                logger.warning('[签到] 超过请求阈值...')
                return '签到失败...出现验证码!\n请过段时间使用[签到]或由管理员[全部重签]或手动至米游社进行签到！'
    # 签到失败
    else:
        im = '签到失败!'
        logger.warning(f'[签到] {uid} 签到失败, 结果: {im}')
        return im
    # 获取签到列表
    sign_list = await get_sign_list(uid)
    status = sign_data['message']
    # 获取签到奖励物品，拿旧的总签到天数 + 1 为新的签到天数，再 -1 即为今日奖励物品的下标
    getitem = sign_list['data']['awards'][
        int(sign_info['total_sign_day']) + 1 - 1
    ]
    get_im = f'本次签到获得{getitem["name"]}x{getitem["cnt"]}'
    new_sign_info = await get_sign_info(uid)
    new_sign_info = new_sign_info['data']
    day_of_month = int(new_sign_info['today'].split('-')[-1])
    signed_count = int(new_sign_info['total_sign_day'])
    sign_missed = day_of_month - signed_count
    if new_sign_info['is_sign']:
        mes_im = '签到成功'
    else:
        mes_im = f'签到失败, 状态为:{status}'
        sign_missed -= 1
    sign_missed = sign_info.get('sign_cnt_missed') or sign_missed
    im = f'{mes_im}!\n{get_im}\n本月漏签次数：{sign_missed}'
    logger.info(f'[签到] {uid} 签到完成, 结果: {mes_im}, 漏签次数: {sign_missed}')
    return im


async def single_daily_sign(uid: str, gid: str, qid: str):
    if gid == 'on':
        im = await sign_in(str(uid))
        # 多人推送情况
        if qid in group_msg_list:
            group_msg_list[qid] += '\n' + im
        else:
            private_msg_list[qid] = im
    else:
        im = await sign_in(str(uid))
        # 向群消息推送列表添加这个群
        if gid not in group_msg_list:
            group_msg_list[gid] = {
                'success': 0,
                'failed': 0,
                'push_message': '',
            }
        # 检查是否开启简洁签到
        if await config_check('SignReportSimple'):
            # 如果失败, 则添加到推送列表
            if im.startswith('签到失败') or im.startswith('网络有点忙'):
                # 不用MessageSegment.at(row[2])，因为不方便移植
                message = f'[CQ:at,qq={qid}] {im}'
                group_msg_list[gid]['failed'] += 1
                group_msg_list[gid]['push_message'] += '\n' + message
            else:
                group_msg_list[gid]['success'] += 1
        # 没有开启简洁签到, 则每条消息都要携带@信息
        else:
            # 不用MessageSegment.at(row[2])，因为不方便移植
            message = f'[CQ:at,qq={qid}] {im}'
            group_msg_list[gid]['push_message'] += '\n' + message
            group_msg_list[gid]['success'] -= 1


async def daily_sign():
    """
    :说明:
      将数据库中全部Status不为`off`的用户进行签到,
      并返回签到信息private_msg_list, group_msg_list,
      private_msg_list = [{'qid': 'msg'}, ...],
      group_msg_list = [
        {'gid': {'success': 0, 'failed': 0, 'push_message': ''}}, ...
      ],
      如开启简洁签到,
      success = 签到成功数,
      failed = 签到失败数,
      不开启简洁签到,
      success将为负数,
    :返回:
      * {'private_msg_list': ..., 'group_msg_list': ...} (dict): 要发送的私聊消息和群聊消息
    """
    c_data = await get_all_signin_list()
    global already
    tasks = []
    for row in c_data:
        tasks.append(single_daily_sign(row['UID'], row['StatusB'], row['QID']))
        if len(tasks) >= 1:
            await asyncio.gather(*tasks)
            if already >= 1:
                delay = 1
            else:
                delay = 50 + random.randint(3, 45)
            logger.info(f'[签到] 已签到{len(tasks)}个用户, 等待{delay}秒进行下一次签到')
            tasks.clear()
            already = 0
            await asyncio.sleep(delay)
    await asyncio.gather(*tasks)
    tasks.clear()
    result = {
        'private_msg_list': deepcopy(private_msg_list),
        'group_msg_list': deepcopy(group_msg_list),
    }
    private_msg_list.clear()
    group_msg_list.clear()
    logger.info(result)
    return result

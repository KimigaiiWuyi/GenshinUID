import random
import asyncio
from copy import deepcopy

from gsuid_core.gss import gss
from gsuid_core.logger import logger
from gsuid_core.utils.plugins_config.gs_config import core_plugins_config

from ..utils.mys_api import mys_api
from ..utils.database import get_sqla
from ..genshinuid_config.gs_config import gsconfig

private_msg_list = {}
group_msg_list = {}
already = 0


# 签到函数
async def sign_in(uid: str) -> str:
    logger.info(f'[签到] {uid} 开始执行签到')
    # 获得签到信息
    sign_info = await mys_api.get_sign_info(uid)
    # 初步校验数据
    if isinstance(sign_info, int):
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
        sign_data = await mys_api.mys_sign(uid=uid, header=Header)
        # 检测数据
        if isinstance(sign_data, int):
            logger.warning(f'[签到] {uid} 出错, 请检查Cookies是否过期！')
            return '签到失败...请检查Cookies是否过期！'
        if 'risk_code' in sign_data:
            # 出现校验码
            if sign_data['risk_code'] == 375:
                if core_plugins_config.get_config('CaptchaPass').data:
                    gt = sign_data['gt']
                    ch = sign_data['challenge']
                    vl, ch = await mys_api._pass(gt, ch, Header)
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
        elif (int(str(uid)[0]) > 5) and (sign_data['data']['code'] == 'ok'):
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
    sign_list = await mys_api.get_sign_list(uid)
    new_sign_info = await mys_api.get_sign_info(uid)
    if isinstance(sign_list, int) or isinstance(new_sign_info, int):
        logger.warning(f'[签到] {uid} 出错, 请检查Cookies是否过期！')
        return '签到失败...请检查Cookies是否过期！'
    # 获取签到奖励物品，拿旧的总签到天数 + 1 为新的签到天数，再 -1 即为今日奖励物品的下标
    getitem = sign_list['awards'][int(sign_info['total_sign_day']) + 1 - 1]
    get_im = f'本次签到获得{getitem["name"]}x{getitem["cnt"]}'
    day_of_month = int(new_sign_info['today'].split('-')[-1])
    signed_count = int(new_sign_info['total_sign_day'])
    sign_missed = day_of_month - signed_count
    if new_sign_info['is_sign']:
        mes_im = '签到成功'
    else:
        mes_im = '签到失败...'
        sign_missed -= 1
    sign_missed = sign_info.get('sign_cnt_missed') or sign_missed
    im = f'{mes_im}!\n{get_im}\n本月漏签次数：{sign_missed}'
    logger.info(f'[签到] {uid} 签到完成, 结果: {mes_im}, 漏签次数: {sign_missed}')
    return im


async def single_daily_sign(bot_id: str, uid: str, gid: str, qid: str):
    im = await sign_in(uid)
    if gid == 'on':
        if qid not in private_msg_list:
            private_msg_list[qid] = []
        private_msg_list[qid].append({'bot_id': bot_id, 'uid': uid, 'msg': im})
    else:
        # 向群消息推送列表添加这个群
        if gid not in group_msg_list:
            group_msg_list[gid] = {
                'bot_id': bot_id,
                'success': 0,
                'failed': 0,
                'push_message': '',
            }
        # 检查是否开启简洁签到
        if gsconfig.get_config('SignReportSimple').data:
            # 如果失败, 则添加到推送列表
            if im.startswith(('签到失败', '网络有点忙', 'OK', 'ok')):
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
    global already
    tasks = []
    for bot_id in gss.active_bot:
        sqla = get_sqla(bot_id)
        user_list = await sqla.get_all_user()
        for user in user_list:
            if user.sign_switch != 'off':
                tasks.append(
                    single_daily_sign(
                        user.bot_id, user.uid, user.sign_switch, user.user_id
                    )
                )
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

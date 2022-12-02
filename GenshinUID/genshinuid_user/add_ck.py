from pathlib import Path
from http.cookies import SimpleCookie

from nonebot.log import logger

from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_cache_and_check import refresh_ck
from ..utils.db_operation.db_operation import select_db, stoken_db, cookies_db
from ..utils.mhy_api.get_mhy_data import (
    get_mihoyo_bbs_info,
    get_cookie_token_by_stoken,
    get_stoken_by_login_ticket,
)

pic_path = Path(__file__).parent / 'pic'
id_list = [
    'login_uid',
    'login_uid_v2',
    'account_mid_v2',
    'account_mid',
    'account_id',
    'stuid',
    'ltuid',
    'ltmid',
    'stmid',
    'stmid_v2',
    'ltmid_v2',
    'stuid_v2',
    'ltuid_v2',
]
sk_list = ['stoken', 'stoken_v2']
ck_list = ['cookie_token', 'cookie_token_v2']
lt_list = ['login_ticket', 'login_ticket_v2']


async def deal_ck(mes, qid, mode: str = 'PIC'):
    im = await _deal_ck(mes, qid)
    if mode == 'PIC':
        im = await _deal_ck_to_pic(im)
    return im


async def _deal_ck_to_pic(im: str) -> bytes:
    ok_num = im.count('成功')
    if ok_num < 1:
        status_pic = pic_path / 'ck_no.png'
    elif ok_num < 2:
        status_pic = pic_path / 'ck_ok.png'
    else:
        status_pic = pic_path / 'all_ok.png'
    with open(status_pic, 'rb') as f:
        img = f.read()
    return img


async def get_account_id(simp_dict: SimpleCookie) -> str:
    for _id in id_list:
        if _id in simp_dict:
            account_id = simp_dict[_id].value
            break
    else:
        account_id = ''
    return account_id


async def _deal_ck(mes, qid) -> str:
    simp_dict = SimpleCookie(mes)
    uid = await select_db(qid, mode='uid')
    if isinstance(uid, str):
        if '未找到绑定的UID' in uid:
            return UID_HINT
    else:
        return UID_HINT
    im_list = []
    is_add_stoken = False
    status = True
    app_cookie, stoken = '', ''
    account_id, cookie_token = '', ''
    if status:
        for lt in lt_list:
            if lt in simp_dict:
                # 寻找stoken
                login_ticket = simp_dict[lt].value
                account_id = await get_account_id(simp_dict)
                if not account_id:
                    return '该CK字段出错, 缺少login_uid或stuid或ltuid字段!'
                stoken_data = await get_stoken_by_login_ticket(
                    login_ticket, account_id
                )
                stoken = stoken_data['data']['list'][0]['token']
                app_cookie = f'stuid={account_id};stoken={stoken}'
                cookie_token_data = await get_cookie_token_by_stoken(
                    stoken, account_id
                )
                cookie_token = cookie_token_data['data']['cookie_token']
                is_add_stoken = True
                status = False
                break
    if status:
        for sk in sk_list:
            if sk in simp_dict:
                account_id = await get_account_id(simp_dict)
                if not account_id:
                    return '该CK字段出错, 缺少login_uid或stuid或ltuid字段!'
                stoken = simp_dict[sk].value
                if stoken.startswith('v2_'):
                    if 'mid' in simp_dict:
                        mid = simp_dict['mid'].value
                        app_cookie = (
                            f'stuid={account_id};stoken={stoken};mid={mid}'
                        )
                    else:
                        return 'v2类型SK必须携带mid...'
                else:
                    app_cookie = f'stuid={account_id};stoken={stoken}'
                cookie_token_data = await get_cookie_token_by_stoken(
                    stoken, account_id
                )
                cookie_token = cookie_token_data['data']['cookie_token']
                is_add_stoken = True
                status = False
                break
    if status:
        for ck in ck_list:
            if ck in simp_dict:
                # 寻找uid
                account_id = await get_account_id(simp_dict)
                if not account_id:
                    return '该CK字段出错, 缺少login_uid或stuid或ltuid字段!'
                cookie_token = simp_dict[ck].value
                status = False
                break
    if status:
        return (
            '添加Cookies失败!Cookies中应该包含cookie_token或者login_ticket相关信息！'
            '\n可以尝试退出米游社登陆重新登陆获取！'
        )

    account_cookie = f'account_id={account_id};cookie_token={cookie_token}'

    try:
        if int(uid[0]) < 6:
            mys_data = await get_mihoyo_bbs_info(account_id, account_cookie)
        else:
            mys_data = await get_mihoyo_bbs_info(
                account_id, account_cookie, True
            )
        # 剔除除了原神之外的其他游戏
        if mys_data:
            for i in mys_data['data']['list']:
                if i['game_id'] == 2:
                    uid = i['game_role_id']
                    break
            else:
                return f'你的米游社账号{account_id}尚未绑定原神账号，请前往米游社操作！'
        else:
            logger.warning('该CK似乎未通过校验, 这并不影响正常使用...但可能会造成奇怪的问题...')
    except:
        print('Null mys_data')

    if not uid:
        return f'你的米游社账号{account_id}尚未绑定原神账号，请前往米游社操作！'

    await refresh_ck(uid, account_id)
    await cookies_db(uid, account_cookie, qid)
    if is_add_stoken:
        await stoken_db(app_cookie, uid)
        im_list.append(f'添加Stoken成功，stuid={account_id}，stoken={stoken}')
    im_list.append(
        f'添加Cookies成功，account_id={account_id}，cookie_token={cookie_token}'
    )
    im_list.append(
        'Cookies和Stoken属于个人重要信息，如果你是在不知情的情况下添加，请马上修改米游社账户密码，保护个人隐私！'
    )
    im_list.append(
        (
            '如果需要【gs开启自动签到】和【gs开启推送】还需要在【群聊中】使用命令“绑定uid”绑定你的uid。'
            '\n例如：绑定uid123456789。'
        )
    )
    im_list.append('你可以使用命令【绑定信息】检查你的账号绑定情况！')
    im = '\n'.join(im_list)
    return im

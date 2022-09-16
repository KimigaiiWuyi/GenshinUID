from pathlib import Path
from http.cookies import SimpleCookie

from ..utils.db_operation.db_cache_and_check import refresh_ck
from ..utils.db_operation.db_operation import select_db, stoken_db, cookies_db
from ..utils.mhy_api.get_mhy_data import (
    get_mihoyo_bbs_info,
    get_cookie_token_by_stoken,
    get_stoken_by_login_ticket,
)

pic_path = Path(__file__).parent / 'pic'


async def deal_ck(mes, qid, mode: str = 'PIC'):
    im = await _deal_ck(mes, qid)
    if mode == 'PIC':
        im = await _deal_ck_to_pic(im)
    return im


async def _deal_ck_to_pic(im) -> bytes:
    ok_num = im.count('成功')
    if ok_num < 1:
        status_pic = pic_path / 'ck_no.png'
    elif ok_num < 2:
        status_pic = pic_path / 'ck_ok.png'
    else:
        status_pic = pic_path / 'all_ok.png'
    with open(status_pic, 'rb') as f:
        im = f.read()
    return im


async def _deal_ck(mes, qid) -> str:
    simp_dict = SimpleCookie(mes)
    '''
    uid = await select_db(qid, 'uid')
    if isinstance(uid, str):
        pass
    else:
        return '该用户没有绑定过UID噢~'
    '''
    im_list = []
    is_add_stoken = False
    app_cookie, stoken = '', ''
    if 'login_ticket' in simp_dict:
        # 寻找stoken
        login_ticket = simp_dict['login_ticket'].value
        if 'login_uid' in simp_dict:
            account_id = simp_dict['login_uid'].value
        elif 'stuid' in simp_dict:
            account_id = simp_dict['stuid'].value
        elif 'ltuid' in simp_dict:
            account_id = simp_dict['ltuid'].value
        else:
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
    elif 'cookie_token' in simp_dict:
        # 寻找uid
        account_id = simp_dict['account_id'].value
        cookie_token = simp_dict['cookie_token'].value
    else:
        return (
            '添加Cookies失败!Cookies中应该包含cookie_token或者login_ticket相关信息！'
            '\n可以尝试退出米游社登陆重新登陆获取！'
        )
    account_cookie = f'account_id={account_id};cookie_token={cookie_token}'
    mys_data = await get_mihoyo_bbs_info(account_id, account_cookie)
    # 剔除除了原神之外的其他游戏
    for i in mys_data['data']['list']:
        if i['game_id'] == 2:
            uid = i['game_role_id']
            break
    else:
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

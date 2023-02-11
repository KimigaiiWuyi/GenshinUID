import io
import json
import base64
import asyncio
from http.cookies import SimpleCookie
from typing import Any, List, Tuple, Union, Literal, NoReturn

import qrcode
from nonebot.log import logger
from nonebot.matcher import Matcher
from qrcode.constants import ERROR_CORRECT_L
from nonebot.adapters.ntchat import MessageSegment

from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..utils.mhy_api.get_mhy_data import (
    check_qrcode,
    get_cookie_token,
    create_qrcode_url,
    get_mihoyo_bbs_info,
    get_stoken_by_game_token,
    get_cookie_token_by_stoken,
)

disnote = '''免责声明：您将通过扫码完成获取米游社sk以及ck。
登录米游社相当于将账号授权于机器人，可能会带来未知的账号风险。
若您的账号封禁、被盗等处罚与我方无关。
登录后即代表您同意机器人使用协议并知晓会带来未知的账号风险！
若想取消授权，请到米游社退出登录以清除机器人绑定的登录状态。

请用米游社/原神扫描下方二维码登录：'''


def get_qrcode_base64(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    img_byte = io.BytesIO()
    img.save(img_byte, format='PNG')  # type: ignore
    img_byte = img_byte.getvalue()
    return base64.b64encode(img_byte).decode()


async def refresh(
    code_data: dict,
) -> Union[Tuple[Literal[False], None], Tuple[Literal[True], Any]]:
    scanned = False
    while True:
        await asyncio.sleep(2)
        status_data = await check_qrcode(
            code_data['app_id'], code_data['ticket'], code_data['device']
        )
        if status_data['retcode'] != 0:
            logger.warning('二维码已过期')
            return False, None
        if status_data['data']['stat'] == 'Scanned':
            if not scanned:
                logger.info('二维码已扫描')
                scanned = True
            continue
        if status_data['data']['stat'] == 'Confirmed':
            logger.info('二维码已确认')
            break
    return True, json.loads(status_data['data']['payload']['raw'])


async def qrcode_login(matcher: Matcher, user_id) -> str:
    async def send_group_msg(msg: str, at_list: List) -> NoReturn:
        await matcher.finish(
            MessageSegment.room_at_msg(content=msg, at_list=at_list)
        )

    wxid_list = []
    wxid_list.append(user_id)
    code_data = await create_qrcode_url()
    try:
        await matcher.send(
            MessageSegment.image(
                f'base64://{get_qrcode_base64(code_data["url"])}'
            )
        )
        await matcher.send(
            MessageSegment.room_at_msg(
                content='{$@}' + disnote, at_list=wxid_list
            )
        )
    except Exception:
        logger.warning('[扫码登录] {user_id} 图片发送失败')
    status, game_token_data = await refresh(code_data)
    if status:
        assert game_token_data is not None  # 骗过 pyright
        logger.info('[扫码登录]game_token获取成功')
        cookie_token = await get_cookie_token(**game_token_data)
        stoken_data = await get_stoken_by_game_token(
            account_id=int(game_token_data['uid']),
            game_token=game_token_data['token'],
        )
        account_id = game_token_data['uid']
        stoken = stoken_data['data']['token']['token']
        mid = stoken_data['data']['user_info']['mid']
        app_cookie = f'stuid={account_id};stoken={stoken};mid={mid}'
        ck = await get_cookie_token_by_stoken(stoken, account_id, app_cookie)
        ck = ck['data']['cookie_token']
        cookie_check = f'account_id={account_id};cookie_token={ck}'
        get_uid = await get_mihoyo_bbs_info(account_id, cookie_check)
        im = None
        if get_uid:
            for i in get_uid['data']['list']:
                if i['game_id'] == 2:
                    uid_check = i['game_role_id']
                    break
            else:
                im = f'你的米游社账号{account_id}尚未绑定原神账号，请前往米游社操作！'
                await send_group_msg(im, wxid_list)
        else:
            im = '请求失败, 请稍后再试...'
            await send_group_msg(im, wxid_list)

        uid_bind = await select_db(user_id, mode='uid')
        if uid_bind == "未找到绑定的UID~":
            logger.warning('game_token获取失败')
            await matcher.finish(UID_HINT)
        if str(uid_bind) == uid_check or str(uid_bind) == account_id:
            return SimpleCookie(
                {
                    'stoken_v2': stoken_data['data']['token']['token'],
                    'stuid': stoken_data['data']['user_info']['aid'],
                    'mid': stoken_data['data']['user_info']['mid'],
                    'cookie_token': cookie_token['data']['cookie_token'],
                }
            ).output(header='', sep=';')
        else:
            logger.warning('game_token获取失败：非触发者本人扫码')
            im = (
                '{$@}' + f'检测到扫码登录UID{uid_check}与绑定UID{uid_bind}不同,'
                'gametoken获取失败，请重新发送[扫码登录]进行登录'
            )
            await send_group_msg(im, wxid_list)
    else:
        logger.warning('game_token获取失败')
        await send_group_msg('{$@}game_token获取失败：二维码已过期', wxid_list)

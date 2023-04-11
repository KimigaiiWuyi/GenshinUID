import io
import json
import base64
import asyncio
from http.cookies import SimpleCookie
from typing import Any, List, Tuple, Union, Literal

import qrcode
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger
from qrcode.constants import ERROR_CORRECT_L
from gsuid_core.segment import MessageSegment

from ..utils.mys_api import mys_api
from ..utils.database import get_sqla

disnote = '''免责声明:您将通过扫码完成获取米游社sk以及ck。
本Bot将不会保存您的登录状态。
我方仅提供米游社查询及相关游戏内容服务
若您的账号封禁、被盗等处罚与我方无关。
害怕风险请勿扫码!
'''


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
        status_data = await mys_api.check_qrcode(
            code_data['app_id'], code_data['ticket'], code_data['device']
        )
        if isinstance(status_data, int):
            logger.warning('二维码已过期')
            return False, None
        if status_data['stat'] == 'Scanned':
            if not scanned:
                logger.info('二维码已扫描')
                scanned = True
            continue
        if status_data['stat'] == 'Confirmed':
            logger.info('二维码已确认')
            break
    return True, json.loads(status_data['payload']['raw'])


async def qrcode_login(bot: Bot, ev: Event, user_id: str) -> str:
    sqla = get_sqla(ev.bot_id)

    async def send_msg(msg: str):
        await bot.send(msg)
        return ''

    code_data = await mys_api.create_qrcode_url()
    if isinstance(code_data, int):
        return await send_msg('链接创建失败...')
    try:
        im = []
        im.append(MessageSegment.text('请使用米游社扫描下方二维码登录：'))
        im.append(
            MessageSegment.image(
                f'base64://{get_qrcode_base64(code_data["url"])}'
            )
        )
        im.append(
            MessageSegment.text(
                '免责声明:您将通过扫码完成获取米游社sk以及ck。\n'
                '本Bot将不会保存您的登录状态。\n'
                '我方仅提供米游社查询及相关游戏内容服务,\n'
                '若您的账号封禁、被盗等处罚与我方无关。\n'
                '害怕风险请勿扫码~'
            )
        )
        await bot.send(MessageSegment.node(im))
    except Exception as e:
        logger.error(e)
        logger.warning(f'[扫码登录] {user_id} 图片发送失败')
    status, game_token_data = await refresh(code_data)
    if status:
        assert game_token_data is not None  # 骗过 pyright
        logger.info('game_token获取成功')
        cookie_token = await mys_api.get_cookie_token(**game_token_data)
        stoken_data = await mys_api.get_stoken_by_game_token(
            account_id=int(game_token_data['uid']),
            game_token=game_token_data['token'],
        )
        if isinstance(stoken_data, int):
            return await send_msg('获取SK失败...')
        account_id = game_token_data['uid']
        stoken = stoken_data['token']['token']
        mid = stoken_data['user_info']['mid']
        app_cookie = f'stuid={account_id};stoken={stoken};mid={mid}'
        ck = await mys_api.get_cookie_token_by_stoken(
            stoken, account_id, app_cookie
        )
        if isinstance(ck, int):
            return await send_msg('获取CK失败...')
        ck = ck['cookie_token']
        cookie_check = f'account_id={account_id};cookie_token={ck}'
        get_uid = await mys_api.get_mihoyo_bbs_info(account_id, cookie_check)
        # 剔除除了原神之外的其他游戏
        im = None
        if isinstance(get_uid, List):
            for i in get_uid:
                if i['game_id'] == 2:
                    uid_check = i['game_role_id']
                    break
            else:
                im = f'你的米游社账号{account_id}尚未绑定原神账号，请前往米游社操作！'
                return await send_msg(im)
        else:
            im = '请求失败, 请稍后再试...'
            return await send_msg(im)

        uid_bind = await sqla.get_bind_uid(user_id)
        # 没有在gsuid绑定uid的情况
        if not uid_bind:
            logger.warning('game_token获取失败')
            im = '你还没有绑定uid, 请输入[绑定uid123456]绑定你的uid, 再发送[扫码登录]进行绑定'
            return await send_msg(im)
        if isinstance(cookie_token, int):
            return await send_msg('获取CK失败...')
        # 比对gsuid数据库和扫码登陆获取到的uid
        if str(uid_bind) == uid_check or str(uid_bind) == account_id:
            return SimpleCookie(
                {
                    'stoken_v2': stoken_data['token']['token'],
                    'stuid': stoken_data['user_info']['aid'],
                    'mid': stoken_data['user_info']['mid'],
                    'cookie_token': cookie_token['cookie_token'],
                }
            ).output(header='', sep=';')
        else:
            logger.warning('game_token获取失败')
            im = (
                f'检测到扫码登录UID{uid_check}与绑定UID{uid_bind}不同, '
                'gametoken获取失败, 请重新发送[扫码登录]进行登录！'
            )
    else:
        logger.warning('game_token获取失败')
        im = 'game_token获取失败: 二维码已过期'
    return await send_msg(im)

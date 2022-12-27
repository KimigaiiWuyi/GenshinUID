import io
import json
import base64
import asyncio
from http.cookies import SimpleCookie
from typing import Any, Tuple, Union, Literal

import qrcode
from PIL import Image
from nonebot.log import logger
from qrcode.constants import ERROR_CORRECT_L

from ..utils.mhy_api.get_mhy_data import (
    check_qrcode,
    get_cookie_token,
    create_qrcode_url,
    get_stoken_by_game_token,
)


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
            # print(status_data['data']['payload']['raw'])
            break
    return True, json.loads(status_data['data']['payload']['raw'])


async def qrcode_login(bot, user_id) -> str:
    code_data = await create_qrcode_url()
    im = (
        '请扫描下方二维码登录：'
        f'[CQ:image,file=base64://{get_qrcode_base64(code_data["url"])}]'
    )
    try:
        await bot.call_api(
            api='send_private_msg',
            user_id=user_id,
            message=im,
        )
    except Exception:
        logger.warning('[扫码登录] {user_id} 图片发送失败')
    status, game_token_data = await refresh(code_data)
    if status:
        assert game_token_data is not None  # 骗过 pyright
        logger.info('game_token获取成功')
        cookie_token = await get_cookie_token(**game_token_data)
        stoken_data = await get_stoken_by_game_token(
            account_id=int(game_token_data['uid']),
            game_token=game_token_data['token'],
        )
        return SimpleCookie(
            {
                'stoken_v2': stoken_data['data']['token']['token'],
                'stuid': stoken_data['data']['user_info']['aid'],
                'mid': stoken_data['data']['user_info']['mid'],
                'cookie_token': cookie_token['data']['cookie_token'],
            }
        ).output(header='', sep=';')
    else:
        logger.warning('game_token获取失败')
        await bot.call_api(
            api='send_private_msg',
            user_id=user_id,
            message='game_token获取失败：二维码已过期',
        )
        return ''

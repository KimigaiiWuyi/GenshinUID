import io
import json
import base64
import asyncio
from http.cookies import SimpleCookie
from typing import Any, Tuple, Union, Literal

import qrcode
from nonebot.log import logger

from ..utils.message.send_msg import send_forward_msg
from ..utils.db_operation.db_operation import select_db
from ..utils.mhy_api.get_mhy_data import (
    check_qrcode,
    get_cookie_token,
    create_qrcode_url,
    get_mihoyo_bbs_info,
    get_stoken_by_game_token,
    get_cookie_token_by_stoken,
)

disnote = '''免责声明:您将通过扫码完成获取米游社sk以及ck。
本Bot将不会保存您的登录状态。
我方仅提供米游社查询及相关游戏内容服务
若您的账号封禁、被盗等处罚与我方无关。
害怕风险请勿扫码!
'''


def get_qrcode_base64(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_byte = io.BytesIO()
    img.save(img_byte, format="PNG")
    img_byte = img_byte.getvalue()
    return base64.b64encode(img_byte).decode()


async def refresh(
    code_data: dict,
) -> Union[Tuple[Literal[False], None], Tuple[Literal[True], Any]]:
    scanned = False
    while True:
        await asyncio.sleep(2)
        status_data = await check_qrcode(
            code_data["app_id"], code_data["ticket"], code_data["device"]
        )
        if status_data["retcode"] != 0:
            logger.warn("二维码已过期")
            return False, None
        if status_data["data"]["stat"] == "Scanned":
            if not scanned:
                logger.info("二维码已扫描")
                scanned = True
            continue
        if status_data["data"]["stat"] == "Confirmed":
            logger.info("二维码已确认")
            # print(status_data["data"]["payload"]["raw"])
            break
    return True, json.loads(status_data["data"]["payload"]["raw"])


async def qrcode_login(bot, group_id, user_id) -> str:
    async def send_group_msg(msg: str):
        await bot.call_action(
            action='send_group_msg',
            group_id=group_id,
            message=msg,
        )
        return ""

    code_data = await create_qrcode_url()
    try:
        im = []
        qrc = f'[CQ:image,file=base64://{get_qrcode_base64(code_data["url"])}]'
        im.append('请使用米游社扫描下方二维码登录：')
        im.append(qrc)
        im.append(disnote)
        await send_forward_msg(bot, group_id, "扫码小助手", str(user_id), im)
    except Exception:
        logger.warn(f"[扫码登录] {group_id} 图片发送失败")
    status, game_token_data = await refresh(code_data)
    if status:
        assert game_token_data is not None  # 骗过 pyright
        logger.info("game_token获取成功")
        cookie_token = await get_cookie_token(**game_token_data)
        stoken_data = await get_stoken_by_game_token(
            account_id=int(game_token_data["uid"]),
            game_token=game_token_data["token"],
        )
        account_id = game_token_data['uid']
        stoken = stoken_data['data']['token']['token']
        mid = stoken_data['data']['user_info']['mid']
        app_cookie = f'stuid={account_id};stoken={stoken};mid={mid}'
        ck = await get_cookie_token_by_stoken(stoken, account_id, app_cookie)
        ck = ck['data']['cookie_token']
        cookie_check = f'account_id={account_id};cookie_token={ck}'
        get_uid = await get_mihoyo_bbs_info(account_id, cookie_check)
        # 剔除除了原神之外的其他游戏
        im = None
        if get_uid:
            for i in get_uid['data']['list']:
                if i['game_id'] == 2:
                    uid_check = i['game_role_id']
                    break
            else:
                im = f'你的米游社账号{account_id}尚未绑定原神账号，请前往米游社操作！'
                return await send_group_msg(im)
        else:
            im = '请求失败, 请稍后再试...'
            return await send_group_msg(im)
        uid_bind = await select_db(user_id, mode='uid')
        # 没有在gsuid绑定uid的情况
        if uid_bind == "未找到绑定的UID~":
            logger.warning('game_token获取失败')
            im = '你还没有绑定uid，请输入[绑定uid123456]绑定你的uid，再发送[扫码登录]进行绑定'
            return await send_group_msg(im)
        # 比对gsuid数据库和扫码登陆获取到的uid
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
            logger.warning('game_token获取失败')
            im = 'game_token获取失败：被非绑定指定uid用户扫取，取消绑定，请重新发送[扫码登录]登录账号'
    else:
        logger.warning('game_token获取失败')
        im = 'game_token获取失败：二维码已过期'
    return await send_group_msg(im)

import io
import json
import time
import uuid
import base64
import random
import asyncio
from hashlib import md5
from string import digits, ascii_letters

import qrcode
import hoshino.aiorequests as aiorequests

CN_DS_SALT = "JwYDpKvLj6MrMqqYU6jTKF17KNO2PXoS"


def _md5(self) -> str:
    return md5(self.encode()).hexdigest()


def ds(body=None, query=None) -> str:
    t = int(time.time())
    r = "".join(random.choices(ascii_letters, k=6))
    b = json.dumps(body) if body else ""
    q = "&".join(f"{k}={v}" for k, v in sorted(query.items())) if query else ""
    h = _md5(f"salt={CN_DS_SALT}&t={t}&r={r}&b={b}&q={q}")
    return f"{t},{r},{h}"


async def get_stoken(aigis: str = "", data: dict = {}):
    resp = await aiorequests.post(
        url="https://passport-api.mihoyo.com/account/ma-cn-session/app/getTokenByGameToken",
        headers={
            "x-rpc-app_version": "2.41.0",
            "DS": ds(data),
            "x-rpc-aigis": aigis,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-rpc-game_biz": "bbs_cn",
            "x-rpc-sys_version": "11",
            "x-rpc-device_id": uuid.uuid4().hex,
            "x-rpc-device_fp": "".join(
                random.choices(ascii_letters + digits, k=13)
            ),
            "x-rpc-device_name": "GenshinUid_login_device_lulu",
            "x-rpc-device_model": "GenshinUid_login_device_lulu",
            "x-rpc-app_id": "bll8iq97cem8",
            "x-rpc-client_type": "2",
            "User-Agent": "okhttp/4.8.0",
        },
        json=data,
        proxies={
            "http": None,
            "https": None,
        },
    )
    return await resp.json()


def showqrcode(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("qrcode.png")
    # 打印到终端
    qr.print_ascii(invert=True)


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


async def createurl():
    device_id: str = "".join(random.choices(ascii_letters + digits, k=64))
    app_id: str = "4"
    data = {"app_id": app_id, "device": device_id}
    res = await aiorequests.post(
        url="https://hk4e-sdk.mihoyo.com/hk4e_cn/combo/panda/qrcode/fetch?",
        json=data,
        proxies={"http": None, "https": None},
    )
    # print(res.text)
    url = (await res.json())["data"]["url"]
    ticket = url.split("ticket=")[1]
    return {
        "app_id": app_id,
        "ticket": ticket,
        "device": device_id,
        "url": url,
    }


async def check(code_data: dict):
    data = {
        "app_id": code_data["app_id"],
        "ticket": code_data["ticket"],
        "device": code_data["device"],
    }
    res = await aiorequests.post(
        url="https://hk4e-sdk.mihoyo.com/hk4e_cn/combo/panda/qrcode/query?",
        json=data,
        proxies={"http": None, "https": None},
    )
    return await res.json()


async def refresh(code_data: dict):
    scanned = False
    while True:
        await asyncio.sleep(2)
        status_data = await check(code_data)
        if status_data["retcode"] != 0:
            print("二维码已过期")
            return -1, None
        if status_data["data"]["stat"] == "Scanned":
            if not scanned:
                print("二维码已扫描")
                scanned = True
            continue
        if status_data["data"]["stat"] == "Confirmed":
            print("二维码已确认")
            # print(status_data["data"]["payload"]["raw"])
            break
    return 0, json.loads(status_data["data"]["payload"]["raw"])


async def get_cookie_token(game_token_data: dict):
    res = await aiorequests.get(
        url=f"https://api-takumi.mihoyo.com/auth/api/getCookieAccountInfoByGameToken?game_token={game_token_data['token']}&account_id={game_token_data['uid']}",
        proxies={"http": None, "https": None},
    )
    return await res.json()


async def main_bot(bot, sid, userid, gid):
    code_data = await createurl()
    im = f"[CQ:image,file=base64://{get_qrcode_base64(code_data['url'])}]"
    try:
        await bot.send_msg(
            self_id=sid, user_id=userid, group_id=gid, message=im
        )
    except:
        pass
    sta, game_token_data = await refresh(code_data)
    if sta == 0:
        print("game_token获取成功")
        cookie_token = await get_cookie_token(game_token_data)
        stoken_data = await get_stoken(
            data={
                "account_id": int(game_token_data["uid"]),
                "game_token": game_token_data["token"],
            }
        )
        cookie = f"stoken_v2={stoken_data['data']['token']['token']};stuid={stoken_data['data']['user_info']['aid']};mid={stoken_data['data']['user_info']['mid']};cookie_token={cookie_token['data']['cookie_token']};"
        return cookie
    else:
        print("game_token获取失败")
        im = "game_token获取失败,二维码已过期"
        try:
            await bot.send_msg(
                self_id=sid, user_id=userid, group_id=gid, message=im
            )
        except:
            pass
    return "none"


if __name__ == '__main__':

    async def main():
        code_data = await createurl()
        showqrcode(code_data["url"])
        sta, game_token_data = await refresh(code_data)
        if sta == 0:
            print("game_token获取成功")
            cookie_token = await get_cookie_token(game_token_data)
            stoken_data = await get_stoken(
                data={
                    "account_id": int(game_token_data["uid"]),
                    "game_token": game_token_data["token"],
                }
            )
            print(
                f"stoken_v2={stoken_data['data']['token']['token']};stuid={stoken_data['data']['user_info']['aid']};mid={stoken_data['data']['user_info']['mid']};cookie_token={cookie_token['data']['cookie_token']};"
            )
        else:
            print("game_token获取失败")

    asyncio.run(main())
# input("按回车键退出")
# exit(0)

import time
from urllib.parse import quote

from nonebot.adapters.onebot.v11 import Bot

from ..utils.message.error_reply import SK_HINT
from ..utils.message.send_msg import send_forward_msg
from ..utils.mhy_api.get_mhy_data import get_authkey_by_cookie


async def post_url(bot: Bot, uid: str, group_id: str, qid: str):
    async def send_group_msg(msg: str):
        await bot.call_api(
            api='send_group_msg',
            group_id=group_id,
            message=msg,
        )
        return ''

    authkey = await get_authkey_by_cookie(uid)
    if authkey == {}:
        return await send_group_msg(SK_HINT)
    authkey = authkey['data']['authkey']
    now = time.time()
    region = ""
    if uid[0] == "1" or uid[0] == "2":
        region = 'cn_gf01'
    elif uid[0] == "5":
        region = "'cn_qd01'"
    elif uid[0] == "6":
        region = "'os_usa'"
    elif uid[0] == "7":
        region = "'os_euro'"
    elif uid[0] == "8":
        region = "'os_asia'"
    elif uid[0] == "9":
        region = "'os_cht'"
    else:
        region = 'cn_gf01'
    msgs = []
    msgs.append(f"uid：{uid}的抽卡记录链接为：")
    url = (
        f"https://hk4e-api.mihoyo.com/event/gacha_info/api/getGachaLog?"
        f"authkey_ver=1&sign_type=2&auth_appid=webview_gacha&init_type=301&"
        f"gacha_id=fecafa7b6560db5f3182222395d88aaa6aaac1bc"
        f"&timestamp={str(int(now))}"
        f"&lang=zh-cn&device_type=mobile&plat_type=ios&region={region}"
        f"&authkey={quote(authkey,'utf-8')}"
        f"&game_biz=hk4e_cn&gacha_type=301&page=1&size=5&end_id=0"
    )
    msgs.append(url)
    await send_forward_msg(bot, group_id, "抽卡链接", qid, msgs)
    return "成功执行"

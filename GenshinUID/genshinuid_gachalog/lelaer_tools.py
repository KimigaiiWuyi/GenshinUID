import time
import random
import string
from urllib.parse import quote

import aiofiles
from httpx import post
from gsuid_core.logger import logger
from requests_toolbelt import MultipartEncoder

from ..utils.mys_api import mys_api
from ..utils.error_reply import get_error
from ..gsuid_utils.api.mys.request import RECOGNIZE_SERVER
from .export_and_import import export_gachalogs, import_gachalogs


async def get_gachaurl(uid: str):
    server_id = RECOGNIZE_SERVER.get(str(uid)[0])
    authkey_rawdata = await mys_api.get_authkey_by_cookie(uid)
    if isinstance(authkey_rawdata, int):
        return get_error(authkey_rawdata)
    authkey = authkey_rawdata['authkey']
    now = time.time()
    url = (
        f"https://hk4e-api.mihoyo.com/event/gacha_info/api/getGachaLog?"
        f"authkey_ver=1&sign_type=2&auth_appid=webview_gacha&init_type=301&"
        f"gacha_id=fecafa7b6560db5f3182222395d88aaa6aaac1bc"
        f"&timestamp={str(int(now))}"
        f"&lang=zh-cn&device_type=mobile&plat_type=ios&region={server_id}"
        f"&authkey={quote(authkey,'utf-8')}"
        f"&game_biz=hk4e_cn&gacha_type=301&page=1&size=5&end_id=0"
    )
    logger.info(url)
    return url


async def get_lelaer_gachalog(uid: str):
    gachalog_url = await get_gachaurl(uid)
    data = {'uid': uid, 'gachaurl': gachalog_url, 'lang': 'zh-Hans'}
    history_data = post(
        'https://www.lelaer.com/outputGacha.php',
        data=data,
        verify=False,
        timeout=30,
    ).text
    logger.info(history_data)
    return await import_gachalogs(history_data, 'json', uid)


async def export_gachalog_to_lelaer(uid: str):
    gachalog_url = await get_gachaurl(uid)
    export = await export_gachalogs(uid)
    if export['retcode'] == 'ok':
        file_path = export['url']
    else:
        return '导出抽卡记录失败...'
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        record_data = await f.read()

        fields = {
            'upload': ('data.json', record_data, 'application/json'),
            "importType": "uigf",
            "gachaurl": gachalog_url,
        }
        boundary = '----WebKitFormBoundary' + ''.join(
            random.sample(string.ascii_letters + string.digits, 16)
        )
        data = MultipartEncoder(fields=fields, boundary=boundary)
        headers = {
            "Content-Type": data.content_type,
        }
        history_data = post(
            'https://www.lelaer.com/uigf.php',
            content=data.to_string(),
            headers=headers,
            verify=False,
            timeout=30,
        )
        status_code = history_data.status_code

        if status_code == 200 and '导入成功' in history_data.text:
            return '[提瓦特小助手]抽卡记录上传成功，请前往小程序查看'
        else:
            return '[提瓦特小助手]上传失败'

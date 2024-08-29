import time
from urllib.parse import quote

import httpx
import aiofiles
from gsuid_core.logger import logger
from urllib3 import encode_multipart_formdata
from gsuid_core.utils.error_reply import get_error_img
from gsuid_core.utils.api.mys.api import GET_GACHA_LOG_URL
from gsuid_core.utils.api.mys.base_request import RECOGNIZE_SERVER

from ..utils.mys_api import mys_api
from .export_and_import import export_gachalogs, import_gachalogs


async def get_gachaurl(uid: str):
    server_id = RECOGNIZE_SERVER.get(str(uid)[0])
    authkey_rawdata = await mys_api.get_authkey_by_cookie(uid)
    if isinstance(authkey_rawdata, int):
        return await get_error_img(authkey_rawdata)
    authkey = authkey_rawdata['authkey']
    now = time.time()
    url = (
        f"{GET_GACHA_LOG_URL}?"
        f"authkey_ver=1&sign_type=2&auth_appid=webview_gacha&init_type=301&"
        f"gacha_id=fecafa7b6560db5f3182222395d88aaa6aaac1bc"
        f"&timestamp={str(int(now))}"
        f"&lang=zh-cn&device_type=mobile&plat_type=ios&region={server_id}"
        f"&authkey={quote(authkey, 'utf-8')}"
        f"&game_biz=hk4e_cn&gacha_type=301&page=1&size=5&end_id=0"
    )
    logger.info(url)
    return url


async def get_lelaer_gachalog(uid: str):
    gachalog_url = await get_gachaurl(uid)
    data = {'uid': uid, 'gachaurl': gachalog_url, 'lang': 'zh-Hans'}
    async with httpx.AsyncClient(
        verify=False,
        timeout=30,
    ) as client:
        history_data = await client.post(
            'https://www.lelaer.com/outputGacha.php', data=data
        )
        logger.debug(history_data.content)
        history_log = history_data.text
        return await import_gachalogs(history_log, 'json', uid)


async def export_gachalog_to_lelaer(uid: str):
    gachalog_url = await get_gachaurl(uid)
    export = await export_gachalogs(uid, '2')
    if export['retcode'] == 'ok':
        file_path = export['url']
    else:
        return '导出抽卡记录失败...'
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        record_data = await f.read()

        data = {
            'upload': ('data.json', record_data, 'application/json'),
            'importType': 'uigf',
            "gachaurl": gachalog_url,
        }

        body, header = encode_multipart_formdata(data)

        headers = {"Content-Type": header}
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            history_data = await client.post(
                'https://www.lelaer.com/uigf.php',
                content=body,
                headers=headers,
            )
            status_code = history_data.status_code
            history_res = history_data.text
            if status_code == 200 and '导入成功' in history_res:
                return '[提瓦特小助手]抽卡记录上传成功，请前往小程序查看'
            else:
                return '[提瓦特小助手]上传失败'

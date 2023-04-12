import json
import base64
from datetime import datetime

from httpx import get

from .get_gachalogs import save_gachalogs
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH

INT_TO_TYPE = {
    '100': '新手祈愿',
    '200': '常驻祈愿',
    '301': '角色祈愿',
    '400': '角色祈愿',
    '302': '武器祈愿',
}


async def import_gachalogs(history_url: str, type: str, uid: str) -> str:
    if type == 'url':
        history_data: dict = json.loads(get(history_url).text)
    else:
        data_bytes = base64.b64decode(history_url)
        try:
            history_data = json.loads(data_bytes.decode())
        except UnicodeDecodeError:
            history_data = json.loads(data_bytes.decode('gbk'))
    if 'info' in history_data and 'uid' in history_data['info']:
        data_uid = history_data['info']['uid']
        if data_uid != uid:
            return f'该抽卡记录UID{data_uid}与你绑定UID{uid}不符合！'
        raw_data = history_data['list']
        result = {'新手祈愿': [], '常驻祈愿': [], '角色祈愿': [], '武器祈愿': []}
        for item in raw_data:
            item['uid'] = uid
            item['item_id'] = ''
            item['count'] = '1'
            item['lang'] = 'zh-cn'
            item['id'] = str(item['id'])
            del item['uigf_gacha_type']
            result[INT_TO_TYPE[item['gacha_type']]].append(item)
        im = await save_gachalogs(uid, result)
        return im
    else:
        return '请传入正确的UIGF文件!'


async def export_gachalogs(uid: str) -> dict:
    path = PLAYER_PATH / uid
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    # 获取当前时间
    now = datetime.now()
    current_time = now.strftime('%Y-%m-%d %H:%M:%S')

    # 抽卡记录json路径
    gachalogs_path = path / 'gacha_logs.json'
    if gachalogs_path.exists():
        with open(gachalogs_path, "r", encoding='UTF-8') as f:
            raw_data = json.load(f)
        result = {
            'info': {
                'uid': uid,
                'lang': 'zh-cn',
                'export_time': current_time,
                'export_app': 'GenshinUID',
                'export_app_version': '4.0',
                'export_timestamp': round(now.timestamp()),
                'uigf_version': 'v2.2',
            },
            'list': [],
        }
        for i in ['新手祈愿', '常驻祈愿', '角色祈愿', '武器祈愿']:
            for item in raw_data['data'][i]:
                if item['gacha_type'] == '400':
                    item['uigf_gacha_type'] = '301'
                else:
                    item['uigf_gacha_type'] = item['gacha_type']
                result['list'].append(item)
        # 保存文件
        with open(path / f'UIGF_{uid}.json', 'w', encoding='UTF-8') as file:
            json.dump(result, file, ensure_ascii=False)
        im = {
            'retcode': 'ok',
            'data': '导出成功!',
            'name': f'UIGF_{uid}.json',
            'url': str((path / f'UIGF_{uid}.json').absolute()),
        }
    else:
        im = {
            'retcode': 'error',
            'data': '你还没有抽卡记录可以导出!',
            'name': '',
            'url': '',
        }

    return im

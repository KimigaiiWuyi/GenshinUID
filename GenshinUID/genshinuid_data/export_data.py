import re
import json

from ..utils.download_resource.RESOURCE_PATH import MAIN_PATH
from ..utils.db_operation.db_operation import get_all_bind, get_user_bind_data

DATA_PATH = MAIN_PATH / 'v3_data.json'
BOT_ID = 'onebot'
RECOGNIZE_SERVER = {
    '1': 'cn_gf01',
    '2': 'cn_gf01',
    '5': 'cn_qd01',
    '6': 'os_usa',
    '7': 'os_euro',
    '8': 'os_asia',
    '9': 'os_cht',
}


async def export_v3():
    result = {'bot_id': BOT_ID, 'bind': [], 'user': []}
    bind_list = await get_all_bind()
    for bind in bind_list:
        bind_data = {}
        bind_data['bot_id'] = BOT_ID
        bind_data['user_id'] = str(bind['USERID'])
        bind_data['uid'] = str(bind['UID'])  # 导出bind数据
        bind_data['mys_id'] = str(bind['MYSID'])
        if bind_data not in result['bind']:
            result['bind'].append(bind_data)
        uid_list = bind['UID'].split('_')
        for uid in uid_list:
            new_data = {}
            data = await get_user_bind_data(uid)
            if not data:
                continue
            new_data['bot_id'] = BOT_ID
            new_data['user_id'] = data['QID']
            new_data['region'] = RECOGNIZE_SERVER[uid[0]]
            new_data['stoken'] = data['Stoken']
            new_data['cookie'] = data['Cookies']
            account_id = re.search(r'account_id=(\d*)', new_data['cookie'])
            assert account_id is not None
            new_data['mys_id'] = str(account_id.group(1))
            new_data['uid'] = uid
            new_data['push_switch'] = data['StatusA']
            new_data['sign_switch'] = data['StatusB']
            new_data['bbs_switch'] = data['StatusC']
            new_data['status'] = data['Extra']
            if new_data not in result['user']:
                result['user'].append(new_data)
    with open(DATA_PATH, 'w', encoding='UTF-8') as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

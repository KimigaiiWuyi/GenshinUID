import json
from time import time
from re import sub, compile, findall
from typing import List, Union, Literal
from datetime import datetime, timezone, timedelta

from httpx import AsyncClient
from gsuid_core.utils.api.mys.api import BBS_URL

TZ = timezone(timedelta(hours=8))


MYJ = (
    f'{BBS_URL}/painter/api/user_instant/list?offset=0&size=20&uid=75276550',
)  # 米游姬个人中心

url = {
    'act_id': MYJ,
    'index': 'https://api-takumi.mihoyo.com/event/miyolive/index',
    'code': 'https://api-takumi-static.mihoyo.com/event/miyolive/refreshCode',
}


async def get_data(
    type: Literal['index', 'code', 'act_id'],
    data: dict = {},
) -> dict:
    '''米哈游接口请求'''

    async with AsyncClient() as client:
        try:
            if type == 'index':
                res = await client.get(
                    url[type], headers={'x-rpc-act_id': data.get('actId', '')}
                )
            elif type == 'code':
                res = await client.get(
                    url[type],
                    params={
                        'version': data.get('version', ''),
                        'time': f'{int(time())}',
                    },
                    headers={'x-rpc-act_id': data.get('actId', '')},
                )
            else:
                res = await client.get(url[type])
            return res.json()
        except Exception as e:
            return {'error': f'[{e.__class__.__name__}] {type} 接口请求错误'}


async def get_act_id() -> str:
    '''获取 ``act_id``'''

    ret = await get_data('act_id')
    if ret.get('error') or ret.get('retcode') != 0:
        return ''

    act_id = ''
    keywords = ['前瞻特别节目']
    for p in ret['data']['list']:
        post = p.get('post', {}).get('post', {})
        if not post:
            continue
        if not all(word in post['subject'] for word in keywords):
            continue
        shit = json.loads(post['structured_content'])
        for segment in shit:
            link = segment.get('attributes', {}).get('link', '')
            if '观看' in segment.get('insert', '') and link:
                matched = findall(r'act_id=(.*?)\&', link)
                if matched:
                    act_id = matched[0]
        if act_id:
            break

    return act_id


async def get_live_data(act_id: str) -> dict:
    '''获取直播数据，尤其是 ``code_ver``'''

    ret = await get_data('index', {'actId': act_id})
    if ret.get('error') or ret.get('retcode') != 0:
        return {'error': ret.get('error') or '前瞻直播数据异常'}

    live_raw = ret['data']['live']
    live_temp = json.loads(ret['data']['template'])
    live_data = {
        'code_ver': live_raw['code_ver'],
        'title': live_raw['title'].replace('特别直播', ''),
        'header': live_temp['kvDesktop'],
        'room': live_temp['liveConfig'][0]['desktop'],
    }
    now = datetime.fromtimestamp(time(), TZ)
    start = datetime.strptime(live_raw['start'], '%Y-%m-%d %H:%M:%S').replace(
        tzinfo=TZ
    )
    if now < start:
        live_data['start'] = live_raw['start']

    return live_data


async def get_code(version: str, act_id: str) -> Union[dict, List[dict]]:
    '''获取兑换码'''

    ret = await get_data('code', {'version': version, 'actId': act_id})
    if ret.get('error') or ret.get('retcode') != 0:
        return {'error': ret.get('error') or '兑换码数据异常'}
    code_data = []
    for code_info in ret['data']['code_list']:
        remove_tag = compile('<.*?>')
        code_data.append(
            {
                'items': sub(remove_tag, '', code_info['title']),
                'code': code_info['code'],
            }
        )
    return code_data


async def get_code_msg() -> str:
    '''生成最新前瞻直播兑换码消息'''

    act_id = await get_act_id()
    if not act_id:
        return '暂无前瞻直播资讯！'

    live_data = await get_live_data(act_id)
    if live_data.get('error'):
        return live_data['error']

    code_data = await get_code(live_data['code_ver'], act_id)
    if isinstance(code_data, dict):
        return code_data['error']

    code_msg = f'{live_data["title"]}\n'
    # 三个兑换码
    index = 0
    for code in code_data:
        index = index + 1
        if code.get('code'):
            # 该兑换码已开放
            code_msg += f'{code["items"]}:\n{code["code"]}\n'
        else:
            # 该兑换码未开放
            code_msg += f'第 {index} 个兑换码暂未发放\n'

    return code_msg.strip()

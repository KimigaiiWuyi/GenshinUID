import json
from typing import List
from pathlib import Path

TASK_PATH = Path(__file__).parent / 'task.json'

with open(TASK_PATH, "r", encoding='UTF-8') as f:
    task_data = json.load(f)

task_im = '''「任务」 {}{}
「攻略」 {}'''

extra_im = '''
「类型」 {}
「地区」 {}
「时长预估」 {}
「版本」 {}'''


async def _get_tag(result_task: dict) -> str:
    if result_task['ext'] != '{}':
        detail = json.loads(r'%s' % result_task['ext'])
        detail = detail['c_231']
        tag = detail['filter']['text'].replace('","', '|')[2:-2]
        tag_list = tag.split('|')
        tag_data = {}
        for i in tag_list:
            tag_data[i.split('/')[0]] = i.split('/')[1]

        type = tag_data['任务类型']
        region = tag_data['所属区域']
        time = tag_data['任务耗时']
        version = tag_data['版本']
        extra = extra_im.format(type, region, time, version)
    else:
        extra = ''
    title = result_task['title']
    url = result_task['bbs_url']
    title = title.replace('羊皮卷', '')
    im = task_im.format(title, extra, url)

    return im


async def get_task_detail(task_name: str) -> str:
    all_task = task_data['data']['list'][0]['children']
    task_list = []

    for item in all_task:
        task_list.extend(item['list'])

    for task in task_list:
        if task_name in task['title']:
            result_task = task
            break
    else:
        return '没有找到该任务...'

    im = await _get_tag(result_task)

    return im


async def get_region_task(region: str) -> List:
    all_task = task_data['data']['list'][0]['children']

    task_list = []
    for item in all_task:
        if region in item['name']:
            task_list.extend(item['list'])
            break
    else:
        return []

    all_list = []
    mes_list = []
    for index, task in enumerate(task_list):
        tag = await _get_tag(task)
        mes_list.append(
            {
                'type': 'node',
                'data': {
                    'name': '小仙',
                    'uin': '3399214199',
                    'content': tag,
                },
            }
        )
        if index != 0 and index % 44 == 0:
            all_list.append(mes_list)
            mes_list = []
    all_list.append(mes_list)

    return all_list

import re

from .template import all_achi, daily_achi, achi_template, daily_template


async def get_daily_achi(task: str) -> str:
    _similarity = 0
    detail = {}
    if task in daily_achi:
        detail = daily_achi[task]
    else:
        for _task in daily_achi:
            __task = ''.join(re.findall('[\u4e00-\u9fa5]', _task))
            __task = __task.replace('每日委托', '').replace('世界任务', '')
            similarity = len(set(__task) & set(task))
            if similarity >= len(__task) / 2:
                if similarity > _similarity:
                    _similarity = similarity
                    detail = daily_achi[_task]
                    task = _task
        else:
            if detail == {}:
                return '该委托暂无成就...'

    achi = detail['achievement']
    desc = detail['desc']
    guide = detail['guide']
    link = detail['link']

    im = daily_template.format(task, achi, desc, guide)
    im = f'{im}\n{link}' if link else im
    return im


async def get_achi(achi: str) -> str:
    _similarity = 0
    detail = {}
    if achi in all_achi:
        detail = all_achi[achi]
    else:
        for _achi in all_achi:
            __achi = ''.join(re.findall('[\u4e00-\u9fa5]', _achi))
            __achi = __achi.replace('每日委托', '').replace('世界任务', '')
            similarity = len(set(__achi) & set(achi))
            if similarity >= len(__achi) / 2:
                if similarity > _similarity:
                    _similarity = similarity
                    detail = all_achi[_achi]
                    achi = _achi
        else:
            if detail == {}:
                return '暂无该成就...'

    book = detail['book']
    desc = detail['desc']
    guide = detail['guide']
    link = detail['link']

    im = achi_template.format(book, achi, desc)
    im = f'{im}\n{guide}' if guide else im
    im = f'{im}\n{link}' if link else im
    return im

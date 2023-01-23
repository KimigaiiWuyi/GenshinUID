from .template import all_achi, daily_achi, achi_template, daily_template


async def get_daily_achi(task: str) -> str:
    if task in daily_achi:
        detail = daily_achi[task]
    else:
        for _task in daily_achi:
            similarity = len(set(_task) & set(task))
            if similarity >= len(_task) / 2:
                detail = daily_achi[_task]
                task = _task
                break
        else:
            return '该委托暂无成就...'

    achi = detail['achievement']
    desc = detail['desc']
    guide = detail['guide']
    link = detail['link']

    im = daily_template.format(task, achi, desc, guide)
    im = f'{im}\n{link}' if link else im
    return im


async def get_achi(achi: str) -> str:
    if achi in all_achi:
        detail = all_achi[achi]
    else:
        for _achi in all_achi:
            similarity = len(set(_achi) & set(achi))
            if similarity >= len(_achi) / 2:
                detail = all_achi[_achi]
                achi = _achi
                break
        else:
            return '暂无该成就...'

    book = detail['book']
    desc = detail['desc']
    guide = detail['guide']
    link = detail['link']

    im = achi_template.format(book, achi, desc)
    im = f'{im}\n{guide}' if guide else im
    im = f'{im}\n{link}' if link else im
    return im

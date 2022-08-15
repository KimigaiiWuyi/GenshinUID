import asyncio

from .download_from_fandom import download_by_fandom, get_char_url_list
from .download_from_minigg import download_by_minigg


async def download_all_resource():
    lst = await get_char_url_list()
    ret = await asyncio.gather(download_by_fandom(lst), download_by_minigg())
    ret = [str(x) for x in ret if x]
    if ret:
        return '\n'.join(ret)
    return '全部资源下载完成!'

from .download_from_minigg import download_by_minigg
from .download_from_fandom import get_char_url_list, download_by_fandom


async def download_all_resource():
    lst = await get_char_url_list()
    faild_str = ''
    faild_str += await download_by_fandom(lst)
    faild_str += await download_by_minigg()
    if faild_str:
        return faild_str
    return '全部资源下载完成!'

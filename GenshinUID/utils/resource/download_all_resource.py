from .download_from_miniggicu import download_all_file_from_miniggicu


async def download_all_resource():
    await download_all_file_from_miniggicu()
    return 'Genshin全部资源下载完成!'

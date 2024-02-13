from gsuid_core.utils.download_resource.download_core import download_all_file

from .RESOURCE_PATH import (
    REF_PATH,
    REL_PATH,
    CHAR_PATH,
    ICON_PATH,
    GUIDE_PATH,
    WEAPON_PATH,
    CHAR_SIDE_PATH,
    GACHA_IMG_PATH,
    CHAR_STAND_PATH,
    CHAR_NAMECARD_PATH,
    CHAR_NAMECARDPIC_PATH,
)


async def download_all_file_from_miniggicu():
    await download_all_file(
        'GenshinUID',
        {
            'resource/char_namecard': CHAR_NAMECARD_PATH,
            'resource/char_side': CHAR_SIDE_PATH,
            'resource/char_stand': CHAR_STAND_PATH,
            'resource/chars': CHAR_PATH,
            'resource/gacha_img': GACHA_IMG_PATH,
            'resource/icon': ICON_PATH,
            'resource/reliquaries': REL_PATH,
            'resource/weapon': WEAPON_PATH,
            'wiki/guide': GUIDE_PATH,
            'wiki/ref': REF_PATH,
            'resource/char_namecard_pic': CHAR_NAMECARDPIC_PATH,
        },
    )
    for d_files in ['100000067.png', '100000068.png']:
        path = CHAR_PATH / d_files
        if path.exists():
            path.unlink()

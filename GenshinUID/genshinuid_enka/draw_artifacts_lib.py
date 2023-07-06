import json
from typing import Dict, Union, Optional

import aiofiles
from PIL import Image, ImageDraw

from .etc.etc import TEXT_PATH
from .start import refresh_player_list
from ..utils.image.convert import convert_img
from .draw_normal import _get_single_artifact_img
from ..utils.fonts.genshin_fonts import gs_font_36
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from ..utils.image.image_tools import get_qq_avatar, draw_pic_with_ring


async def get_artifacts_lib_data(uid: str) -> Optional[Dict]:
    path = PLAYER_PATH / uid / 'artifacts.json'
    data = None
    if not path.exists():
        await refresh_player_list(uid)

    if path.exists():
        async with aiofiles.open(path, 'rb') as file:
            data = json.loads(await file.read())
        all_list = [x for v in data['data'].values() for x in v]

        if len(all_list) == 0:
            return None
        elif 'cv_score' not in all_list[0]:
            path.unlink()
            await refresh_player_list(uid)
            async with aiofiles.open(path, 'rb') as file:
                data = json.loads(await file.read())

    return data


async def draw_lib(user_id: str, uid: str) -> Union[bytes, str]:
    data = await get_artifacts_lib_data(uid)
    if data is None:
        return '你还没有圣遗物数据...请尝试使用[强制刷新]获取数据!'

    all_list = [x for v in data['data'].values() for x in v]
    all_list.sort(key=lambda x: x['cv_score'], reverse=True)

    lst = all_list[:20]

    bg = Image.open(TEXT_PATH / 'artifacts_lib_bg.png')
    avatar = await get_qq_avatar(user_id)
    avatar_img = await draw_pic_with_ring(avatar, 280)

    bg.paste(avatar_img, (115, 88), avatar_img)

    for index, artifact in enumerate(lst):
        img = await _get_single_artifact_img(artifact)
        bg.paste(img, (24 + (index % 4) * 310, 570 + (index // 4) * 360), img)

    bg_draw = ImageDraw.Draw(bg)
    bg_draw.text((268, 498), f'UID {uid}', 'white', gs_font_36, 'mm')
    all_black = Image.new('RGBA', bg.size, (0, 0, 0))
    bg = Image.alpha_composite(all_black, bg)
    return await convert_img(bg)

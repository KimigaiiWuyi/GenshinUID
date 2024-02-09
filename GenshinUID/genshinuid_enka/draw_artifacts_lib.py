import json
from decimal import Decimal
from typing import Dict, Union, Optional

import aiofiles
from PIL import Image, ImageDraw
from gsuid_core.models import Event

from .etc.etc import TEXT_PATH
from .start import refresh_player_list
from ..utils.image.convert import convert_img
from ..utils.image.image_tools import get_avatar
from .draw_normal import _get_single_artifact_img
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from ..utils.fonts.genshin_fonts import gs_font_25, gs_font_36, gs_font_38


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


async def draw_lib(ev: Event, uid: str, num: int) -> Union[bytes, str]:
    data = await get_artifacts_lib_data(uid)
    if data is None:
        return '你还没有圣遗物数据...请尝试使用[刷新圣遗物仓库]获取数据!'

    all_list = [x for v in data['data'].values() for x in v]
    all_list.sort(key=lambda x: x['cv_score'], reverse=True)

    all_num = len(all_list)
    full_rank = 0
    can_use = 0
    all_value_score = 0
    all_cv_score = 0
    high_cv = 0
    high_value = 0
    for art in all_list:
        all_value_score += art['value_score']
        all_cv_score += art['cv_score']
        if art['aritifactLevel'] == 20:
            full_rank += 1
        if art['value_score'] >= 5.2 or art['cv_score'] >= 35.5:
            can_use += 1

        if art['value_score'] >= 6.5:
            high_value += 1
        if art['cv_score'] >= 44.5:
            high_cv += 1

    avg_value = round(all_value_score / all_num, 2)
    avg_cv = round(all_cv_score / all_num, 2)
    use_percent = Decimal(can_use * 100).quantize(Decimal('0.00')) / Decimal(
        all_num
    )
    high_percent = Decimal(high_cv * 100).quantize(Decimal('0.00')) / Decimal(
        all_num
    )

    all_page = all_num // 20 + 1
    lst = all_list[0 + 20 * (num - 1) : 20 * num]  # noqa:E203

    if num > all_page:
        return f'[UID{uid}] 圣遗物仓库没有 {num} 页!\n最多为 {all_page} 页!'

    bg = Image.open(TEXT_PATH / 'artifacts_lib_bg.png')
    avatar_img = await get_avatar(ev, 280)

    bg.paste(avatar_img, (120, 88), avatar_img)

    for index, artifact in enumerate(lst):
        img = await _get_single_artifact_img(artifact)
        bg.paste(img, (24 + (index % 4) * 310, 570 + (index // 4) * 360), img)

    bg_draw = ImageDraw.Draw(bg)
    bg_draw.text((268, 498), f'UID {uid}', 'white', gs_font_36, 'mm')

    xo = 236
    yo = 156
    bg_draw.text((650, 141), f'{all_num}', 'white', gs_font_38, 'mm')
    bg_draw.text((650 + xo, 141), f'{full_rank}', 'white', gs_font_38, 'mm')
    bg_draw.text((650 + xo * 2, 141), f'{can_use}', 'white', gs_font_38, 'mm')

    bg_draw.text((650, 141 + yo), f'{avg_value}', 'white', gs_font_38, 'mm')
    bg_draw.text((650 + xo, 141 + yo), f'{avg_cv}', 'white', gs_font_38, 'mm')
    bg_draw.text(
        (650 + xo * 2, 141 + yo),
        f'{use_percent:.2f}%',
        'white',
        gs_font_38,
        'mm',
    )

    bg_draw.text(
        (650, 141 + yo * 2), f'{high_value}', 'white', gs_font_38, 'mm'
    )
    bg_draw.text(
        (650 + xo, 141 + yo * 2), f'{high_cv}', 'white', gs_font_38, 'mm'
    )
    bg_draw.text(
        (650 + xo * 2, 141 + yo * 2),
        f'{high_percent:.2f}%',
        'white',
        gs_font_38,
        'mm',
    )

    extra_notice = (
        f'可用 圣遗物仓库{num+1} 命令查看第{num+1}页'
        if num < all_page
        else '暂无更多页数'
    )

    bg_draw.text(
        (650, 2420),
        f'当前 {num} / {all_page} 页, {extra_notice}',
        (210, 210, 210),
        gs_font_25,
        'mm',
    )

    # 最后生成图片
    all_black = Image.new('RGBA', bg.size, (0, 0, 0))
    bg = Image.alpha_composite(all_black, bg)
    return await convert_img(bg)

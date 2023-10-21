from typing import Union

from PIL import Image, ImageDraw
from gsuid_core.utils.image.convert import convert_img

from .draw_rank_list import RANK_TEXT
from ..utils.api.cv.request import _CvApi
from .draw_role_rank import REGION_MAP, grey
from ..genshinuid_config.gs_config import gsconfig
from ..utils.map.GS_MAP_PATH import icon2Name, artifact2attr
from .draw_normal import get_artifact_score_data, _get_single_artifact_img
from ..utils.fonts.genshin_fonts import (
    gs_font_15,
    gs_font_18,
    gs_font_24,
    gs_font_26,
)

is_enable_akasha = gsconfig.get_config('EnableAkasha').data

EQUIP_MAP = {
    'EQUIP_BRACER': '生之花',
    'EQUIP_NECKLACE': '死之羽',
    'EQUIP_SHOES': '时之沙',
    'EQUIP_RING': '空之杯',
    'EQUIP_DRESS': '理之冠',
}

SUBSTAT_MAP = {
    'Flat ATK': '攻击力',
    'Flat HP': '血量',
    'Flat DEF': '防御力',
    'ATK%': '百分比攻击力',
    'HP%': '百分比血量',
    'DEF%': '百分比防御',
    'Elemental Mastery': '元素精通',
    'Energy Recharge': '元素充能效率',
    'Crit RATE': '暴击率',
    'Crit DMG': '暴击伤害',
    'Cryo DMG Bonus': '冰元素伤害加成',
    'Pyro DMG Bonus': '火元素伤害加成',
    'Hydro DMG Bonus': '水元素伤害加成',
    'Electro DMG Bonus': '雷元素伤害加成',
    'Anemo DMG Bonus': '风元素伤害加成',
    'Geo DMG Bonus': '岩元素伤害加成',
    'Dendro DMG Bonus': '草元素伤害加成',
    'Healing Bonus': '治疗加成',
    'Physical Bonus': '物理伤害加成',
}


async def draw_arti_rank_img(sort_by: str) -> Union[str, bytes]:
    if not is_enable_akasha:
        return '未开启排名系统...'
    cv_api = _CvApi()

    sort_by = sort_by.strip()
    if not sort_by:
        sort_by = '双爆'

    raw_data = await cv_api.get_artifacts_list(sort_by)
    if raw_data is None:
        return '输入的排序值错误...'

    img = Image.open(RANK_TEXT / 'star.jpg')

    for index, arti in enumerate(raw_data):
        arti_img = Image.open(RANK_TEXT / 'arti_bg.png')
        region: str = arti['owner']['region']
        nickname: str = arti['owner']['nickname']
        uid: str = arti['uid']

        icon_url: str = arti['icon']
        name = icon2Name[icon_url.split('/')[-1].split('.')[0]]
        # rel_img = Image.open(REL_PATH / f'{name}.png')

        aritifact = {
            'aritifactName': name,
            'aritifactSetsName': artifact2attr[name],
            'aritifactPieceName': EQUIP_MAP[arti['equipType']],
            'aritifactStar': arti['stars'],
            'aritifactLevel': arti['level'] - 1,
            'reliquaryMainstat': {
                'statValue': int(arti['mainStatValue']),
                'statName': SUBSTAT_MAP[arti['mainStatKey']],
            },
            'reliquarySubstats': [],
        }

        for sub in arti['substats']:
            aritifact['reliquarySubstats'].append(
                {
                    'statValue': round(arti['substats'][sub], 1),
                    'statName': SUBSTAT_MAP[sub],
                }
            )

        if region in REGION_MAP:
            region_color = REGION_MAP[region]
        else:
            region_color = (128, 128, 128)

        new_aritifact = await get_artifact_score_data(aritifact, None, '无疑')
        _arti_img = await _get_single_artifact_img(new_aritifact)

        arti_img.paste(_arti_img, (0, 0), _arti_img)
        arti_draw = ImageDraw.Draw(arti_img)

        arti_draw.rounded_rectangle((27, 366, 112, 396), 20, region_color)
        arti_draw.text((70, 381), region, 'white', gs_font_24, 'mm')
        arti_draw.text((120, 381), nickname, 'white', gs_font_24, 'lm')
        arti_draw.text((155, 333), f'UID {uid}', grey, gs_font_15, 'mm')

        img.paste(
            arti_img,
            (15 + 318 * (index % 4), 468 + 410 * (index // 4)),
            arti_img,
        )
    img_draw = ImageDraw.Draw(img)
    img_draw.text(
        (650, 425), f'前20 / 当前排序 {sort_by}', 'white', gs_font_26, 'mm'
    )
    img_draw.text(
        (650, img.size[1] - 35),
        'Power by Wuyi无疑 & '
        'Data by AKS & CV '
        'Created by GsCore & GenshinUID',
        (200, 200, 200),
        gs_font_18,
        anchor='mm',
    )
    await cv_api.close()

    return await convert_img(img)

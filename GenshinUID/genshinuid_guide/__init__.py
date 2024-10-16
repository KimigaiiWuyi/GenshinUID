import re
from typing import List

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.message_models import Button
from gsuid_core.segment import MessageSegment

from .get_guide import get_gs_guide
from ..version import Genshin_version

# from .get_abyss_data import get_review
from ..utils.image.convert import convert_img
from .get_new_abyss_data import get_review_data
from ..utils.resource.RESOURCE_PATH import REF_PATH
from .get_bbs_post_guide import get_material_way_post
from ..utils.map.name_covert import alias_to_char_name

sv_char_guide = SV('查询角色攻略')
sv_abyss_review = SV('查询深渊阵容')
sv_bbs_post_guide = SV('查询BBS攻略')


@sv_bbs_post_guide.on_suffix(('路线'))
async def send_bbs_post_guide(bot: Bot, ev: Event):
    name = ev.text.strip().replace('材料', '').replace('采集', '')
    await bot.send(await get_material_way_post(name))


@sv_char_guide.on_prefix(('参考攻略', '攻略', '推荐'))
@sv_char_guide.on_suffix(('攻略', '推荐'))
async def send_guide_pic(bot: Bot, ev: Event):
    name = ev.text.strip()
    im = await get_gs_guide(name)

    if im:
        await bot.logger.info('获得{}攻略成功！'.format(name))
        a = Button(f'🎴参考面板{name}', f'参考面板{name}')
        await bot.send_option(im, [a])
    else:
        await bot.logger.warning('未找到{}攻略图片'.format(name))


@sv_char_guide.on_prefix(('参考面板'))
async def send_bluekun_pic(bot: Bot, ev: Event):
    if ev.text in ['冰', '水', '火', '草', '雷', '风', '岩']:
        name = ev.text
    else:
        name = await alias_to_char_name(ev.text.strip())
    img = REF_PATH / '{}.jpg'.format(name)
    if img.exists():
        img = await convert_img(img)
        await bot.logger.info('获得{}参考面板图片成功！'.format(name))
        await bot.send_option(img, [Button(f'🎴{name}攻略', f'{name}攻略')])
    else:
        await bot.logger.warning('未找到{}参考面板图片'.format(name))


@sv_abyss_review.on_command(('版本深渊', '深渊阵容', '深渊怪物'))
async def send_abyss_review(bot: Bot, ev: Event):
    floor = '12'
    if not ev.text:
        version = Genshin_version[:-2]
    else:
        if '.' in ev.text:
            num = ev.text.index('.')
            version = ev.text[num - 1 : num + 2]  # noqa:E203
            _deal = ev.text.replace(version, '').strip()
            if _deal:
                floor = re.findall(r'[0-9]+', _deal)[0]
        else:
            floor = ev.text
            version = Genshin_version[:-2]

    im = await get_review_data(version, floor)
    # im = await get_review(version)

    if isinstance(im, bytes):
        c = Button('♾️深渊概览', '深渊概览')
        input_version = float(version)
        now_version = float(Genshin_version[:-2])
        if input_version <= now_version:
            gv = Genshin_version.split('.')
            adv_version = f'{gv[0]}.{int(gv[1])+1}'
        else:
            adv_version = now_version
        d = Button(f'♾️版本深渊{adv_version}', f'深渊概览{adv_version}')
        await bot.send_option(im, [c, d])
    elif isinstance(im, List):
        mes = [MessageSegment.text(str(msg)) for msg in im]
        await bot.send(MessageSegment.node(mes))
    elif isinstance(im, str):
        await bot.send(im)

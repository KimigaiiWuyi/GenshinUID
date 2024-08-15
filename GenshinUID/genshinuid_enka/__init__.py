import re
import json
from typing import Tuple

import aiofiles
from PIL import Image
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger
from gsuid_core.message_models import Button
from gsuid_core.utils.error_reply import UID_HINT

from .to_data import switch_api
from .to_card import enka_to_card
from ..utils.convert import get_uid
from .get_akasha_data import get_rank
from .start import refresh_player_list
from .to_data_by_mys import mys_to_card
from .draw_artifacts_lib import draw_lib
from .draw_rank_list import draw_rank_img
from ..utils.image.convert import convert_img
from ..utils.map.GS_MAP_PATH import alias_data
from .draw_arti_rank import draw_arti_rank_img
from .draw_char_info import draw_all_char_list
from .draw_char_rank import draw_cahrcard_list
from .draw_role_rank import draw_role_rank_img
from ..genshinuid_config.gs_config import gsconfig
from .get_enka_img import draw_enka_img, get_full_char
from ..genshinuid_enka.start import check_artifacts_list
from ..utils.resource.RESOURCE_PATH import TEMP_PATH, PLAYER_PATH

EnableCharCardByMys = gsconfig.get_config('EnableCharCardByMys').data

sv_enka_admin = SV('面板管理', pm=1)
sv_enka_config = SV('面板设置', pm=2)
sv_akasha = SV('排名查询', priority=10)
sv_get_enka = SV('面板查询', priority=10)
sv_get_original_pic = SV('查看面板原图', priority=5)


@sv_akasha.on_command('排名统计')
async def sned_rank_data(bot: Bot, ev: Event):
    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(f'[排名统计]uid: {uid}')
    await bot.send(await get_rank(uid))


@sv_akasha.on_command('排名列表')
async def sned_rank_pic(bot: Bot, ev: Event):
    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(f'[排名列表]uid: {uid}')
    im = await draw_rank_img(ev, uid)
    await bot.send_option(
        im,
        [
            Button('♾️角色排名公子', '角色排名公子'),
            Button('♾️圣遗物双爆排名', '圣遗物排名双爆'),
        ],
    )


@sv_akasha.on_prefix('角色排行榜')
async def sned_role_rank_pic(bot: Bot, ev: Event):
    # 获取角色名
    msg = ''.join(re.findall('[\u4e00-\u9fa5 ]', ev.text))
    if not msg:
        return
    logger.info(f'[角色排行榜]角色: {msg}')
    a = Button('💖排名列表', '排名列表')
    b = Button(f'✅查询{msg}', f'查询{msg}')
    c = Button(f'💖角色排名{msg}', f'角色排名{msg}')
    d = Button('✅圣遗物排名', '圣遗物排名')

    im = await draw_role_rank_img(msg)
    await bot.send_option(im, [a, c, b, d])


@sv_akasha.on_prefix('角色排名')
async def sned_my_role_rank_pic(bot: Bot, ev: Event):
    # 获取角色名
    msg = ''.join(re.findall('[\u4e00-\u9fa5 ]', ev.text))
    if not msg:
        return
    logger.info(f'[角色排名]角色: {msg}')
    a = Button('💖排名列表', '排名列表')
    b = Button(f'✅查询{msg}', f'查询{msg}')
    c = Button(f'💖角色排行榜{msg}', f'角色排行榜{msg}')
    d = Button('✅圣遗物排名', '圣遗物排名')

    msg = msg.replace('附近', '')
    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)

    im = await draw_role_rank_img(msg, uid)
    await bot.send_option(im, [a, c, b, d])


@sv_akasha.on_command('圣遗物排名')
async def sned_arti_rank_pic(bot: Bot, ev: Event):
    # 获取排序名
    msg = ''.join(re.findall('[\u4e00-\u9fa5 ]', ev.text))
    logger.info(f'[圣遗物排名]排序: {msg}')
    im = await draw_arti_rank_img(msg)
    await bot.send_option(
        im,
        [
            Button('♾️双爆排名', '圣遗物排名双爆'),
            Button('♾️暴击率排名', '圣遗物排名暴击率'),
            Button('♾️元素精通排名', '圣遗物排名元素精通'),
            Button('♾️暴击伤害排名', '圣遗物排名暴击伤害'),
        ],
    )


@sv_enka_admin.on_fullmatch('刷新全部圣遗物仓库')
async def sned_fresh_all_list(bot: Bot, ev: Event):
    await bot.send('开始执行...可能时间较久, 执行完成会有提示, 请勿重复执行!')
    await check_artifacts_list()
    await bot.send('执行完成!')


@sv_get_enka.on_fullmatch(('刷新圣遗物仓库', '强制刷新圣遗物仓库'), block=True)
async def sned_fresh_list(bot: Bot, ev: Event):
    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(f'[刷新圣遗物仓库]uid: {uid}')
    await bot.send(f'UID{uid}开始刷新, 请勿重复触发!')
    if ev.command.startswith('强制'):
        is_force = True
    else:
        is_force = False
    await bot.send(await refresh_player_list(uid, is_force))


@sv_get_enka.on_command('圣遗物仓库')
async def sned_aritifacts_list(bot: Bot, ev: Event):
    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(f'[圣遗物仓库]uid: {uid}')

    if ev.text and ev.text.isdigit():
        num = int(ev.text)
        if num == 0:
            num = 1
    else:
        num = 1

    im = await draw_lib(ev, uid, num)
    await bot.send_option(
        im,
        [
            Button('♾️双爆排名', '圣遗物排名双爆'),
            Button('♾️暴击率排名', '圣遗物排名暴击率'),
            Button('♾️元素精通排名', '圣遗物排名元素精通'),
            Button('♾️暴击伤害排名', '圣遗物排名暴击伤害'),
        ],
    )


@sv_get_original_pic.on_fullmatch(('原图'))
async def sned_original_pic(bot: Bot, ev: Event):
    if ev.reply:
        path = TEMP_PATH / f'{ev.reply}.jpg'
        if path.exists():
            logger.info('[原图]访问图片: {}'.format(path))
            with open(path, 'rb') as f:
                await bot.send(f.read())


@sv_enka_config.on_fullmatch('切换api')
async def send_change_api_info(bot: Bot, ev: Event):
    await bot.send(await switch_api())


@sv_get_enka.on_prefix('查询')
async def send_char_info(bot: Bot, ev: Event):
    name = ev.text.strip()
    im = await _get_char_info(bot, ev, name)
    if isinstance(im, str):
        await bot.send(im)
    elif isinstance(im, Tuple):
        if isinstance(im[0], Image.Image):
            img = await convert_img(im[0])
        else:
            img = im[0]
        await bot.send_option(
            img,
            [
                Button('🔄更换武器', f'查询{name}换'),
                Button('⏫提高命座', f'查询六命{name}'),
                Button('*️⃣保存面板', f'保存面板{name}为 '),
                Button('🔀对比面板', f'对比面板 {name} '),
            ],
        )
        if im[1]:
            with open(TEMP_PATH / f'{ev.msg_id}.jpg', 'wb') as f:
                f.write(im[1])
    elif im is None:
        return
    else:
        await bot.send('发生未知错误')


async def _get_char_info(bot: Bot, ev: Event, text: str):
    # 获取角色名
    msg = ''.join(re.findall('[\u4e00-\u9fa5 ]', text))
    if not msg:
        return
    await bot.logger.info('开始执行[查询角色面板]')
    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[查询角色面板]uid: {}'.format(uid))

    im = await draw_enka_img(msg, uid, ev.image)
    return im


@sv_get_enka.on_command('对比面板')
async def contrast_char_info(bot: Bot, ev: Event):
    if not ev.text.strip():
        return await bot.send('参考格式: 对比面板 公子 公子换可莉圣遗物')
    contrast_list = ev.text.strip().split(' ')
    if len(contrast_list) <= 1:
        return await bot.send(
            '输入格式错误...参考格式: 对比面板 公子 公子换可莉圣遗物'
        )
    elif len(contrast_list) >= 4:
        return await bot.send('不支持对比四个及以上的面板...')

    img_list = []
    max_y = 0
    for i in contrast_list:
        im = await _get_char_info(bot, ev, i)
        if isinstance(im, str):
            return await bot.send(im)
        elif isinstance(im, Tuple):
            data = im[0]
            if isinstance(data, bytes):
                return await bot.send(
                    '输入了错误的格式...参考格式: 对比面板 公子 公子换可莉圣遗物'
                )
            elif isinstance(data, str):
                return await bot.send(data)
            else:
                assert isinstance(data, Image.Image)
                img_list.append(data)
                max_y = max(max_y, data.size[1])

    base_img = Image.new('RGBA', (950 * len(img_list), max_y))
    for index, img in enumerate(img_list):
        base_img.paste(img, (950 * index, 0), img)

    await bot.send(await convert_img(base_img))


@sv_get_enka.on_command('保存面板')
async def save_char_info(bot: Bot, ev: Event):
    if not ev.text.strip():
        return await bot.send(
            '后面需要跟自定义的保存名字\n例如：保存面板公子为核爆公子'
        )
    save_list = ev.text.strip().split('为')
    if len(save_list) <= 1:
        return await bot.send(
            '输入格式错误...参考格式: 保存面板公子为核爆公子'
        )

    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)

    save_char, save_name = save_list[0], save_list[1]

    if bool(re.search(r'\d', save_name)):
        return await bot.send('保存名称内不可存在数字!')

    if save_name in alias_data:
        return await bot.send('保存名称不可为已有角色的名称!')
    else:
        for _fix in [
            '队伍',
            '最佳',
            '最优',
            '曲线',
            '成长',
            '展柜',
            '伤害',
            '角色',
            '极限',
            '带',
            '换',
        ]:
            if _fix in save_name:
                return await bot.send(f'保存名称不能含有【{_fix}】等保留词...')

        for _name in alias_data:
            if save_name in alias_data[_name]:
                return await bot.send('保存名称不可为已有角色的别名!')
        else:
            char_data = await get_full_char(save_char, uid)
            if isinstance(char_data, str):
                return await bot.send(char_data)
            SELF_PATH = PLAYER_PATH / str(uid) / 'SELF'
            if not SELF_PATH.exists():
                SELF_PATH.mkdir()
            path = SELF_PATH / f'{save_name}.json'
            async with aiofiles.open(path, 'wb') as file:
                await file.write(json.dumps(char_data).encode('utf-8'))
            return await bot.send_option(
                f'保存成功!你可以使用[查询{save_name}]调用该面板!',
                [
                    Button(f'✅查询{save_name}', f'查询{save_name}'),
                    Button('💖刷新面板', '刷新面板'),
                ],
            )


@sv_get_enka.on_command(('强制刷新', '刷新面板'))
async def send_card_info(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info('[强制刷新]uid: {}'.format(uid))
    if EnableCharCardByMys:
        im = await mys_to_card(uid)
    else:
        im = await enka_to_card(uid)
    logger.info(f'UID{uid}获取角色数据成功！')

    if isinstance(im, Tuple):
        buttons = [
            Button(f'✅查询{i["avatarName"]}', f'查询{i["avatarName"]}')
            for i in im[1]
        ]
        buttons.append(Button('📦圣遗物仓库', '圣遗物仓库'))
        buttons.append(Button('💖排名列表', '排名列表'))
        await bot.send_option(im[0], buttons)
    else:
        await bot.send(im)


@sv_get_enka.on_command(('毕业度统计', '毕业都统计'))
async def send_charcard_list(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_cahrcard_list(str(uid), ev)
    await bot.logger.info(f'[毕业度统计] UID{uid}获取角色数据成功！')
    await bot.send(im)


@sv_get_enka.on_command(('角色橱窗'))
async def send_char_detail_list(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_all_char_list(str(uid))
    await bot.logger.info(f'[角色橱窗] UID{uid}获取角色数据成功！')
    await bot.send(im)

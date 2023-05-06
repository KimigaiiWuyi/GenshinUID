import re
import json
from typing import List, Tuple

import aiofiles
from PIL import Image
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import UID_HINT

from .to_data import switch_api
from .to_card import enka_to_card
from ..utils.convert import get_uid
from ..utils.image.convert import convert_img
from ..utils.map.GS_MAP_PATH import alias_data
from .draw_char_rank import draw_cahrcard_list
from .get_enka_img import draw_enka_img, get_full_char
from ..utils.resource.RESOURCE_PATH import TEMP_PATH, PLAYER_PATH

sv_enka_config = SV('面板设置', pm=2)
sv_get_enka = SV('面板查询', priority=10)
sv_get_original_pic = SV('查看面板原图', priority=5)


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
    im = await _get_char_info(bot, ev, ev.text)
    if isinstance(im, str):
        await bot.send(im)
    elif isinstance(im, Tuple):
        if isinstance(im[0], Image.Image):
            img = await convert_img(im[0])
        else:
            img = im[0]
        await bot.send(img)
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


@sv_get_enka.on_prefix('对比面板')
async def contrast_char_info(bot: Bot, ev: Event):
    contrast_list = ev.text.strip().split(' ')
    if len(contrast_list) <= 1:
        return await bot.send('输入格式错误...参考格式: 对比面板 公子 公子换可莉圣遗物')
    elif len(contrast_list) >= 4:
        return await bot.send('不支持对比四个及以上的面板...')

    img_list: List[Image.Image] = []
    max_y = 0
    for i in contrast_list:
        im = await _get_char_info(bot, ev, i)
        if isinstance(im, str):
            return await bot.send(im)
        elif isinstance(im, Tuple):
            if isinstance(im[0], bytes):
                return await bot.send('输入了错误的格式...参考格式: 对比面板 公子 公子换可莉圣遗物')
            elif isinstance(im[0], str):
                return await bot.send(im[0])
            else:
                img_list.append(im[0])
                max_y = max(max_y, im[0].size[1])

    base_img = Image.new('RGBA', (950 * len(img_list), max_y))
    for index, img in enumerate(img_list):
        base_img.paste(img, (950 * index, 0), img)

    await bot.send(await convert_img(base_img))


@sv_get_enka.on_prefix('保存面板')
async def save_char_info(bot: Bot, ev: Event):
    save_list = ev.text.strip().split('为')
    if len(save_list) <= 1:
        return await bot.send('输入格式错误...参考格式: 保存面板公子为核爆公子')

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
            return await bot.send(f'保存成功!你可以使用[查询{save_name}]调用该面板!')


@sv_get_enka.on_command('强制刷新')
async def send_card_info(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[强制刷新]uid: {}'.format(uid))
    im = await enka_to_card(uid)
    await bot.logger.info(f'UID{uid}获取角色数据成功！')
    await bot.send(im)


@sv_get_enka.on_command('毕业度统计')
async def send_charcard_list(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    user_id = ev.at if ev.at else ev.user_id
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_cahrcard_list(str(uid), user_id)
    await bot.logger.info(f'UID{uid}获取角色数据成功！')
    await bot.send(im)

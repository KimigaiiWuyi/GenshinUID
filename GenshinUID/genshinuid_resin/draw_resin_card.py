import json
import asyncio
from io import BytesIO
from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw
from gsuid_core.logger import logger
from gsuid_core.utils.api.mys.models import Expedition
from gsuid_core.utils.database.models import GsBind, GsUser
from gsuid_core.utils.error_reply import (
    UID_HINT,
    get_error,
    get_error_img,
    draw_error_img,
    get_error_type,
)

from ..utils.mys_api import mys_api
from ..utils.image.convert import convert_img
from ..genshinuid_config.gs_config import gsconfig
from ..genshinuid_enka.to_data import get_enka_info
from ..utils.resource.download_url import download_file
from ..utils.api.mys.models import FakeResin, DayilyTask
from ..utils.api.mys.models import Expedition as WidgetExpedition
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH, CHAR_SIDE_TEMP_PATH
from ..utils.api.mys.models import (
    Transformer,
    WidgetResin,
    RecoveryTime,
    ArchonProgress,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_20,
    gs_font_26,
    gs_font_28,
    gs_font_32,
    gs_font_58,
    gs_font_70,
)

TEXT_PATH = Path(__file__).parent / 'texture2D'
ok_pic = Image.open(TEXT_PATH / 'ok.png')
no_pic = Image.open(TEXT_PATH / 'no.png')
un_pic = Image.open(TEXT_PATH / 'un.png')

first_color = (29, 29, 29)
second_color = (98, 98, 98)
green_color = (15, 196, 35)
orange_color = (237, 115, 61)
red_color = (235, 61, 75)

use_widget = gsconfig.get_config('WidgetResin').data


async def _draw_task_img(
    char: Union[Expedition, WidgetExpedition],
) -> Image.Image:
    go_img = Image.open(TEXT_PATH / 'go_bg.png')

    if not char['avatar_side_icon']:
        return go_img

    char_temp = char['avatar_side_icon'].split('/')[-1]
    side_path = CHAR_SIDE_TEMP_PATH / char_temp
    if not side_path.exists():
        await download_file(
            char['avatar_side_icon'],
            13,
            char_temp,
        )
    # avatar_id = await enName_to_avatarId(char_en_name)
    char_pic = (
        Image.open(side_path)
        .convert('RGBA')
        .resize((115, 115), Image.Resampling.LANCZOS)  # type: ignore
    )
    go_img.paste(char_pic, (0, -12), char_pic)
    go_draw = ImageDraw.ImageDraw(go_img)

    if char['status'] == 'Finished':
        status_mark = '待收取'
        status_color = red_color
    else:
        status_mark = '已派遣'
        status_color = green_color

    go_draw.text(
        (60, 125),
        status_mark,
        font=gs_font_20,
        fill=status_color,
        anchor='mm',
    )

    return go_img


async def get_resin_img(bot_id: str, user_id: str):
    try:
        uid_list = await GsBind.get_uid_list_by_game(user_id, bot_id)
        logger.info('[每日信息]UID: {}'.format(uid_list))
        if uid_list is None:
            return UID_HINT
        # 进行校验UID是否绑定CK
        useable_uid_list = []
        for uid in uid_list:
            status = await GsUser.get_user_cookie_by_uid(uid)
            if status is not None:
                useable_uid_list.append(uid)
        logger.info('[每日信息]可用UID: {}'.format(useable_uid_list))
        if len(useable_uid_list) == 0:
            return '请先绑定一个可用CK & UID再来查询哦~'
        # 开始绘图任务
        task = []
        img = Image.new(
            'RGBA', (700 * len(useable_uid_list), 1300), (0, 0, 0, 0)
        )
        for uid_index, uid in enumerate(useable_uid_list):
            task.append(_draw_all_resin_img(img, uid, uid_index))
        await asyncio.gather(*task)
        res = await convert_img(img)
        logger.info('[查询每日信息]绘图已完成,等待发送!')
    except TypeError:
        logger.exception('[查询每日信息]绘图失败!')
        res = '你绑定过的UID中可能存在过期CK~请重新绑定一下噢~'

    return res


async def _draw_all_resin_img(img: Image.Image, uid: str, index: int):
    resin_img = await draw_resin_img(uid)
    resin_img = resin_img.convert('RGBA')
    img.paste(resin_img, (700 * index, 0), resin_img)


async def seconds2hours(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return '%02d小时%02d分' % (h, m)


def transform_fake_resin(data: WidgetResin) -> FakeResin:
    del data['daily_task']  # type: ignore
    data = FakeResin(
        **data,
        remain_resin_discount_num=-99,
        resin_discount_num_limit=0,
        transformer=Transformer(
            obtained=True,
            recovery_time=RecoveryTime(
                Day=-99, Hour=1, Minute=1, Second=1, reached=False
            ),
            wiki='',
            noticed=False,
            latest_job_id='123',
        ),
        daily_task=DayilyTask(
            total_num=-1,
            finished_num=-1,
            is_extra_task_reward_received=False,
            task_rewards=[],
            attendance_rewards=[],
        ),
        archon_quest_progress=ArchonProgress(
            list=[],
            is_open_archon_quest=False,
            is_finish_all_mainline=False,
            is_finish_all_interchapter=False,
            wiki_url='False',
        ),
    )
    return data


async def draw_bar(
    status: str = 'un', text: str = '洞天宝钱', data: str = '未知'
) -> Image.Image:
    bar = Image.open(TEXT_PATH / 'bar_bg.png')
    bar_draw = ImageDraw.ImageDraw(bar)
    bar_draw.text((219, 50), text, (31, 32, 26), gs_font_32, 'lm')
    bar_draw.text((367, 52), data, (49, 49, 49), gs_font_28, 'lm')
    if status == 'ok':
        bar.paste(ok_pic, (151, 25), ok_pic)
    elif status == 'un':
        bar.paste(un_pic, (151, 25), un_pic)
    else:
        bar.paste(no_pic, (151, 25), no_pic)
    return bar


async def _get_error_img(retcode: int):
    error_img = await get_error_img(retcode)
    if isinstance(error_img, str):
        error_message = get_error(retcode)
        error_type = get_error_type(retcode)
        error_img = await draw_error_img(retcode, error_message, error_type)
    bio = BytesIO(error_img)
    return Image.open(bio)


async def draw_resin_img(uid: str) -> Image.Image:
    img = Image.open(TEXT_PATH / 'bg.png')

    # 获取数据
    if use_widget and int(str(uid)[0]) <= 5:
        _daily_data = await mys_api.get_widget_resin_data(uid)
        if isinstance(_daily_data, int):
            return await _get_error_img(_daily_data)
        daily_data = transform_fake_resin(_daily_data)
        data_res = '当前数据源：小组件 （可能存在数据不准、数据缺失）'
        warn = '数据未知...'

        is_sign = 'ok' if _daily_data['has_signed'] else 'no'
    else:
        daily_data = await mys_api.get_daily_data(uid)
        if isinstance(daily_data, int):
            return await _get_error_img(daily_data)
        data_res = '当前数据源：战绩'
        warn = '未知情况'

        sign_info = await mys_api.get_sign_info(uid)
        if isinstance(sign_info, int):
            is_sign = 'un'
        else:
            is_sign = 'ok' if sign_info['is_sign'] else 'no'

    enta_data_path = PLAYER_PATH / uid / 'rawData.json'
    if enta_data_path.exists():
        with open(enta_data_path, 'r', encoding='utf-8') as f:
            player_data = json.load(f)
    else:
        try:
            player_data = await get_enka_info(uid)
        except Exception:
            player_data = {}

    # 处理数据
    if player_data and 'playerInfo' in player_data:
        name = player_data['playerInfo']['nickname']
        '''
        if 'signature' in player_data['playerInfo']:
            signature = player_data['playerInfo']['signature']
        else:
            signature = '该旅行者还没有签名噢~'
        '''
        world_level = player_data['playerInfo']['level']
        world_level_str = f'探索等级{str(world_level)}'
    else:
        name = '旅行者'
        # signature = '暂无获取数据'
        world_level_str = '暂无数据'

    # 树脂
    resin = daily_data['current_resin']
    max_resin = daily_data['max_resin']
    resin_str = f'{resin}/{max_resin}'
    resin_percent = resin / max_resin
    if resin_percent > 0.8:
        resin_color = red_color
    else:
        resin_color = second_color
    resin_recovery_time = await seconds2hours(
        int(daily_data['resin_recovery_time'])
    )

    # 洞天宝钱
    home_coin = daily_data['current_home_coin']
    max_home_coin = daily_data['max_home_coin']
    home_coin_str = f'{home_coin} / {max_home_coin}'
    if max_home_coin - home_coin < 200:
        coin_status = 'no'
    else:
        coin_status = 'ok'
    coin_bar = await draw_bar(coin_status, '洞天宝钱', home_coin_str)

    # 完成委托
    finish_task = daily_data['finished_task_num']
    total_task = daily_data['total_task_num']
    is_task_reward = daily_data['is_extra_task_reward_received']
    task_str = f'{finish_task} / {total_task}'
    if is_task_reward:
        task_status = 'ok'
    else:
        task_status = 'no'
    task_bar = await draw_bar(task_status, '完成委托', task_str)

    # 周本减半
    weekly_half = daily_data['remain_resin_discount_num']
    max_weekly_half = daily_data['resin_discount_num_limit']
    weekly_half_str = f'{weekly_half} / {max_weekly_half}'
    if weekly_half == -99:
        weekly_status = 'un'
        weekly_half_str = warn
    elif weekly_half == 0:
        weekly_status = 'ok'
    else:
        weekly_status = 'no'
    weekly_bar = await draw_bar(weekly_status, '周本减半', weekly_half_str)

    # 参量质变仪
    transformer = daily_data['transformer']['recovery_time']['reached']
    transformer_day = daily_data['transformer']['recovery_time']['Day']
    transformer_hour = daily_data['transformer']['recovery_time']['Hour']
    transformer_str = f'还剩{transformer_day}天{transformer_hour}小时'
    if transformer_day == -99:
        trans_status = 'un'
        transformer_str = warn
    elif transformer:
        trans_status = 'no'
    else:
        trans_status = 'ok'
    trans_bar = await draw_bar(trans_status, '参量质变', transformer_str)

    # 魔神任务
    archon_quest = daily_data['archon_quest_progress']
    if archon_quest['wiki_url'] == 'False':
        archon_status = 'un'
        archon_str = '数据未知...'
    else:
        if (
            archon_quest['is_finish_all_interchapter']
            and archon_quest['is_finish_all_mainline']
            and archon_quest['is_open_archon_quest']
            and not archon_quest['list']
        ):
            archon_status = 'ok'
            archon_str = '已全部完成'
        else:
            archon_status = 'no'
            if archon_quest['list']:
                archon_str = archon_quest['list'][0]['chapter_num']
            else:
                archon_str = '暂未开启...'

    archon_bar = await draw_bar(archon_status, '魔神任务', archon_str)

    img_draw = ImageDraw.Draw(img)

    for _ in range(5):
        if len(daily_data['expeditions']) < 5:
            daily_data['expeditions'].append(
                Expedition(
                    avatar_side_icon='', status='Ongoing', remained_time=233
                )
            )
        else:
            break

    # 派遣
    for index, char in enumerate(daily_data['expeditions']):
        go_img = await _draw_task_img(char)
        img.paste(go_img, (81 + index * 106, 1051), go_img)

    # 绘制树脂圆环
    ring_pic = Image.open(TEXT_PATH / 'ring.apng')
    percent = (
        round(resin_percent * 49) if round(resin_percent * 49) <= 49 else 49
    )
    ring_pic.seek(percent)
    img.paste(ring_pic, (0, -21), ring_pic)

    # 写树脂剩余时间
    img_draw.text(
        (350, 466),
        f'还剩{resin_recovery_time}',
        font=gs_font_28,
        fill=resin_color,
        anchor='mm',
    )

    # 写UID
    img_draw.text((350, 135), f'UID{uid}', (38, 38, 38), gs_font_26, 'mm')

    # 写探索等级
    img_draw.text(
        (350, 354),
        world_level_str,
        font=gs_font_28,
        fill=second_color,
        anchor='mm',
    )

    # 写树脂
    img_draw.text(
        (350, 408),
        resin_str,
        font=gs_font_70,
        fill=first_color,
        anchor='mm',
    )

    img_draw.text((350, 89), name, (13, 13, 13), gs_font_58, 'mm')
    img_draw.text((350, 1235), data_res, (92, 92, 92), gs_font_20, 'mm')

    delay = 78
    img.paste(coin_bar, (0, 642), coin_bar)
    img.paste(task_bar, (0, 642 + delay), task_bar)
    img.paste(weekly_bar, (0, 642 + delay * 2), weekly_bar)
    img.paste(trans_bar, (0, 642 + delay * 3), trans_bar)
    img.paste(archon_bar, (0, 642 + delay * 4), archon_bar)

    sign_pic = Image.open(TEXT_PATH / f'sign_{is_sign}.png')
    img.paste(sign_pic, (275, 500), sign_pic)

    return img

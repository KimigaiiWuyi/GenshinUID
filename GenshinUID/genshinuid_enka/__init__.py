import re
import random
from typing import Tuple

from .draw_char_card import *
from .draw_char_card import draw_char_img
from ..all_import import *  # noqa: F401,F403
from .draw_char_rank import draw_cahrcard_list
from ..utils.enka_api.get_enka_data import switch_api
from ..utils.enka_api.enka_to_data import enka_to_data
from ..utils.db_operation.db_operation import get_all_uid
from ..utils.message.error_reply import *  # noqa: F401,F403
from ..utils.alias.alias_to_char_name import alias_to_char_name
from ..utils.enka_api.enka_to_card import enka_to_card, draw_enka_card
from ..utils.download_resource.RESOURCE_PATH import TEMP_PATH, PLAYER_PATH

CONVERT_TO_INT = {
    '零': 0,
    '一': 1,
    '二': 2,
    '三': 3,
    '四': 4,
    '五': 5,
    '六': 6,
    '满': 6,
}
AUTO_REFRESH = False


@sv.on_fullmatch('切换api')
async def send_change_api_info(bot: HoshinoBot, ev: CQEvent):
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return

    if qid not in bot.config.SUPERUSERS:
        return

    im = await switch_api()
    await bot.send(ev, im)


@sv.on_fullmatch('原图')
async def send_original_pic(bot: HoshinoBot, ev: CQEvent):
    if ev.reply:
        msg_id = ev.reply.message_id
        path = TEMP_PATH / f'{msg_id}.jpg'
        if path.exists():
            logger.info('[原图]访问图片: {}'.format(path))
            with open(path, 'rb') as f:
                im = await convert_img(f.read())
                await bot.send(ev, im)


@sv.on_rex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(uid|查询|mys)([0-9]+)?'
    r'([\u4e00-\u9fa5]+)'
    r'(\[CQ:at,qq=[0-9]+\])?( )?',
)
async def send_char_info(bot: HoshinoBot, ev: CQEvent):
    args = ev['match'].groups()
    if args[4] is None:
        return
    else:
        # 获取角色名
        msg = ''.join(re.findall('[\u4e00-\u9fa5]', args[4]))
        is_curve = False
        if '成长曲线' in msg or '曲线' in msg:
            is_curve = True
            msg = msg.replace('成长曲线', '').replace('曲线', '')
        msg_list = msg.split('换')
        char_name = msg_list[0]
        talent_num = None
        weapon = None
        weapon_affix = None
        if '命' in char_name and char_name[0] in CONVERT_TO_INT:
            talent_num = CONVERT_TO_INT[char_name[0]]
            char_name = char_name[2:]
        if len(msg_list) > 1:
            if (
                '精' in msg_list[1]
                and msg_list[1][1] != '六'
                and msg_list[1][1] != '零'
                and msg_list[1][1] in CONVERT_TO_INT
            ):
                weapon_affix = CONVERT_TO_INT[msg_list[1][1]]
                weapon = msg_list[1][2:]
            else:
                weapon = msg_list[1]
    logger.info('开始执行[查询角色面板]')
    logger.info('[查询角色面板]参数: {}'.format(args))
    # 获取角色名
    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))
    image = re.search(r'\[CQ:image,file=(.*),url=(.*)]', str(ev.message))

    img = None
    if image:
        img = image.group(2)
    if at:
        qid = int(at.group(1))
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return
    logger.info('[查询角色面板]QQ: {}'.format(qid))

    # 获取uid
    if args[3] is None:
        uid = await select_db(qid, mode='uid')
        uid = str(uid)
    else:
        uid = args[3]
    logger.info('[查询角色面板]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await bot.send(ev, UID_HINT)

    player_path = PLAYER_PATH / str(uid)
    if char_name == '展柜角色':
        char_file_list = player_path.glob('*')
        char_list = []
        for i in char_file_list:
            file_name = i.name
            if '\u4e00' <= file_name[0] <= '\u9fff':
                char_list.append(file_name.split('.')[0])
        img = await draw_enka_card(uid=uid, char_list=char_list)
        img = await convert_img(img)
        await bot.send(ev, img)
        return
    else:
        if '旅行者' in char_name:
            char_name = '旅行者'
        else:
            char_name = await alias_to_char_name(char_name)
        char_path = player_path / f'{char_name}.json'
        if char_path.exists():
            with open(char_path, 'r', encoding='utf8') as fp:
                char_data = json.load(fp)
        else:
            await bot.send(ev, CHAR_HINT.format(char_name), at_sender=True)
            return

    im = await draw_char_img(
        char_data, weapon, weapon_affix, talent_num, img, is_curve
    )

    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, Tuple):
        img = await convert_img(im[0])
        req = await bot.send(ev, img)
        msg_id = req['message_id']
        if im[1]:
            with open(TEMP_PATH / f'{msg_id}.jpg', 'wb') as f:
                f.write(im[1])
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')


async def refresh_char_data():
    """
    :说明:
      刷新全部绑定uid的角色展柜面板进入本地缓存。
    """
    uid_list = await get_all_uid()
    t = 0
    for uid in uid_list:
        try:
            im = await enka_to_data(uid)
            logger.info(im)
            t += 1
            await asyncio.sleep(35 + random.randint(1, 20))
        except:
            logger.exception(f'{uid}刷新失败！')
            logger.error(f'{uid}刷新失败！本次自动刷新结束！')
            return f'执行失败从{uid}！共刷新{str(t)}个角色！'
    else:
        logger.info(f'共刷新{str(t)}个角色！')
        return f'执行成功！共刷新{str(t)}个角色！'


@sv.scheduled_job('cron', hour='4')
async def daily_refresh_charData():
    global AUTO_REFRESH
    if AUTO_REFRESH:
        await refresh_char_data()


@sv.on_prefix('强制刷新')
async def send_card_info(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return

    uid = re.findall(r'\d+', message)  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))

    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return

    if len(uid) >= 1:
        uid = uid[0]
    else:
        if m == '全部数据':
            if qid in bot.config.SUPERUSERS:
                await bot.send(ev, '开始刷新全部数据，这可能需要相当长的一段时间！！')
                im = await refresh_char_data()
                await bot.send(ev, str(im))
                return
            else:
                return
        else:
            uid = await select_db(qid, mode='uid')
            uid = str(uid)
            if '未找到绑定的UID' in uid:
                await bot.send(ev, UID_HINT)
                return
    im = await enka_to_card(uid)
    logger.info(f'UID{uid}获取角色数据成功！')
    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')


@sv.on_prefix('毕业度统计')
async def send_charcard_list(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return

    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))

    if at:
        qid = int(at.group(1))
        message = message.replace(str(at), '')
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return

    # 获取uid
    uid = re.findall(r'\d+', message)
    if uid:
        uid = uid[0]
    else:
        uid = await select_db(qid, mode='uid')

    im = await draw_cahrcard_list(str(uid), qid)

    logger.info(f'UID{uid}获取角色数据成功！')
    if isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, str(im))

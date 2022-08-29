import re
import random
from pathlib import Path

from .draw_char_card import *
from .draw_char_card import draw_char_img
from ..all_import import *  # noqa: F401,F403
from ..utils.enka_api.enka_to_data import enka_to_data
from ..utils.db_operation.db_operation import get_all_uid
from ..utils.message.error_reply import *  # noqa: F401,F403
from ..utils.mhy_api.convert_mysid_to_uid import convert_mysid
from ..utils.alias.alias_to_char_name import alias_to_char_name

AUTO_REFRESH = False
PLAYER_PATH = Path(__file__).parents[1] / 'player'


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
        char_name = args[4]
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
        char_list_str = ','.join(char_list)
        await bot.send(ev, f'UID{uid}当前缓存角色:{char_list_str}', at_sender=True)
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

    im = await draw_char_img(char_data, img)

    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
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
    im = await enka_to_data(uid)
    logger.info(f'UID{uid}获取角色数据成功！')
    await bot.send(ev, str(im))


@sv.on_prefix('毕业度统计')
async def send_charcard_list(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return
    limit = re.findall(r'\d+', message)  # str
    if len(limit) >= 1:
        limit = int(limit[0])
    else:
        limit = 24

    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))

    if at:
        qid = int(at.group(1))
        message = message.replace(str(at), '')
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return

    uid = await select_db(qid, mode='uid')

    im = await draw_cahrcard_list(str(uid), limit)

    logger.info(f'UID{uid}获取角色数据成功！')
    if isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, str(im))

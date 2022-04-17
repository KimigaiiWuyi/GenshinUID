import base64
from functools import wraps

from nonebot import get_bot, get_driver, on_command, on_regex, require
from nonebot.adapters.onebot.v11 import (PRIVATE_FRIEND, Bot,
                                         GroupMessageEvent, Message,
                                         MessageEvent, MessageSegment)
from nonebot.adapters.onebot.v11.exception import ActionFailed
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

# from .get_data import *
# sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from .get_image import *
from .get_mihoyo_bbs_data import *

config = get_driver().config
try:
    priority = config.genshinuid_priority
except AttributeError:
    priority = 2
superusers = {int(x) for x in config.superusers}

# todo: 将重复代码提取为函数，增加代码复用性
# 不得不说重复代码太多了很影响项目维护，同一个功能出问题所有同样的代码都要改，还容易漏

scheduler = require('nonebot_plugin_apscheduler').scheduler

get_weapon = on_command('武器', priority=priority)
get_char = on_command('角色', priority=priority)
get_cost = on_command('材料', priority=priority)
get_polar = on_command('命座', priority=priority)
get_talents = on_command('天赋', priority=priority)
get_enemies = on_command('原魔', priority=priority)
get_audio = on_command('语音', priority=priority)
get_artifacts = on_command('圣遗物', priority=priority)
get_food = on_command('食物', priority=priority)

get_uid_info = on_command('uid', priority=priority)
get_mys_info = on_command('mys', priority=priority)

get_event = on_command('活动列表', priority=priority)
get_lots = on_command('御神签', priority=priority)
get_help = on_command('gs帮助', priority=priority)

open_switch = on_command('gs开启', priority=priority)
close_switch = on_command('gs关闭', priority=priority)

link_mys = on_command('绑定mys', priority=priority)
link_uid = on_command('绑定uid', priority=priority)

monthly_data = on_command('每月统计', priority=priority)
daily_data = on_command('当前状态', priority=priority)

get_genshin_info = on_command('当前信息', priority=priority)

add_cookie = on_command('添加', permission=PRIVATE_FRIEND, priority=priority)

search = on_command('查询', priority=priority)
get_sign = on_command('签到', priority=priority)
get_mihoyo_coin = on_command('开始获取米游币', priority=priority)
check = on_command('校验全部Cookies', priority=priority)

all_recheck = on_command('全部重签', permission=SUPERUSER, priority=priority)
all_bbscoin_recheck = on_command('全部重获取', permission=SUPERUSER, priority=priority)

get_char_adv = on_regex('[\u4e00-\u9fa5]+(用什么|能用啥|怎么养)', priority=priority)
get_weapon_adv = on_regex('[\u4e00-\u9fa5]+(能给谁|给谁用|要给谁|谁能用)', priority=priority)

get_guide_pic = on_regex('[\u4e00-\u9fa5]+(推荐|攻略)', priority=priority)

FILE_PATH = os.path.join(os.path.join(os.path.dirname(__file__), ''), 'mihoyo_libs/mihoyo_bbs')
INDEX_PATH = os.path.join(FILE_PATH, 'index')
TEXTURE_PATH = os.path.join(FILE_PATH, 'texture2d')


@scheduler.scheduled_job('cron', hour='2')
async def draw_event():
    await draw_event_pic()


# 每日零点清空cookies使用缓存
@scheduler.scheduled_job('cron', hour='0')
async def clean_cache():
    await delete_cache()


# 每隔半小时检测树脂是否超过设定值
@scheduler.scheduled_job('cron', minute='*/30')
async def push():
    bot = get_bot()
    now_data = await daily()
    if now_data is not None:
        for i in now_data:
            if i['gid'] == 'on':
                await bot.call_api(api='send_private_msg', **{'user_id': i['qid'], 'message': i['message']})
            else:
                await bot.call_api(api='send_group_msg',
                                   **{'group_id': i['gid'],
                                      'message' : MessageSegment.at(i['qid']) + f'\n{i["message"]}'})
    else:
        pass


# 每日零点半进行米游社签到
@scheduler.scheduled_job('cron', hour='0', minute='30')
async def sign_at_night():
    await daily_sign()


async def daily_sign():
    bot = get_bot()
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute(
        'SELECT *  FROM NewCookiesTable WHERE StatusB != ?', ('off',))
    c_data = cursor.fetchall()
    temp_list = []
    for row in c_data:
        im = await sign(str(row[0]))
        if row[4] == 'on':
            try:
                await bot.call_api(api='send_private_msg',
                                   user_id=row[2], message=im)
            except Exception:
                logger.exception(f'{im} Error')
        else:
            message = MessageSegment.at(row[2]) + f'\n{im}'
            if await config_check('SignReportSimple'):
                for i in temp_list:
                    if row[4] == i['push_group']:
                        if im == '签到失败，请检查Cookies是否失效。' or im.startswith('网络有点忙，请稍后再试~!'):
                            i['failed'] += 1
                            i['push_message'] += '\n' + message
                        else:
                            i['success'] += 1
                        break
                else:
                    if im == '签到失败，请检查Cookies是否失效。':
                        temp_list.append(
                            {'push_group': row[4], 'push_message': message, 'success': 0, 'failed': 1})
                    else:
                        temp_list.append(
                            {'push_group': row[4], 'push_message': '', 'success': 1, 'failed': 0})
            else:
                for i in temp_list:
                    if row[4] == i['push_group'] and i['num'] < 4:
                        i['push_message'] += '\n' + message
                        i['num'] += 1
                        break
                else:
                    temp_list.append(
                        {'push_group': row[4], 'push_message': message, 'num': 1})
        await asyncio.sleep(6 + random.randint(1, 3))
    if await config_check('SignReportSimple'):
        for i in temp_list:
            try:
                report = '以下为签到失败报告：{}'.format(
                    i['push_message']) if i['push_message'] != '' else ''
                await bot.call_api(
                    api='send_group_msg', group_id=i['push_group'],
                    message='今日自动签到已完成！\n本群共签到成功{}人，共签到失败{}人。{}'.format(i['success'], i['failed'], report))
            except Exception:
                logger.exception('签到报告发送失败：{}'.format(i['push_message']))
            await asyncio.sleep(4 + random.randint(1, 3))
    else:
        for i in temp_list:
            try:
                await bot.call_api(
                    api='send_group_msg', group_id=i['push_group'], message=i['push_message'])
            except Exception:
                logger.exception('签到报告发送失败：{}'.format(i['push_message']))
            await asyncio.sleep(4 + random.randint(1, 3))


# 每日零点五十进行米游币获取
@scheduler.scheduled_job('cron', hour='0', minute='50')
async def sign_at_night():
    await daily_mihoyo_bbs_sign()


async def daily_mihoyo_bbs_sign():
    bot = get_bot()
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute(
        'SELECT *  FROM NewCookiesTable WHERE StatusC != ?', ('off',))
    c_data = cursor.fetchall()
    logger.info(c_data)
    for row in c_data:
        logger.info('正在执行{}'.format(row[0]))
        if row[8]:
            await asyncio.sleep(5 + random.randint(1, 3))
            im = await mihoyo_coin(str(row[2]), str(row[8]))
            logger.info(im)
            try:
                await bot.call_api(api='send_private_msg',
                                   user_id=row[2], message=im)
            except Exception:
                logger.exception(f'{im} Error')
    logger.info('已结束。')


def handle_exception(name: str, log_msg: str = None, fail_msg: str = None):
    """
        :说明:

          捕获命令执行过程中发生的异常并回报。

        :参数:

          * ``name: str``: 项目的名称。
          * ``log_msg: str = None``: 自定义捕获异常后在日志中留存的信息。留空则使用默认信息。
          * ``fail_msg: str = None``: 自定义捕获异常后向用户回报的信息，仅在提供自定义日志信息时有效。开头带@则艾特用户。留空则与日志信息相同。
    """
    def wrapper(func):
        @wraps(func)
        async def inner(log_msg: str = log_msg, fail_msg: str =fail_msg, **kwargs):
            matcher: Matcher = kwargs['matcher']
            try:
                await func(**kwargs)
            except ActionFailed as e:
                # 此为bot本身由于风控或网络问题发不出消息，并非代码本身出问题
                await matcher.send(f'发送消息失败{e.info["wording"]}')
                logger.exception(f'发送{name}消息失败')
            except FinishException:
                # `finish` 会抛出此异常，应予以抛出而不处理
                raise 
            except Exception as e:
                # 代码本身出问题
                if log_msg:
                    if not fail_msg:
                        fail_msg = log_msg
                    if fail_msg[0] == '@':
                        await matcher.send(f'{fail_msg[1:]}\n错误信息为{e}', at_sender=True)
                    else:
                        await matcher.send(f'{fail_msg}\n错误信息为{e}')
                    if log_msg[0] == '@':
                        log_msg = log_msg[1:]
                    logger.exception(log_msg)
                else:
                    await matcher.send(f'发生错误 {e}，请检查后台输出。')
                    logger.exception(f'获取{name}信息错误')
        return inner
    return wrapper


@get_help.handle()
@handle_exception('帮助')
async def send_help_pic(matcher: Matcher, args: Message = CommandArg()):
    if args:
        # 防止只要是这个开头就一律响应
        return
    help_path = os.path.join(INDEX_PATH,'help.png')
    f = open(help_path, 'rb')
    ls_f = b64encode(f.read()).decode()
    img_mes = 'base64://' + ls_f
    f.close()
    await get_help.send(MessageSegment.image(img_mes))


@get_guide_pic.handle()
@handle_exception('建议')
async def send_guide_pic(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    with open(os.path.join(INDEX_PATH,'char_alias.json'),'r',encoding='utf8')as fp:
        char_data = json.load(fp)
    name = message
    for i in char_data:
        if message in i:
            name = i
        else:
            for k in char_data[i]:
                if message in k:
                    name = i
    #name = str(event.get_message()).strip().replace(' ', '')[:-2]
    url = 'https://img.genshin.minigg.cn/guide/{}.jpg'.format(name)
    await get_guide_pic.send(MessageSegment.image(url))

@get_char_adv.handle()
@handle_exception('建议')
async def send_char_adv(matcher: Matcher, args: Message = CommandArg()):
    name = args.extract_plain_text().strip().replace(' ', '')
    im = await char_adv(name)
    await get_char_adv.send(im)


@get_weapon_adv.handle()
@handle_exception('建议')
async def send_weapon_adv(matcher: Matcher, args: Message = CommandArg()):
    name = args.extract_plain_text().strip().replace(' ', '')
    im = await weapon_adv(name)
    await get_weapon_adv.send(im)


@get_audio.handle()
@handle_exception('语音','语音发送失败，可能是FFmpeg环境未配置。')
async def send_audio(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    im = await audio_wiki(name, message)
    if name == '列表':
        await get_audio.send(MessageSegment.image(im))
    else:
        if isinstance(im, str):
            await get_audio.send(im)
        else:
            await get_audio.send(MessageSegment.record(im))


@get_lots.handle()
@handle_exception('御神签')
async def send_lots(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    if args:
        return
    qid = int(event.sender.user_id)
    raw_data = await get_a_lots(qid)
    im = base64.b64decode(raw_data).decode('utf-8')
    await get_lots.send(im)


@get_enemies.handle()
@handle_exception('怪物')
async def send_enemies(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await enemies_wiki(message)
    await get_enemies.send(im)


@get_food.handle()
@handle_exception('食物')
async def send_food(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await foods_wiki(message)
    await get_food.send(im)


@get_artifacts.handle()
@handle_exception('圣遗物')
async def send_artifacts(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await artifacts_wiki(message)
    await get_artifacts.send(im)


@get_weapon.handle()
@handle_exception('武器')
async def send_weapon(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    level = re.findall(r'[0-9]+', message)
    if len(level) == 1:
        im = await weapon_wiki(name, level=level[0])
    else:
        im = await weapon_wiki(name)
    await get_weapon.send(im)


@get_talents.handle()
@handle_exception('天赋')
async def send_talents(bot: Bot, event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    num = re.findall(r'[0-9]+', message)
    if len(num) == 1:
        im = await char_wiki(name, 'talents', num[0])
        if isinstance(im, list):
            await bot.call_api('send_group_forward_msg', group_id=event.group_id, messages=im)
            return
    else:
        im = '参数不正确。'
    await get_talents.send(im)


@get_char.handle()
@handle_exception('角色')
async def send_char(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    level = re.findall(r'[0-9]+', message)
    if len(level) == 1:
        im = await char_wiki(name, 'char', level=level[0])
    else:
        im = await char_wiki(name)
    await get_char.send(im)


@get_cost.handle()
@handle_exception('材料')
async def send_cost(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    im = await char_wiki(message, 'costs')
    await get_cost.send(im)


@get_polar.handle()
@handle_exception('命座')
async def send_polar(matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    num = int(re.findall(r'\d+', message)[0])  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    if num <= 0 or num > 6:
        await get_polar.finish('你家{}有{}命？'.format(m, num))
    im = await char_wiki(m, 'constellations', num)
    await get_polar.send(im)


@get_event.handle()
@handle_exception('活动')
async def send_events(matcher: Matcher, args: Message = CommandArg()):
    if args:
        return
    img_path = os.path.join(FILE_PATH, 'event.jpg')
    while True:
        if os.path.exists(img_path):
            with open(img_path, 'rb') as f:
                im = MessageSegment.image(f.read())
            break
        else:
            await draw_event_pic()
    await get_event.send(im)


@add_cookie.handle()
@handle_exception('Cookie', '校验失败！请输入正确的Cookies！')
async def add_cookie_func(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    mes = args.extract_plain_text().strip().replace(' ', '')
    im = await deal_ck(mes, int(event.sender.user_id))
    await add_cookie.send(im)


# 开启 自动签到 和 推送树脂提醒 功能
@open_switch.handle()
async def open_switch_func(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    try:
        message = args.extract_plain_text().strip().replace(' ', '')
        m = ''.join(re.findall('[\u4e00-\u9fa5]', message))

        qid = int(event.sender.user_id)
        at = re.search(r'\[CQ:at,qq=(\d*)]', message)

        if m == '自动签到':
            try:
                if at and qid in superusers:
                    qid = at.group(1)
                elif at and at.group(1) != qid:
                    await open_switch.send('你没有权限。', at_sender=True)
                    return
                else:
                    pass
                gid = event.get_session_id().split('_')[1] if len(
                    event.get_session_id().split('_')) == 3 else 'on'
                uid = await select_db(qid, mode='uid')
                im = await open_push(int(uid[0]), qid, str(gid), 'StatusB')
                await open_switch.send(im, at_sender=True)
            except Exception:
                await open_switch.send('未绑定uid信息！', at_sender=True)
        elif m == '推送':
            try:
                if at and qid in superusers:
                    qid = at.group(1)
                elif at and at.group(1) != qid:
                    await open_switch.send('你没有权限。', at_sender=True)
                    return
                else:
                    pass
                gid = event.get_session_id().split('_')[1] if len(
                    event.get_session_id().split('_')) == 3 else 'on'
                uid = await select_db(qid, mode='uid')
                im = await open_push(int(uid[0]), qid, str(gid), 'StatusA')
                await open_switch.send(im, at_sender=True)
            except Exception:
                await open_switch.send('未绑定uid信息！', at_sender=True)
        elif m == '自动米游币':
            try:
                if at and qid in superusers:
                    qid = at.group(1)
                elif at and at.group(1) != qid:
                    await close_switch.send('你没有权限。', at_sender=True)
                    return
                else:
                    pass
                gid = event.get_session_id().split('_')[1] if len(
                    event.get_session_id().split('_')) == 3 else 'on'
                uid = await select_db(qid, mode='uid')
                im = await open_push(int(uid[0]), qid, str(gid), 'StatusC')
                await open_switch.send(im, at_sender=True)
            except Exception:
                await open_switch.send('未绑定uid信息！', at_sender=True)
        elif m == '简洁签到报告':
            try:
                if qid in superusers:
                    _ = await config_check('SignReportSimple', 'OPEN')
                    await open_switch.send('成功!', at_sender=True)
                else:
                    return
            except ActionFailed as e:
                await open_switch.send('机器人发送消息失败：{}'.format(e.info['wording']))
                logger.exception('发送设置成功信息失败')
            except Exception as e:
                await open_switch.send('发生错误 {},请检查后台输出。'.format(e))
                logger.exception('设置简洁签到报告失败')
    except ActionFailed as e:
        await open_switch.send('机器人发送消息失败：{}'.format(e.info['wording']))
        logger.exception('发送开启自动签到信息失败')
    except Exception as e:
        await open_switch.send('发生错误 {},请检查后台输出。'.format(e))
        logger.exception('开启自动签到失败')


# 关闭 自动签到 和 推送树脂提醒 功能
@close_switch.handle()
async def close_switch_func(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    try:
        message = args.extract_plain_text().strip().replace(' ', '')
        m = ''.join(re.findall('[\u4e00-\u9fa5]', message))

        qid = int(event.sender.user_id)
        at = re.search(r'\[CQ:at,qq=(\d*)]', message)

        if m == '自动签到':
            try:
                if at and qid in superusers:
                    qid = at.group(1)
                elif at and at.group(1) != qid:
                    await close_switch.send('你没有权限。', at_sender=True)
                    return
                else:
                    pass
                uid = await select_db(qid, mode='uid')
                im = await open_push(int(uid[0]), qid, 'off', 'StatusB')
                await close_switch.send(im, at_sender=True)
            except Exception:
                await close_switch.send('未绑定uid信息！', at_sender=True)
        elif m == '推送':
            try:
                if at and qid in superusers:
                    qid = at.group(1)
                elif at and at.group(1) != qid:
                    await close_switch.send('你没有权限。', at_sender=True)
                    return
                else:
                    pass
                uid = await select_db(qid, mode='uid')
                im = await open_push(int(uid[0]), qid, 'off', 'StatusA')
                await close_switch.send(im, at_sender=True)
            except Exception:
                await close_switch.send('未绑定uid信息！', at_sender=True)
        elif m == '自动米游币':
            try:
                if at and qid in superusers:
                    qid = at.group(1)
                elif at and at.group(1) != qid:
                    await close_switch.send('你没有权限。', at_sender=True)
                    return
                else:
                    pass
                uid = await select_db(qid, mode='uid')
                im = await open_push(int(uid[0]), qid, 'off', 'StatusC')
                await close_switch.send(im, at_sender=True)
            except Exception:
                await close_switch.send('未绑定uid信息！', at_sender=True)
        elif m == '简洁签到报告':
            try:
                if qid in superusers:
                    _ = await config_check('SignReportSimple', 'CLOSED')
                    await close_switch.send('成功!', at_sender=True)
                else:
                    return
            except ActionFailed as e:
                await close_switch.send('机器人发送消息失败：{}'.format(e.info['wording']))
                logger.exception('发送设置成功信息失败')
            except Exception as e:
                await close_switch.send('发生错误 {},请检查后台输出。'.format(e))
                logger.exception('设置简洁签到报告失败')
    except ActionFailed as e:
        await close_switch.send('机器人发送消息失败：{}'.format(e.info['wording']))
        logger.exception('发送开启自动签到信息失败')
    except Exception as e:
        await close_switch.send('发生错误 {},请检查后台输出。'.format(e))
        logger.exception('关闭自动签到失败')


# 图片版信息
@get_genshin_info.handle()
@handle_exception('当前','获取/发送当前信息失败', '@未找到绑定信息')
async def send_genshin_info(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    qid = int(event.sender.user_id)
    uid = await select_db(qid, mode='uid')
    image = re.search(r'\[CQ:image,file=(.*),url=(.*)]', message)
    uid = uid[0]
    im = await draw_info_pic(uid, image)
    await get_genshin_info.send(MessageSegment.image(im), at_sender=True)


# 群聊内 每月统计 功能
@monthly_data.handle()
@handle_exception('每月统计','获取/发送每月统计失败', '@未找到绑定信息')
async def send_monthly_data(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    if args:
        return
    qid = int(event.sender.user_id)
    uid = await select_db(qid, mode='uid')
    uid = uid[0]
    im = await award(uid)
    await monthly_data.send(im, at_sender=True)


# 群聊内 签到 功能
@get_sign.handle()
async def get_sing_func(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    if args:
        return
    im = None
    try:
        qid = int(event.sender.user_id)
        uid = await select_db(qid, mode='uid')
        uid = uid[0]
        im = await sign(uid)
    except TypeError:
        im = '没有找到绑定信息。'
    except Exception as e:
        im = '发生错误 {},请检查后台输出。'.format(e)
        logger.exception('签到失败')
    finally:
        try:
            await get_sign.send(im, at_sender=True)
        except ActionFailed as e:
            await get_sign.send('机器人发送消息失败：{}'.format(e.info['wording']))
            logger.exception('发送签到信息失败')


# 获取米游币
@get_mihoyo_coin.handle()
async def send_mihoyo_coin(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    if args:
        return
    im = None
    await get_mihoyo_coin.send('开始操作……', at_sender=True)
    try:
        qid = int(event.sender.user_id)
        im_mes = await mihoyo_coin(qid)
        im = im_mes
    except TypeError or AttributeError:
        im = '没有找到绑定信息。'
        logger.exception('获取米游币失败')
    except Exception as e:
        im = '发生错误 {},请检查后台输出。'.format(e)
        logger.exception('获取米游币失败')
    finally:
        try:
            await get_mihoyo_coin.send(im, at_sender=True)
        except ActionFailed as e:
            await get_mihoyo_coin.send('机器人发送消息失败：{}'.format(e.info['wording']))
            logger.exception('发送签到信息失败')


# 群聊内 校验Cookies 是否正常的功能，不正常自动删掉
@check.handle()
@handle_exception('Cookie校验','Cookie校验错误')
async def check_cookies(bot: Bot, matcher: Matcher, args: Message = CommandArg()):
    if args:
        return
    raw_mes = await check_db()
    im = raw_mes[0]
    await check.send(im)
    for i in raw_mes[1]:
        await bot.call_api(api='send_private_msg', **{
            'user_id': i[0],
            'message': ('您绑定的Cookies（uid{}）已失效，以下功能将会受到影响：\n'
                        '查看完整信息列表\n查看深渊配队\n自动签到/当前状态/每月统计\n'
                        '请及时重新绑定Cookies并重新开关相应功能。').format(i[1])
        })
        await asyncio.sleep(3 + random.randint(1, 3))


# 群聊内 查询当前树脂状态以及派遣状态 的命令
@daily_data.handle()
async def send_daily_data(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    try:
        if args:
            return
        uid = await select_db(int(event.sender.user_id), mode='uid')
        uid = uid[0]
        mes = await daily('ask', uid)
        im = mes[0]['message']
        await daily_data.send(im, at_sender=True)
    except TypeError:
        im = '没有找到绑定信息。'
        await daily_data.send(im, at_sender=True)
    except ActionFailed as e:
        await daily_data.send('机器人发送消息失败：{}'.format(e.info['wording']))
        logger.exception('发送当前状态信息失败')
    except Exception as e:
        await daily_data.send('发生错误 {},请检查后台输出。'.format(e))
        logger.exception('查询当前状态错误')


# 群聊内 查询uid 的命令
@get_uid_info.handle()
async def send_uid_info(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    try:
        message = args.extract_plain_text().strip().replace(' ', '')
        image = re.search(r'\[CQ:image,file=(.*),url=(.*)]', message)
        uid = re.findall(r'\d+', message)[0]  # str
        m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
        if m == '深渊':
            try:
                if len(re.findall(r'\d+', message)) == 2:
                    floor_num = re.findall(r'\d+', message)[1]
                    im = await draw_abyss_pic(uid, event.sender.nickname, floor_num, image)
                    if im.startswith('base64://'):
                        await get_uid_info.send(MessageSegment.image(im), at_sender=True)
                    else:
                        await get_uid_info.send(im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid, event.sender.nickname, image)
                    if im.startswith('base64://'):
                        await get_uid_info.send(MessageSegment.image(im), at_sender=True)
                    else:
                        await get_uid_info.send(im, at_sender=True)
            except ActionFailed as e:
                await get_uid_info.send('机器人发送消息失败：{}'.format(e.info['wording']))
                logger.exception('发送uid深渊信息失败')
            except (TypeError, IndexError):
                await get_uid_info.send('获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('深渊数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await get_uid_info.send('获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('深渊数据获取失败（数据状态问题）')
        elif m == '上期深渊':
            try:
                if len(re.findall(r'\d+', message)) == 2:
                    floor_num = re.findall(r'\d+', message)[1]
                    im = await draw_abyss_pic(uid, event.sender.nickname, floor_num, image, 2, '2')
                    if im.startswith('base64://'):
                        await get_uid_info.send(MessageSegment.image(im), at_sender=True)
                    else:
                        await get_uid_info.send(im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid, event.sender.nickname, image, 2, '2')
                    if im.startswith('base64://'):
                        await get_uid_info.send(MessageSegment.image(im), at_sender=True)
                    else:
                        await get_uid_info.send(im, at_sender=True)
            except ActionFailed as e:
                await get_uid_info.send('机器人发送消息失败：{}'.format(e.info['wording']))
                logger.exception('发送米游社深渊信息失败')
            except (TypeError, IndexError):
                await get_uid_info.send('获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('上期深渊数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await get_uid_info.send('获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('上期深渊数据获取失败（数据状态问题）')
        else:
            try:
                im = await draw_pic(uid, event.sender.nickname, image, 2)
                if im.startswith('base64://'):
                    await get_uid_info.send(MessageSegment.image(im), at_sender=True)
                else:
                    await get_uid_info.send(im, at_sender=True)
            except ActionFailed as e:
                await get_uid_info.send('机器人发送消息失败：{}'.format(e.info['wording']))
                logger.exception('发送uid信息失败')
            except (TypeError, IndexError):
                await get_uid_info.send('获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await get_uid_info.send('获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('数据获取失败（数据状态问题）')
    except Exception as e:
        await get_uid_info.send('发生错误 {},请检查后台输出。'.format(e))
        logger.exception('uid查询异常')


# 群聊内 绑定uid 的命令，会绑定至当前qq号上
@link_uid.handle()
@handle_exception('绑定uid','绑定uid异常')
async def link_uid_to_qq(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    uid = re.findall(r'\d+', message)[0]  # str
    await connect_db(int(event.sender.user_id), uid)
    await link_uid.send('绑定uid成功！', at_sender=True)


# 群聊内 绑定米游社通行证 的命令，会绑定至当前qq号上，和绑定uid不冲突，两者可以同时绑定
@link_mys.handle()
@handle_exception('绑定米游社通行证','绑定米游社通行证异常')
async def link_mihoyo_bbs_to_qq(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    message = args.extract_plain_text().strip().replace(' ', '')
    mys = re.findall(r'\d+', message)[0]  # str
    await connect_db(int(event.sender.user_id), None, mys)
    await link_mys.send('绑定米游社id成功！', at_sender=True)


# 群聊内 绑定过uid/mysid的情况下，可以查询，默认优先调用米游社通行证，多出世界等级一个参数
@search.handle()
async def get_info(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    try:
        message = args.extract_plain_text().strip().replace(' ', '')
        image = re.search(r'\[CQ:image,file=(.*),url=(.*)]', message)
        at = re.search(r'\[CQ:at,qq=(\d*)]', message)
        if at:
            qid = at.group(1)
            mi = await bot.call_api('get_group_member_info', **{'group_id': event.group_id, 'user_id': qid})
            nickname = mi['nickname']
            uid = await select_db(qid)
            message = message.replace(at.group(0), '')
        else:
            nickname = event.sender.nickname
            uid = await select_db(int(event.sender.user_id))

        m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
        if uid:
            if m == '深渊':
                try:
                    if len(re.findall(r'\d+', message)) == 1:
                        floor_num = re.findall(r'\d+', message)[0]
                        im = await draw_abyss_pic(uid[0], nickname, floor_num, image, uid[1])
                        if im.startswith('base64://'):
                            await search.send(MessageSegment.image(im), at_sender=True)
                        else:
                            await search.send(im, at_sender=True)
                    else:
                        im = await draw_abyss0_pic(uid[0], nickname, image, uid[1])
                        if im.startswith('base64://'):
                            await search.send(MessageSegment.image(im), at_sender=True)
                        else:
                            await search.send(im, at_sender=True)
                except ActionFailed as e:
                    await search.send('机器人发送消息失败：{}'.format(e.info['wording']))
                    logger.exception('发送uid深渊信息失败')
                except (TypeError, IndexError):
                    await search.send('获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                    logger.exception('深渊数据获取失败（Cookie失效/不公开信息）')
                except Exception:
                    await search.send('获取失败，请检查 cookie 及网络状态。')
                    logger.exception('深渊数据获取失败（数据状态问题）')
            elif m == '上期深渊':
                try:
                    if len(re.findall(r'\d+', message)) == 1:
                        floor_num = re.findall(r'\d+', message)[0]
                        im = await draw_abyss_pic(uid[0], nickname, floor_num, image, uid[1], '2')
                        if im.startswith('base64://'):
                            await search.send(MessageSegment.image(im), at_sender=True)
                        else:
                            await search.send(im, at_sender=True)
                    else:
                        im = await draw_abyss0_pic(uid[0], nickname, image, uid[1], '2')
                        if im.startswith('base64://'):
                            await search.send(MessageSegment.image(im), at_sender=True)
                        else:
                            await search.send(im, at_sender=True)
                except ActionFailed as e:
                    await search.send('机器人发送消息失败：{}'.format(e.info['wording']))
                    logger.exception('发送uid上期深渊信息失败')
                except (TypeError, IndexError):
                    await search.send('获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                    logger.exception('上期深渊数据获取失败（Cookie失效/不公开信息）')
                except Exception as e:
                    await search.send('获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                    logger.exception('上期深渊数据获取失败（数据状态问题）')
            elif m == '词云':
                try:
                    im = await draw_word_cloud(uid[0], image, uid[1])
                    if im.startswith('base64://'):
                        await search.send(MessageSegment.image(im), at_sender=True)
                    else:
                        await search.send(im, at_sender=True)
                except ActionFailed as e:
                    await search.send('机器人发送消息失败：{}'.format(e.info['wording']))
                    logger.exception('发送uid词云信息失败')
                except (TypeError, IndexError):
                    await search.send('获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                    logger.exception('词云数据获取失败（Cookie失效/不公开信息）')
                except Exception as e:
                    await search.send('获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                    logger.exception('词云数据获取失败（数据状态问题）')
            elif m == '':
                try:
                    im = await draw_pic(uid[0], nickname, image, uid[1])
                    if im.startswith('base64://'):
                        await search.send(MessageSegment.image(im), at_sender=True)
                    else:
                        await search.send(im, at_sender=True)
                except ActionFailed as e:
                    await search.send('机器人发送消息失败：{}'.format(e.info['wording']))
                    logger.exception('发送uid信息失败')
                except (TypeError, IndexError):
                    await search.send('获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                    logger.exception('uid数据获取失败（Cookie失效/不公开信息）')
                except Exception as e:
                    await search.send('获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                    logger.exception('数据获取失败（数据状态问题）')
            else:
                pass
        else:
            await search.send('未找到绑定记录！')
    except Exception as e:
        await search.send('发生错误 {},请检查后台输出。'.format(e))
        logger.exception('查询异常')


# 群聊内 查询米游社通行证 的命令
@get_mys_info.handle()
async def send_mihoyo_bbs_info(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    try:
        message = args.extract_plain_text().strip().replace(' ', '')
        image = re.search(r'\[CQ:image,file=(.*),url=(.*)]', message)
        uid = re.findall(r'\d+', message)[0]  # str
        m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
        if m == '深渊':
            try:
                if len(re.findall(r'\d+', message)) == 2:
                    floor_num = re.findall(r'\d+', message)[1]
                    im = await draw_abyss_pic(uid, event.sender.nickname, floor_num, image, 3)
                    if im.startswith('base64://'):
                        await get_mys_info.send(MessageSegment.image(im), at_sender=True)
                    else:
                        await get_mys_info.send(im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid, event.sender.nickname, image, 3)
                    if im.startswith('base64://'):
                        await get_mys_info.send(MessageSegment.image(im), at_sender=True)
                    else:
                        await get_mys_info.send(im, at_sender=True)
            except ActionFailed as e:
                await get_mys_info.send('机器人发送消息失败：{}'.format(e.info['wording']))
                logger.exception('发送米游社深渊信息失败')
            except (TypeError, IndexError):
                await get_mys_info.send('获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('深渊数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await get_mys_info.send('获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('深渊数据获取失败（数据状态问题）')
        elif m == '上期深渊':
            try:
                if len(re.findall(r'\d+', message)) == 1:
                    floor_num = re.findall(r'\d+', message)[0]
                    im = await draw_abyss_pic(uid, event.sender.nickname, floor_num, image, 3, '2')
                    if im.startswith('base64://'):
                        await get_mys_info.send(MessageSegment.image(im), at_sender=True)
                    else:
                        await get_mys_info.send(im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid, event.sender.nickname, image, 3, '2')
                    if im.startswith('base64://'):
                        await get_mys_info.send(MessageSegment.image(im), at_sender=True)
                    else:
                        await get_mys_info.send(im, at_sender=True)
            except ActionFailed as e:
                await get_mys_info.send('机器人发送消息失败：{}'.format(e.info['wording']))
                logger.exception('发送uid上期深渊信息失败')
            except (TypeError, IndexError):
                await get_mys_info.send('获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('上期深渊数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await get_mys_info.send('获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('上期深渊数据获取失败（数据状态问题）')
        else:
            try:
                im = await draw_pic(uid, event.sender.nickname, image, 3)
                if im.startswith('base64://'):
                    await get_mys_info.send(MessageSegment.image(im), at_sender=True)
                else:
                    await get_mys_info.send(im, at_sender=True)
            except ActionFailed as e:
                await get_mys_info.send('机器人发送消息失败：{}'.format(e.info['wording']))
                logger.exception('发送米游社信息失败')
            except (TypeError, IndexError):
                await get_mys_info.send('获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('米游社数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await get_mys_info.send('获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('米游社数据获取失败（数据状态问题）')
    except Exception as e:
        await get_mys_info.send('发生错误 {},请检查后台输出。'.format(e))
        logger.exception('米游社查询异常')


@all_recheck.handle()
async def recheck(args: Message = CommandArg()):
    if args:
        return
    await all_recheck.send('已开始执行')
    await daily_sign()


@all_bbscoin_recheck.handle()
async def bbs_recheck(args: Message = CommandArg()):
    if args:
        return
    await all_bbscoin_recheck.send('已开始执行')
    await daily_mihoyo_bbs_sign()

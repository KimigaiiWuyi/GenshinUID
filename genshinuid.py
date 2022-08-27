import base64
from pathlib import Path
import traceback

from aiocqhttp.exceptions import ActionFailed
from aiohttp import ClientConnectorError
from hoshino import Service
from hoshino.typing import CQEvent, HoshinoBot
from nonebot import MessageSegment, get_bot

from .mihoyo_libs.get_image import *
from .mihoyo_libs.get_mihoyo_bbs_data import *
from .enkaToData.enkaToData import *
from .enkaToData.drawCharCard import *

R_PATH = Path(__file__).parents[0]

sv = Service('genshinuid')
hoshino_bot = get_bot()

FILE_PATH = os.path.join(os.path.join(os.path.dirname(__file__), 'mihoyo_libs'), 'mihoyo_bbs')
INDEX_PATH = os.path.join(FILE_PATH, 'index')
Texture_PATH = os.path.join(FILE_PATH, 'texture2d')

AUTO_REFRESH = False
CK_HINT = '''获取Cookies教程：https://github.com/KimigaiiWuyi/GenshinUID/issues/255
绑定uid：uid为原神uid，如绑定uid12345
绑定mys：mys为米游社通行证，如绑定mys12345'''

@sv.on_fullmatch('gs帮助')
async def send_help_pic(bot: HoshinoBot, ev: CQEvent):
    try:
        help_path = os.path.join(INDEX_PATH,'help.png')
        f = open(help_path, 'rb')
        ls_f = b64encode(f.read()).decode()
        img_mes = 'base64://' + ls_f
        f.close()
        await bot.send(ev, MessageSegment.image(img_mes))
    except Exception:
        logger.exception('获取帮助失败。')

@sv.on_prefix('毕业度统计')
async def send_charcard_list(bot: HoshinoBot, ev: CQEvent):
    message = ev.message.extract_plain_text()
    message = message.replace(' ', '')
    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))
    limit = re.findall(r'\d+', message)  # str
    if len(limit) >= 1:
        limit = int(limit[0])
    else:
        limit = 24
    if at:
        at = at.group(1)
        uid = await select_db(at, mode='uid')
        message = message.replace(str(at), '')
    else:
        uid = await select_db(int(ev.sender['user_id']), mode='uid')
    uid = uid[0]
    im = await draw_cahrcard_list(uid, limit)
    
    if im.startswith('base64://'):
        await bot.send(ev, MessageSegment.image(im))
    else:
        await bot.send(ev, str(im))
    logger.info(f'UID{uid}获取角色数据成功！')

@sv.on_rex('[\u4e00-\u9fa5]+(推荐|攻略)')
async def send_guide_pic(bot: HoshinoBot, ev: CQEvent):
    try:
        message = str(ev.message).strip().replace(' ', '')[:-2]
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
        if httpx.head(url).status_code == 200:
            await bot.send(ev, MessageSegment.image(url))
        else:
            return
    except Exception:
        logger.exception('获取建议失败。')

@sv.on_rex('[\u4e00-\u9fa5]+(用什么|能用啥|怎么养)')
async def send_char_adv(bot: HoshinoBot, ev: CQEvent):
    try:
        name = str(ev.message).strip().replace(' ', '')[:-3]
        im = await char_adv(name)
        await bot.send(ev, im)
    except Exception:
        logger.exception('获取建议失败。')


@sv.on_rex('[\u4e00-\u9fa5]+(能给谁|给谁用|要给谁|谁能用)')
async def send_weapon_adv(bot: HoshinoBot, ev: CQEvent):
    try:
        name = str(ev.message).strip().replace(' ', '')[:-3]
        im = await weapon_adv(name)
        await bot.send(ev, im)
    except Exception:
        logger.exception('获取建议失败。')

@sv.on_prefix('参考面板')
async def send_bluekun_pic(bot: HoshinoBot, ev: CQEvent):
    pic_json = {'雷':'https://upload-bbs.mihoyo.com/upload/2022/04/04/160367110/1f5e3773874fcf3177b63672b02a88d7_859652593462461477.jpg',
                '火':'https://upload-bbs.mihoyo.com/upload/2022/04/04/160367110/c193d7abc4139afccd1ba892d5bb3a99_6658340945648783394.jpg',
                '冰':'https://upload-bbs.mihoyo.com/upload/2022/04/04/160367110/afcd1a31744c16f81ad9d8f2d75688a0_4525405643656826681.jpg',
                '风':'https://upload-bbs.mihoyo.com/upload/2022/04/04/160367110/689e93122216bfd8d231b8366e42ef46_1275479383799739625.jpg',
                '水':'https://upload-bbs.mihoyo.com/upload/2022/05/31/160367110/de5d77307f6997f5e94e2834f9ca86f0_8212017873163996402.png',
                '岩':'https://upload-bbs.mihoyo.com/upload/2022/04/04/160367110/d9a7c73f2c2f08ba6f0e960d4e815012_5142810778120366748.jpg'}
    try:
        message = ev.message.extract_plain_text().replace(' ', '')
        await bot.send(ev, MessageSegment.image(pic_json[message]))
    except:
        logger.exception('获取参考面板失败。')

@sv.on_prefix('语音')
async def send_audio(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        message = message.replace(' ', '')
        name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
        im = await audio_wiki(name, message)
        if name == '列表':
            ls_f = base64.b64encode(im).decode()
            img = 'base64://' + ls_f
            await bot.send(ev, MessageSegment.image(img))
        else:
            audios = 'base64://' + b64encode(im).decode()
            await bot.send(ev, MessageSegment.record(audios))
    except ActionFailed as e:
        logger.exception('获取语音失败')
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
    except Exception as e:
        logger.exception('获取语音失败或ffmpeg未配置')
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))


@sv.on_fullmatch('活动列表')
async def send_polar(bot: HoshinoBot, ev: CQEvent):
    try:
        img_path = os.path.join(FILE_PATH, 'event.jpg')
        while 1:
            if os.path.exists(img_path):
                f = open(img_path, 'rb')
                ls_f = base64.b64encode(f.read()).decode()
                img_mihoyo_bbs = 'base64://' + ls_f
                f.close()
                break
            else:
                await draw_event_pic()
        await bot.send(ev, MessageSegment.image(img_mihoyo_bbs))
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送活动列表失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('获取活动列表错误')


@sv.on_fullmatch('御神签')
async def send_lots(bot: HoshinoBot, ev: CQEvent):
    try:
        qid = ev.sender['user_id']
        raw_data = await get_a_lots(qid)
        im = base64.b64decode(raw_data).decode('utf-8')
        await bot.send(ev, im)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送御神签失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('获取御神签错误')


@sv.on_prefix('材料')
async def send_cost(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        message = message.replace(' ', '')
        im = await char_wiki(message, 'costs')
        await bot.send(ev, im)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送材料信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('获取材料信息错误')


@sv.on_prefix('原魔')
async def send_enemies(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        im = await enemies_wiki(message)
        await bot.send(ev, im)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送怪物信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('获取怪物信息错误')


@sv.on_prefix('食物')
async def send_food(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        im = await foods_wiki(message)
        await bot.send(ev, im)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送食物信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('获取食物信息错误')


@sv.on_prefix('圣遗物')
async def send_artifacts(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        im = await artifacts_wiki(message)
        await bot.send(ev, im)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送圣遗物信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('获取圣遗物信息错误')


@sv.on_prefix('天赋')
async def send_talents(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
        num = re.findall(r'[0-9]+', message)
        if len(num) == 1:
            im = await char_wiki(name, 'talents', num[0])
            if isinstance(im, list):
                await hoshino_bot.send_group_forward_msg(group_id=ev.group_id, messages=im)
                return
        else:
            im = '参数不正确。'
        await bot.send(ev, im)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送天赋信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('获取天赋信息错误')


@sv.on_prefix('武器')
async def send_weapon(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
        level = re.findall(r'[0-9]+', message)
        if len(level) == 1:
            im = await weapon_wiki(name, level=level[0])
        else:
            im = await weapon_wiki(name)
        await bot.send(ev, im, at_sender=True)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送武器信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('获取武器信息错误')


@sv.on_prefix('角色')
async def send_char(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        message = message.replace(' ', '')
        name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
        level = re.findall(r'[0-9]+', message)
        if len(level) == 1:
            im = await char_wiki(name, 'char', level=level[0])
        else:
            im = await char_wiki(name)
        await bot.send(ev, im)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送角色信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('获取角色信息错误')


@sv.on_prefix('命座')
async def send_polar(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        num = int(re.findall(r'\d+', message)[0])  # str
        m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
        if num <= 0 or num > 6:
            await bot.send(ev, '你家{}有{}命？'.format(m, num), at_sender=True)
        else:
            im = await char_wiki(m, 'constellations', num)
            await bot.send(ev, im, at_sender=True)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送命座信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('获取命座信息错误')


# 每日零点清空cookies使用缓存
@sv.scheduled_job('cron', hour='0')
async def clean_cache():
    await delete_cache()


@sv.scheduled_job('cron', hour='2')
async def draw_event():
    await draw_event_pic()

@sv.scheduled_job('cron', hour='4')
async def daily_refresh_charData():
    global AUTO_REFRESH
    if AUTO_REFRESH:
        await refresh_charData()

async def refresh_charData():
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute('SELECT UID  FROM UIDDATA WHERE UID IS NOT NULL')
    c_data = cursor.fetchall()
    t = 0
    for row in c_data:
        uid = row[0]
        try:
            im = await enkaToData(uid)
            logger.info(im)
            t += 1
            await asyncio.sleep(18 + random.randint(2, 6))
        except:
            logger.exception(f'{uid}刷新失败！')
            logger.error(f'{uid}刷新失败！本次自动刷新结束！')
            return f'执行失败从{uid}！共刷新{str(t)}个角色！'
    else:
        return f'执行成功！共刷新{str(t)}个角色！'
    
@sv.on_prefix('强制刷新')
async def send_card_info(bot: HoshinoBot, ev: CQEvent):
    message = ev.message.extract_plain_text()
    uid = re.findall(r'\d+', message)  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    qid = str(ev.sender['user_id'])
    try:
        if len(uid) >= 1:
            uid = uid[0]
        else:
            if m == '全部数据':
                if qid in bot.config.SUPERUSERS:
                    await bot.send(ev, '开始刷新全部数据，这可能需要相当长的一段时间！！')
                    im = await refresh_charData()
                    await bot.send(ev, str(im))
                    return
                else:
                    return
            else:
                uid = await select_db(qid, mode='uid')
                uid = uid[0]
        im = await enkaToData(uid)
        await bot.send(ev, str(im))
        logger.info(f'UID{uid}获取角色数据成功！')
    except:
        await bot.send(ev, '获取角色数据失败！')
        logger.exception('获取角色数据失败！')

@sv.on_fullmatch('开始获取米游币')
async def send_mihoyo_coin(bot: HoshinoBot, ev: CQEvent):
    await bot.send(ev, '开始操作……', at_sender=True)
    try:
        qid = ev.sender['user_id']
        im_mes = await mihoyo_coin(int(qid))
        im = im_mes
    except TypeError or AttributeError:
        im = '没有找到绑定信息。\n' + CK_HINT
        logger.exception('获取米游币失败')
    except Exception as e:
        im = '发生错误 {},请检查后台输出。'.format(e)
        logger.exception('获取米游币失败')
    finally:
        try:
            await bot.send(ev, im, at_sender=True)
        except ActionFailed as e:
            await bot.send(ev, '机器人发送消息失败：{}'.format(e.info['wording']))
            logger.exception('发送签到信息失败')


@sv.on_fullmatch('全部重签')
async def _(bot: HoshinoBot, ev: CQEvent):
    try:
        if ev.user_id not in bot.config.SUPERUSERS:
            return
        await bot.send(ev, '已开始执行')
        await daily_sign()
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
    except Exception as e:
        traceback.print_exc()
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))


@sv.on_fullmatch('全部重获取')
async def bbscoin_resign(bot: HoshinoBot, ev: CQEvent):
    try:
        if ev.user_id not in bot.config.SUPERUSERS:
            return
        await bot.send(ev, '已开始执行')
        await daily_mihoyo_bbs_sign()
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
    except Exception as e:
        traceback.print_exc()
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))


# 每隔半小时检测树脂是否超过设定值
@sv.scheduled_job('cron', minute='*/30')
async def push():
    daily_data = await daily()
    if daily_data is not None:
        for i in daily_data:
            if i['gid'] == 'on':
                await hoshino_bot.send_private_msg(user_id=i['qid'], message=i['message'])
            else:
                await hoshino_bot.send_group_msg(group_id=i['gid'], message=f'[CQ:at,qq={i["qid"]}]'
                                                                            + '\n' + i['message'])
    else:
        pass


# 每日零点半进行米游社签到
@sv.scheduled_job('cron', hour='0', minute='30')
async def daily_sign_schedule():
    await daily_sign()


async def daily_sign():
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
                await hoshino_bot.send_private_msg(user_id=row[2], message=im)
            except:
                logger.exception(f'{im} Error')
        else:
            message = f'[CQ:at,qq={row[2]}]\n{im}'
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
                        temp_list.append({'push_group': row[4], 'push_message': message, 'success': 0, 'failed': 1})
                    else:
                        temp_list.append({'push_group': row[4], 'push_message': '', 'success': 1, 'failed': 0})
            else:
                for i in temp_list:
                    if row[4] == i['push_group'] and i['num'] < 4:
                        i['push_message'] += '\n' + message
                        i['num'] += 1
                        break
                else:
                    temp_list.append({'push_group': row[4], 'push_message': message, 'num': 1})
        await asyncio.sleep(6 + random.randint(1, 3))
    if await config_check('SignReportSimple'):
        for i in temp_list:
            try:
                report = '以下为签到失败报告：{}'.format(i['push_message']) if i['push_message'] != '' else ''
                await hoshino_bot.send_group_msg(group_id=i['push_group'],
                                                 message='今日自动签到已完成！\n本群共签到成功{}人，'
                                                         '共签到失败{}人。{}'.format(i['success'], i['failed'], report))
            except:
                logger.exception('签到报告发送失败：{}'.format(i['push_message']))
            await asyncio.sleep(4 + random.randint(1, 3))
    else:
        for i in temp_list:
            try:
                await hoshino_bot.send_group_msg(group_id=i['push_group'], message=i['push_message'])
            except:
                logger.exception('签到报告发送失败：{}'.format(i['push_message']))
            await asyncio.sleep(4 + random.randint(1, 3))
    conn.close()
    return


# 每日零点五十进行米游币获取
@sv.scheduled_job('cron', hour='0', minute='50')
async def sign_at_night():
    await daily_mihoyo_bbs_sign()


async def daily_mihoyo_bbs_sign():
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute(
        'SELECT *  FROM NewCookiesTable WHERE StatusC != ?', ('off',))
    c_data = cursor.fetchall()
    im_success = 0
    im_failed = 0
    im_failed_str = ''
    for row in c_data:
        logger.info('正在执行{}'.format(row[0]))
        if row[8]:
            await asyncio.sleep(5 + random.randint(1, 3))
            im = await mihoyo_coin(str(row[2]), str(row[8]))
            try:
                logger.info('已执行完毕：{}'.format(row[0]))
                im_success += 1
                if await config_check('MhyBBSCoinReport'):
                    await hoshino_bot.send_private_msg(user_id=row[2], message=im)
            except Exception:
                logger.exception('执行失败：{}'.format(row[0]))
                im_failed += 1
                im_failed_str += '\n' + '执行失败：{}'.format(row[0])
    faild_im = '\n以下为签到失败报告：{}'.format(im_failed_str) if im_failed_str != '' else ''
    im = '今日获取mhycoin成功数量：{}，失败数量：{}{}'.format(im_success, im_failed, faild_im)
    for qid in hoshino_bot.config.SUPERUSERS:
        await hoshino_bot.send_private_msg(user_id = qid, message = im)
        await asyncio.sleep(5 + random.randint(1, 3))
    logger.info('已结束。')


# 私聊事件
@hoshino_bot.on_message('private')
async def setting(ctx):
    message = ctx['raw_message']
    sid = int(ctx['self_id'])
    userid = int(ctx['sender']['user_id'])
    gid = 0
    if '添加 ' in message:
        try:
            mes = message.replace('添加 ', '')
            im = await deal_ck(mes, userid)
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid,
                                       message=im)
        except ActionFailed as e:
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid,
                                       message='机器人发送消息失败：{}'.format(e))
            logger.exception('发送Cookie校验信息失败')
        except Exception as e:
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid,
                                       message='校验失败！请输入正确的Cookies！\n错误信息为{}'.format(e))
            logger.exception('Cookie校验失败')
    elif 'gs开启推送' in message:
        try:
            uid = await select_db(userid, mode='uid')
            im = await open_push(int(uid[0]), userid, 'on', 'StatusA')
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=im)
        except ActionFailed as e:
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid,
                                       message='机器人发送消息失败：{}'.format(e))
            logger.exception('私聊）发送开启推送信息失败')
        except Exception:
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message='未找到绑定记录！\n' + CK_HINT)
            logger.exception('开启推送失败')
    elif 'gs关闭推送' in message:
        try:
            uid = await select_db(userid, mode='uid')
            im = await open_push(int(uid[0]), userid, 'off', 'StatusA')
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=im)
        except ActionFailed as e:
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid,
                                       message='机器人发送消息失败：{}'.format(e))
            logger.exception('私聊）发送关闭推送信息失败')
        except Exception:
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message='未找到绑定记录！\n' + CK_HINT)
            logger.exception('关闭推送失败')
    elif 'gs开启自动米游币' in message:
        try:
            uid = await select_db(userid, mode='uid')
            im = await open_push(int(uid[0]), userid, 'on', 'StatusC')
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid,
                                       message=im, at_sender=True)
        except Exception:
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid,
                                       message='未绑定uid信息！', at_sender=True)
    elif 'gs关闭自动米游币' in message:
        try:
            uid = await select_db(userid, mode='uid')
            im = await open_push(int(uid[0]), userid, 'off', 'StatusC')
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid,
                                       message=im, at_sender=True)
        except Exception:
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid,
                                       message='未绑定uid信息！', at_sender=True)
    elif 'gs开启自动签到' in message:
        try:
            uid = await select_db(userid, mode='uid')
            im = await open_push(int(uid[0]), userid, 'on', 'StatusB')
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=im)
        except ActionFailed as e:
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid,
                                       message='机器人发送消息失败：{}'.format(e))
            logger.exception('私聊）发送开启自动签到信息失败')
        except Exception:
            traceback.print_exc()
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message='未找到绑定记录！\n' + CK_HINT)
            logger.exception('开启自动签到失败')
    elif 'gs关闭自动签到' in message:
        try:
            uid = await select_db(userid, mode='uid')
            im = await open_push(int(uid[0]), userid, 'off', 'StatusA')
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=im)
        except ActionFailed as e:
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid,
                                       message='机器人发送消息失败：{}'.format(e))
            logger.exception('私聊）发送关闭自动签到信息失败')
        except Exception:
            traceback.print_exc()
            await hoshino_bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message='未找到绑定记录！\n' + CK_HINT)
            logger.exception('关闭自动签到失败')


# 群聊开启 自动签到 和 推送树脂提醒 功能
@sv.on_prefix('gs开启')
async def open_switch_func(bot: HoshinoBot, ev: CQEvent):
    try:
        at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))
        message = ev.message.extract_plain_text()
        m = ''.join(re.findall('[\u4e00-\u9fa5]', message))

        qid = ev.sender['user_id']

        if m == '自动签到':
            try:
                if at:
                    if qid in bot.config.SUPERUSERS:
                        qid = at.group(1)
                    else:
                        await bot.send(ev, '你没有权限。', at_sender=True)
                        return
                else:
                    qid = ev.sender['user_id']
                gid = ev.group_id
                uid = await select_db(qid, mode='uid')
                im = await open_push(int(uid[0]), ev.sender['user_id'], str(gid), 'StatusB')
                await bot.send(ev, im, at_sender=True)
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送开启自动签到信息失败')
            except Exception:
                await bot.send(ev, '未绑定uid信息！', at_sender=True)
                logger.exception('开启自动签到失败')
        elif m == '推送':
            try:
                if at:
                    if qid in bot.config.SUPERUSERS:
                        qid = at.group(1)
                    else:
                        await bot.send(ev, '你没有权限。', at_sender=True)
                        return
                else:
                    qid = ev.sender['user_id']
                gid = ev.group_id
                uid = await select_db(qid, mode='uid')
                im = await open_push(int(uid[0]), ev.sender['user_id'], str(gid), 'StatusA')
                await bot.send(ev, im, at_sender=True)
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送开启推送信息失败')
            except Exception:
                await bot.send(ev, '未绑定uid信息！', at_sender=True)
                logger.exception('开启推送失败')
        elif m == '简洁签到报告':
            try:
                if qid in bot.config.SUPERUSERS:
                    _ = await config_check('SignReportSimple', 'OPEN')
                    await bot.send(ev, '成功!', at_sender=True)
                else:
                    return
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送设置成功信息失败')
            except Exception as e:
                await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
                logger.exception('设置简洁签到报告失败')
        elif m == '米游币推送':
            try:
                if qid in bot.config.SUPERUSERS:
                    _ = await config_check('MhyBBSCoinReport', 'OPEN')
                    await bot.send(ev, '米游币推送已开启！\n该选项不会影响到实际米游币获取，仅开启私聊推送！\n*【管理员命令全局生效】', at_sender=True)
                else:
                    return
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送设置成功信息失败')
            except Exception as e:
                await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
                logger.exception('设置米游币推送失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('开启功能失败')


# 群聊关闭 自动签到 和 推送树脂提醒 功能
@sv.on_prefix('gs关闭')
async def close_switch_func(bot: HoshinoBot, ev: CQEvent):
    try:
        at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))
        message = ev.message.extract_plain_text()
        m = ''.join(re.findall('[\u4e00-\u9fa5]', message))

        qid = ev.sender['user_id']

        if m == '自动签到':
            try:
                if at:
                    if qid in bot.config.SUPERUSERS:
                        qid = at.group(1)
                    else:
                        await bot.send(ev, '你没有权限。', at_sender=True)
                        return
                else:
                    qid = ev.sender['user_id']
                uid = await select_db(qid, mode='uid')
                im = await open_push(int(uid[0]), ev.sender['user_id'], 'off', 'StatusB')
                await bot.send(ev, im, at_sender=True)
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送关闭自动签到信息失败')
            except Exception:
                await bot.send(ev, '未绑定uid信息！', at_sender=True)
                logger.exception('关闭自动签到失败')
        elif m == '推送':
            try:
                if at:
                    if qid in bot.config.SUPERUSERS:
                        qid = at.group(1)
                    else:
                        await bot.send(ev, '你没有权限。', at_sender=True)
                        return
                else:
                    qid = ev.sender['user_id']
                uid = await select_db(qid, mode='uid')
                im = await open_push(int(uid[0]), ev.sender['user_id'], 'off', 'StatusA')
                await bot.send(ev, im, at_sender=True)
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送关闭推送信息失败')
            except Exception:
                await bot.send(ev, '未绑定uid信息！', at_sender=True)
                logger.exception('关闭推送失败')
        elif m == '简洁签到报告':
            try:
                if qid in bot.config.SUPERUSERS:
                    _ = await config_check('SignReportSimple', 'CLOSED')
                    await bot.send(ev, '成功!', at_sender=True)
                else:
                    return
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送设置成功信息失败')
            except Exception as e:
                await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
                logger.exception('设置简洁签到报告失败')
        elif m == '米游币推送':
            try:
                if qid in bot.config.SUPERUSERS:
                    _ = await config_check('MhyBBSCoinReport', 'CLOSED')
                    await bot.send(ev, '米游币推送已关闭！\n该选项不会影响到实际米游币获取，仅关闭私聊推送！\n*【管理员命令全局生效】', at_sender=True)
                else:
                    return
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送设置成功信息失败')
            except Exception as e:
                await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
                logger.exception('设置米游币推送失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('关闭功能失败')


# 群聊内 每月统计 功能
@sv.on_fullmatch('每月统计')
async def send_monthly_data(bot: HoshinoBot, ev: CQEvent):
    try:
        uid = await select_db(ev.sender['user_id'], mode='uid')
        uid = uid[0]
        im = await award(uid)
        await bot.send(ev, im, at_sender=True)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送每月统计信息失败')
    except Exception:
        await bot.send(ev, '没有找到绑定信息。\n' + CK_HINT, at_sender=True)
        logger.exception('获取每月统计失败')


# 群聊内 签到 功能
@sv.on_fullmatch('米游社签到')
async def get_sing_func(bot: HoshinoBot, ev: CQEvent):
    try:
        uid = await select_db(ev.sender['user_id'], mode='uid')
        uid = uid[0]
        im = await sign(uid)
        await bot.send(ev, im, at_sender=True)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送签到信息失败')
    except Exception:
        await bot.send(ev, '没有找到绑定信息。\n' + CK_HINT, at_sender=True)
        logger.exception('签到失败')


# 群聊内 校验Cookies 是否正常的功能，不正常自动删掉
@sv.on_fullmatch('校验全部Cookies')
async def check_cookies(bot: HoshinoBot, ev: CQEvent):
    try:
        raw_mes = await check_db()
        im = raw_mes[0]
        await bot.send(ev, im)
        for i in raw_mes[1]:
            await bot.send_private_msg(user_id=i[0],
                                       message='您绑定的Cookies（uid{}）已失效，以下功能将会受到影响：\n查看完整信息列表\n'
                                               '查看深渊配队\n自动签到/当前状态/每月统计\n'
                                               '请及时重新绑定Cookies并重新开关相应功能。'.format(i[1]))
            await asyncio.sleep(3 + random.randint(1, 3))
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送Cookie校验信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('Cookie校验错误')


# 群聊内 校验Stoken 是否正常的功能，不正常自动删掉
@sv.on_fullmatch('校验全部Stoken')
async def check_stoken(bot: HoshinoBot, ev: CQEvent):
    try:
        raw_mes = await check_stoken_db()
        im = raw_mes[0]
        await bot.send(ev, im)
        for i in raw_mes[1]:
            await bot.send_private_msg(user_id=i[0],
                                       message='您绑定的Stoken（uid{}）已失效，以下功能将会受到影响：\n'
                                               'gs开启自动米游币，开始获取米游币。\n'
                                               '重新添加后需要重新开启自动米游币。'.format(i[1]))
            await asyncio.sleep(3 + random.randint(1, 3))
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送Cookie校验信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('Cookie校验错误')


# 群聊内 查询当前树脂状态以及派遣状态 的命令
@sv.on_fullmatch('当前状态')
async def send_daily_data(bot: HoshinoBot, ev: CQEvent):
    try:
        uid = await select_db(ev.sender['user_id'], mode='uid')
        uid = uid[0]
        mes = await daily('ask', uid)
        im = mes[0]['message']
    except Exception:
        im = '没有找到绑定信息。\n' + CK_HINT
        logger.exception('获取当前状态失败')

    try:
        await bot.send(ev, im, at_sender=True)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送当前状态信息失败')


# 图片版信息
@sv.on_fullmatch('当前信息')
async def send_genshin_info(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        uid = await select_db(ev.sender['user_id'], mode='uid')
        uid = uid[0]
        image = re.search(r'\[CQ:image,file=(.*),url=(.*)]', message)
        im = await draw_info_pic(uid, image)
        try:
            await bot.send(ev, MessageSegment.image(im), at_sender=True)
        except ActionFailed as e:
            await bot.send(ev, '机器人发送消息失败：{}'.format(e))
            logger.exception('发送当前信息信息失败')
    except Exception:
        im = '没有找到绑定信息。\n' + CK_HINT
        await bot.send(ev, im, at_sender=True)
        logger.exception('获取当前信息失败')


# 群聊内 查询uid 的命令
@sv.on_prefix('uid')
async def send_uid_info(bot: HoshinoBot, ev: CQEvent):
    try:
        image = re.search(r'\[CQ:image,file=(.*),url=(.*)]', str(ev.message))
        message = ev.message.extract_plain_text()
        uid = re.findall(r'\d+', message)[0]  # str
        m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
        if m == '深渊':
            try:
                if len(re.findall(r'\d+', message)) == 2:
                    floor_num = re.findall(r'\d+', message)[1]
                    im = await draw_abyss_pic(uid, ev.sender['nickname'], floor_num, image)
                    if im.startswith('base64://'):
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                    else:
                        await bot.send(ev, im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid, ev.sender['nickname'], image)
                    if im.startswith('base64://'):
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                    else:
                        await bot.send(ev, im, at_sender=True)
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送uid深渊信息失败')
            except TypeError:
                await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('深渊数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('深渊数据获取失败（数据状态问题）')
        elif m == '上期深渊':
            try:
                if len(re.findall(r'\d+', message)) == 2:
                    floor_num = re.findall(r'\d+', message)[1]
                    im = await draw_abyss_pic(uid, ev.sender['nickname'], floor_num, image, 2, '2')
                    if im.startswith('base64://'):
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                    else:
                        await bot.send(ev, im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid, ev.sender['nickname'], image, 2, '2')
                    if im.startswith('base64://'):
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                    else:
                        await bot.send(ev, im, at_sender=True)
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送uid上期深渊信息失败')
            except TypeError:
                await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('上期深渊数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('上期深渊数据获取失败（数据状态问题）')
        elif m == '':
            try:
                im = await draw_pic(uid, ev.sender['nickname'], image, 2)
                if im.startswith('base64://'):
                    await bot.send(ev, MessageSegment.image(im), at_sender=True)
                else:
                    await bot.send(ev, im, at_sender=True)
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送uid信息失败')
            except TypeError:
                await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('数据获取失败（数据状态问题）')
        else:
            try:
                if m == '展柜角色':
                    uid_fold = R_PATH / 'enkaToData' / 'player' / str(uid)
                    char_file_list = uid_fold.glob('*')
                    char_list = []
                    for i in char_file_list:
                        file_name = str(i).split('/')[-1]
                        if '\u4e00' <= file_name[0] <= '\u9fff':
                            char_list.append(file_name.split('.')[0])
                    char_list_str = ','.join(char_list)
                    await bot.send(ev, f'UID{uid}当前缓存角色:{char_list_str}', at_sender=True)
                else:
                    char_name = m
                    with open(os.path.join(INDEX_PATH, 'char_alias.json'),
                            'r',
                            encoding='utf8') as fp:
                        char_data = json.load(fp)
                    for i in char_data:
                        if char_name in i:
                            char_name = i
                        else:
                            for k in char_data[i]:
                                if char_name in k:
                                    char_name = i
                    if '旅行者' in char_name:
                        char_name = '旅行者'
                    with open(R_PATH / 'enkaToData' / 'player' / str(uid) / f'{char_name}.json',
                            'r',
                            encoding='utf8') as fp:
                        raw_data = json.load(fp)
                    im = await draw_char_card(raw_data, image)
                    await bot.send(ev, MessageSegment.image(im), at_sender=True)
            except FileNotFoundError:
                await bot.send(ev, f'你还没有{m}的缓存噢！\n请先使用【强制刷新】命令来缓存数据！\n或者使用【查询展柜角色】命令查看已缓存角色！', at_sender=True)
                logger.exception('获取信息失败,你可以使用强制刷新命令进行刷新。')
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送uid信息失败')
            except TypeError:
                await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('数据获取失败（数据状态问题）')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('uid查询异常')


# 群聊内 绑定uid 的命令，会绑定至当前qq号上
@sv.on_prefix('绑定uid')
async def link_uid_to_qq(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        uid = re.findall(r'\d+', message)[0]  # str
        await connect_db(ev.sender['user_id'], uid)
        await bot.send(ev, '绑定uid成功！', at_sender=True)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送绑定信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('绑定uid异常')


# 群聊内 绑定米游社通行证 的命令，会绑定至当前qq号上，和绑定uid不冲突，两者可以同时绑定
@sv.on_prefix('绑定mys')
async def link_mihoyo_bbs_to_qq(bot: HoshinoBot, ev: CQEvent):
    try:
        message = ev.message.extract_plain_text()
        mys = re.findall(r'\d+', message)[0]  # str
        await connect_db(ev.sender['user_id'], None, mys)
        await bot.send(ev, '绑定米游社id成功！', at_sender=True)
    except ActionFailed as e:
        await bot.send(ev, '机器人发送消息失败：{}'.format(e))
        logger.exception('发送绑定信息失败')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('绑定米游社通行证异常')


# 群聊内 绑定过uid/mysid的情况下，可以查询，默认优先调用米游社通行证，多出世界等级一个参数
@sv.on_prefix('查询')
async def get_info(bot, ev):
    try:
        image = re.search(r'\[CQ:image,file=(.*),url=(.*)]', str(ev.message))
        at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.raw_message.strip()))
        message = ev.message.extract_plain_text()
        if at:
            qid = at.group(1)
            mi = await bot.get_group_member_info(group_id=ev.group_id, user_id=qid)
            nickname = mi['nickname']
            uid = await select_db(qid)
        else:
            nickname = ev.sender['nickname']
            uid = await select_db(ev.sender['user_id'])

        m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
        if uid:
            if m == '深渊':
                try:
                    if len(re.findall(r'\d+', message)) == 1:
                        floor_num = re.findall(r'\d+', message)[0]
                        im = await draw_abyss_pic(uid[0], nickname, floor_num, image, uid[1])
                        if im.startswith('base64://'):
                            await bot.send(ev, MessageSegment.image(im), at_sender=True)
                        else:
                            await bot.send(ev, im, at_sender=True)
                    else:
                        im = await draw_abyss0_pic(uid[0], nickname, image, uid[1])
                        if im.startswith('base64://'):
                            await bot.send(ev, MessageSegment.image(im), at_sender=True)
                        else:
                            await bot.send(ev, im, at_sender=True)
                except ActionFailed as e:
                    await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                    logger.exception('发送uid深渊信息失败')
                except TypeError:
                    await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                    logger.exception('深渊数据获取失败（Cookie失效/不公开信息）')
                except Exception as e:
                    await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                    logger.exception('深渊数据获取失败（数据状态问题）')
            elif m == '上期深渊':
                try:
                    if len(re.findall(r'\d+', message)) == 1:
                        floor_num = re.findall(r'\d+', message)[0]
                        im = await draw_abyss_pic(uid[0], nickname, floor_num, image, uid[1], '2')
                        if im.startswith('base64://'):
                            await bot.send(ev, MessageSegment.image(im), at_sender=True)
                        else:
                            await bot.send(ev, im, at_sender=True)
                    else:
                        im = await draw_abyss0_pic(uid[0], nickname, image, uid[1], '2')
                        if im.startswith('base64://'):
                            await bot.send(ev, MessageSegment.image(im), at_sender=True)
                        else:
                            await bot.send(ev, im, at_sender=True)
                except ActionFailed as e:
                    await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                    logger.exception('发送uid上期深渊信息失败')
                except TypeError:
                    await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                    logger.exception('上期深渊数据获取失败（Cookie失效/不公开信息）')
                except Exception as e:
                    await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                    logger.exception('上期深渊数据获取失败（数据状态问题）')
            elif m == '词云':
                try:
                    im = await draw_word_cloud(uid[0], image, uid[1])
                    if im.startswith('base64://'):
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                    else:
                        await bot.send(ev, im, at_sender=True)
                except ActionFailed as e:
                    await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                    logger.exception('发送uid词云信息失败')
                except TypeError:
                    await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                    logger.exception('词云数据获取失败（Cookie失效/不公开信息）')
                except Exception as e:
                    await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                    logger.exception('词云数据获取失败（数据状态问题）')
            elif m == '收集':
                try:
                    im = await draw_collect_card(uid[0], nickname, image, uid[1])
                    if im.startswith('base64://'):
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                    else:
                        await bot.send(ev, im, at_sender=True)
                except ActionFailed as e:
                    await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                    logger.exception('发送uid信息失败')
                except TypeError:
                    await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                    logger.exception('数据获取失败（Cookie失效/不公开信息）')
                except ClientConnectorError:
                    await bot.send(ev, '获取失败：连接超时')
                    logger.exception('连接超时')
                except Exception as e:
                    await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                    logger.exception('数据获取失败（数据状态问题）')
            elif m == '':
                try:
                    im = await draw_pic(uid[0], nickname, image, uid[1])
                    if im.startswith('base64://'):
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                    else:
                        await bot.send(ev, im, at_sender=True)
                except ActionFailed as e:
                    await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                    logger.exception('发送uid信息失败')
                except TypeError:
                    await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                    logger.exception('数据获取失败（Cookie失效/不公开信息）')
                except ClientConnectorError:
                    await bot.send(ev, '获取失败：连接超时')
                    logger.exception('连接超时')
                except Exception as e:
                    await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                    logger.exception('数据获取失败（数据状态问题）')
            else:
                try:
                    if at:
                        qid = at.group(1)
                    else:
                        qid = ev.sender['user_id']
                    uid = await select_db(qid, mode='uid')
                    uid = uid[0]
                    if m == '展柜角色':
                        uid_fold = R_PATH / 'enkaToData' / 'player' / str(uid)
                        char_file_list = uid_fold.glob('*')
                        char_list = []
                        for i in char_file_list:
                            file_name = i.name
                            if '\u4e00' <= file_name[0] <= '\u9fff':
                                char_list.append(file_name.split('.')[0])
                        char_list_str = ','.join(char_list)
                        await bot.send(ev, f'UID{uid}当前缓存角色:{char_list_str}', at_sender=True)
                    else:
                        char_name = m
                        with open(os.path.join(INDEX_PATH, 'char_alias.json'),
                                'r',
                                encoding='utf8') as fp:
                            char_data = json.load(fp)
                        for i in char_data:
                            if char_name in i:
                                char_name = i
                            else:
                                for k in char_data[i]:
                                    if char_name in k:
                                        char_name = i
                        if '旅行者' in char_name:
                            char_name = '旅行者'
                        with open(R_PATH / 'enkaToData' / 'player' / str(uid) / f'{char_name}.json',
                                'r',
                                encoding='utf8') as fp:
                            raw_data = json.load(fp)
                        im = await draw_char_card(raw_data, image)
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                except FileNotFoundError:
                    await bot.send(ev, f'你还没有{m}的缓存噢！\n请先使用【强制刷新】命令来缓存数据！\n或者使用【查询展柜角色】命令查看已缓存角色！', at_sender=True)
                    logger.exception('获取信息失败,你可以使用强制刷新命令进行刷新。')
                except Exception:
                    logger.exception('获取信息失败,你可以使用强制刷新命令进行刷新。')
        else:
            await bot.send(ev, '未找到绑定记录！\n' + CK_HINT)
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('查询异常')


# 群聊内 查询米游社通行证 的命令
@sv.on_prefix('mys')
async def send_mihoyo_bbs_info(bot: HoshinoBot, ev: CQEvent):
    try:
        image = re.search(r'\[CQ:image,file=(.*),url=(.*)]', str(ev.message))
        message = ev.message.extract_plain_text()
        uid = re.findall(r'\d+', message)[0]  # str
        m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
        if m == '深渊':
            try:
                if len(re.findall(r'\d+', message)) == 2:
                    floor_num = re.findall(r'\d+', message)[1]
                    im = await draw_abyss_pic(uid, ev.sender['nickname'], floor_num, image, 3)
                    if im.startswith('base64://'):
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                    else:
                        await bot.send(ev, im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid, ev.sender['nickname'], image, 3)
                    if im.startswith('base64://'):
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                    else:
                        await bot.send(ev, im, at_sender=True)
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送米游社深渊信息失败')
            except TypeError:
                await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('深渊数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('深渊数据获取失败（数据状态问题）')
        elif m == '上期深渊':
            try:
                if len(re.findall(r'\d+', message)) == 1:
                    floor_num = re.findall(r'\d+', message)[0]
                    im = await draw_abyss_pic(uid, ev.sender['nickname'], floor_num, image, 3, '2')
                    if im.startswith('base64://'):
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                    else:
                        await bot.send(ev, im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid, ev.sender['nickname'], image, 3, '2')
                    if im.startswith('base64://'):
                        await bot.send(ev, MessageSegment.image(im), at_sender=True)
                    else:
                        await bot.send(ev, im, at_sender=True)
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送米游社上期深渊信息失败')
            except TypeError:
                await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('上期深渊数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('上期深渊数据获取失败（数据状态问题）')
        else:
            try:
                im = await draw_pic(uid, ev.sender['nickname'], image, 3)
                if im.startswith('base64://'):
                    await bot.send(ev, MessageSegment.image(im), at_sender=True)
                else:
                    await bot.send(ev, im, at_sender=True)
            except ActionFailed as e:
                await bot.send(ev, '机器人发送消息失败：{}'.format(e))
                logger.exception('发送米游社信息失败')
            except TypeError:
                await bot.send(ev, '获取失败，可能是Cookies失效或者未打开米游社角色详情开关。')
                logger.exception('米游社数据获取失败（Cookie失效/不公开信息）')
            except Exception as e:
                await bot.send(ev, '获取失败，有可能是数据状态有问题,\n{}\n请检查后台输出。'.format(e))
                logger.exception('米游社数据获取失败（数据状态问题）')
    except Exception as e:
        await bot.send(ev, '发生错误 {},请检查后台输出。'.format(e))
        logger.exception('米游社查询异常')

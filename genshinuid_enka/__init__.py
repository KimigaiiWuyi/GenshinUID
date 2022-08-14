from pathlib import Path

from .draw_char_card import *
from .draw_char_card import draw_char_img
from ..all_import import *  # noqa: F401,F403
from ..utils.enka_api.enka_to_data import enka_to_data
from ..utils.db_operation.db_operation import get_all_uid
from ..utils.message.error_reply import *  # noqa: F401,F403
from ..utils.mhy_api.convert_mysid_to_uid import convert_mysid
from ..utils.alias.alias_to_char_name import alias_to_char_name

refresh = on_command('强制刷新')
get_charcard_list = on_command('毕业度统计')
get_char_info = on_regex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(uid|查询|mys)([0-9]+)?'
    r'([\u4e00-\u9fffa-zA-Z0-9]*)'
    r'(\[CQ:at,qq=[0-9]+\])?( )?$',
    priority=2,
)

refresh_scheduler = require('nonebot_plugin_apscheduler').scheduler

PLAYER_PATH = Path(__file__).parents[1] / 'player'


@get_char_info.handle()
@handle_exception('查询角色面板')
async def send_char_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
    custom: ImageAndAt = Depends(),
):
    logger.info('开始执行[查询角色面板]')
    logger.info('[查询角色面板]参数: {}'.format(args))
    at = custom.get_first_at()
    if at:
        qid = at
    else:
        qid = event.user_id
    logger.info('[查询角色面板]QQ: {}'.format(qid))

    if args[2] != 'mys':
        if args[3] is None:
            uid = await select_db(qid, mode='uid')
            uid = str(uid)
        elif len(args[3]) != 9:
            return
        else:
            uid = args[3]
    else:
        uid = await convert_mysid(args[3])

    logger.info('[查询角色面板]uid: {}'.format(uid))

    player_path = PLAYER_PATH / str(uid)
    if args[4] == '展柜角色':
        char_file_list = player_path.glob('*')
        char_list = []
        for i in char_file_list:
            file_name = i.name
            if '\u4e00' <= file_name[0] <= '\u9fff':
                char_list.append(file_name.split('.')[0])
        char_list_str = ','.join(char_list)
        await matcher.finish(f'UID{uid}当前缓存角色:{char_list_str}', at_sender=True)
    elif args[4] is None:
        return
    else:
        char_name = await alias_to_char_name(args[4])
        char_path = player_path / f'{char_name}.json'
        if char_path.exists():
            with open(char_path, 'r', encoding='utf8') as fp:
                char_data = json.load(fp)
        else:
            await matcher.finish(CHAR_HINT.format(char_name), at_sender=True)

    im = await draw_char_img(char_data)

    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')


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
            await asyncio.sleep(18 + random.randint(2, 6))
        except:
            logger.exception(f'{uid}刷新失败！')
            logger.error(f'{uid}刷新失败！本次自动刷新结束！')
            return f'执行失败从{uid}！共刷新{str(t)}个角色！'
    else:
        logger.info(f'共刷新{str(t)}个角色！')
        return f'执行成功！共刷新{str(t)}个角色！'


@refresh_scheduler.scheduled_job('cron', hour='4')
async def daily_refresh_charData():
    await refresh_char_data()


@refresh.handle()
@handle_exception('强制刷新')
async def send_card_info(
    matcher: Matcher,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    args: Message = CommandArg(),
):
    message = args.extract_plain_text().strip().replace(' ', '')
    uid = re.findall(r'\d+', message)  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    qid = int(event.sender.user_id)  # type: ignore

    if len(uid) >= 1:
        uid = uid[0]
    else:
        if m == '全部数据':
            if qid in SUPERUSERS:
                await matcher.send('开始刷新全部数据，这可能需要相当长的一段时间！！')
                im = await refresh_char_data()
                await matcher.finish(str(im))
            else:
                return
        else:
            uid = await select_db(qid, mode='uid')
            uid = str(uid)
    im = await enka_to_data(uid)
    logger.info(f'UID{uid}获取角色数据成功！')
    await matcher.finish(str(im))


@get_charcard_list.handle()
@handle_exception('毕业度统计')
async def send_charcard_list(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Message = CommandArg(),
    custom: ImageAndAt = Depends(),
):

    message = args.extract_plain_text().strip().replace(' ', '')
    limit = re.findall(r'\d+', message)  # str
    if len(limit) >= 1:
        limit = int(limit[0])
    else:
        limit = 24
    at = custom.get_first_at()
    if at:
        uid = await select_db(at, mode='uid')
        message = message.replace(str(at), '')
    else:
        uid = await select_db(int(event.sender.user_id), mode='uid')  # type: ignore
    im = await draw_cahrcard_list(str(uid), limit)

    logger.info(f'UID{uid}获取角色数据成功！')
    if isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish(str(im))

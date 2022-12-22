from hoshino import Service, priv
from hoshino.typing import MessageSegment
from .main import consume_remind
from ..all_import import UID_HINT, select_db
from .ann_card import ann_list_card, ann_detail_card, sub_ann, unsub_ann, check_ann_state

sv_help = '''
原神公告
原神公告#ID
'''.strip()

sv = Service(
    name='原神公告',  # 功能名
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
    visible=True,  # 可见性
    enable_on_default=True,  # 默认启用
    # bundle = '娱乐', #分组归类
    help_=sv_help  # 帮助说明
)

prefix = '原神'


@sv.on_prefix((f'{prefix}公告#', f'{prefix}公告'))
async def ann_(bot, ev):
    ann_id = ev.message.extract_plain_text().strip()
    if not ann_id:
        img = await ann_list_card()
        await bot.send(ev, MessageSegment.image(img), at_sender=True)
        return
    
    if not ann_id.isdigit():
        raise Exception("公告ID不正确")
    try:
        img = await ann_detail_card(int(ann_id))
        await bot.send(ev, MessageSegment.image(img), at_sender=True)
    except Exception as e:
        await bot.finish(ev, str(e))


@sv.on_fullmatch(f'订阅{prefix}公告')
async def sub_ann_(bot, ev):
    if not priv.check_priv(ev, priv.ADMIN):
        raise Exception("你没有权限开启原神公告推送")
    try:
        await bot.send(ev, sub_ann(ev.group_id))
    except Exception as e:
        await bot.finish(ev, str(e))


@sv.on_fullmatch((f'取消订阅{prefix}公告', f'取消{prefix}公告', f'退订{prefix}公告'))
async def unsub_ann_(bot, ev):
    if not priv.check_priv(ev, priv.ADMIN):
        raise Exception("你没有权限取消原神公告推送")
    try:
        await bot.send(ev, unsub_ann(ev.group_id))
    except Exception as e:
        await bot.finish(ev, str(e))


@sv.on_fullmatch(f'取消{prefix}公告红点')
async def consume_remind_(bot, ev):
    try:
        qid = int(ev.sender['user_id'])
        uid = await select_db(qid, mode='uid')
        uid = str(uid)
        if '未找到绑定的UID' in uid:
            await bot.send(ev, UID_HINT)
            return
        await bot.send(ev, await consume_remind(uid), at_sender=True)
    except Exception as e:
        await bot.finish(ev, str(e))

@sv.scheduled_job('cron',minute=10)
async def check_ann():
    await check_ann_state()
from base64 import b64encode
from pathlib import Path

import pytest
from nonebot import logger
from nonebug import App


@pytest.mark.asyncio
async def test_weapon(app: App, get_weapon_message):
    from nonebot.adapters.onebot.v11 import Message
    from .utils import make_sender, make_event
    from ..genshin_uid import get_weapon as matcher
    weapon_message_1, weapon_message_2 = get_weapon_message

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('武器天空之刃')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, weapon_message_1, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('武器阿')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, weapon_message_2, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('武器翼90')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, '天空之翼\n等级：90（突破6）\n攻击力：674\n暴击率：22.1%', None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('武器0')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, '武器不存在。', None)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_character(app: App, get_character_message, get_async_http_client, get_http_client):
    from nonebot.adapters.onebot.v11 import Message
    from .utils import make_sender, make_event
    from ..genshin_uid import get_char as matcher

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('角色七七')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, get_character_message, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('角色莉90')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, '可莉\n等级：90\n血量：10286\n攻击力：310\n防御力：614\n火元素伤害加成：28.8%', None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('角色火')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        # 由于数据动态更新，这里从小灰灰API获取消息进行校验，并进行log输出
        params = {
            'url': 'https://info.minigg.cn/characters',
            'params': {
                'query': '火'
            }
        }
        try:
            data = await get_async_http_client.get(**params)
        except RuntimeError:
            logger.warning('Use async HTTP Client failed, use sync HTTP Client instead.')
            data = get_http_client.get(**params)
        data = data.json()
        logger.info('Character 角色火 >>>' + str(data))
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, ','.join(data), None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('角色单手剑')
        params = {
            'url': 'https://info.minigg.cn/characters',
            'params': {
                'query': '单手剑'
            }
        }
        try:
            data = await get_async_http_client.get(**params)
        except RuntimeError:
            logger.warning('Use async HTTP Client failed, use sync HTTP Client instead.')
            data = get_http_client.get(**params)
        data = data.json()
        logger.info('Character 角色单手剑 >>>' + str(data))
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, ','.join(data), None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('角色八月')
        params = {
            'url': 'https://info.minigg.cn/characters',
            'params': {
                'query': '八月'
            }
        }
        try:
            data = await get_async_http_client.get(**params)
        except RuntimeError:
            logger.warning('Use async HTTP Client failed, use sync HTTP Client instead.')
            data = get_http_client.get(**params)
        data = data.json()
        logger.info('Character 角色八月 >>>' + str(data))
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, ','.join(data), None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('角色琉璃袋')
        params = {
            'url': 'https://info.minigg.cn/characters',
            'params': {
                'query': '琉璃袋'
            }
        }
        try:
            data = await get_async_http_client.get(**params)
        except RuntimeError:
            logger.warning('Use async HTTP Client failed, use sync HTTP Client instead.')
            data = get_http_client.get(**params)
        data = data.json()
        logger.info('Character 角色琉璃袋 >>>' + str(data))
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, ','.join(data), None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('角色0')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, '不存在该角色或类型。', None)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_polar(app: App, get_polar_message):
    from nonebot.adapters.onebot.v11 import Message
    from .utils import make_sender, make_event
    from ..genshin_uid import get_polar as matcher
    polar_message_1, polar_message_2 = get_polar_message

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('命座3可')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, polar_message_1, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('命座6芭芭拉')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, polar_message_2, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('命座8刻晴')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, '你家刻晴有8命？', None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('命座1零')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, '不存在该角色或命座数量。', None)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_cost(app: App, get_cost_message, get_async_http_client, get_http_client):
    from nonebot.adapters.onebot.v11 import Message
    from .utils import make_sender, make_event
    from ..genshin_uid import get_cost as matcher
    cost_message_1, cost_message_2 = get_cost_message

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('材料甘雨')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, cost_message_1, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('材料刻')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, cost_message_2, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('材料天光')
        params = {
            'url': 'https://info.minigg.cn/talents',
            'params': {
                'query': '天光'
            }
        }
        try:
            data = await get_async_http_client.get(**params)
        except RuntimeError:
            logger.warning('Use async HTTP Client failed, use sync HTTP Client instead.')
            data = get_http_client.get(**params)
        data = data.json()
        logger.info('Cost 材料天光 >>>' + str(data))
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, ','.join(data), None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('材料0')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, '不存在该角色或类型。', None)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_artifacts(app: App, get_artifacts_message):
    from nonebot.adapters.onebot.v11 import Message
    from .utils import make_sender, make_event
    from ..genshin_uid import get_artifacts as matcher
    artifacts_message_1, artifacts_message_2 = get_artifacts_message

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('圣遗物冒险家')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, artifacts_message_1, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('圣遗物海')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, artifacts_message_2, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('圣遗物0')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, '该圣遗物不存在。', None)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_food(app: App, get_food_message):
    from nonebot.adapters.onebot.v11 import Message
    from .utils import make_sender, make_event
    from ..genshin_uid import get_food as matcher
    food_message_1, food_message_2 = get_food_message

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('食物鸡')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, food_message_1, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('食物仙跳墙')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, food_message_2, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('食物0')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, '该食物不存在。', None)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_enemies(app: App, get_enemies_message):
    from nonebot.adapters.onebot.v11 import Message
    from .utils import make_sender, make_event
    from ..genshin_uid import get_enemies as matcher
    enemies_message_1, enemies_message_2 = get_enemies_message

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('原魔公子')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, enemies_message_1, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('原魔丘丘人')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, enemies_message_2, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('原魔0')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, '该原魔不存在。', None)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_character_adv(app: App, get_character_adv_message):
    from nonebot.adapters.onebot.v11 import Message
    from .utils import make_sender, make_event
    from ..genshin_uid import get_char_adv as matcher
    character_adv_message_1, character_adv_message_2 = get_character_adv_message

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('可莉用什么')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, character_adv_message_1, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('可莉能用啥')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, character_adv_message_1, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('可莉怎么养')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, character_adv_message_1, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('刻用什么')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, character_adv_message_2, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('刻怎么养')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, character_adv_message_2, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('刻能用啥')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, character_adv_message_2, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('零用什么')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_weapon_adv(app: App, get_weapon_adv_message):
    from nonebot.adapters.onebot.v11 import Message
    from .utils import make_sender, make_event
    from ..genshin_uid import get_weapon_adv as matcher

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('天空之刃给谁用')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "神里绫华、七七、琴、凯亚、班尼特、旅行者（雷）、久岐忍可能会用到【天空之刃】", None)

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('天空之刃能给谁')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "神里绫华、七七、琴、凯亚、班尼特、旅行者（雷）、久岐忍可能会用到【天空之刃】", None)

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('天空之刃要给谁')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "神里绫华、七七、琴、凯亚、班尼特、旅行者（雷）、久岐忍可能会用到【天空之刃】", None)

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('天空之刃谁能用')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "神里绫华、七七、琴、凯亚、班尼特、旅行者（雷）、久岐忍可能会用到【天空之刃】", None)

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('阿莫斯给谁用')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "温迪、达达利亚、甘雨、宵宫、埃洛伊、安柏可能会用到【阿莫斯之弓】", None)

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('阿莫斯能给谁')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "温迪、达达利亚、甘雨、宵宫、埃洛伊、安柏可能会用到【阿莫斯之弓】", None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('阿莫斯要给谁')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "温迪、达达利亚、甘雨、宵宫、埃洛伊、安柏可能会用到【阿莫斯之弓】", None)

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('阿莫斯谁能用')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "温迪、达达利亚、甘雨、宵宫、埃洛伊、安柏可能会用到【阿莫斯之弓】", None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('剑给谁用')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, get_weapon_adv_message, None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('啊给谁用')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "没有角色能使用【啊】", None)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_talent(app: App, get_talent_message):
    from nonebot.adapters.onebot.v11 import Message
    from .utils import make_sender, make_event
    from ..genshin_uid import get_talents as matcher

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('天赋1心海')
        event = make_event(message=msg, message_type="group", sub_type="normal", sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_api(
            "send_group_forward_msg", {
                "group_id": 10002,
                "messages": get_talent_message
            }, None
        )
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('天赋5达')
        event = make_event(message=msg, message_type="group", sub_type="normal", sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "【水形剑】\n处于**魔王武装·狂澜**的近战状态时，普通攻击与重击在造成暴击时，会为命中的敌人施加断流效果。", None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('天赋0')
        event = make_event(message=msg, message_type="group", sub_type="normal", sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "不存在该角色。", None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('天赋10可')
        event = make_event(message=msg, message_type="group", sub_type="normal", sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "不存在该天赋。", None)
        ctx.should_finished()


@pytest.mark.asyncio
async def test_audio(app: App):
    from nonebot.adapters.onebot.v11 import Message, MessageSegment
    from .utils import make_sender, make_event
    from ..genshin_uid import get_audio as matcher

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('语音列表')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        with open(Path(__file__).parent.parent / "genshin_uid" /
                  "mihoyo_libs" / "mihoyo_bbs" / "index" / "语音.png", "rb") as f:
            img = "base64://" + b64encode(f.read()).decode()
        ctx.should_call_send(event, MessageSegment.image(img), None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('语音可莉300001')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        with open(Path(__file__).parent / "assets" / "klee_300001.ogg", "rb") as f:
            audio = "base64://" + b64encode(f.read()).decode()
        ctx.should_call_send(event, MessageSegment.record(audio), None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('语音')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "请输入角色名。", None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('语音可莉114514')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "没有找到语音，请检查语音ID与角色名是否正确，如无误则可能未收录该语音", None)
        ctx.should_finished()

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot()
        msg = Message('语音可莉')
        event = make_event(message=msg, sender=make_sender(), to_me=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, "请输入语音ID。", None)
        ctx.should_finished()

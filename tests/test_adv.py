import pytest
from nonebug import App

MESSAGE = """「安柏」
-=-=-=-=-=-=-=-=-=-
推荐5★武器：阿莫斯之弓、天空之翼、终末嗟叹之诗
推荐4★武器：绝弦
推荐圣遗物搭配：
[昔日宗室之仪]四件套"""


@pytest.mark.asyncio
@pytest.mark.parametrize(argnames="alias", argvalues=["安柏用什么", "安柏怎么养"])
async def test_adv_char_chat(app: App, alias, load_adv: None):
    from utils import make_event
    from nonebot.adapters.onebot.v11 import Bot, Message

    from GenshinUID.genshinuid_adv import get_char_adv

    async with app.test_matcher(get_char_adv) as ctx:
        bot = ctx.create_bot(base=Bot)
        event = make_event(message=Message(alias))
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, MESSAGE, True)
        ctx.should_finished()

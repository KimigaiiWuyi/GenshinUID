from pathlib import Path

import pytest
from nonebug import App

# TODO: update guide tests
# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     argnames="alias",
#     argvalues=[
#         "钟离推荐",
#         "钟离攻略",
#         "岩王爷攻略",  # alias
#     ],
# )
# async def test_get_guide_pic(app: App, alias ):
#     from utils import make_event
#     from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment

#     from GenshinUID.genshinuid_guide import get_guide_pic

#     async with app.test_matcher(get_guide_pic) as ctx:
#         bot = ctx.create_bot(base=Bot)

#         event = make_event(message=Message(alias))
#         ctx.receive_event(bot, event)
#         ctx.should_call_send(
#             event,
#             MessageSegment.image(
#                 "https://file.microgg.cn/MiniGG/guide/钟离.jpg"
#             ),
#             True,
#         )
#         ctx.should_finished()


# @pytest.mark.asyncio
# async def test_get_guide_pic_traveler(app: App ):
#     from utils import make_event
#     from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment

#     from GenshinUID.genshinuid_guide import get_guide_pic

#     async with app.test_matcher(get_guide_pic) as ctx:
#         bot = ctx.create_bot(base=Bot)

#         event = make_event(message=Message("旅行者风推荐"))
#         ctx.receive_event(bot, event)
#         ctx.should_call_send(
#             event,
#             MessageSegment.image(
#                 "https://file.microgg.cn/MiniGG/guide/旅行者-风.jpg"
#             ),
#             True,
#         )
#         ctx.should_finished()


# @pytest.mark.asyncio
# async def test_get_guide_pic_failed(app: App ):
#     from utils import make_event
#     from nonebot.adapters.onebot.v11 import Bot, Message

#     from GenshinUID.genshinuid_guide import get_guide_pic

#     async with app.test_matcher(get_guide_pic) as ctx:
#         bot = ctx.create_bot(base=Bot)

#         event = make_event(message=Message("蔡徐坤攻略"))
#         ctx.receive_event(bot, event)
#         ctx.should_finished()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames="alias",
    argvalues=[
        "参考面板钟离",
        "参考面板岩王爷",  # alias
    ],
)
async def test_get_bluekun_pic(app: App, alias):
    from utils import make_event
    from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment

    from GenshinUID.genshinuid_guide import get_bluekun_pic

    with open(Path("../GenshinUID/genshinuid_guide/img/钟离.jpg"), "rb") as f:
        data = f.read()
    async with app.test_matcher(get_bluekun_pic) as ctx:
        bot = ctx.create_bot(base=Bot)

        event = make_event(message=Message(alias))
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, MessageSegment.image(data), True)
        ctx.should_finished()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames="alias",
    argvalues=[
        "岩",
        "冰",
    ],
)
async def test_get_bluekun_pic_element(app: App, alias):
    from utils import make_event
    from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment

    from GenshinUID.genshinuid_guide import get_bluekun_pic

    with open(
        Path(f"../GenshinUID/genshinuid_guide/img/{alias}.jpg"), "rb"
    ) as f:
        data = f.read()
    async with app.test_matcher(get_bluekun_pic) as ctx:
        bot = ctx.create_bot(base=Bot)

        event = make_event(message=Message(f"参考面板{alias}"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, MessageSegment.image(data), True)
        ctx.should_finished()

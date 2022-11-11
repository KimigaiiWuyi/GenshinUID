from pathlib import Path

import pytest
from nonebug import App


@pytest.mark.asyncio
@pytest.mark.parametrize(argnames="alias", argvalues=["版本规划", "原石预估"])
async def test_get_primogems_data(app: App, alias, load_etc: None):
    from utils import make_event
    from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment

    from GenshinUID.version import Genshin_version
    from GenshinUID.genshinuid_etcimg import get_primogems_data

    with open(
        Path(
            (
                "../GenshinUID/genshinuid_etcimg"
                f"/primogems_data/{Genshin_version[:3]}.png"
            )
        ),
        "rb",
    ) as f:
        data = f.read()

    async with app.test_matcher(get_primogems_data) as ctx:
        bot = ctx.create_bot(base=Bot)
        event = make_event(message=Message(alias))
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            MessageSegment.image(data),
            True,
        )
        ctx.should_finished()


@pytest.mark.asyncio
async def test_primogems_version(app: App, load_etc: None):
    from utils import make_event
    from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment

    from GenshinUID.version import Genshin_version
    from GenshinUID.genshinuid_etcimg import get_primogems_data

    with open(
        Path(
            f"../GenshinUID/genshinuid_etcimg/primogems_data/{Genshin_version[:3]}.png"
        ),
        "rb",
    ) as f:
        data = f.read()

    async with app.test_matcher(get_primogems_data) as ctx:
        bot = ctx.create_bot(base=Bot)
        event = make_event(message=Message(f"版本规划{Genshin_version[:3]}"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            MessageSegment.image(data),
            True,
        )
        ctx.should_finished()


@pytest.mark.asyncio
async def test_primogems_failed(app: App, load_etc: None):
    from utils import make_event
    from nonebot.adapters.onebot.v11 import Bot, Message

    from GenshinUID.genshinuid_etcimg import get_primogems_data

    # primogems_img.exists() is False
    async with app.test_matcher(get_primogems_data) as ctx:
        bot = ctx.create_bot(base=Bot)

        event = make_event(message=Message("版本规划1.0"))
        ctx.receive_event(bot, event)
        ctx.should_finished()

    # str(args) in version is False
    async with app.test_matcher(get_primogems_data) as ctx:
        event = make_event(message=Message("版本规划abc"))
        ctx.receive_event(bot, event)
        ctx.should_finished()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames="alias",
    argvalues=[
        "伤害乘区",
        "血量表",
        "抗性表",
        "血量排行",
        "伤害乘区",
    ],
)
async def test_get_img_data(app: App, alias, load_etc: None):
    from utils import make_event
    from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment

    from GenshinUID.genshinuid_etcimg import get_img_data

    with open(
        Path(f"../GenshinUID/genshinuid_etcimg/img_data/{alias}.jpg"),
        "rb",
    ) as f:
        data = f.read()

    async with app.test_matcher(get_img_data) as ctx:
        bot = ctx.create_bot(base=Bot)

        event = make_event(message=Message(f"查询{alias}"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, MessageSegment.image(data), True)
        ctx.should_finished()

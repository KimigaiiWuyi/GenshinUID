import random
import string

from httpx import AsyncClient

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

sv_gs_code = SV("原神获得兑换码")

URL = "https://mihoyoapi.genshinnet.com:4443/getCode"


@sv_gs_code.on_fullmatch(
    ("给我一个兑换码", "给我兑换码"),
    to_ai="""获取一个可用的原神兑换码

    当用户说"给我一个兑换码"、"给我兑换码"时调用。
    从兑换码池中获取一个可用兑换码，每个兑换码只能兑换一次。

    Args:
        text: 无需参数，留空即可
    """,
)
async def get_code_func(bot: Bot, ev: Event):
    async with AsyncClient() as client:
        try:
            characters = string.ascii_letters + string.digits
            cd = "".join(random.choices(characters, k=32))
            res = await client.get(
                URL,
                headers={"virtualid": cd},
            )
            data = res.json()
            if data["code"] == 0:
                im = f"✅[原神兑换码] 请尽快兑换哦!\n✨{data['msg']}"
                im += "\n🚨 该兑换码每人只能兑换一次, 请勿重复刷取!"
                await bot.send(im)
        except Exception:
            logger.error(t("log.genshinuid.msg_d735c9"))
            await bot.send("👽️获取兑换码失败!请勿重新尝试!")

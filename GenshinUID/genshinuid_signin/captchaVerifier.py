import asyncio
from typing import Any, Dict

from httpx import AsyncClient
from nonebot.log import logger


async def get(url: str) -> Dict[str, Any]:
    async with AsyncClient() as client:
        return (await client.get(url)).json()


async def captchaVerifier():
    captcha_cnt = 0
    while captcha_cnt < 5:
        captcha_cnt += 1
        try:
            logger.info(f'测试新版自动过码中，当前尝试第{captcha_cnt}次。')
            await asyncio.sleep(1)
            uuid = (await get(url="https://pcrd.tencentbot.top/geetest"))[
                "uuid"
            ]
            # logger.info(f'uuid={uuid}')
            ccnt = 0
            while ccnt < 3:
                ccnt += 1
                await asyncio.sleep(5)
                res = await get(
                    url=f"https://pcrd.tencentbot.top/check/{uuid}"
                )
                if "queue_num" in res:
                    nu = res["queue_num"]
                    logger.info(f"queue_num={nu}")
                    tim = min(int(nu), 3) * 5
                    logger.info(f"sleep={tim}")
                    await asyncio.sleep(tim)
                else:
                    info = res["info"]
                    if info in ["fail", "url invalid"]:
                        break
                    elif info == "in running":
                        await asyncio.sleep(5)
                    else:
                        logger.info(f'info={info}')
                        return info
        except Exception:
            logger.exception("Raised an exception while verifying the captcha")

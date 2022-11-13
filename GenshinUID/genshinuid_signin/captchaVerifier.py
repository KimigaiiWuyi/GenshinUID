import asyncio
from json import loads

from .aiorequests import get


async def captchaVerifier():
    captcha_cnt = 0
    while captcha_cnt < 5:
        captcha_cnt += 1
        try:
            print(f'测试新版自动过码中，当前尝试第{captcha_cnt}次。')

            await asyncio.sleep(1)
            uuid = loads(
                await (
                    await get(url="https://pcrd.tencentbot.top/geetest")
                ).content
            )["uuid"]
            # print(f'uuid={uuid}')

            ccnt = 0
            while ccnt < 3:
                ccnt += 1
                await asyncio.sleep(5)
                res = await (
                    await get(url=f"https://pcrd.tencentbot.top/check/{uuid}")
                ).content
                res = loads(res)
                if "queue_num" in res:
                    nu = res["queue_num"]
                    print(f"queue_num={nu}")
                    tim = min(int(nu), 3) * 5
                    print(f"sleep={tim}")
                    await asyncio.sleep(tim)
                else:
                    info = res["info"]
                    if info in ["fail", "url invalid"]:
                        break
                    elif info == "in running":
                        await asyncio.sleep(5)
                    else:
                        print(f'info={info}')
                        return info
        except:
            pass

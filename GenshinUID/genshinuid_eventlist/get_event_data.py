import datetime

from httpx import AsyncClient


async def get_genshin_events(mode: str = 'List') -> dict:
    """
    :说明:
      接受mode: str = 'List'或'Calendar'或'Content'。
      'List'模式为米游社列表, 包含最基本的信息。
      'Content'模式为游戏内活动公告, 包含html页面, 时间信息来源。
      'Calendar'模式为米游社日历, 一般不用。
    :参数:
      * mode (str): 'List'或'Calendar'或'Content'。
    :返回:
      * data (dict): json.loads。
    """
    if mode == 'Calendar':
        now_time = datetime.datetime.now().strftime('%Y-%m-%d')
        base_url = (
            'https://api-takumi.mihoyo.com'
            '/event/bbs_activity_calendar/getActList'
        )
        params = {
            'time': now_time,
            'game_biz': 'ys_cn',
            'page': 1,
            'tag_id': 0,
        }
    else:
        base_url = (
            'https://hk4e-api.mihoyo.com'
            f'/common/hk4e_cn/announcement/api/getAnn{mode}'
        )
        params = {
            'game': 'hk4e',
            'game_biz': 'hk4e_cn',
            'lang': 'zh-cn',
            'bundle_id': 'hk4e_cn',
            'platform': 'pc',
            'region': 'cn_gf01',
            'level': 55,
            'uid': 100000000,
        }

    async with AsyncClient() as client:
        req = await client.get(
            url=base_url,
            headers={
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/95.0.4638.69 Safari/537.36'
                )
            },
            params=params,
        )
    return req.json()

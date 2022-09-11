from .get_mhy_data import get_mihoyo_bbs_info


async def convert_mysid(mysid: str) -> str:
    """
    :说明:
      将MYSID转换为UID
    :参数:
      * mysid (str): MYSID。
    :返回:
      * uid (str): UID。
    """
    raw_data = await get_mihoyo_bbs_info(mysid)
    raw_data = raw_data['data']['list']
    for game in raw_data:
        if game['game_id'] == '2':
            return game['uid']
    else:
        return '获取米游社数据失败~!'

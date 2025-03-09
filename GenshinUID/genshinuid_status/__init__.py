from gsuid_core.status.plugin_status import register_status
from gsuid_core.utils.database.models import GsBind, GsUser

from ..utils.image.image_tools import get_ICON


async def get_user_num():
    datas = await GsUser.get_all_stoken()
    return len(datas)


async def get_add_num():
    datas = await GsBind.get_all_data()
    all_uid = []
    for data in datas:
        if data.uid:
            all_uid.extend(data.uid.split('_'))
    return len(set(all_uid))


async def get_sign_num():
    datas = await GsUser.get_sign_user_list()
    return len(datas) if datas else 0


register_status(
    get_ICON(),
    'GenshinUID',
    {
        '绑定UID': get_add_num,
        '绑定账户': get_user_num,
        '开启签到': get_sign_num,
    },
)

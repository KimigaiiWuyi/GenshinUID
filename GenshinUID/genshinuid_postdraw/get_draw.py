from typing import List, Union

from gsuid_core.segment import MessageSegment
from gsuid_core.utils.error_reply import get_error_img
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import get_pic

from ..utils.mys_api import mys_api


async def post_my_draw(uid: str) -> Union[List, str, bytes]:
    bs_index = await mys_api.get_bs_index(uid)

    # 错误检查
    if isinstance(bs_index, int):
        return await get_error_img(bs_index)

    im_list = []

    for role in bs_index['role']:
        if not role['is_partake']:
            data = await mys_api.post_draw(uid, role['role_id'])
            if isinstance(data, int):
                im_list.append(await get_error_img(data))
            else:
                retcode = data['retcode']
                if retcode != 0:
                    message = (
                        data['message']
                        if 'message' in data
                        else f'错误码{retcode}'
                    )
                    im_list.append(message)
                else:
                    image = await get_pic(role['take_picture'])
                    image = await convert_img(image)
                    im_list.append(
                        MessageSegment.text(
                            f'[留影叙佳期] UID{uid}成功获取{role["name"]}的画片!'
                        )
                    )
                    im_list.append(MessageSegment.image(image))
    if im_list == []:
        im_list.append(f'[留影叙佳期]UID{uid}没有需要获取的画片了~')
    return im_list

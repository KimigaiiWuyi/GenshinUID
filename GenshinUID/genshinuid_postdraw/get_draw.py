from typing import Union

from gsuid_core.utils.error_reply import get_error_img

from ..utils.mys_api import mys_api


async def post_my_draw(uid: str) -> Union[str, bytes]:
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
                    im_list.append(f'[留影叙佳期] UID{uid}成功获取{role["name"]}的画片!')
    if im_list == []:
        im_list.append(f'[留影叙佳期]UID{uid}没有需要获取的画片了~')
    return '\n'.join(im_list)

from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.utils.cache import gs_cache
from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.image.mys.bbs import get_post_img

from ..utils.mys_api import mys_api

CID = "1386819"
colloctions = []


@gs_cache(14200)
async def get_material_way_post(name: str):
    global colloctions
    if not colloctions:
        colloctions = await mys_api.get_bbs_collection(CID)

    if isinstance(colloctions, int):
        error = get_error(colloctions)
        colloctions = []
        return error

    logger.info(t("log.genshinuid.bbs_guide_name_2d1843", name=name))

    for c in colloctions:
        post = c["post"]
        if name in post["subject"]:
            post_id = post["post_id"]
            break
    else:
        return "未找到该攻略, 等待补充, 或请检查输入材料名是否正确。"

    return await get_post_img(post_id)

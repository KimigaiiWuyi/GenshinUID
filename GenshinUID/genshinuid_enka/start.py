import re
import json
import asyncio
from copy import deepcopy

import aiofiles

from gsuid_core.i18n import t
from gsuid_core.logger import logger

from .to_data import ARTIFACT_DATA, input_artifacts_data
from ..utils.message import PREFIX
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH

pattern = r"^[\u4e00-\u9fa5]"


async def refresh_player_list(uid: str, is_force: bool = False) -> str:
    player = PLAYER_PATH / uid
    if not player.exists():
        return f"该UID{uid}对应面板数据不存在, 请先进行 [{PREFIX}刷新面板]!"

    path = player / "artifacts.json"
    all_artifacts = deepcopy(ARTIFACT_DATA)
    if not path.exists():
        logger.info(t("log.genshinuid.uid_uid_1c3c20", uid=uid))
    else:
        async with aiofiles.open(path, "r", encoding="UTF-8") as file:
            all_artifacts = json.loads(await file.read())

    all_list = [x for v in all_artifacts["data"].values() for x in v]

    if len(all_list) >= 1 and "cv_score" not in all_list[0]:
        path.unlink()
    elif not is_force and len(all_list) >= 1:
        return "无需刷新圣遗物列表"
        # return '删除旧数据中...请重新刷新!'

    logger.info(t("log.genshinuid.uid_uid_463d41", uid=uid))
    num = 0
    for char in player.iterdir():
        match = re.match(pattern, char.name)
        if match:
            async with aiofiles.open(char, "r", encoding="UTF-8") as file:
                char_data = json.loads(await file.read())

            for artifact in char_data["equipList"]:
                all_artifacts = await input_artifacts_data(
                    artifact,
                    all_artifacts,
                    char_data["avatarId"],
                    char_data,
                )
                num += 1

    await asyncio.sleep(0.15)
    # 保存原始数据
    async with aiofiles.open(path, "w", encoding="UTF-8") as file:
        await file.write(json.dumps(all_artifacts, indent=4, ensure_ascii=False))

    return f"刷新成功, 本次刷新 {num} 个圣遗物!"


async def check_artifacts_list():
    logger.info(t("log.genshinuid.msg_c03676"))
    for player in PLAYER_PATH.iterdir():
        await refresh_player_list(player.name)
    logger.info(t("log.genshinuid.msg_44a88a"))

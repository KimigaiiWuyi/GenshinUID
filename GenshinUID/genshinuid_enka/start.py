import re
import json
import asyncio
from copy import deepcopy

import aiofiles
from gsuid_core.logger import logger

from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from .to_data import ARTIFACT_DATA, input_artifacts_data

pattern = r'^[\u4e00-\u9fa5]'


async def refresh_player_list(uid: str) -> str:
    player = PLAYER_PATH / uid
    path = player / 'artifacts.json'
    all_artifacts = deepcopy(ARTIFACT_DATA)
    if not path.exists():
        logger.info(f'UID{uid} 不存在圣遗物列表,开始生成中...')
    else:
        async with aiofiles.open(path, 'r', encoding='UTF-8') as file:
            all_artifacts = json.loads(await file.read())

    all_list = [x for v in all_artifacts['data'].values() for x in v]

    if len(all_list) >= 1 and 'cv_score' not in all_list[0]:
        path.unlink()
    elif len(all_list) >= 1:
        return '无需刷新圣遗物列表'
        # return '删除旧数据中...请重新刷新!'

    logger.info(f'开始刷新UID{uid}圣遗物列表...')
    num = 0
    for char in player.iterdir():
        match = re.match(pattern, char.name)
        if match:
            async with aiofiles.open(char, 'r', encoding='UTF-8') as file:
                char_data = json.loads(await file.read())

            for artifact in char_data['equipList']:
                all_artifacts = await input_artifacts_data(
                    artifact,
                    all_artifacts,
                    char_data['avatarId'],
                    char_data,
                )
                num += 1

    await asyncio.sleep(0.15)
    # 保存原始数据
    async with aiofiles.open(path, 'w', encoding='UTF-8') as file:
        await file.write(
            json.dumps(all_artifacts, indent=4, ensure_ascii=False)
        )

    return f'刷新成功, 本次刷新 {num} 个圣遗物!'


async def check_artifacts_list():
    logger.info('开始检查是否创建圣遗物列表...')
    for player in PLAYER_PATH.iterdir():
        await refresh_player_list(player.name)
    logger.info('圣遗物列表检查完成!')

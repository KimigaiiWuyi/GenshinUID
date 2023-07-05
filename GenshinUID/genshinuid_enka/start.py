import re
import json
from copy import deepcopy

import aiofiles
from gsuid_core.logger import logger

from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from .to_data import ARTIFACT_DATA, input_artifacts_data


async def check_artifacts_list():
    pattern = r'^[\u4e00-\u9fa5]'
    logger.info('开始检查是否创建圣遗物列表...')
    for player in PLAYER_PATH.iterdir():
        path = player / 'artifacts.json'
        all_artifacts = deepcopy(ARTIFACT_DATA)
        if not path.exists():
            logger.info(f'UID{player.name} 不存在圣遗物列表,开始生成中...')
            for char in player.iterdir():
                match = re.match(pattern, char.name)
                if match:
                    async with aiofiles.open(
                        char, 'r', encoding='UTF-8'
                    ) as file:
                        char_data = json.loads(await file.read())

                    for artifact in char_data['equipList']:
                        all_artifacts = await input_artifacts_data(
                            artifact, all_artifacts, char_data['avatarId']
                        )
        # 保存原始数据
        async with aiofiles.open(path, 'w', encoding='UTF-8') as file:
            await file.write(
                json.dumps(all_artifacts, indent=4, ensure_ascii=False)
            )
    logger.info('圣遗物列表检查完成!')

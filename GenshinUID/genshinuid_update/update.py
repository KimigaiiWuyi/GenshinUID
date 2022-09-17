from pathlib import Path
from typing import Union

import git
from nonebot.log import logger
from git.exc import GitCommandError


async def update_genshinuid(
    level: int = 0, repo_path: Union[str, Path, None] = None
) -> str:
    if repo_path is None:
        repo_path = Path(__file__).parents[2]
    repo = git.Repo(repo_path)  # type: ignore
    o = repo.remotes.origin

    # 清空暂存
    if level >= 2:
        logger.warning('[gs更新] 正在执行 git clean --xdf')
        repo.git.clean('-xdf')
    # 还原上次更改
    if level >= 1:
        logger.warning('[gs更新] 正在执行 git reset --hard')
        repo.git.reset('--hard')

    try:
        pull_log = o.pull()
        logger.info(f'[gs更新] {pull_log}')
        im = '更新成功!'
    except GitCommandError as e:
        im = f'更新失败!错误信息为{e}!\n >> 可以尝试使用[gs强制更新]或者[gs强行强制更新](危险)!'

    commits = list(repo.iter_commits(max_count=10))
    log_list = []
    for commit in commits:
        if isinstance(commit.message, str):
            if '✨' in commit.message or '🐛' in commit.message:
                log_list.append(commit.message.replace('\n', ''))
    log = '\n'.join(log_list)
    logger.info(f'[gs更新]\n{log}')
    return f'{im}\n >> 最近有效更新为:\n{log}'

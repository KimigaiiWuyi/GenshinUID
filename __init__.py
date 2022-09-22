import os
import shutil
from typing import List
from pathlib import Path

from nonebot.log import logger
from nonebot import load_plugins

dir_ = Path(__file__).parent


def copy_and_delete_files():
    if "player" in os.listdir(dir_) or "resource" in os.listdir(dir_):
        logger.info("检测到未迁移的文件夹，执行迁移")
    is_first = True
    for path in dir_.iterdir():
        if path.name.startswith("genshinuid_") or path.name == "utils":
            if is_first:
                logger.info("检测到残留文件夹，执行删除")
                is_first = False
            try:
                shutil.rmtree(path)
                logger.info(f"删除文件夹：{path}")
            except OSError as e:
                logger.warning(f"无法删除文件夹：{e}")
        elif path.name in {"resource", "player"}:
            dst = Path().joinpath(
                (
                    "data/GenshinUID/"
                    f"{'players' if path.name == 'player' else path.name}"
                )
            )
            try:
                shutil.copytree(
                    path,
                    dst,
                    dirs_exist_ok=True,
                )
                logger.success(f"复制文件夹 {path} -> {dst} 成功")
            except shutil.Error as e:
                failed_src: List[Path] = []
                exc: str
                src: str
                for tup in e.args[0]:
                    src, dst, exc = tup
                    failed_src.append(Path(src).absolute())
                    logger.warning(f"复制文件夹 {src} -> {dst} 失败：{exc}")
                now_src = {i.absolute() for i in path.iterdir()}
                successful_src = filter(lambda x: x not in now_src, failed_src)
                for i in successful_src:
                    try:
                        shutil.rmtree(i)
                    except OSError as e:
                        logger.warning(f"删除文件夹 {i} 失败：{e.strerror}")
            else:
                try:
                    shutil.rmtree(path)
                    logger.success(f"删除文件夹 {path} 成功")
                except OSError as e:
                    logger.warning(f"删除文件夹 {path} 失败：{e.strerror}")


copy_and_delete_files()
load_plugins(str(dir_ / "GenshinUID"))

import os
import base64
from pathlib import Path

import aiohttp


async def download_image(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()


def get_bytes_from_base64_str(data_str: str) -> bytes:
    prefix = "base64://"
    if data_str.startswith(prefix):
        pure_b64_str = data_str[len(prefix) :]
    else:
        pure_b64_str = data_str

    mp3_bytes = base64.b64decode(pure_b64_str)

    return mp3_bytes


def to_json(msg: list, name: str, uin: str):
    return {
        "type": "node",
        "data": {"name": name, "uin": uin, "content": msg},
    }


def store_file(path: Path, file: str):
    file_content = base64.b64decode(file)
    with open(path, "wb") as f:
        f.write(file_content)


def del_file(path: Path):
    if path.exists():
        os.remove(path)

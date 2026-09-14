import os
import base64
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

import aiohttp


def file_uri_to_path(uri: str) -> str | None:
    """file:// URI → 本地路径; 非 file 方案返回 None."""
    parsed = urlparse(uri)
    if parsed.scheme != "file":
        return None
    netloc = unquote(parsed.netloc or "")
    path = unquote(parsed.path or "")
    if os.name == "nt":
        if netloc and netloc.lower() not in {"", "localhost", "127.0.0.1"}:
            if len(netloc) == 2 and netloc[1] == ":" and netloc[0].isalpha():
                converted = url2pathname(f"/{netloc}{path}")
            else:
                converted = url2pathname(f"//{netloc}{path}")
        else:
            converted = url2pathname(path)
            if len(converted) >= 4 and converted[0] in {"/", "\\"} and converted[2] == ":" and converted[1].isalpha():
                converted = converted[1:]
        return converted or None
    if netloc and netloc.lower() not in {"", "localhost", "127.0.0.1"}:
        return None
    return path or None


def existing_file_uri_path(uri: str) -> Path | None:
    """file:// 在本机存在时返回 Path, 否则 None(交给协议端原样读)."""
    raw = file_uri_to_path(uri)
    if raw is None:
        return None
    path = Path(raw)
    return path if path.is_file() else None


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

import io
import json
from typing import Any, Dict, Union, Literal, Optional, cast
from pathlib import Path

from PIL import Image
from httpx import AsyncClient

from gsuid_core.i18n import t
from gsuid_core.logger import logger

from .api import HAKUSH_U_API, HAKUSH_ROLECOMBAT_API, HAKUSH_ROLECOMBATS_API
from .models import RoleCombatData, RoleCombatEvent


class _HakushAPI:
    ssl_verify = True
    _HEADER = {"User-Agent": "GenshinUID & GsCore"}

    async def get_hakush_rolecombats(
        self,
    ) -> Union[Dict[str, RoleCombatEvent], int]:
        data = await self._hakush_request(HAKUSH_ROLECOMBATS_API)
        if isinstance(data, Dict):
            return cast(Dict[str, RoleCombatEvent], data)
        else:
            return -500

    async def get_hakush_rolecombat(self, id: str) -> Union[RoleCombatData, int]:
        data = await self._hakush_request(HAKUSH_ROLECOMBAT_API.format(id))
        if isinstance(data, Dict):
            return cast(RoleCombatData, data)
        else:
            return -500

    async def get_hakush_ui(self, ui_name: str, save_path: Path) -> Image.Image:
        png_file_path = save_path / f"{ui_name}.png"
        if png_file_path.exists():
            return Image.open(png_file_path)
        url = f"{HAKUSH_U_API}/{ui_name}.webp"
        data = await self._hakush_request(url)
        if isinstance(data, bytes):
            webp_stream = io.BytesIO(data)
            with Image.open(webp_stream) as img:
                img.save(str(png_file_path), "PNG")
                return img
        else:
            return Image.new("RGBA", (256, 256))

    async def _hakush_request(
        self,
        url: str,
        method: Literal["GET", "POST"] = "GET",
        header: Dict[str, Any] = _HEADER,
        params: Optional[Dict[str, Any]] = None,
        _json: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict, int, bytes]:
        async with AsyncClient(timeout=None) as client:
            logger.debug(t("log.genshinuid.hakush_url_9a0f99", url=url))
            resp = await client.request(
                method,
                url,
                headers=header,
                params=params,
                json=_json,
            )
            try:
                raw_data = await resp.json()
            except:  # noqa
                try:
                    raw_data = json.loads(resp.text)
                except:  # noqa
                    try:
                        raw_data = resp.content
                    except:  # noqa
                        raw_data = {
                            "retcode": -999,
                            "data": resp.text,
                        }
            if not isinstance(raw_data, bytes):
                logger.debug(raw_data)
            return raw_data


hakush_api = _HakushAPI()

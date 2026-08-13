from pathlib import Path

from .config import gs_config

_CORE_PATH = Path().cwd().parent / "gsuid_core"


def _core_path() -> Path:
    configured = gs_config().gsuid_core_path
    return Path(configured) if configured else _CORE_PATH


CORE_PATH = _CORE_PATH
GSUID_PATH = CORE_PATH / "gsuid_core" / "plugins" / "GenshinUID"

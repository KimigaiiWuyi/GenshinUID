from __future__ import annotations

import sys
from pathlib import Path

_CORE_ROOT = Path(__file__).resolve().parents[4]
_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_ROLEINFO = _PLUGIN_ROOT / "GenshinUID" / "genshinuid_roleinfo"
if str(_CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(_CORE_ROOT))
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))
if str(_ROLEINFO) not in sys.path:
    sys.path.insert(0, str(_ROLEINFO))

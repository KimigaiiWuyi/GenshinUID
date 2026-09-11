from __future__ import annotations

from GenshinUID.utils.resource.RESOURCE_PATH import (
    HG_ICON_PATH,
    MZ_ICON_PATH,
    ELEMENT_ICON_PATH,
)


def test_mz_hg_sit_next_to_element() -> None:
    assert ELEMENT_ICON_PATH.name == "element"
    assert MZ_ICON_PATH.parent == ELEMENT_ICON_PATH.parent
    assert HG_ICON_PATH.parent == ELEMENT_ICON_PATH.parent
    assert (MZ_ICON_PATH / "0.png").exists()
    assert (MZ_ICON_PATH / "6.png").exists()
    assert (HG_ICON_PATH / "0.png").exists()
    assert (HG_ICON_PATH / "10.png").exists()

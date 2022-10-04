from typing import TYPE_CHECKING, Optional

import pytest

if TYPE_CHECKING:
    from nonebot.plugin import Plugin


@pytest.fixture
def load_metadata(nonebug_init: None) -> Optional["Plugin"]:
    import nonebot

    return nonebot.load_plugin("GenshinUID.genshinuid_meta")


@pytest.fixture
def load_adv(nonebug_init: None) -> Optional["Plugin"]:
    import nonebot

    return nonebot.load_plugin("GenshinUID.genshinuid_adv")


@pytest.fixture
def load_etc(nonebug_init: None) -> Optional["Plugin"]:
    import nonebot

    return nonebot.load_plugin("GenshinUID.genshinuid_etcimg")


@pytest.fixture
def load_guide(nonebug_init: None) -> Optional["Plugin"]:
    import nonebot

    return nonebot.load_plugin("GenshinUID.genshinuid_guide")

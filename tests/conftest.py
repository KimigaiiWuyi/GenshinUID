import pytest
import nonebot
from nonebug import NONEBOT_INIT_KWARGS
from nonebot.adapters.onebot.v11 import Adapter

PLUGINS = ["meta", "adv", "etcimg", "guide"]


@pytest.fixture(scope="session", autouse=True)
def load_bot():
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)

    nonebot.load_all_plugins(
        [f"GenshinUID.genshinuid_{name}" for name in PLUGINS], []
    )


def pytest_configure(config: pytest.Config):
    config.stash[NONEBOT_INIT_KWARGS] = {
        "genshinuid_disabled_plugins": {"xkdata", "abyss", "adv"},
        "genshinuid_priority": 5,
    }

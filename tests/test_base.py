import pytest
from nonebug import App


@pytest.mark.parametrize(
    "nonebug_init",
    [
        pytest.param(
            {
                "genshinuid_disabled_plugins": {"xkdata", "abyss", "adv"},
                "genshinuid_priority": 5,
            },
            id="config",
        )
    ],
    indirect=True,
)
def test_config(app: App):
    from GenshinUID import config

    assert config.config.disabled_plugins == {"xkdata", "abyss", "adv"}
    assert config.priority == 5


def test_default_config(app: App):
    from GenshinUID import config

    assert len(config.config.disabled_plugins) == 0
    assert config.priority == 2

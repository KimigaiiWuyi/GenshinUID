from nonebug import App


def test_config(app: App):
    from GenshinUID import config

    assert config.config.disabled_plugins == {"xkdata", "abyss", "adv"}
    assert config.priority == 5

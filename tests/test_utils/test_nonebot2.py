from nonebug import App


def test_get_superusers(app: App):
    from GenshinUID.utils.nonebot2.utils import get_superusers

    superusers = get_superusers()
    assert len(superusers) == 2
    assert set(superusers) == {10000, 10001}

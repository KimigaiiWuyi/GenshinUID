import pytest
from nonebug import App


@pytest.mark.parametrize(
    "nonebug_init",
    [
        pytest.param(
            {
                "superusers": {
                    "onebot:10000",
                    "10001",
                    "other:10002",
                    "abcdef",
                },
            },
            id="nb_config",
        )
    ],
    indirect=True,
)
def test_get_superusers(app: App):
    from GenshinUID.utils.nonebot2.utils import get_superusers

    superusers = get_superusers()
    assert len(superusers) == 2
    assert set(superusers) == {10000, 10001}

import pytest
from nonebug import App


@pytest.mark.asyncio
async def test_metadata(app: App, load_metadata: None):
    from GenshinUID.genshinuid_meta import __plugin_meta__

    assert __plugin_meta__.name == 'GenshinUID'
    assert (
        __plugin_meta__.description == '基于NoneBot2的原神Uid查询/原神Wiki/米游社签到/树脂提醒插件'
    )


@pytest.mark.asyncio
async def test_register_menu(app: App, load_metadata: None):
    from GenshinUID.genshinuid_meta import sub_menus, register_menu

    @register_menu(
        'test',
        'trigger',
        'test register_menu',
        trigger_method='114514',
        detail_des='test register_menu',
    )
    async def _example() -> None:
        pass

    assert len(sub_menus) == 1
    menu = sub_menus[0]
    assert menu['func'] == 'test'
    assert menu['trigger_condition'] == 'trigger'
    assert menu['trigger_method'] == '114514'
    assert menu['brief_des'] == 'test register_menu'
    assert menu['detail_des'] == 'test register_menu'

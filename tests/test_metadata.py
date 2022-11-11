import pytest
from nonebug import App


@pytest.mark.asyncio
async def test_metadata(app: App, load_metadata: None):
    from GenshinUID.genshinuid_meta import __plugin_meta__

    assert __plugin_meta__.name == 'GenshinUID'
    assert (
        __plugin_meta__.description == '基于NoneBot2的原神Uid查询/原神Wiki/米游社签到/树脂提醒插件'
    )
    assert __plugin_meta__.usage == (
        '发送 <ft color=(238,120,0)>gs帮助</ft> 可以获取帮助列表，也可以参考下面的表格\n'
        '可以使用 <ft color=(238,120,0)>菜单 gsuid </ft><ft color=(0,148,200)>[序号]</ft> '
        '指令获取某功能详细介绍\n'
        ' \n'
        '菜单描述中的指令：\n'
        '<ft color=(0,148,200)>[中括号及其中的内容]</ft>，'
        '或<ft color=(0,148,200)>用“xx”代表的内容</ft> '
        '为<ft color=(238,120,0)>必选</ft>的参数，'
        '请将它们替换为适当的值；\n'
        '<ft color=(125,125,125)>(小括号及其中的内容)</ft> '
        '为<ft color=(238,120,0)>可选</ft>参数，'
        '可以省略；\n'
        '<ft color=(238,120,0)>{大括号及其中的内容}</ft> '
        '为<ft color=(238,120,0)>选择其一</ft>参数，'
        '请将它们替换为用 <ft color=(238,120,0)>|</ft> 分割后括号中内容的其中一个值'
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

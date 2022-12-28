from typing import Optional

from nonebot.plugin import PluginMetadata

sub_menus = []
__plugin_meta__ = PluginMetadata(
    name='GenshinUID',
    description='基于NoneBot2的原神Uid查询/原神Wiki/米游社签到/树脂提醒插件',
    usage=(
        '发送 <ft color=(238,120,0)>gs帮助</ft> 可以获取帮助列表，也可以参考下面的表格\n'
        '可以使用 <ft color=(238,120,0)>菜单 gsuid </ft>'
        '<ft color=(0,148,200)>[序号]</ft> '
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
    ),
    extra={'menu_data': sub_menus, 'menu_template': 'default'},
)


def register_menu_func(
    func: str,
    trigger_condition: str,
    brief_des: str,
    trigger_method: str = '指令',
    detail_des: Optional[str] = None,
):
    sub_menus.append(
        {
            'func': func,
            'trigger_method': trigger_method,
            'trigger_condition': trigger_condition,
            'brief_des': brief_des,
            'detail_des': detail_des or brief_des,
        }
    )


def register_menu(*args, **kwargs):
    def decorator(f):
        register_menu_func(*args, **kwargs)
        return f

    return decorator

from fastapi import Request
import fastapi_amis_admin  # 不能删
from nonebot.typing import overrides
from fastapi_user_auth import admin as user_auth_admin
from fastapi_amis_admin.admin import admin as amis_admin
from fastapi_amis_admin.amis.components import App, Tpl, Grid, Html, Page

login_html = f'''<p align="center">
  <a href="https://github.com/KimigaiiWuyi/GenshinUID/"><img src="https://s2.loli.net/2022/01/31/kwCIl3cF1Z2GxnR.png" width="256" height="256" alt="GenshinUID"></a>
</p>
<h1 align = "center">GenshinUID 3.1 WebConsole</h1>
<h4 align = "center">✨基于<a href="https://github.com/Ice-Cirno/HoshinoBot" target="_blank">HoshinoBot</a>/<a href="https://github.com/nonebot/nonebot2" target="_blank">NoneBot2</a>/<a href="https://bot.q.qq.com/wiki/#" target="_blank">QQ官方频道Bot</a>的原神多功能插件✨</h4>
<div align = "center">
        <a href="https://github.com/KimigaiiWuyi/GenshinUID/wiki" target="_blank">安装文档</a> &nbsp; · &nbsp;
        <a href="https://github.com/KimigaiiWuyi/GenshinUID/wiki/File5-%E3%80%8C%E6%8C%87%E4%BB%A4%E5%88%97%E8%A1%A8%E3%80%8D" target="_blank">指令列表</a> &nbsp; · &nbsp;
        <a href="https://github.com/KimigaiiWuyi/GenshinUID/issues/226">常见问题</a>
</div>'''

footer_html = '''<p align="right">
<div class="p-2 text-center bg-light">Copyright © 2021 - 2022
<a href="https://github.com/KimigaiiWuyi/GenshinUID" target="_blank" class="link-secondary">GenshinUID 3.1</a> X 
<a target="_blank" href="https://github.com/amisadmin/fastapi_amis_admin/" class="link-secondary" rel="noopener">fastapi_amis_admin 0.2.1</a>
</div> 
</p>'''


@overrides(user_auth_admin)
def attach_page_head(page: Page) -> Page:
    page.body = [
        Html(html=login_html),
        Grid(
            columns=[
                {"body": [page.body], "lg": 2, "md": 4, "valign": "middle"}
            ],
            align='center',
            valign='middle',
        ),
    ]
    return page


@overrides(amis_admin.AdminApp)
async def _get_page_as_app(self, request: Request) -> App:
    app = App()
    app.brandName = self.site.settings.site_title
    app.header = Tpl(
        className='w-full',
        tpl='<div class="flex justify-between"><div></div>'
        f'<div><a href="https://github.com/KimigaiiWuyi/GenshinUID" target="_blank" '
        'title="Copyright"><i class="fa fa-github fa-2x"></i></a></div></div>',
    )  # type: ignore
    app.footer = footer_html
    children = await self.get_page_schema_children(request)
    app.pages = [{'children': children}] if children else []  # type: ignore
    return app


amis_admin.AdminApp._get_page_as_app = _get_page_as_app
user_auth_admin.attach_page_head = attach_page_head

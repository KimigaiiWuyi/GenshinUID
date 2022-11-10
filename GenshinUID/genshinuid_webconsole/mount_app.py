import platform
import contextlib
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Set,
    List,
    Type,
    Union,
    Callable,
    Optional,
    cast,
)

import fastapi_amis_admin
from pydantic import BaseModel
from sqlmodel import Relationship
from sqlalchemy.orm import backref
from fastapi import FastAPI, Request
from nonebot import get_app, get_driver
from fastapi_amis_admin import amis, admin
from fastapi_amis_admin.crud import BaseApiOut
from sqlalchemy.ext.asyncio import AsyncEngine
from fastapi_user_auth.site import AuthAdminSite
from fastapi_amis_admin.amis.types import AmisAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_amis_admin.models.fields import Field
from fastapi_amis_admin.crud.schema import CrudEnum
from fastapi_amis_admin.admin.settings import Settings
from fastapi_amis_admin.utils.translation import i18n as _
from fastapi_user_auth.auth.models import User, UserRoleLink
from fastapi_amis_admin.admin.site import DocsAdmin, ReDocsAdmin
from fastapi_amis_admin.amis.constants import LevelEnum, DisplayModeEnum
from fastapi_amis_admin.amis.components import (
    App,
    Form,
    Grid,
    Page,
    Alert,
    Action,
    Property,
    ActionType,
    Horizontal,
    InputExcel,
    InputTable,
    PageSchema,
    ButtonToolbar,
)

from ..version import GenshinUID_version
from ..genshinuid_user.add_ck import _deal_ck
from .login_page import amis_admin, user_auth_admin  # 不要删!!
from ..utils.db_operation.database.db_config import DATABASE_URL
from ..utils.db_operation.database.models import (
    Config,
    UidData,
    PushData,
    CookiesCache,
    NewCookiesTable,
)

if TYPE_CHECKING:
    from quart import Quart
    from asgiref.typing import Scope, HTTPScope, WebSocketScope

AppType = Union[FastAPI, 'Quart']


class FastApiMiddleware:
    def __init__(
        self, app: 'Quart', fastapi: FastAPI, routes: Set[str]
    ) -> None:
        self.fastapi = fastapi
        self.app = app.asgi_app
        self.routes = routes

    async def __call__(
        self, scope: 'Scope', receive: Callable, send: Callable
    ) -> None:
        if scope['type'] in ('http', 'websocket'):
            scope = cast(Union['HTTPScope', 'WebSocketScope'], scope)
            for path in self.routes:
                if scope['path'].startswith(path):
                    return await self.fastapi(
                        scope, receive, send  # type: ignore
                    )
            return await self.app(scope, receive, send)  # type: ignore


# 自定义后台管理站点
class GenshinUIDAdminSite(AuthAdminSite):
    template_name = str(Path(__file__).parent / 'genshinuid.html')

    def __init__(
        self,
        settings: Settings,
        fastapi: FastAPI = None,  # type: ignore
        engine: AsyncEngine = None,  # type: ignore
    ):
        super().__init__(settings, fastapi, engine)
        # 取消注册默认管理类
        self.unregister_admin(DocsAdmin, ReDocsAdmin)
        self.unregister_admin(admin.HomeAdmin)

    async def get_page(self, request: Request) -> App:
        app = await super().get_page(request)
        app.brandName = 'GenshinUID'
        app.logo = 'https://s2.loli.net/2022/01/31/kwCIl3cF1Z2GxnR.png'
        return app


def get_asgi() -> Optional[AppType]:
    try:
        return get_app()
    except AssertionError:
        return None


# 从 nb 获取 FastAPI
app = get_asgi()
if app is None:
    raise RuntimeError('App is not ReverseDriver')

with contextlib.suppress(ImportError):
    from quart import Quart  # noqa: F811

    if isinstance(app, Quart):
        fastapi = FastAPI()
        app.asgi_app = FastApiMiddleware(app, fastapi, {'/genshinuid'})  # type: ignore
        app = fastapi


app = cast(FastAPI, app)
settings = Settings(
    database_url_async=DATABASE_URL,
    database_url='',
    root_path='/genshinuid',
    site_icon='https://s2.loli.net/2022/01/31/kwCIl3cF1Z2GxnR.png',
    site_title='GenshinUID网页控制台',
    language='zh_CN',
)


# 显示主键
async def patched_get_create_form(
    self, request: Request, bulk: bool = False
) -> Form:
    fields = list(self.schema_create.__fields__.values())
    if not bulk:
        return Form(
            api=f'post:{self.router_path}/item',
            name=CrudEnum.create,
            body=await self._conv_modelfields_to_formitems(
                request, fields, CrudEnum.create
            ),
        )
    columns, keys = [], {}
    for field in fields:
        column = await self.get_list_column(
            request, self.parser.get_modelfield(field, deepcopy=True)
        )
        keys[column.name] = '${' + column.label + '}'
        column.name = column.label
        columns.append(column)
    return Form(
        api=AmisAPI(
            method='post',
            url=f'{self.router_path}/item',
            data={'&': {'$excel': keys}},
        ),
        mode=DisplayModeEnum.normal,
        body=[
            InputExcel(name='excel'),
            InputTable(
                name='excel',
                showIndex=True,
                columns=columns,
                addable=True,
                copyable=True,
                editable=True,
                removable=True,
            ),
        ],
    )


admin.BaseModelAdmin.get_create_form = patched_get_create_form


# 创建AdminSite实例
site = GenshinUIDAdminSite(settings)
auth = site.auth

if float(fastapi_amis_admin.__version__[:3]) >= 0.3:

    class MyUser(User, table=True):
        point: float = Field(default=0, title=_('Point'))  # type: ignore
        phone: str = Field(None, title=_('Tel'), max_length=15)  # type: ignore
        parent_id: int = Field(None, title=_('Parent'), foreign_key='auth_user.id')  # type: ignore
        children: List['User'] = Relationship(
            sa_relationship_kwargs=dict(
                backref=backref('parent', remote_side='User.id'),
            ),
        )

    auth.user_model = MyUser

config = get_driver().config
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f'http://{config.host}:{config.port}'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

gsuid_webconsole_help = '''
## 初次使用

欢迎进入网页控制台!

Admin账户可以通过左侧的选项进入不同的数据库直接修改,**首次登陆的Admin账户别忘了修改你的密码!**

普通账户可以通过左侧的选项进行绑定CK或者SK

未来还会加入更多功能!

## 丨我该如何获取Cookies？[#92](https://github.com/KimigaiiWuyi/GenshinUID/issues/92)（[@RemKeeper](https://github.com/RemKeeper)）

```js
var cookie = document.cookie;
var Str_Num = cookie.indexOf('_MHYUUID=');
cookie = cookie.substring(Str_Num);
var ask = confirm('Cookie:' + cookie + '按确认，然后粘贴至Cookies或者Login_ticket选框内');
if (ask == true) {
  copy(cookie);
  msg = cookie
} else {
  msg = 'Cancel'
}
```

1. 复制上面全部代码，然后打开[米游社BBS](https://bbs.mihoyo.com/ys/)
2. 在页面上右键检查或者Ctrl+Shift+i
3. 选择控制台（Console），粘贴，回车，在弹出的窗口点确认（点完自动复制）
4. 然后在和机器人的私聊窗口，粘贴发送即可

**警告：Cookies属于个人隐私，其效用相当于账号密码，请勿随意公开！**

## 丨获取米游社Stoken([AutoMihoyoBBS](https://github.com/Womsxd/AutoMihoyoBBS#%E8%8E%B7%E5%8F%96%E7%B1%B3%E6%B8%B8%E7%A4%BECookie))

```js
var cookie = document.cookie;
var ask = confirm('Cookie:' + cookie + '按确认，然后粘贴至Cookies或者Login_ticket选框内');
if (ask == true) {
  copy(cookie);
  msg = cookie
} else {
  msg = 'Cancel'
}
```

1. 复制上面全部代码，然后打开[米游社账户登录界面](http://user.mihoyo.com/)
2. 在页面上右键检查或者Ctrl+Shift+i
3. 选择控制台（Console），粘贴，回车，在弹出的窗口点确认（点完自动复制）
4. 然后在和机器人的私聊窗口，粘贴发送即可

**警告：Cookies属于个人隐私，其效用相当于账号密码，请勿随意公开！**

## 获取CK通则

**如果获取到的Cookies字段不全，无法通过校验**
**推荐重新登陆米游社再进行获取**

## 网页端 #92 [@RemKeeper](https://github.com/RemKeeper)
[通过网页控制台简易获取Cookies](https://github.com/KimigaiiWuyi/GenshinUID/issues/92)
## 安卓 [@shirokurakana](https://github.com/shirokurakana)
[通过额外APP获取Cookies](https://github.com/KimigaiiWuyi/GenshinUID/issues/203)
## IOS [@741807012](https://github.com/741807012)
[通过快捷指令获取Cookies](https://github.com/KimigaiiWuyi/GenshinUID/issues/201)
'''


@site.register_admin
class AmisPageAdmin(admin.PageAdmin):
    page_schema = '入门使用'
    page = Page.parse_obj(
        {
            'type': 'page',
            'body': {
                'type': 'markdown',
                'value': f'{gsuid_webconsole_help}',
            },
        }
    )


@site.register_admin
class UserBindFormAdmin(admin.FormAdmin):
    page_schema = PageSchema(label='绑定CK或SK', icon='fa fa-link')  # type: ignore

    async def get_form(self, request: Request) -> Form:
        form = await super().get_form(request)
        form.body.sort(key=lambda form_item: form_item.type, reverse=True)  # type: ignore
        form.update_from_kwargs(
            title='',
            mode=DisplayModeEnum.horizontal,
            submitText='绑定',
            actionsClassName='no-border m-none p-none',
            panelClassName='',
            wrapWithPanel=True,
            horizontal=Horizontal(left=3, right=9),
            actions=[
                ButtonToolbar(
                    buttons=[
                        Action(
                            actionType='submit',
                            label='绑定',
                            level=LevelEnum.primary,
                        )
                    ]
                )
            ],
        )
        return form

    async def get_page(self, request: Request) -> Page:
        page = await super().get_page(request)
        page.body = [
            Alert(
                level='warning',
                body='CK获取可查看左侧栏 [入门使用] 相关细则!',
            ),
            amis.Divider(),
            Grid(
                columns=[
                    {
                        'body': [page.body],
                        'lg': 10,
                        'md': 10,
                        'valign': 'middle',
                    }
                ],
                align='center',
                valign='middle',
            ),
        ]
        return page

    # 创建表单数据模型
    class schema(BaseModel):
        QQ: str = Field(..., title='QQ号', min_length=3, max_length=30)  # type: ignore
        Cookies: str = Field(..., title='Cookies或者Login_ticket')  # type: ignore

    # 处理表单提交数据
    async def handle(
        self, request: Request, data: schema, **kwargs
    ) -> BaseApiOut[Any]:
        try:
            im = await _deal_ck(data.Cookies, data.QQ)
        except:
            return BaseApiOut(status=-1, msg='你输入的CK可能已经失效,请按照[入门使用]进行操作!')
        ok_num = im.count('成功')
        if ok_num < 1:
            return BaseApiOut(status=-1, msg=im)
        else:
            return BaseApiOut(msg=im)


@site.register_admin
class UserAuth(admin.ModelAdmin):
    pk_name = 'user_id'
    page_schema = PageSchema(label='用户授权', icon='fa fa-user-o')  # type: ignore

    # 配置管理模型
    model = UserRoleLink

    async def has_page_permission(self, request: Request) -> bool:
        return await auth.requires(roles='admin', response=False)(request)


@site.register_admin
class CKadmin(admin.ModelAdmin):
    pk_name = 'UID'
    page_schema = PageSchema(label='CK管理', icon='fa fa-database')  # type: ignore

    # 配置管理模型
    model = NewCookiesTable

    async def has_page_permission(self, request: Request) -> bool:
        return await auth.requires(roles='admin', response=False)(request)


@site.register_admin
class Configadmin(admin.ModelAdmin):
    pk_name = 'Name'
    page_schema = PageSchema(label='配置项管理', icon='fa fa-toggle-on')  # type: ignore

    # 配置管理模型
    model = Config

    async def has_page_permission(self, request: Request) -> bool:
        return await auth.requires(roles='admin', response=False)(request)


@site.register_admin
class pushadmin(admin.ModelAdmin):
    pk_name = 'UID'
    page_schema = PageSchema(label='推送管理', icon='fa fa-bullhorn')  # type: ignore

    # 配置管理模型
    model = PushData

    async def has_page_permission(self, request: Request) -> bool:
        return await auth.requires(roles='admin', response=False)(request)


@site.register_admin
class cacheadmin(admin.ModelAdmin):
    pk_name = 'UID'
    page_schema = PageSchema(label='缓存管理', icon='fa fa-recycle')  # type: ignore

    # 配置管理模型
    model = CookiesCache

    async def has_page_permission(self, request: Request) -> bool:
        return await auth.requires(roles='admin', response=False)(request)


@site.register_admin
class bindadmin(admin.ModelAdmin):
    pk_name = 'USERID'
    page_schema = PageSchema(label='绑定管理', icon='fa fa-users')  # type: ignore

    # 配置管理模型
    model = UidData

    async def has_page_permission(self, request: Request) -> bool:
        return await auth.requires(roles='admin', response=False)(request)


# 注册管理类
@site.register_admin
class GitHubIframeAdmin(admin.IframeAdmin):
    # 设置页面菜单信息
    page_schema = PageSchema(label='安装Wiki', icon='fa fa-github')  # type: ignore
    # 设置跳转链接
    src = 'https://github.com/KimigaiiWuyi/GenshinUID/wiki'


# 注册自定义首页
@site.register_admin
class MyHomeAdmin(admin.HomeAdmin):
    group_schema = None
    page_schema = PageSchema(
        label=('主页'),
        icon='fa fa-home',
        url='/home',
        isDefaultPage=True,
        sort=100,
    )  # type: ignore
    page_path = '/home'

    async def get_page(self, request: Request) -> Page:
        page = await super().get_page(request)
        page.body = [
            Alert(
                level='warning',
                body=' 警告: 初始admin账号请务必前往「用户授权」➡「用户管理」处修改密码!',
            ),
            amis.Divider(),
            Property(
                title='GenshinUID Info',
                column=4,
                items=[
                    Property.Item(label='system', content=platform.system()),
                    Property.Item(
                        label='python', content=platform.python_version()
                    ),
                    Property.Item(label='version', content=GenshinUID_version),
                    Property.Item(label='license', content='GPLv3'),
                ],
            ),
        ]
        return page


# 挂载后台管理系统
site.mount_app(app)

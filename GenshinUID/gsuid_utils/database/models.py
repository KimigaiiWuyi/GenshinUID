from typing import Optional

from sqlmodel import Field, SQLModel


class GsBind(SQLModel, table=True):
    __table_args__ = {'keep_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True, title='序号')
    bot_id: str = Field(title='平台')
    user_id: str = Field(title='账号')
    uid: Optional[str] = Field(default=None, title='UID')
    mys_id: Optional[str] = Field(default=None, title='米游社通行证')


class GsUser(SQLModel, table=True):
    __table_args__ = {'keep_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True, title='序号')
    bot_id: str = Field(title='平台')
    uid: str = Field(title='UID')
    mys_id: Optional[str] = Field(default=None, title='米游社通行证')
    region: Optional[str] = Field(default=None, title='地区')
    cookie: Optional[str] = Field(default=None, title='Cookie')
    stoken: Optional[str] = Field(default=None, title='Stoken')
    user_id: str = Field(title='账号')
    push_switch: str = Field(title='全局推送开关')
    sign_switch: str = Field(title='自动签到')
    bbs_switch: str = Field(title='自动米游币')
    status: Optional[str] = Field(default=None, title='状态')


class GsCache(SQLModel, table=True):
    __table_args__ = {'keep_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True, title='序号')
    cookie: str = Field(default=None, title='Cookie')
    uid: Optional[str] = Field(default=None, title='UID')
    mys_id: Optional[str] = Field(default=None, title='米游社通行证')


class GsPush(SQLModel, table=True):
    __table_args__ = {'keep_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True, title='序号')
    uid: str = Field(title='UID')
    coin_push: Optional[str] = Field(title='洞天宝钱推送')
    coin_value: Optional[int] = Field(title='洞天宝钱阈值')
    coin_is_push: Optional[str] = Field(title='洞天宝钱是否已推送')
    resin_push: Optional[str] = Field(title='体力推送')
    resin_value: Optional[int] = Field(title='体力阈值')
    resin_is_push: Optional[str] = Field(title='体力是否已推送')
    go_push: Optional[str] = Field(title='派遣推送')
    go_value: Optional[int] = Field(title='派遣阈值')
    go_is_push: Optional[str] = Field(title='派遣是否已推送')
    transform_push: Optional[str] = Field(title='质变仪推送')
    transform_value: Optional[int] = Field(title='质变仪阈值')
    transform_is_push: Optional[str] = Field(title='质变仪是否已推送')

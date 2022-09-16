from fastapi import Request
from fastapi_amis_admin import admin
from fastapi_user_auth.auth import AuthRouter
from starlette.responses import RedirectResponse
from fastapi_amis_admin.admin.site import AdminSite
from fastapi_amis_admin.amis.components import Page, PageSchema

from .web_config import GenshinUIDAdminSite, app, site
from ..utils.db_operation.database.models import (
    Config,
    UidData,
    PushData,
    CookiesCache,
    NewCookiesTable,
)

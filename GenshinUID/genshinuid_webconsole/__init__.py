from sqlmodel import SQLModel
from nonebot.log import logger
from nonebot import get_bot, on_startup

from ..utils.db_operation.db_operation import config_check

config = get_bot().config


async def run_webconsole():
    # 语言本地化
    from fastapi_user_auth import i18n as user_auth_i18n
    from fastapi_amis_admin import i18n as admin_auth_i18n

    admin_auth_i18n.set_language('zh_CN')
    user_auth_i18n.set_language('zh_CN')

    # 导入app
    from .mount_app import auth, site

    logger.info('尝试挂载WebConsole')

    await site.db.async_run_sync(
        SQLModel.metadata.create_all, is_session=False  # type: ignore
    )
    # 创建默认测试用户, 请及时修改密码!!!
    await auth.create_role_user()

    logger.info(
        ('WebConsole挂载成功：' f'http://{config.HOST}:{config.PORT}/genshinuid')
    )


@on_startup
async def start_check():
    if await config_check('OpenWeb'):
        await run_webconsole()

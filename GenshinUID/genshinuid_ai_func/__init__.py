"""GenshinUID 纯数据 AI 工具。

触发器出图仍走各模块 to_ai；本包只向 Agent 暴露结构化文本数据，
不注册「配队/攻略」一类场景特化工具。
"""

from . import (
    kb as _kb,  # noqa: F401
    user as _user,  # noqa: F401
    catalog as _catalog,  # noqa: F401
)

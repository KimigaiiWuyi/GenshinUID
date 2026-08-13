from pydantic import BaseModel, field_validator


class PluginConfig(BaseModel):
    gsuid_core_botid: str = "NoneBot2"
    gsuid_core_host: str = "localhost"
    gsuid_core_port: str = "8765"
    gsuid_core_ws_token: str = ""
    gsuid_core_repeat: bool = False
    gsuid_core_reply_img: bool = True
    gsuid_core_path: str | None = None

    @field_validator(
        "gsuid_core_botid",
        "gsuid_core_host",
        "gsuid_core_port",
        "gsuid_core_ws_token",
        mode="before",
    )
    @classmethod
    def _coerce_str(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value)


def gs_config() -> PluginConfig:
    from nonebot import get_plugin_config

    return get_plugin_config(PluginConfig)

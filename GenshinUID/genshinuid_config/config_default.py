from typing import Dict

from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsStrConfig,
    GsBoolConfig,
    GsDictConfig,
    GsListConfig,
    GsTimeRConfig,
)

CONIFG_DEFAULT: Dict[str, GSC] = {
    "Ann_Groups": GsDictConfig(
        "推送公告群组",
        "原神公告推送群组",
        {},
    ),
    "Ann_Ids": GsListConfig(
        "推送公告ID",
        "原神公告推送ID列表",
        [],
    ),
    "SignTime": GsTimeRConfig(
        "每晚签到时间设置",
        "每晚米游社签到时间设置（时，分）",
        (0, 38),
    ),
    "GroupSignReport": GsBoolConfig(
        "群聊签到报告",
        "开启后将在群聊内发送用户签到报告",
        True,
    ),
    "BBSTaskTime": GsTimeRConfig(
        "每晚米游社任务时间设置",
        "每晚米游社任务时间设置（时，分）",
        (1, 41),
    ),
    "MhyBBSCoinReport": GsBoolConfig(
        "米游币推送",
        "开启后会私聊每个用户当前米游币任务完成情况",
        False,
    ),
    "MhyBBSCoinReportGroup": GsBoolConfig(
        "米游币群聊推送",
        "开启后会在群聊中推送当前群米游币任务完成情况",
        True,
    ),
    "PrivateReport": GsBoolConfig(
        "米游币任务完成私聊报告",
        "关闭后将不再给主人推送当天米游币任务完成情况",
        False,
    ),
    "PrivateSignReport": GsBoolConfig(
        "签到私聊报告",
        "关闭后将不再给任何私聊用户推送当天签到任务完成情况",
        False,
    ),
    "RandomPic": GsBoolConfig(
        "随机图",
        "开启后[查询心海]等命令展示图将替换为随机图片",
        False,
    ),
    "random_pic_API": GsStrConfig(
        "随机图API",
        "用于面板查询的随机图API",
        "https://genshin-res.cherishmoon.fun/img?name=",
        ["https://genshin-res.cherishmoon.fun/img?name="],
    ),
    "SchedSignin": GsBoolConfig(
        "定时签到",
        "开启后每晚00:30将开始自动签到任务",
        True,
    ),
    "SchedMhyBBSCoin": GsBoolConfig(
        "定时米游币",
        "开启后每晚01:16将开始自动米游币任务",
        True,
    ),
    "SchedGetDraw": GsBoolConfig(
        "定时留影叙佳期",
        "开启后每晚03:25将开始自动米游币任务",
        True,
    ),
    "SchedResinPush": GsBoolConfig(
        "定时检查体力",
        "开启后每隔半小时检查一次开启推送的人的体力状态",
        True,
    ),
    "CrazyNotice": GsBoolConfig(
        "催命模式",
        "开启后当达到推送阈值将会一直推送",
        False,
    ),
    "OldPanle": GsBoolConfig(
        "旧面板",
        "会稍微增加面板访问速度,但会损失很多功能",
        False,
    ),
    "ColorBG": GsBoolConfig(
        "多彩面板",
        "面板颜色不按照属性来渲染,而按照自定义颜色",
        False,
    ),
    "DefaultBaseBG": GsBoolConfig(
        "固定背景",
        "开启后部分功能的背景图将固定为特定背景",
        False,
    ),
    "PicWiki": GsBoolConfig(
        "图片版WIKI",
        "开启后支持的WIKI功能将转为图片版",
        True,
    ),
    "WidgetResin": GsBoolConfig(
        "体力使用组件API",
        "开启后mr功能将转为调用组件API, 可能缺失数据、数据不准",
        True,
    ),
    "EnableAkasha": GsBoolConfig(
        "排名系统",
        "开启后强制刷新将同时刷新AkashaSystem",
        False,
    ),
    "help_column": GsStrConfig(
        "帮助图列数",
        "修改帮助图有多少列",
        "6",
    ),
    "EnableCharCardByMys": GsBoolConfig(
        "从米游社获取面板替代Enka服务",
        "开启后角色卡片将从米游社获取, 可能会遇到验证码",
        False,
    ),
    "GachaLogOrder": GsStrConfig(
        "抽卡记录渲染顺序",
        "每个卡池五星卡片的排列顺序。旧到新：最早出金在前；新到旧：最近出金在前",
        "旧到新",
        ["旧到新", "新到旧"],
    ),
}

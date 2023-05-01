from typing import Dict

from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsStrConfig,
    GsBoolConfig,
    GsDictConfig,
    GsListConfig,
    GsListStrConfig,
)

CONIFG_DEFAULT: Dict[str, GSC] = {
    'random_pic_API': GsStrConfig(
        '随机图API',
        '用于面板查询的随机图API',
        'https://genshin-res.cherishmoon.fun/img?name=',
    ),
    'Ann_Groups': GsDictConfig(
        '推送公告群组',
        '原神公告推送群组',
        {},
    ),
    'Ann_Ids': GsListConfig(
        '推送公告ID',
        '原神公告推送ID列表',
        [],
    ),
    'SignTime': GsListStrConfig('每晚签到时间设置', '每晚米游社签到时间设置（时，分）', ['0', '38']),
    'BBSTaskTime': GsListStrConfig(
        '每晚米游社任务时间设置', '每晚米游社任务时间设置（时，分）', ['1', '41']
    ),
    'MhyBBSCoinReport': GsBoolConfig(
        '米游币推送',
        '开启后会私聊每个用户当前米游币任务完成情况',
        False,
    ),
    'SignReportSimple': GsBoolConfig(
        '简洁签到报告',
        '开启后可以大大减少每日签到报告字数',
        True,
    ),
    'PrivateReport': GsBoolConfig(
        '私聊报告',
        '关闭后将不再给主人推送当天米游币任务完成情况',
        False,
    ),
    'RandomPic': GsBoolConfig(
        '随机图',
        '开启后[查询心海]等命令展示图将替换为随机图片',
        False,
    ),
    'SchedSignin': GsBoolConfig(
        '定时签到',
        '开启后每晚00:30将开始自动签到任务',
        True,
    ),
    'SchedMhyBBSCoin': GsBoolConfig(
        '定时米游币',
        '开启后每晚01:16将开始自动米游币任务',
        True,
    ),
    'CrazyNotice': GsBoolConfig(
        '催命模式',
        '开启后当达到推送阈值将会一直推送',
        False,
    ),
    'OldPanle': GsBoolConfig(
        '旧面板',
        '会稍微增加面板访问速度,但会损失很多功能',
        False,
    ),
    'ColorBG': GsBoolConfig(
        '多彩面板',
        '面板颜色不按照属性来渲染,而按照自定义颜色',
        False,
    ),
    'DefaultPayWX': GsBoolConfig(
        '支付默认微信',
        '开启后使用gsrc命令将会以微信作为优先付款方式',
        False,
    ),
    'DefaultBaseBG': GsBoolConfig(
        '固定背景',
        '开启后部分功能的背景图将固定为特定背景',
        False,
    ),
    'PicWiki': GsBoolConfig(
        '图片版WIKI',
        '开启后支持的WIKI功能将转为图片版',
        True,
    ),
}

import json,os

FILE_PATH = os.path.dirname(__file__)

class Config:
    def __init__(self):
        self.test_guild_id = ""
        self.switch_list = {
                                "uid":"SearchRole",
                                "mys":"SearchRole",
                                "查询":"SearchRole",
                                "绑定uid":"LinkUID",
                                "绑定mys":"LinkUID",
                                "角色":"CharInfo",
                                "武器":"WeaponInfo",
                                "材料":"CostInfo",
                                "天赋":"TalentsInfo",
                                "命座":"PolarInfo",
                                "攻略":"guideInfo",
                                "信息":"CardInfo",
                                "御神签":"GetLots",
                                "语音":"AudioInfo",
                                "食物":"Foods",
                                "原魔":"Enemies",
                                "圣遗物":"Artifacts",
                                "添加":"AddCk",
                                "当前状态":"DailyData",
                                "每月统计":"MonthData",
                                "签到":"Sign"
                            }

    async def load_ark(self,ark = ""):
        ark_path = os.path.join(FILE_PATH,"ARK")
        with open(os.path.join(ark_path,"{}.json".format(ark)),'r') as load_f:
            im = json.load(load_f)
        return im
        
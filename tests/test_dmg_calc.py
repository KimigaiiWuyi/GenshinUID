"""回归：`dmg_map.json` 空占位（`"角色": []`）不应让面板查询抛 IndexError。

`update_effects.py` 只给新角色 `[]` 占位；`get_char_dmg_percent` 命中键但
取不到参考面板时必须按「无匹配」处理，而不是索引空列表。
"""

import asyncio
from copy import deepcopy

from GenshinUID.genshinuid_enka.etc.base_info import baseFightProp
from GenshinUID.genshinuid_enka.mono.Character import Character
from GenshinUID.genshinuid_enka.dmg_calc.dmg_calc import get_char_dmg_percent


def _mitia_card_prop() -> dict:
    fight_prop = deepcopy(baseFightProp)
    fight_prop.update({"baseHp": 11633.6, "baseAtk": 372.1, "baseDef": 791.6})
    return {
        "avatarId": 10000136,
        "avatarName": "米提亚",
        "avatarElement": "Electro",
        "avatarLevel": "90",
        "avatarFetter": 10,
        "avatarEnName": "Mitya",
        "talentList": [{"talentId": 300 + i, "talentName": f"T{i}", "talentIcon": ""} for i in range(1, 7)],
        "weaponInfo": {
            "weaponName": "秘星典谕",
            "weaponType": "法器",
            "weaponAffix": 1,
            "weaponStar": 5,
            "weaponLevel": 90,
            "promoteLevel": 6,
            "weaponStats": [{"statValue": 674}],
            "weaponEffect": "",
        },
        "avatarSkill": [
            {"skillLevel": 9, "skillIcon": "Skill_A_02"},
            {"skillLevel": 9, "skillIcon": ""},
            {"skillLevel": 9, "skillIcon": ""},
        ],
        "avatarFightProp": fight_prop,
        "equipList": [],
        "equipSets": {"type": "", "set": ""},
    }


def test_empty_dmg_map_entry_does_not_crash() -> None:
    async def main() -> None:
        char = Character(_mitia_card_prop())
        await char.init_prop()
        dmg_data = await get_char_dmg_percent(char)
        assert dmg_data
        assert char.percent == "0.00"
        assert char.seq_str == "无匹配"

    asyncio.run(main())

PERCENT_ATTR = ['dmgBonus', 'addAtk', 'addDef', 'addHp']

baseWeaponInfo = {
    'itemId': 0,
    'nameTextMapHash': '0',
    'weaponIcon': 'UI_EquipIcon_Bow_Changed',
    'weaponType': '',
    'weaponName': '',
    'weaponStar': 0,
    'promoteLevel': 0,
    'weaponLevel': 0,
    'weaponAffix': 1,
    'weaponStats': [
        {
            'appendPropId': '',
            'statName': '基础攻击力',
            'statValue': 0,
        },
        {
            'appendPropId': '',
            'statName': '',
            'statValue': 0,
        },
    ],
    'weaponEffect': '',
}

baseFightProp = {
    'hp': 0.0,
    'baseHp': 0.0,
    'addHp': 0.0,
    'exHp': 0.0,
    'atk': 0.0,
    'baseAtk': 0.0,
    'addAtk': 0.0,
    'exAtk': 0.0,
    'def': 0.0,
    'baseDef': 0.0,
    'addDef': 0.0,
    'exDef': 0.0,
    'elementalMastery': 0.0,
    'critRate': 0.05,
    'critDmg': 0.5,
    'energyRecharge': 1.0,
    'healBonus': 0.0,
    'healedBonus': 0.0,
    'physicalDmgSub': 0.0,
    'physicalDmgBonus': 0.0,
    'dmgBonus': 0.0,
}

ATTR_MAP = {
    '元素精通': 'elementalMastery',
    '物理伤害加成': 'physicalDmgBonus',
    '元素伤害加成': 'dmgBonus',
    '充能效率': 'energyRecharge',
    '暴击伤害': 'critDmg',
    '暴击率': 'critRate',
    '攻击力': 'addAtk',
    '防御力': 'addDef',
    '生命值': 'addHp',
    '百分比血量': 'addHp',
}

ELEMENT_MAP = {
    '风': 'Anemo',
    '冰': 'Cryo',
    '草': 'Dendro',
    '雷': 'Electro',
    '岩': 'Geo',
    '水': 'Hydro',
    '火': 'Pyro',
}

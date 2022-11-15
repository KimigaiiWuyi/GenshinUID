from ...utils.data_convert.convert_skill_data import get_skill_data

power_add = {
    '优菈': {
        'Q每层能量伤害': {
            'type': 'F1P',
            'value': [
                0.7499200105667114,
                0.8109599947929382,
                0.871999979019165,
                0.9592000246047974,
                1.0202399492263794,
                1.090000033378601,
                1.185920000076294,
                1.2818399667739868,
                1.3777600526809692,
                1.4823999404907227,
                1.6023000478744507,
                1.7433019876480103,
                1.8843050003051758,
                2.0253069400787354,
                2.1791279315948486,
            ],
        }
    }
}


async def get_extra_value(
    char_name: str, power_name: str, skill_level: int
) -> float:
    if char_name in power_add and power_name in power_add[char_name]:
        value = power_add[char_name][power_name]['value'][skill_level - 1]
        type = power_add[char_name][power_name]['type']
        value = await get_skill_data(type, value)
    else:
        return 0.0
    return value

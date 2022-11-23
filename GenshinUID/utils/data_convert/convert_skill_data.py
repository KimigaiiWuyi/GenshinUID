from typing import Literal


async def get_skill_data(
    mode: Literal['F1P', 'F2P', 'F1', 'F2', 'P', 'I'], data: int
) -> float:

    if mode == 'F1P':
        result = '%.1f%%' % (data * 100)
    elif mode == 'F2P':
        result = '%.2f%%' % (data * 100)
    elif mode == 'F1':
        result = '%.1f' % data
    elif mode == 'F2':
        result = '%.2f' % data
    elif mode == 'P':
        result = str(round(data * 100)) + '%'
    elif mode == 'I':
        result = '%.2f' % data
    result = float(result.replace('%', ''))
    return result

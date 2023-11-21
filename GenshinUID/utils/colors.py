from typing import Dict, List, Tuple, Union

first_color = (29, 29, 29)
sec_color = (35, 35, 35)
brown_color = (41, 25, 0)
light_color = (255, 233, 201)
red_color = (255, 66, 66)
green_color = (74, 189, 119)
gray_color = (70, 70, 70)
blue_color = (31, 152, 237)
white_color = (255, 255, 255)

COLOR_MAP: Dict[int, Tuple[int, int, int]] = {
    0: (200, 12, 12),
    1: (200, 100, 12),
    2: (151, 80, 186),
    3: (33, 142, 212),
    4: (47, 107, 56),
    5: (64, 64, 66),
}


def get_color(
    value: float, data: Union[List[int], List[float]], reverse: bool = False
) -> Tuple[int, int, int]:
    for index, i in enumerate(data):
        if (reverse and value <= i) or (value >= i):
            return COLOR_MAP[index]
    else:
        return COLOR_MAP[5]

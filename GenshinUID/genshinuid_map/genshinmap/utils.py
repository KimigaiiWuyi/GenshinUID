from __future__ import annotations

from math import ceil
from io import BytesIO
from typing import List, Tuple, Union
from asyncio import gather, create_task

from PIL import Image
from httpx import AsyncClient

from .models import Maps, Point, XYPoint

CLIENT = AsyncClient()


async def get_img(url: str) -> Image.Image:
    resp = await CLIENT.get(url)
    resp.raise_for_status()
    return Image.open(BytesIO(resp.read()))


async def make_map(map: Maps) -> Image.Image:
    """
    获取所有地图并拼接

    警告：可能导致内存溢出

    在测试中，获取并合成「提瓦特」地图时占用了约 1.4 GiB

    建议使用 `genshinmap.utils.get_map_by_pos` 获取地图单片

    参数：
        map: `Maps`
            地图数据，可通过 `get_maps` 获取

    返回：
        `PIL.Image.Image` 对象

    另见：
        `get_map_by_pos`
    """
    img = Image.new("RGBA", tuple(map.total_size))
    x = 0
    y = 0
    maps: List[Image.Image] = await gather(
        *[create_task(get_img(url)) for url in map.slices]
    )
    for m in maps:
        img.paste(m, (x, y))
        x += 4096
        if x >= map.total_size[0]:
            x = 0
            y += 4096
    return img


async def get_map_by_pos(
    map: Maps, x: Union[int, float], y: Union[int, float] = 0
) -> Image.Image:
    """
    根据横坐标获取地图单片

    参数：
        map: `Maps`
            地图数据，可通过 `get_maps` 获取

        x: `int | float`
            横坐标

        y: `int | float` (default: 0)
            纵坐标

    返回：
        `PIL.Image.Image` 对象
    """
    return await get_img(map.slices[_pos_to_index(x, y)])


def get_points_by_id(id_: int, points: List[Point]) -> List[XYPoint]:
    """
    根据 Label ID 获取坐标点

    参数：
        id_: `int`
            Label ID

        points: `list[Point]`
            米游社坐标点列表，可通过 `get_points` 获取

    返回：
        `list[XYPoint]`
    """
    return [
        XYPoint(point.x_pos, point.y_pos)
        for point in points
        if point.label_id == id_
    ]


def convert_pos(points: List[XYPoint], origin: List[int]) -> List[XYPoint]:
    """
    将米游社资源坐标转换为以左上角为原点的坐标系的坐标

    参数：
        points: `list[XYPoint]`
            米游社资源坐标

        origin: `list[Point]`
            米游社地图 Origin，可通过 `get_maps` 获取

    返回：
        `list[XYPoint]`

    示例：
        >>> from genshinmap.models import XYPoint
        >>> points = [XYPoint(1200, 5000), XYPoint(-4200, 1800)]
        >>> origin = [4844,4335]
        >>> convert_pos(points, origin)
        [XYPoint(x=6044, y=9335), XYPoint(x=644, y=6135)]
    """
    return [XYPoint(x + origin[0], y + origin[1]) for x, y in points]


def convert_pos_crop(
    top_left_index: int, points: List[XYPoint]
) -> List[XYPoint]:
    """
    根据左上角地图切片的索引转换坐标（已经通过 `convert_pos` 转换）

    参数：
        top_left_index: `int`
            左上角地切片图的索引

        points: `list[XYPoint]`
            米游社资源坐标（已经通过 `convert_pos` 转换）

    返回：
        `list[XYPoint]`

    示例：
        >>> from genshinmap.models import XYPoint
        >>> points = [XYPoint(0, 0), XYPoint(20, 20)]
        >>> convert_pos_crop(0, points)
        [XYPoint(x=0, y=0), XYPoint(x=20, y=20)]
        >>> convert_pos_crop(1, points)
        [XYPoint(x=-4096, y=0), XYPoint(x=-4076, y=20)]
        >>> convert_pos_crop(4, points)
        [XYPoint(x=0, y=-4096), XYPoint(x=20, y=-4076)]
        >>> convert_pos_crop(5, points)
        [XYPoint(x=-4096, y=-4096),XYPoint(x=-4076, y=-4076)]
    """
    y, x = divmod(top_left_index, 4)
    if x == y == 0:
        return points
    x *= 4096
    y *= 4096
    result = []
    for point in points:
        px, py = point
        result.append(XYPoint(px - x, py - y))
    return result


def _pos_to_index(x: Union[int, float], y: Union[int, float]) -> int:
    # 4 * (y // 4096) {0,4,8}
    # x // 4096 {0,1,2,3}
    return 4 * (int(y // 4096)) + int(x // 4096)


def _generate_matrix(
    top_left: int, top_right: int, bottom_left: int
) -> List[int]:
    result = []
    while True:
        result.extend(iter(range(top_left, top_right + 1)))
        if top_left == bottom_left:
            break
        top_left_copy = top_left
        top_left += 4
        top_right = top_left + (top_right - top_left_copy)
    return result


def crop_image_and_points(
    points: List[XYPoint],
) -> Tuple[List[int], int, List[XYPoint]]:
    """
    根据坐标（需通过 `convert_pos` 转换）计算地图切片索引，间隔（即贴完一张图片后还需要贴几张才换行）和转换后的坐标

    参数：
        points: `list[XYPoint]`
            米游社资源坐标（已经通过 `convert_pos` 转换）

    返回：
        `tuple[list[int], int, list[XYPoint]]`

        第 1 个元素为地图切片索引的列表
        第 2 个元素为间隔
        第 3 个元素为使用 `convert_pos_crop` 转换后的坐标

    示例：
        >>> points = [XYPoint(x=4200, y=8000), XYPoint(x=4150, y=10240)]
        >>> crop_image_and_points(points)
        ([5, 9], 0, [XYPoint(x=104, y=3904), XYPoint(x=54, y=6144)])
    """
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    x1, y1 = min(xs), min(ys)
    x2, y2 = max(xs), max(ys)

    x1 = int(x1 // 4096 * 4096)
    x2 = x1 if x1 + 4096 >= x2 else ceil(x2 / 4096) * 4096 - 4096
    y1 = int(y1 // 4096 * 4096)
    y2 = y1 if y1 + 4096 >= y2 else ceil(y2 / 4096) * 4096 - 4096
    index_x1, index_x2 = _pos_to_index(x1, y1), _pos_to_index(x2, y1)
    return (
        _generate_matrix(index_x1, index_x2, _pos_to_index(x1, y2)),
        index_x2 - index_x1,
        convert_pos_crop(index_x1, points),
    )

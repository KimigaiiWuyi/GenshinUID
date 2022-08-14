from pathlib import Path

from PIL import Image

from .genshinmap import utils, models, request

TEXT_PATH = Path(__file__).parent / 'texture2d'


async def create_genshin_map():
    mark_god_pic = Image.open(TEXT_PATH / 'mark_god.png')
    mark_trans_pic = Image.open(TEXT_PATH / 'mark_trans.png')
    for map_id in models.MapID:
        maps = await request.get_maps(map_id)
        points = await request.get_points(map_id)
        mark_god = utils.get_points_by_id(2, points)
        mark_trans = utils.get_points_by_id(3, points)
        mark_god_converted = utils.convert_pos(mark_god, maps.detail.origin)
        mark_trans_converted = utils.convert_pos(
            mark_trans, maps.detail.origin
        )
        maps = await request.get_maps(map_id)
        map_img = await utils.make_map(maps.detail)
        for mark_god_point in mark_god_converted:
            map_img.paste(
                mark_god_pic,
                (int(mark_god_point.x) - 32, int(mark_god_point.y) - 64),
                mark_god_pic,
            )
        for mark_trans_point in mark_trans_converted:
            map_img.paste(
                mark_trans_pic,
                (int(mark_trans_point.x) - 32, int(mark_trans_point.y) - 64),
                mark_trans_pic,
            )
        map_img.save(Path(__file__).parent / 'map_data' / f'{map_id.name}.png')

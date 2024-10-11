import json
from io import BytesIO
from time import sleep
from typing import Dict
from pathlib import Path

import httpx
from PIL import Image

MAP_PATH = Path(__file__).parent.parent / 'utils' / 'map' / 'data'

with open(MAP_PATH / 'enName2AvatarID_mapping_5.1.0.json') as f:
    enmap: Dict[str, str] = json.load(f)

suffix = 'webp'

char_list = ['Chasca', 'Olorun']
base = 'https://api.hakush.in/gi/UI'
# title = 'https://enka.network/ui/{}'
# hakush = 'https://api.hakush.in/gi/UI/'
# ambr = 'https://gi.yatta.top/assets/UI'


icon_list = [
    'Skill_E_{}_01.' + suffix,
    'Skill_E_{}_02.' + suffix,
    'Skill_S_{}_01.' + suffix,
    'Skill_S_{}_02.' + suffix,
    'UI_Talent_S_{}_01.' + suffix,
    'UI_Talent_S_{}_02.' + suffix,
    'UI_Talent_S_{}_03.' + suffix,
    'UI_Talent_S_{}_04.' + suffix,
    'UI_Talent_S_{}_05.' + suffix,
    'UI_Talent_S_{}_06.' + suffix,
    'UI_Talent_S_{}_07.' + suffix,
    'UI_Talent_U_{}_01.' + suffix,
    'UI_Talent_U_{}_02.' + suffix,
    'UI_Talent_C_{}_01.' + suffix,
    'UI_Talent_C_{}_02.' + suffix,
    'UI_Gacha_AvatarImg_{}.' + suffix,
    'UI_NameCardIcon_{}.' + suffix,
    'UI_AvatarIcon_{}.' + suffix,
    'UI_NameCardPic_{}_P.' + suffix,
]
is_download = True


def download(icon_name: str, url: str):
    icon_name = icon_name.split('.')[0] + '.png'
    path = Path(__file__).parent / icon_name
    if path.exists():
        print(f'{icon_name}已经存在!，跳过！')
        return
    print(f'正在下载{icon_name}')
    print(url)
    while True:
        try:
            char_data = httpx.get(url, follow_redirects=True, timeout=80)
            break
        except:  # noqa:E722
            sleep(4)

    if char_data.headers['Content-Type'] == 'image/png':
        char_bytes = char_data.content
    elif char_data.headers['Content-Type'] == 'image/webp':
        webp_image = BytesIO(char_data.content)
        img = Image.open(webp_image)
        png_bytes = BytesIO()
        img.save(png_bytes, 'PNG')
        png_bytes.seek(0)
        char_bytes = png_bytes.read()
    else:
        print(f'{icon_name}不存在，跳过！')
        return

    with open(path, '+wb') as handler:
        handler.write(char_bytes)
        print('下载成功！')


def main():
    for char in char_list:
        for icon in icon_list:
            print(icon)
            if icon.startswith('UI_NameCardPic'):
                _title = base + '/namecard'
            else:
                _title = base
            title = _title + '/{}'
            icon_name = icon.format(char)
            url = title.format(icon_name)
            print(url)
            if is_download:
                download(icon_name, url)


def download_namecard_pic(start: int = 10000002):
    for _enname in enmap:
        en = _enname.split(' ')[-1]
        avatar_id = enmap[_enname]
        if int(avatar_id) < start:
            continue

        if en == 'Jean':
            en = 'Qin'
        elif en == 'Baizhu':
            en = 'Baizhuer'
        elif en == 'Alhaitham':
            en = 'Alhatham'
        elif en == 'Jin':
            en = 'Yunjin'
        elif en == 'Miko':
            en = 'Yae'
        elif en == 'Heizou':
            en = 'Heizo'
        elif en == 'Amber':
            en = 'Ambor'
        elif en == 'Noelle':
            en = 'Noel'
        elif en == 'Yanfei':
            en = 'Feiyan'
        elif en == 'Shogun':
            en = 'Shougun'
        elif en == 'Lynette':
            en = 'Linette'
        elif en == 'Lyney':
            en = 'Liney'
        elif en == 'Tao':
            en = 'Hutao'
        elif en == 'Thoma':
            en = 'Tohma'
        url = f'{base}/UI_NameCardPic_{en}_P.' + suffix
        download(f'{avatar_id}.' + suffix, url)


if __name__ == '__main__':
    # download_namecard_pic(10000063)
    main()

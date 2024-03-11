import json
from typing import Dict
from pathlib import Path

import httpx

MAP_PATH = Path(__file__).parent.parent / 'utils' / 'map' / 'data'

with open(MAP_PATH / 'enName2AvatarID_mapping_4.5.0.json') as f:
    enmap: Dict[str, str] = json.load(f)

char_list = ['Chiori']
base = 'https://api.ambr.top/assets/UI'
# title = 'https://enka.network/ui/{}'
icon_list = [
    'Skill_E_{}_01.png',
    'Skill_E_{}_02.png',
    'Skill_S_{}_01.png',
    'Skill_S_{}_02.png',
    'UI_Talent_S_{}_01.png',
    'UI_Talent_S_{}_02.png',
    'UI_Talent_S_{}_03.png',
    'UI_Talent_S_{}_04.png',
    'UI_Talent_S_{}_05.png',
    'UI_Talent_S_{}_06.png',
    'UI_Talent_S_{}_07.png',
    'UI_Talent_U_{}_01.png',
    'UI_Talent_U_{}_02.png',
    'UI_Talent_C_{}_01.png',
    'UI_Talent_C_{}_02.png',
    'UI_Gacha_AvatarImg_{}.png',
    'UI_NameCardIcon_{}.png',
    'UI_AvatarIcon_{}.png',
    'UI_NameCardPic_{}_P.png',
]
is_download = True


def download(icon_name: str, url: str):
    path = Path(__file__).parent / icon_name
    if path.exists():
        print(f'{icon_name}已经存在!，跳过！')
        return
    print(f'正在下载{icon_name}')
    char_data = httpx.get(url, follow_redirects=True, timeout=80)
    if char_data.headers['Content-Type'] == 'image/png':
        char_bytes = char_data.content
    else:
        print(f'{icon_name}不存在，跳过！')
        return
    # img_data = httpx.get(url).content
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


def download_namecard_pic():
    for _enname in enmap:
        en = _enname.split(' ')[-1]
        avatar_id = enmap[_enname]
        if en == 'Jean':
            en = 'Qin'
        elif en == 'Baizhu':
            en = 'Baizhuer'
        elif en == 'Alhaitham':
            en = 'Alhatham'
        elif en == 'Jin':
            en = 'Yunjin'
        elif en == 'Miko':
            en = 'Yae1'
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
        url = f'{base}/namecard/UI_NameCardPic_{en}_P.png'
        download(f'{avatar_id}.png', url)


# download_namecard_pic()
main()

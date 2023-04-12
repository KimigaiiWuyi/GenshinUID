from pathlib import Path

import httpx

char_list = ['Momoka']
title = 'https://api.ambr.top/assets/UI/{}'
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
]
is_download = True

for char in char_list:
    for icon in icon_list:
        icon_name = icon.format(char)
        url = title.format(icon_name)
        print(url)
        if is_download:
            print(f'正在下载{icon_name}')
            char_data = httpx.get(url, follow_redirects=True, timeout=80)
            if char_data.headers['Content-Type'] == 'image/png':
                char_bytes = char_data.content
            else:
                print(f'{icon_name}不存在，跳过！')
                continue
            img_data = httpx.get(url).content
            with open(Path(__file__).parent / icon_name, '+wb') as handler:
                handler.write(char_bytes)
                print('下载成功！')

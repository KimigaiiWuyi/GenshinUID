from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from base64 import b64encode
from httpx import get
import math
import json

R_PATH = Path(__file__).parents[0]
TEXT_PATH = R_PATH / 'texture2D'
ICON_PATH = R_PATH / 'icon'
GACHA_PATH = R_PATH / 'gachaImg'
PLAYER_PATH = R_PATH / 'player'
RELIC_PATH = R_PATH / 'relicIcon'


COLOR_MAP = {'Anemo':(3, 90, 77),'Cryo':(5, 85, 151),'Dendro':(4, 87, 3),
             'Electro':(47, 1, 85),'Geo':(85, 34, 1),'Hydro':(4, 6, 114),'Pyro':(88, 4, 4)}

def genshin_font_origin(size: int) -> ImageFont:
    return ImageFont.truetype(str(TEXT_PATH / 'yuanshen_origin.ttf'), size=size)

def get_star_png(star: int) -> Image:
        png = Image.open(TEXT_PATH / 's-{}.png'.format(str(star)))
        return png

def strLenth(r: str, size: int, limit: int = 540) -> str:
    result = ''
    temp = 0
    for i in r:
        if temp >= limit:
            result += '\n' + i
            temp = 0
        else:
            result += i

        if i.isdigit():
            temp += round(size / 10 * 6)
        elif i == '/':
            temp += round(size / 10 * 2.2)
        elif i == '.':
            temp += round(size / 10 * 3)
        elif i == '%':
            temp += round(size / 10 * 9.4)
        else:
            temp += size
    return result

async def draw_char_card(raw_data: dict, charUrl: str = None) -> str:
    img = Image.open(TEXT_PATH / '{}.png'.format(raw_data['avatarElement']))
    char_info_1 = Image.open(TEXT_PATH / 'char_info_1.png')
    char_imfo_mask = Image.open(TEXT_PATH / 'char_info_mask.png')

    based_w, based_h = 320, 1024
    if charUrl:
        char_img = Image.open(BytesIO(get(charUrl).content)).convert('RGBA')
    else:
        char_img = Image.open(GACHA_PATH / 'UI_Gacha_AvatarIcon_{}.png'.format(raw_data['avatarEnName'])) #角色图像

    # 确定图片的长宽
    w, h = char_img.size
    if (w, h) != (320, 1024):
        based_scale = '%.3f' % (based_w / based_h)
        scale_f = '%.3f' % (w / h)
        new_w = math.ceil(based_h * float(scale_f))
        new_h = math.ceil(based_w / float(scale_f))
        if scale_f > based_scale:
            bg_img2 = char_img.resize((new_w, based_h), Image.Resampling.LANCZOS)
            char_img = bg_img2.crop((new_w/2 - 160, 0, new_w/2 + 160, based_h))
        else:
            bg_img2 = char_img.resize((based_w, new_h), Image.Resampling.LANCZOS)
            char_img = bg_img2.crop((0, new_h/2 - 512, based_w, new_h/2 + 512))
    else:
        pass
    
    img_temp = Image.new('RGBA', (320, 1024), (0,0,0,0))
    img_temp.paste(char_img,(0,0),char_imfo_mask)
    img.paste(img_temp, (41, 29), img_temp)
    img.paste(char_info_1, (0, 0), char_info_1)

    #holo_img = Image.open(TEXT_PATH / 'icon_holo.png')
    #skill_holo_img = Image.open(TEXT_PATH / 'skillHolo.png')
    lock_img = Image.open(TEXT_PATH / 'icon_lock.png')

    #color_soild = Image.new('RGBA', (950, 1850), COLOR_MAP[raw_data['avatarElement']])
    #img.paste(color_soild, (0, 0), skill_holo_img)

    #color_holo_img = Image.new('RGBA', (100, 100), COLOR_MAP[raw_data['avatarElement']])

    # 命座处理
    for talent_num in range(0,6):
        if talent_num + 1 <= len(raw_data['talentList']):
            talent = raw_data['talentList'][talent_num]
            #img.paste(color_holo_img, (13,270 + talent_num * 66), holo_img)
            talent_img = Image.open(ICON_PATH / '{}.png'.format(talent['talentIcon']))
            talent_img_new = talent_img.resize((50, 50), Image.Resampling.LANCZOS).convert("RGBA")
            img.paste(talent_img_new, (850, 375 + talent_num * 81), talent_img_new)
        else:
            img.paste(lock_img, (850, 375 + talent_num * 81), lock_img)

    # 天赋处理
    skillList = raw_data['avatarSkill']
    a_skill_name = skillList[0]['skillName'].replace('普通攻击·','')
    a_skill_level = skillList[0]['skillLevel']
    e_skill_name = skillList[1]['skillName']
    e_skill_level = skillList[1]['skillLevel']
    q_skill_name = skillList[-1]['skillName']
    q_skill_level = skillList[-1]['skillLevel']
    for skill_num, skill in enumerate(skillList[0:2]+[skillList[-1]]):
        skill_img = Image.open(ICON_PATH / '{}.png'.format(skill['skillIcon']))
        skill_img_new = skill_img.resize((50, 50), Image.Resampling.LANCZOS).convert("RGBA")
        img.paste(skill_img_new, (78, 756 + 101 * skill_num), skill_img_new)

    # 武器部分
    weapon_img = Image.open(TEXT_PATH / 'char_info_weapon.png')
    weapon_star_img = get_star_png(raw_data['weaponInfo']['weaponStar'])
    weaponName = raw_data['weaponInfo']['weaponName']

    weaponAtk = raw_data['weaponInfo']['weaponStats'][0]['statValue']
    weaponLevel = raw_data['weaponInfo']['weaponLevel']
    weaponAffix = raw_data['weaponInfo']['weaponAffix']
    weaponEffect = raw_data['weaponInfo']['weaponEffect']
    weapon_type = raw_data['weaponInfo']['weaponType']

    weapon_img.paste(weapon_star_img, (25,235), weapon_star_img)
    weapon_text = ImageDraw.Draw(weapon_img)
    weapon_text.text((35, 80), weaponName, (255, 255, 255), genshin_font_origin(50), anchor='lm')
    weapon_text.text((35, 120), weapon_type, (255, 255, 255), genshin_font_origin(20), anchor='lm')
    weapon_text.text((35, 160), '基础攻击力', (255, 255, 255), genshin_font_origin(32), anchor='lm')
    weapon_text.text((368, 160), str(weaponAtk), (255, 255, 255), genshin_font_origin(32), anchor='rm')
    if len(raw_data['weaponInfo']['weaponStats']) == 2:
        weapon_sub_info = raw_data['weaponInfo']['weaponStats'][1]['statName']
        weapon_sub_value = raw_data['weaponInfo']['weaponStats'][1]['statValue']
        weapon_text.text((35, 211), weapon_sub_info, (255, 255, 255), genshin_font_origin(32), anchor='lm')
        weapon_text.text((368, 211), str(weapon_sub_value), (255, 255, 255), genshin_font_origin(32), anchor='rm')
    else:
        weapon_text.text((35, 211), '该武器无副词条', (255, 255, 255), genshin_font_origin(32), anchor='lm')
    weapon_text.text((73, 303), f'Lv.{weaponLevel}', (255, 255, 255), genshin_font_origin(28), anchor='mm')
    weapon_text.text((130, 305), f'精炼{str(weaponAffix)}阶', (255, 239, 173), genshin_font_origin(28), anchor='lm')

    weaponEffect = strLenth(weaponEffect, 25, 455)
    weapon_text.text((25, 335), weaponEffect, (255, 255, 255), genshin_font_origin(25))
    img.paste(weapon_img, (387, 570), weapon_img)

    # 圣遗物部分
    artifactsAllScore = 0
    for aritifact in raw_data['equipList']:
        artifacts_img = Image.open(TEXT_PATH / 'char_info_artifacts.png')
        artifacts_piece_img = Image.open(RELIC_PATH / '{}.png'.format(aritifact['icon']))
        artifacts_piece_new_img = artifacts_piece_img.resize((180, 180), Image.Resampling.LANCZOS).convert("RGBA")
        artifacts_piece_new_img.putalpha(artifacts_piece_new_img.getchannel('A').point(lambda x: round(x * 0.5) if x > 0 else 0))
        
        artifacts_img.paste(artifacts_piece_new_img, (100, 35), artifacts_piece_new_img)
        aritifactStar_img = get_star_png(aritifact['aritifactStar'])
        artifactsPos = aritifact['aritifactPieceName']

        artifacts_img.paste(aritifactStar_img, (20, 165), aritifactStar_img)
        artifacts_text = ImageDraw.Draw(artifacts_img)
        artifacts_text.text((30, 66), aritifact['aritifactName'], (255, 255, 255), genshin_font_origin(34), anchor='lm')
        artifacts_text.text((30, 102), artifactsPos, (255, 255, 255), genshin_font_origin(20), anchor='lm')

        mainValue = aritifact['reliquaryMainstat']['statValue']
        mainName = aritifact['reliquaryMainstat']['statName']
        mainLevel = aritifact['aritifactLevel']

        if mainName in ['攻击力', '血量', '防御力', '元素精通']:
            mainValueStr = str(mainValue)
        else:
            mainValueStr = str(mainValue) + '%'

        mainNameNew = mainName.replace('百分比','')

        artifacts_text.text((26, 140), mainNameNew, (255, 255, 255), genshin_font_origin(28), anchor='lm')
        artifacts_text.text((268, 140), mainValueStr, (255, 255, 255), genshin_font_origin(28), anchor='rm')
        artifacts_text.text((55, 219), '+{}'.format(str(mainLevel)), (255, 255, 255), genshin_font_origin(24), anchor='mm')

        artifactsScore = 0
        for index,i in enumerate(aritifact['reliquarySubstats']):
            subName = i['statName']
            subValue = i['statValue']
            if subName in ['攻击力', '血量', '防御力', '元素精通']:
                subValueStr = str(subValue)
                if subName == '血量':
                    artifactsScore += subValue * 0.014
                elif subName == '攻击力':
                    artifactsScore += subValue * 0.12
                elif subName == '防御力':
                    artifactsScore += subValue * 0.18
                elif subName == '元素精通':
                    artifactsScore += subValue * 0.25
            else:
                subValueStr = str(subValue) + '%'
                if subName == '暴击率':
                    artifactsScore += subValue * 2
                elif subName == '暴击伤害':
                    artifactsScore += subValue * 1
                elif subName == '元素精通':
                    artifactsScore += subValue * 0.25
                elif subName == '元素充能效率':
                    artifactsScore += subValue * 0.65
                elif subName == '百分比血量':
                    artifactsScore += subValue * 0.86
                elif subName == '百分比攻击力':
                    artifactsScore += subValue * 1
                elif subName == '百分比防御力':
                    artifactsScore += subValue * 0.7
            artifacts_text.text((20, 263 + index*30), '·{}+{}'.format(subName, subValueStr), (255, 255, 255), genshin_font_origin(25), anchor='lm')
        artifactsAllScore += artifactsScore
        artifacts_text.text((268, 190), f'{math.ceil(artifactsScore)}分', (255, 255, 255), genshin_font_origin(23), anchor='rm')
            
        if artifactsPos == '生之花':
            img.paste(artifacts_img, (18, 1075), artifacts_img)
        elif artifactsPos == '死之羽':
            img.paste(artifacts_img, (318, 1075), artifacts_img)
        elif artifactsPos == '时之沙':
            img.paste(artifacts_img, (618, 1075), artifacts_img)
        elif artifactsPos == '空之杯':
            img.paste(artifacts_img, (18, 1447), artifacts_img)
        elif artifactsPos == '理之冠':
            img.paste(artifacts_img, (318, 1447), artifacts_img)

    char_name = raw_data['avatarName']
    char_level = raw_data['avatarLevel']
    char_fetter = raw_data['avatarFetter']

    # 评分算法
    # 圣遗物总分 + 角色等级 + (a+e+q)*4 + 武器等级 * （ 1+（武器精炼数 -1） * 0.25）
    charAllScore = artifactsAllScore + int(char_level) + \
                     (a_skill_level + e_skill_level + q_skill_level) * 4 + \
                     int(weaponLevel) * (1 + ((int(weaponAffix) - 1) * 0.25))

    # 角色基本信息
    img_text = ImageDraw.Draw(img)
    img_text.text((411, 72), char_name, (255, 255, 255), genshin_font_origin(55), anchor='lm')
    img_text.text((411, 122), '等级{}'.format(char_level), (255, 255, 255), genshin_font_origin(40), anchor='lm')
    img_text.text((747, 126), str(char_fetter), (255, 255, 255), genshin_font_origin(28), anchor='lm')
    
    # aeq
    #img_text.text((110, 771), a_skill_name, (255, 255, 255), genshin_font_origin(26), anchor='lm')
    img_text.text((103, 812), f'{str(a_skill_level)}', (255, 255, 255), genshin_font_origin(30), anchor='mm')

    #img_text.text((110, 872), e_skill_name, (255, 255, 255), genshin_font_origin(26), anchor='lm')
    img_text.text((103, 915), f'{str(e_skill_level)}', (255, 255, 255), genshin_font_origin(30), anchor='mm')

    #img_text.text((110, 973), q_skill_name, (255, 255, 255), genshin_font_origin(26), anchor='lm')
    img_text.text((103, 1016), f'{str(q_skill_level)}', (255, 255, 255), genshin_font_origin(30), anchor='mm')


    fight_prop = raw_data['avatarFightProp']
    hp = fight_prop['hp']
    attack = fight_prop['atk']
    defense = fight_prop['def']
    em = fight_prop['elementalMastery']
    critrate = fight_prop['critRate']
    critdmg = fight_prop['critDmg']
    ce = fight_prop['energyRecharge']
    dmgBonus = fight_prop['dmgBonus']

    hp_green = fight_prop['addHp']
    attack_green = fight_prop['addAtk']
    defense_green = fight_prop['addDef']

    # 属性
    img_text.text((785, 174), str(round(hp)), (255, 255, 255), genshin_font_origin(28), anchor='rm')
    img_text.text((785, 227), str(round(attack)), (255, 255, 255), genshin_font_origin(28), anchor='rm')
    img_text.text((785, 280), str(round(defense)), (255, 255, 255), genshin_font_origin(28), anchor='rm')
    img_text.text((785, 333), str(round(em)), (255, 255, 255), genshin_font_origin(28), anchor='rm')
    img_text.text((785, 386), f'{str(round(critrate*100,2))}%', (255, 255, 255), genshin_font_origin(28), anchor='rm')
    img_text.text((785, 439), f'{str(round(critdmg*100,2))}%', (255, 255, 255), genshin_font_origin(28), anchor='rm')
    img_text.text((785, 492), f'{str(round(ce*100,1))}%', (255, 255, 255), genshin_font_origin(28), anchor='rm')
    img_text.text((785, 545), f'{str(round(dmgBonus*100,1))}%', (255, 255, 255), genshin_font_origin(28), anchor='rm')

    img_text.text((805, 174), f'(+{str(round(hp_green))})', (95, 251, 80), genshin_font_origin(28), anchor='lm')
    img_text.text((805, 227), f'(+{str(round(attack_green))})', (95, 251, 80), genshin_font_origin(28), anchor='lm')
    img_text.text((805, 280), f'(+{str(round(defense_green))})', (95, 251, 80), genshin_font_origin(28), anchor='lm')

    uid = raw_data['playerUid']
    data_time = raw_data['dataTime']
    # uid
    img_text.text((350, 1035), f'UID{uid}', (255, 255, 255), genshin_font_origin(24), anchor='rm')

    # 数据最后更新时间
    img_text.text((780, 600), f'数据最后更新于{data_time}', (255, 255, 255), genshin_font_origin(22), anchor='rm')

    # 角色评分
    img_text.text((904, 1505), f'圣遗物总分', (255, 255, 255), genshin_font_origin(45), anchor='rm')
    img_text.text((904, 1570), f'{round(artifactsAllScore, 1)}', (255, 255, 255), genshin_font_origin(60), anchor='rm')

    img_text.text((904, 1655), f'角色评分', (255, 255, 255), genshin_font_origin(45), anchor='rm')
    img_text.text((904, 1720), f'{round(charAllScore, 1)}', (255, 255, 255), genshin_font_origin(60), anchor='rm')

    img = img.convert('RGB')
    result_buffer = BytesIO()
    img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    resultmes = imgmes
    return resultmes
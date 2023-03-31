from pathlib import Path

from PIL import Image

path = Path(__file__).parent

REF = {
    '冰': {
        '申鹤': 3,
        '神里绫华': 2,
        '优菈': 3,
        '甘雨': 7.1,
        '凯亚': 2,
        '重云': 2,
        '七七': 3,
        '迪奥娜': 1,
        '罗莎莉亚': 1,
        '埃洛伊': 1,
        '莱依拉': 1,
        '米卡': 2,
    },
    '草': {'艾尔海森': 3, '瑶瑶': 2, '纳西妲': 4, '提纳里': 4, '柯莱': 4, '旅行者草': 3},
    '风': {
        '流浪者': 3,
        '珐露珊': 2,
        '鹿野院平藏': 3,
        '早柚': 2,
        '枫原万叶': 3,
        '魈': 3,
        '温迪': 3,
        '琴': 3,
        '砂糖': 3,
        '旅行者风': 1,
    },
    '火': {
        '迪希雅': 4,
        '胡桃': 8.2,
        '托马': 2,
        '宵宫': 2,
        '烟绯': 2,
        '可莉': 2,
        '迪卢克': 2,
        '辛焱': 4,
        '安柏': 2,
        '香菱': 6,
        '班尼特': 4,
    },
    '雷': {
        '赛诺': 6,
        '八重神子': 4,
        '雷电将军': 2,
        '九条裟罗': 2,
        '刻晴': 3,
        '雷泽': 2,
        '菲谢尔': 2,
        '丽莎': 2,
        '北斗': 2,
        '旅行者雷': 1,
        '久岐忍': 3,
        '多莉': 3,
    },
    '水': {
        '妮露': 4,
        '坎蒂丝': 3,
        '夜兰': 4,
        '神里绫人': 3,
        '珊瑚宫心海': 4,
        '达达利亚': 4,
        '行秋': 2,
        '莫娜': 3,
        '芭芭拉': 3,
    },
    '岩': {
        '荒泷一斗': 3,
        '五郎': 1,
        '阿贝多': 4,
        '钟离': 3,
        '诺艾尔': 3,
        '凝光': 3,
        '旅行者岩': 3,
        '云堇': 2,
    },
}


for ELE in REF:
    TITLE = 110
    SIG = 197
    END = 31
    _path = path / f'{ELE}.jpg'
    if not _path.exists():
        continue
    image = Image.open(_path)

    if ELE == '草':
        _MOV = 65
    elif ELE == '火':
        _MOV = 45
    elif ELE == '风':
        SIG = 195
        _MOV = 5
    elif ELE == '岩':
        SIG = 188
        _MOV = 35
    else:
        _MOV = 20

    for index, CHAR in enumerate(REF[ELE]):
        intent = REF[ELE][CHAR]
        if isinstance(intent, float):
            _seg = 2
            if str(intent).split('.')[-1].endswith('2'):
                without = 20
            else:
                without = 55
            intent = round(intent)
        else:
            _seg = 1
            without = 0

        if index == 0:
            refix = 0
        else:
            refix = 10

        MOVE = TITLE * _seg + SIG * intent + END + without
        area = (0, _MOV - refix, 1080, MOVE + _MOV)
        print(area)
        char_img = image.crop(area)
        _MOV += MOVE
        char_img.save(path / f'{CHAR}.jpg')

import json
from pathlib import Path

path = Path(__file__).parent
with open(path / 'all_achi.json', "r", encoding='UTF-8') as f:
    all_achi = json.load(f)

with open(path / 'daily_achi.json', "r", encoding='UTF-8') as f:
    daily_achi = json.load(f)

daily_template = '''任务：【{}】
成就：【{}】
描述：【{}】
攻略：【{}】
'''

achi_template = '''合辑：【{}】
成就：【{}】
描述：【{}】
'''

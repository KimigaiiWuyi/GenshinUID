import hoshino
from hoshino import Service

sv = Service('genshinuidv4', bundle='genshin', help_='发送"原神帮助"查看详情')
hoshino_bot = hoshino.get_bot()
logger = sv.logger

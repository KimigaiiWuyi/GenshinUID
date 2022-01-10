import re,os,random,datetime,math
import time,json,hashlib,base64
import httpx
from bs4 import BeautifulSoup
from httpx import AsyncClient
import urllib.parse

def md5(text):
    md5 = hashlib.md5()
    md5.update(text.encode())
    return md5.hexdigest()

def DSGet(q = "",b = None):
    if b:
        br = json.dumps(b)
    else:
        br = ""
    s = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = md5("salt=" + s + "&t=" + t + "&r=" + r + "&b=" + br + "&q=" + q)
    return t + "," + r + "," + c

async def GetUidPic(raw_data,uid,qid,nickname):
    style = "egenshin"
    url = "https://yuanshen.minigg.cn/generator/user_info?style=" + style + "&uid=" + uid + "&qid=" + qid + "&nickname=" + urllib.parse.quote(nickname) +"&quality=75"
    async with AsyncClient() as client:
        req = await client.post(
            url = url,
            json = raw_data
        )
    return req.text

async def GetInfo(Uid,ck,ServerID="cn_gf01"):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/index?role_id=" + Uid + "&server=" + ServerID,
                headers={
                    'DS': DSGet("role_id=" + Uid + "&server=" + ServerID),
                    'x-rpc-app_version': "2.11.1",
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/',
                    "Cookie": ck})
            data = json.loads(req.text)
        return data
    except Exception as e:
        print(e.with_traceback)
        print("访问失败，请重试！")

async def GetMysInfo(mysid,ck):
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi-record.mihoyo.com/game_record/card/wapi/getGameRecordCard?uid=" + mysid,
                headers={
                    'DS': DSGet("uid="+mysid),
                    'x-rpc-app_version': "2.11.1",
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/',
                    "Cookie": ck})
            data = json.loads(req.text)
        return data
    except Exception as e:
        print(e.with_traceback)
        im = "err，获取米游社信息失败，请重试！"
        return im

async def GetWeaponInfo(name,level = None):
    async with AsyncClient() as client:
        req = await client.get(
            url="https://api.minigg.cn/weapons?query=" + name + "&stats=" + level if level else "https://api.minigg.cn/weapons?query=" + name,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                'Referer': 'https://genshin.minigg.cn/index.html'})
        data = jsonfy(req.text)
    return data

async def GetCharInfo(name,mode = "char",level = None):
    url2 = None
    data2 = None
    baseurl = "https://api.minigg.cn/characters?query="
    if mode == "talents":
        url = "https://api.minigg.cn/talents?query=" + name
    elif mode == "constellations":
        url = "https://api.minigg.cn/constellations?query=" + name
    elif mode == "costs":
        url = baseurl + name + "&costs=1"
        url2 = "https://api.minigg.cn/talents?query=" + name + "&costs=1"
    elif level:
        url = baseurl + name + "&stats=" + level
    else:
        url = baseurl + name

    if url2:
        async with AsyncClient() as client:
            req = await client.get(
                url = url2,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                    'Referer': 'https://genshin.minigg.cn/index.html'})
            data2 = jsonfy(req.text)

    async with AsyncClient() as client:
            req = await client.get(
                url = url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                    'Referer': 'https://genshin.minigg.cn/index.html'})
            data = jsonfy(req.text)
    
    if data != "undefined":
        pass
    else:
        async with AsyncClient() as client:
            req = await client.get(
                url = baseurl + name + "&matchCategories=true",
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                    'Referer': 'https://genshin.minigg.cn/index.html'})
            data = req.text

    return data if data2 == None else [data,data2]

async def GetAudioInfo(name,audioid,language = "cn"):
    url = "https://genshin.minigg.cn/?characters=" + name + "&audioid=" + audioid + "&language=" + language
    async with AsyncClient() as client:
        req = await client.get(
            url=url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                'Referer': 'https://genshin.minigg.cn/index.html'})
    return req.text

async def GetGenshinEvent(mode = "List"):
    if mode == "Calendar":
        now_time = datetime.datetime.now().strftime('%Y-%m-%d')
        base_url = "https://api-takumi.mihoyo.com/event/bbs_activity_calendar/getActList?time={}&game_biz=ys_cn&page=1&tag_id=0".format(now_time)
    else:
        base_url = "https://hk4e-api.mihoyo.com/common/hk4e_cn/announcement/api/getAnn" + mode + "?game=hk4e&game_biz=hk4e_cn&lang=zh-cn&bundle_id=hk4e_cn&platform=pc&region=cn_gf01&level=55&uid=100000000"
    
    async with AsyncClient() as client:
        req = await client.get(
            url = base_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'})
        data = json.loads(req.text)
    return data

def jsonfy(s:str)->object:
    #此函数将不带双引号的json的key标准化
    s = s.replace("stats: [Function (anonymous)]","")
    obj = eval(s, type('js', (dict,), dict(__getitem__=lambda s, n: n))())
    return obj
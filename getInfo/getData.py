import re,os,random,datetime,math,traceback,string
import time,json,hashlib,base64
from bs4 import BeautifulSoup
from httpx import AsyncClient
import urllib.parse

from .getDB import OwnerCookies

mhyVersion = "2.11.1"

def random_hex(length):
    result = hex(random.randint(0,16**length)).replace('0x','').upper()
    if len(result)<length:
        result = "0"*(length-len(result))+result
    return result

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

def oldDSGet():
    n = "h8w582wxwgqvahcdkpvdhbh2w9casgfl"
    i = str(int(time.time()))
    r = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
    c = md5("salt=" + n + "&t=" + i + "&r=" + r)
    return (i + "," + r + "," + c)

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
        traceback.print_exc()
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
        traceback.print_exc()
        im = "err，获取米游社信息失败，请重试！"
        return im

async def GetAward(Uid,ServerID="cn_gf01"):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://hk4e-api.mihoyo.com/event/ys_ledger/monthInfo?month={}&bind_uid={}&bind_region={}&bbs_presentation_style=fullscreen&bbs_auth_required=true&utm_source=bbs&utm_medium=mys&utm_campaign=icon".format("0",Uid,ServerID),
                headers={
                    'x-rpc-app_version': mhyVersion,
                    "Cookie": await OwnerCookies(Uid),
                    'DS': oldDSGet(),
                    "x-rpc-device_id":random_hex(32),
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/'})
            data = json.loads(req.text)
        return data
    except:
        traceback.print_exc()

async def GetDaily(Uid,ServerID="cn_gf01"):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/app/genshin/api/dailyNote?server=" + ServerID + "&role_id=" + Uid,
                headers={
                    'DS': DSGet("role_id=" + Uid + "&server=" + ServerID),
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/',
                    "Cookie": await OwnerCookies(Uid)})
            data = json.loads(req.text)
            #print(data)
        return data
    except requests.exceptions.SSLError:
        try:
            async with AsyncClient() as client:
                req = await client.get(
                    url="https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/dailyNote?server=" + ServerID + "&role_id=" + Uid,
                    headers={
                        'DS': DSGet("role_id=" + Uid + "&server=" + ServerID),
                        'x-rpc-app_version': mhyVersion,
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                        'x-rpc-client_type': '5',
                        'Referer': 'https://webstatic.mihoyo.com/',
                        "Cookie": await OwnerCookies(Uid)})
            data = json.loads(req.text)
            return data
        except json.decoder.JSONDecodeError:
            print("当前状态读取Api失败！")
    except Exception as e:
        print("访问每日信息失败，请重试！")
        print(e.with_traceback)

async def GetSignList():
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/event/bbs_sign_reward/home?act_id=e202009291139501",
                headers={
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/'})
            data = json.loads(req.text)
        return data
    except:
        print("获取签到奖励列表失败，请重试")

async def GetSignInfo(Uid,ServerID="cn_gf01"):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/event/bbs_sign_reward/info?act_id=e202009291139501&region=" + ServerID + "&uid=" + Uid,
                headers={
                    'x-rpc-app_version': mhyVersion,
                    "Cookie": await OwnerCookies(Uid),
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/'})
            data = json.loads(req.text)
        return data
    except:
        print("获取签到信息失败，请重试")

async def MysSign(Uid,ServerID="cn_gf01"):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.post(
                url = "https://api-takumi.mihoyo.com/event/bbs_sign_reward/sign",
                headers={
                    'User_Agent': 'Mozilla/5.0 (Linux; Android 10; MIX 2 Build/QKQ1.190825.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.101 Mobile Safari/537.36 miHoYoBBS/2.3.0',
                    "Cookie": await OwnerCookies(Uid),
                    "x-rpc-device_id":random_hex(32),
                    'Origin': 'https://webstatic.mihoyo.com',
                    'X_Requested_With': 'com.mihoyo.hyperion',
                    'DS': oldDSGet(),
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html?bbs_auth_required=true&act_id=e202009291139501&utm_source=bbs&utm_medium=mys&utm_campaign=icon',
                    'x-rpc-app_version': '2.3.0'
                },
                json = {"act_id": "e202009291139501" ,"uid": Uid ,"region": ServerID}
            )
        data2 = json.loads(req.text)
        return data2
    except:
        traceback.print_exc()
        print("签到失败，请重试")
        
async def GetAudioInfo(name,audioid,language = "cn"):
    url = "https://bot.q.minigg.cn/audio/?characters=" + name + "&audioid=" + audioid + "&language=" + language
    return url

async def GetWeaponInfo(name,level = None):
    async with AsyncClient() as client:
        req = await client.get(
            url="https://info.minigg.cn/weapons?query=" + name + "&stats=" + level if level else "https://info.minigg.cn/weapons?query=" + name,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36'})
    data = json.loads(req.text)
    return data

async def GetMiscInfo(mode,name):
    url = "https://info.minigg.cn/{}?query={}".format(mode,urllib.parse.quote(name, safe=''))
    async with AsyncClient() as client:
        req = await client.get(
            url = url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'})
    data = json.loads(req.text)
    return data

async def GetCharInfo(name,mode = "char",level = None):
    url2 = None
    data2 = None
    baseurl = "https://info.minigg.cn/characters?query="
    if mode == "talents":
        url = "https://info.minigg.cn/talents?query=" + name
    elif mode == "constellations":
        url = "https://info.minigg.cn/constellations?query=" + name
    elif mode == "costs":
        url = baseurl + name + "&costs=1"
        url2 = "https://info.minigg.cn/talents?query=" + name + "&costs=1"
        url3 = "https://info.minigg.cn/talents?query=" + name + "&matchCategories=true"
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
            data2 = json.loads(req.text)
            if "errcode"  not in data2:
                pass
            else:
                async with AsyncClient() as client:
                    req = await client.get(
                        url = url3,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                            'Referer': 'https://genshin.minigg.cn/index.html'})
                    data2 = json.loads(req.text)

    async with AsyncClient() as client:
        req = await client.get(
            url = url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                'Referer': 'https://genshin.minigg.cn/index.html'})
        try:
            data = json.loads(req.text)
            if "errcode"  not in data:
                pass
            else:
                async with AsyncClient() as client:
                    req = await client.get(
                        url = url + "&matchCategories=true",
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                            'Referer': 'https://genshin.minigg.cn/index.html'})
                    data = json.loads(req.text)
        except:
            data = None
    return data if data2 == None else [data,data2]

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
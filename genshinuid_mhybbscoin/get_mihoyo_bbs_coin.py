import time
import random
import string
from copy import deepcopy

from httpx import AsyncClient
from nonebot.log import logger

from ..utils.mhy_api.mhy_api import *
from ..utils.mhy_api.mhy_api_tools import (
    random_hex,
    get_ds_token,
    old_version_get_ds_token,
)

mihoyobbs_List = [
    {
        'id': '1',
        'forumId': '1',
        'name': '崩坏3',
        'url': 'https://bbs.mihoyo.com/bh3/',
    },
    {
        'id': '2',
        'forumId': '26',
        'name': '原神',
        'url': 'https://bbs.mihoyo.com/ys/',
    },
    {
        'id': '3',
        'forumId': '30',
        'name': '崩坏2',
        'url': 'https://bbs.mihoyo.com/bh2/',
    },
    {
        'id': '4',
        'forumId': '37',
        'name': '未定事件簿',
        'url': 'https://bbs.mihoyo.com/wd/',
    },
    {
        'id': '5',
        'forumId': '34',
        'name': '大别野',
        'url': 'https://bbs.mihoyo.com/dby/',
    },
    {
        'id': '6',
        'forumId': '52',
        'name': '崩坏：星穹铁道',
        'url': 'https://bbs.mihoyo.com/sr/',
    },
]


def random_text(num: int) -> str:
    return ''.join(random.sample(string.ascii_lowercase + string.digits, num))


class MihoyoBBSCoin:
    def __init__(self, cookies):
        self.postsList = []
        self.headers = {
            'DS': old_version_get_ds_token(),
            'cookie': cookies,
            'x-rpc-client_type': '2',
            'x-rpc-app_version': '2.34.1',
            'x-rpc-sys_version': '6.0.1',
            'x-rpc-channel': 'miyousheluodi',
            'x-rpc-device_id': random_hex(32),
            'x-rpc-device_name': random_text(random.randint(1, 10)),
            'x-rpc-device_model': 'Mi 10',
            'Referer': 'https://app.mihoyo.com',
            'Host': 'bbs-api.mihoyo.com',
            'User-Agent': 'okhttp/4.8.0',
        }
        self.Task_do = {
            'bbs_Sign': False,
            'bbs_Read_posts': False,
            'bbs_Read_posts_num': 3,
            'bbs_Like_posts': False,
            'bbs_Like_posts_num': 5,
            'bbs_Share': False,
        }
        self.mihoyobbs_List_Use = []
        self.Today_getcoins = 0
        self.Today_have_getcoins = 0  # 这个变量以后可能会用上，先留着了
        self.Have_coins = 0

    async def task_run(self):
        await self.load_mihoyo_bbs_list_use()
        start = await self.get_tasks_list()
        self.postsList = await self.get_list()
        sign = await self.signing()
        read = await self.read_posts()
        like = await self.like_posts()
        share = await self.share_post()
        if start and sign and read and like and share:
            im = '\n'.join([start, sign, read, like, share])
            return im
        else:
            return '米游社币任务执行出错了~'

    async def load_mihoyo_bbs_list_use(self):
        for i in [2, 5]:
            for k in mihoyobbs_List:
                if i == int(k['id']):
                    self.mihoyobbs_List_Use.append(k)

    # 获取任务列表，用来判断做了哪些任务
    async def get_tasks_list(self):
        logger.info('正在获取任务列表')
        async with AsyncClient() as client:
            req = await client.get(url=bbs_Taskslist, headers=self.headers)
        data = req.json()
        if 'err' in data['message'] or data['retcode'] == -100:
            logger.error('获取任务列表失败，你的cookie可能已过期，请重新设置cookie。')
            return '你的Cookies已失效。'
        else:
            self.Today_getcoins = data['data']['can_get_points']
            self.Today_have_getcoins = data['data']['already_received_points']
            self.Have_coins = data['data']['total_points']
            # 如果当日可获取米游币数量为0直接判断全部任务都完成了
            if self.Today_getcoins == 0:
                self.Task_do['bbs_Sign'] = True
                self.Task_do['bbs_Read_posts'] = True
                self.Task_do['bbs_Like_posts'] = True
                self.Task_do['bbs_Share'] = True
            else:
                # 如果第0个大于或等于62则直接判定任务没做
                if data['data']['states'][0]['mission_id'] >= 62:
                    logger.info(f'新的一天，今天可以获得{self.Today_getcoins}个米游币')
                    pass
                else:
                    logger.info(f'似乎还有任务没完成，今天还能获得{self.Today_getcoins}')
                    for i in data['data']['states']:
                        # 58是讨论区签到
                        if i['mission_id'] == 58:
                            if i['is_get_award']:
                                self.Task_do['bbs_Sign'] = True
                        # 59是看帖子
                        elif i['mission_id'] == 59:
                            if i['is_get_award']:
                                self.Task_do['bbs_Read_posts'] = True
                            else:
                                self.Task_do['bbs_Read_posts_num'] -= i[
                                    'happened_times'
                                ]
                        # 60是给帖子点赞
                        elif i['mission_id'] == 60:
                            if i['is_get_award']:
                                self.Task_do['bbs_Like_posts'] = True
                            else:
                                self.Task_do['bbs_Like_posts_num'] -= i[
                                    'happened_times'
                                ]
                        # 61是分享帖子
                        elif i['mission_id'] == 61:
                            if i['is_get_award']:
                                self.Task_do['bbs_Share'] = True
                                # 分享帖子，是最后一个任务，到这里了下面都是一次性任务，直接跳出循环
                                break
            return '今日完成情况!'

    # 获取要帖子列表
    async def get_list(self) -> list:
        temp_list = []
        logger.info('正在获取帖子列表......')
        async with AsyncClient() as client:
            req = await client.get(
                url=bbs_Listurl.format(self.mihoyobbs_List_Use[0]['forumId']),
                headers=self.headers,
            )
        data = req.json()
        for n in range(5):
            temp_list.append(
                [
                    data['data']['list'][n]['post']['post_id'],
                    data['data']['list'][n]['post']['subject'],
                ]
            )
        logger.info('已获取{}个帖子'.format(len(temp_list)))
        return temp_list

    # 进行签到操作
    async def signing(self):
        if self.Task_do['bbs_Sign']:
            return '讨论区任务已经完成过了~'
        else:
            header = deepcopy(self.headers)
            for i in self.mihoyobbs_List_Use:
                header['DS'] = get_ds_token(
                    '', {'gids': i['id']}, 't0qEgfub6cvueAPgR5m9aQWWVciEer7v'
                )
                async with AsyncClient() as client:
                    req = await client.post(
                        url=bbs_Signurl,
                        json={'gids': i['id']},
                        headers=header,
                    )
                data = req.json()
                if 'err' not in data['message']:
                    time.sleep(random.randint(2, 8))
                else:
                    return '你的Cookies已失效。'
            return 'SignM:完成!'

    # 看帖子
    async def read_posts(self):
        if self.Task_do['bbs_Read_posts']:
            return '看帖任务已经完成过了~'
        else:
            num_ok = 0
            for i in range(self.Task_do['bbs_Read_posts_num']):
                async with AsyncClient() as client:
                    req = await client.get(
                        url=bbs_Detailurl.format(self.postsList[i][0]),
                        headers=self.headers,
                    )
                data = req.json()
                if data['message'] == 'OK':
                    num_ok += 1
                time.sleep(random.randint(2, 8))
            return 'ReadM:成功!Read:{}!'.format(str(num_ok))

    # 点赞
    async def like_posts(self):
        if self.Task_do['bbs_Like_posts']:
            return 'Like任务已经完成过了~'
        else:
            num_ok = 0
            num_cancel = 0
            for i in range(self.Task_do['bbs_Like_posts_num']):
                async with AsyncClient() as client:
                    req = await client.post(
                        url=bbs_Likeurl,
                        headers=self.headers,
                        json={
                            'post_id': self.postsList[i][0],
                            'is_cancel': False,
                        },
                    )
                data = req.json()
                if data['message'] == 'OK':
                    num_ok += 1
                # 判断取消点赞是否打开
                if True:
                    time.sleep(random.randint(2, 8))
                    async with AsyncClient() as client:
                        req = await client.post(
                            url=bbs_Likeurl,
                            headers=self.headers,
                            json={
                                'post_id': self.postsList[i][0],
                                'is_cancel': True,
                            },
                        )
                    data = req.json()
                    if data['message'] == 'OK':
                        num_cancel += 1
                time.sleep(random.randint(2, 8))
            return 'LikeM:完成!like:{}，dislike:{}!'.format(
                str(num_ok), str(num_cancel)
            )
            # 分享操作

    async def share_post(self):
        if self.Task_do['bbs_Share']:
            return '分享任务已经完成过了~'
        else:
            for _ in range(3):
                async with AsyncClient() as client:
                    req = await client.get(
                        url=bbs_Shareurl.format(self.postsList[0][0]),
                        headers=self.headers,
                    )
                data = req.json()
                if data['message'] == 'OK':
                    return 'ShareM:完成!'
                else:
                    time.sleep(random.randint(2, 8))
            time.sleep(random.randint(2, 8))

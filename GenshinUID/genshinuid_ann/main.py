import httpx

from .util import Dict, black_ids, filter_list, cache_request_json

# https://webstatic.mihoyo.com/hk4e/announcement/index.html?auth_appid=announcement&authkey_ver=1&bundle_id=hk4e_cn&channel_id=1&game=hk4e&game_biz=hk4e_cn&lang=zh-cn&level=57&platform=pc&region=cn_gf01&sdk_presentation_style=fullscreen&sdk_screen_transparent=true&sign_type=2&uid=105293904#/
api_url = 'https://hk4e-api-static.mihoyo.com/common/hk4e_cn/announcement/api/'
api_params = (
    '?game=hk4e'
    '&game_biz=hk4e_cn'
    '&lang=zh-cn'
    '&bundle_id=hk4e_cn'
    '&level=57'
    '&platform={platform}'
    '&region={region}'
    '&uid={uid}'
)
ann_content_url = f'{api_url}getAnnContent{api_params}'
ann_list_url = f'{api_url}getAnnList{api_params}'


class ann:
    ann_list_data = []
    ann_content_data = []
    today = 0

    def __init__(self, platform='pc', uid='114514', region='cn_gf01'):
        # self.today = datetime.datetime.fromtimestamp(
        #     time.mktime(datetime.date.today().timetuple()))
        self.platform = platform
        self.uid = uid
        self.region = region

    async def get_ann_content(self):
        url = ann_content_url.format(
            platform=self.platform, uid=self.uid, region=self.region
        )
        res = await cache_request_json(url=url)
        if res.retcode == 0:
            self.ann_content_data = res.data.list
        return self.ann_content_data

    async def get_ann_list(self):
        url = ann_list_url.format(
            platform=self.platform, uid=self.uid, region=self.region
        )
        res = await cache_request_json(url=url)
        if res.retcode == 0:
            result = []
            for data in res.data.list:
                data_list = [
                    x for x in data['list'] if not x['ann_id'] in black_ids
                ]
                data['list'] = data_list
                result.append(data)

            self.ann_list_data = result
        return self.ann_list_data

    async def get_ann_ids(self):
        await self.get_ann_list()
        if not self.ann_list_data:
            return []
        ids = []
        for label in self.ann_list_data:
            ids += [x['ann_id'] for x in label['list']]
        return ids


async def get_consume_remind_ann_ids(region, platform, uid):
    ann_list = await ann(
        platform=platform, uid=uid, region=region
    ).get_ann_list()
    ids = []
    for label in ann_list:
        ids += filter_list(label.list, lambda x: x.remind == 1)
    return [x.ann_id for x in ids]


async def consume_remind(uid):
    region = 'cn_gf01'
    if uid[0] == "5":
        region = 'cn_qd01'
    platform = ['pc']
    ids = []
    for p in platform:
        ids += await get_consume_remind_ann_ids(region, p, uid)

    ids = set(ids)
    msg = f'取消公告红点完毕! 一共取消了{len(ids)}个'

    async with httpx.AsyncClient(
        base_url="https://hk4e-api.mihoyo.com/common/hk4e_cn/announcement/api"
    ) as client:
        for ann_id in ids:
            for p in platform:
                res = await client.get(
                    "/consumeRemind",
                    timeout=10,
                    params={
                        'ann_id': ann_id,
                        'auth_appid': 'announcement',
                        'authkey_ver': '1',
                        'bundle_id': 'hk4e_cn',
                        'channel_id': '1',
                        'game': 'hk4e',
                        'game_biz': 'hk4e_cn',
                        'lang': 'zh-cn',
                        'level': '57',
                        'platform': p,
                        'region': region,
                        'sdk_presentation_style': 'fullscreen',
                        'sdk_screen_transparent': 'true',
                        'sign_type': '2',
                        'uid': uid,
                    },
                )
                res = res.json(object_hook=Dict)
                if res.retcode != 0:
                    msg += '\n %s 失败,原因:%s' % (ann_id, res.message)
    return msg

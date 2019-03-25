import requests, re, json, time, cv2
from lxml import etree
from urllib.parse import urljoin, quote, unquote
from eic_utils import *
import numpy as np

tables = [{
        'name': 'code',
        'attr': [{
                'key': 'id',
                'db_type': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            }, {
                'key': 'title',
                'db_type': 'TEXT NOT NULL',
            }, {
                'key': 'time',
                'db_type': 'INTEGER',
            }, {
                'key': 'code',
                'db_type': 'TEXT NOT NULL',
            }, {
                'key': 'use',
                'db_type': 'INTEGER',
            }
        ],
    },
]

db = DataBase('data.db', tables=tables)


def load_headers(path):
    with open(path, 'r') as f:
        data = f.readlines()
    headers = {}
    for row in data:
        row = row.strip()
        x = row.find(':')
        if x == -1: continue
        headers[row[:x].strip()] = row[x+1:].strip()
    return headers

headers = load_headers('./headers.txt')

class Catcher(object):
    def __init__(self):
        self.re_wechat_url_in_sougou = re.compile(r'\'(http[^\']*?)\'')
        self.re_code = re.compile(r'<.*?rgb\([0-9]*, *[0-9]*, *[0-9]*\).*?>(.*?)</.*?>', re.S)
        self.re_tag = re.compile(r'<[^>]*>', re.S)
        self.re_code_pat = re.compile(r'^[0-9a-zA-Z]{8}$')
        pass

    def sougou(self):
        sougou_spider = requests.Session()
        sougou_spider.headers = headers
        sougou_url = 'https://weixin.sogou.com/weixin?query=%E7%8E%8B%E5%9B%BD%E7%BA%AA%E5%85%83'

        response = sougou_spider.get(sougou_url)
        response.encoding = 'utf-8'
        html = response.text

        xml = etree.HTML(html)
        lis = xml.xpath('//div[@class="news-box"]//li')
        for li in lis:
            wechat = li.xpath('.//p[@class="info"]/label/text()')[0]
            if wechat == 'lordsmobilecn':
                url = li.xpath('.//p[@class="tit"]//a/@href')[0]
                url = urljoin(response.url, url)
                response = sougou_spider.get(url)
                response.encoding = 'utf-8'
                html = response.text
                urls = self.re_wechat_url_in_sougou.findall(html)
                return urls[0]
        return None

    def code(self, wechat_spider, code_url):
        response = wechat_spider.get(code_url)
        response.encoding = 'utf-8'
        html = response.text

        codes = self.re_code.findall(html)
        for raw_code in codes:
            code = self.re_tag.sub('', raw_code).strip()
            if self.re_code_pat.match(code):
               return code

    def captcha_wechat(self, wechat_spider):
        timestamp = '{:3f}'.format(time.time()*1000)
        cert_code_url = 'http://mp.weixin.qq.com/mp/verifycode?cert={}'.format(timestamp)
        response = wechat_spider.get(cert_code_url)
        img = bytes_to_img(response.content)
        print(img_to_str(img, 170, 170))
        certcode = input('cert code: ')
        verify_url = 'http://mp.weixin.qq.com/mp/verifycode'
        data = {
            'cert': timestamp,
            'input': certcode,
            'appmsg_token': ''
        }
        response = wechat_spider.post(verify_url, data=data)


    def wechat(self, wechat_url):
        wechat_spider = requests.Session()
        wechat_spider.headers = headers
    
        latest = 0
        while True:
            response = wechat_spider.get(wechat_url)
            response.encoding = 'utf-8'
            html = response.text

            data = None
            for row in html.split('\n'):
                row = row.strip()
                if row.startswith('var msgList'):
                    data = row
                    break

            if data is None:
                self.captcha_wechat(wechat_spider)
                continue
        
            data = data[data.find('{'):-data[::-1].find('}')]

            publishes = json.loads(data)['list']
            for publish in publishes:
                details = publish['app_msg_ext_info']
                url = details['content_url']
                title = details['title']

                datetime = int(publish['comm_msg_info']['datetime'])

                latest = max(latest, datetime)

                if db.count('code', limitation={'title': title, 'time': datetime}) == 1:
                    continue
                
                url = urljoin(response.url, url.replace('&amp;', '&'))
                code = self.code(wechat_spider, url)

                db.add_row('code', data={'code': code, 'title': title, 'time': datetime, 'use': 0})
            break
        return latest


wechat_url = 'http://mp.weixin.qq.com/profile?src=3&timestamp=1553500917&ver=1&signature=CKpRMDe66-ZXcyIs-tonsnuqKTp8w3m-Q0Tiv9kNM*frV-9aGuztodXa3FYPnXjTdK*JX0f03HTccFiPlf*v0w=='

catcher = Catcher()
class Gift():

    def __init__(self, igg_id):
        self.igg_id = igg_id
        pass

    def post(self):
        igg_spider = requests.Session()
        igg_spider.headers = headers
        while True:
            codes = db.select('code', limitation={'use': 0}, keys=['id', 'code'])
            for code in codes:
                url = 'http://lordsmobile.igg.com/event/cdkey/ajax.php?game_id=1051089902'
                data = {
                    'ac': 'receive',
                    'type': '0',
                    'iggid': '{}'.format(self.igg_id),
                    'charname': '',
                    'cdkey': '{}'.format(code['code']),
                }
                response = igg_spider.post(url, data=data)
                ret = response.json()
                cp.log('(#b)data(##): (#y){}(##), (#b)ret(##): (#g){}(##)'.format(data, ret))

                if ret['succ'] == 1 or ret['msg'] == '礼包码不可用':
                    db.upd_row('code', limitation={'id': code['id']}, data={'use': 1})
            if len(codes) == 0: return


    def __call__(self,):
        latest = 0
        delay = 120
        while True:
            s = (time.time() + 8 * 3600) % 86400
            m, h = int(s % 3600 / 60), int(s / 3600)

            while h == 17 and m >= 28 and m <= 45:
                with procedure('catch wechat url from sougou', same_line=False):
                    wechat_url = catcher.sougou()
                with procedure('scan recent publishes', same_line=False):
                    latest = max(latest, catcher.wechat(wechat_url))
                with procedure('post code to igg', same_line=False):
                    self.post()

                s = (time.time() + 8 * 3600) % 86400
                m, h = int(s % 3600 / 60), int(s / 3600)

                if time.time() - latest > 3600:
                    cp.log('work finished at {}:{} :)'.format(h, m))
                    break
                cp.log('work not finished yet at {}:{}, check in {}s later :('.format(h, m, delay))
                time.sleep(120)

            cp.log('work checked at {}:{}, sleep for {}s zZZ'.format(h, m, delay))
            time.sleep(delay)


with open('config.json', 'r') as f:
    config = json.load(f)

gift = Gift(**config)
gift()



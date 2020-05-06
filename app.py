from flask import Flask, request
from itertools import cycle
from aiohttp import ClientSession
import re
import hashlib
import json
import asyncio
import time
import threading
import requests
app = Flask(__name__)
print(threading.current_thread().name)
proxy = cycle([
])
cookie = {}
# 这个url是访问主页面的url
url = ['https://uland.taobao.com/coupon/edetail?e=%2B%2B05maoVmjoGQASttHIRqaBGD5yeBX5iL34hvScNrL2kamxjBDUoNzdC6dt479FzlGfwXtWmS6mmY5Uhoj5R1Wjp926RHPMN4jYDACKRRghcpA3BvVwMOMHVq%2Fdxq%2FDATJnbK5InWznd4dRbTb5WN9VqM6BWlz381n7MM6p1XL5HTZI7gbiaB6ROb1xMOlEO9nFhblz1Gt8%3D&traceId=0b01fd3a15734097834532715e&union_lens=lensId:0b581b6f_0c08_16e5687feb9_a5c1&xId=jV6jKU9TccWDH5pKZGVP4Av37lEPBOMg1UQFl7yBj97Z9znKKiNL4xafr76NZVRSDPLcqSCkLh200fmVTnaDEW'] * 5
Cookie = '_m_h5_tk=f301d274ba60ecfbb53c14a34bd7e06d_1574684570511; _m_h5_tk_enc=37729bec07b4c0bcfb0ec6c87a9cfb5c; cna=EphiFnGyijwCAXc5JiZib9VB; t=50faa610684c78a38b57822aa50386ad; cookie2=5caa1d8f74b3edfeeb58fcc8406c41a2; _tb_token_=3b031ebe7e53; l=dBLBKRQqqVfU0LMxBOCNZQL1hL_tsIRAguSJCRv2i_5I46Ls_8_Okd4fQFp6cjWfTBYp47_ypVw9-etlwTMqWX-vXaLvkxDc.; isg=BMnJJFoD8KM9rYzXcfxdUyUf2PWPB7faqG3QuWs-RbDvsunEs2bNGLfg8BAE8VWA'.replace(' ', '')
headers = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Mobile Safari/537.36',
}
# 拼cookie
for c in Cookie.split(';'):
    a = c.split('=')
    cookie.update({
        a[0]: a[1]
    })


@app.route('/as', methods=['GET'])
def as_api():

    # urlList = get_url_list()
    # 这个URL是访问接口的URL
    print(threading.currentThread())
    URL = 'https://h5api.m.taobao.com/h5/mtop.alimama.union.xt.biz.quan.api.entry/1.0/'
    # 控制并发

    new_loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(new_loop)
    sem = asyncio.Semaphore(10, loop=new_loop)
    # loop = asyncio.get_event_loop()
    task = [asyncio.ensure_future(main(URL, i, sem), loop=new_loop) for i in url]
    new_loop.run_until_complete(asyncio.wait(task))
    new_loop.close()
    return 'hello'

#
# def get_url_list():
#     urlList = []
#     with open('uland.txt') as f:
#         for line in f.readlines():
#             urlList.append(line.strip('\n'))
#     return urlList


# md5加密
def get_md5_hash(string):
    m = hashlib.md5()
    m.update(string.encode())
    return m.hexdigest()


# sign是访问接口的必要参数
def make_sign(token, t, appk, data):
    return get_md5_hash(token+'&'+str(int(t))+'&'+appk+'&'+str(data))


# 请求主页面(用来获取请求接口的recover_id)
async def getMainPage(url):
    async with ClientSession() as session:
        async with session.get(url, headers=headers, proxy=next(proxy)) as res:
            return await res.text()


# 用来制作请求接口的必要参数: data
async def make_data(url, t):
    con = await getMainPage(url)
    p = 'window\.pvid="(.*?)_15'
    forlook = re.findall(p, con)
    recover_id = re.findall(p, con)[0]
    p = r'e=(.*?)&'
    e = re.findall(p, url)[0]
    p = r'union_lens=(.*?)&'
    union_lens = re.findall(p, url)[0]
    vamap = {
            'e': e,
            'type': 'nBuy',
            'union_lens': union_lens,
            'recoveryId': recover_id+'_'+str(int(t))
        }

    data = {
        'floorId': '13193',
        'variableMap': json.dumps(vamap, ensure_ascii=False)
    }
    return data


# 获取param来拼接完整的接口url
async def get_param(cookie, url):
    t = cookie['_m_h5_tk'].split('_')[1]
    appKey = '12574478'
    data = await make_data(url, t)
    data = json.dumps(data, ensure_ascii=False)
    token = cookie['_m_h5_tk'].split('_')[0]
    sign = make_sign(token, t, appKey, data)
    param = {
        'jsv': '2.4.0',
        'appKey': appKey,
        't': t,
        'sign': sign,
        'api': 'mtop.alimama.union.xt.biz.quan.api.entry',
        'v': '1.0',
        'timeout': '20000',
        'AntiCreep': 'true',
        'AntiFlood': 'true',
        'type': 'jsonp',
        'dataType': 'jsonp',
        'callback': 'mtopjsonp2',
        'data': data,
    }
    return param


# 主请求(请求接口, 程序的入口)
async def main(url, url1, sem):
    async with sem:
        param = await get_param(cookie, url1)
        async with ClientSession() as session:
            async with session.get(url, data=param, proxy=next(proxy), cookies=cookie, timeout=5, headers=headers, verify_ssl=False) as res:
                d = await res.text()
                # 部分优惠券链接无法访问
                try:
                    await parse(d, url1)
                except Exception:
                    print(url)
                    print(d)


# 请求商品页面来获取shopId
async def seller(url):
    async with ClientSession() as session:
        async with session.get(url, proxy=next(proxy), headers=headers, timeout=10, verify_ssl=False) as res:
            print(url)
            html = await res.text()
            seller_list = re.findall(r"sellerId=(\d+)", html) if re.findall(r"sellerId=(\d+)", html) else \
                re.findall(r'"userId":(\d+)', html)
            return seller_list[0]


# 解析
async def parse(d, url):
    data = json.loads(d[d.find("{"):d.rfind("}")+1])
    result = data['data']['resultList'][0]
    cbid = result.get('couponActivityId', 'null')
    id = result.get('itemId')
    itemUrl = 'https://detail.m.tmall.com/item.htm?id={}'.format(id)
    shopId = await seller(itemUrl)
    needAmount = result.get('couponStartFee', 'null')[0: -3]
    rebate = result.get('couponAmount', 'null')
    couponDis = '满{}减{}'.format(needAmount, rebate)
    status = True
    if not needAmount and not rebate:
        status = False
    # 有的优惠券失效了, 起止时间是None
    try:
        couponStime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(result.get('couponEffectiveStartTime', '0')[0: 10])))
        couponEtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(result.get('couponEffectiveEndTime', '0')[0: 10])))
    except TypeError:
        couponStime = 'null'
        couponEtime = 'null'
    couponUrl = url
    crawlTime = time.strftime('%Y-%m-%d %H:%M:%S')
    couponType = result.get('couponType')
    shopTitle = result['shop']['shopTitle']
    if couponType == '1':
        msg = '{}|店铺部分商品'.format(shopTitle)
    else:
        msg = '{}|店铺通用'.format(shopTitle)
    final = {
        "CouponBatchID": cbid,
        "CouponDescription": couponDis,
        "CouponName": shopTitle,
        "NeedAmount": needAmount,
        "Discount": '',
        "MaxRebate": "",
        "CouponImage": "",
        "Rebate": rebate,
        "StartTime": couponStime,
        "EndTime": couponEtime,
        "CouponTypeID": '',
        "CouponUrl": couponUrl,
        "OriginCouponUrl": [couponUrl],
        "CrawlTime": crawlTime,
        "MallId": '',
        "flag": '',
        "Status": status,
        "ArticleId": '',
        "couponType": couponType,
        "CouponCode": '',
        "CrawlFlag": '',
        "CoupUrlType": '1',
        "ShopId": shopId,
    }
    res = json.dumps(final, ensure_ascii=False)
    print(res)
    # 写到文件中
    # f1.write(res)
    # f1.write('\n')
    # f1.flush()
    return res


if __name__ == '__main__':
    # f1 = open('result.txt', 'a')
    app.run()
    # f1.close()

# -*- coding:utf-8 -*-
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
# 公司代理
proxy = cycle([

])
cookie = {}
# 这个url是访问主页面的url
g_url = ''
Cookie = 'cna=495kFsllxGQCAXc5Jibriy18; t=3b56b87d295d3dba6bad528bd8779c5a; cookie2=5d10443752f640b73665be8119e9756a; _tb_token_=3555b7e7e57fe; l=dBTZkwsgqVu-Tv4-BOCwNQL1hL_ThIRAguSJCRv2i_5Iq1L1cv7OkpiQcep6cjWfTgYp47_ypVw9-etlwTMqWX-vXaLAXxDc.; _m_h5_tk=1a45f91c2ef01754d072785e51e8bbcd_1574847830964; _m_h5_tk_enc=ca0b7eb4cec88adeccf5d58df04c6e5a; isg=BMHBPEC6eM7ss5T5YyV2WwY30A13_z9y0AXokSMWvUgnCuHcaz5FsO8L6HhMAs0Y'.replace(
    ' ', '')
headers = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Mobile Safari/537.36',
}
# 拼cookie
for c in Cookie.split(';'):
    a = c.split('=')
    cookie.update({
        a[0]: a[1]
    })


@app.route('/', methods=['GET'])
def syn_api():
    u = request.args.get('url')
    p = '(.*?)\?'
    url = re.findall(p, u)[0]
    traceId = request.args.get('traceId')
    union_lens = request.args.get('union_lens')
    xId = request.args.get('xId')
    p = '\?e=(.*)'
    e = re.findall(p, u)[0]
    param = {
        'e': e,
        'traceId': traceId,
        'union_lens': union_lens,
        'xId': xId,
    }
    print(request.args)
    # 这个URL是访问接口的URL
    URL = 'https://h5api.m.taobao.com/h5/mtop.alimama.union.xt.biz.quan.api.entry/1.0/'
    # url是优惠券的链接, URL是接口链接(没拼的)
    res = main(url, URL, param)
    if isinstance(res, tuple):
        return res[0]+res[1]
    return res


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
    return get_md5_hash(token + '&' + str(int(t)) + '&' + appk + '&' + str(data))


# 请求主页面(用来获取请求接口的recover_id)
def getMainPage(url, param):
    res = requests.get(url, params=param, headers=headers, proxies={'all': next(proxy)})
    global g_url
    g_url = res.url
    return res.text


# 用来制作请求接口的必要参数: data
def make_data(url, t, param):
    con = getMainPage(url, param)
    p = 'window\.pvid="(.*?)_15'
    print(url)
    forlook = re.findall(p, con)
    recover_id = re.findall(p, con)[0]
    e = param['e']
    union_lens = param['union_lens']
    # p = r'e=(.*?)&'
    # e = re.findall(p, url)[0]
    # p = r'union_lens=(.*?)&'
    # union_lens = re.findall(p, url)[0]
    vamap = {
        'e': e,
        'type': 'nBuy',
        'union_lens': union_lens,
        'recoveryId': recover_id + '_' + str(int(t))
    }

    data = {
        'floorId': '13193',
        'variableMap': json.dumps(vamap, ensure_ascii=False)
    }
    return data


# 获取param来拼接完整的接口url
def get_param(cookie, url, param):
    t = cookie['_m_h5_tk'].split('_')[1]
    appKey = '12574478'
    data = make_data(url, t, param)
    print(data)
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
def main(url, URL, param):
    param = get_param(cookie, url, param)
    res = requests.get(URL, data=param, proxies={'all': next(proxy)}, cookies=cookie, timeout=5, headers=headers, verify=False)
    d = res.text
    # 部分优惠券链接无法访问
    try:
        print(res.text)
        r = parse(d, url)
        return r
    except KeyError:
        return res.text


# 请求商品页面来获取shopId
def seller(url):
    res = requests.get(url, proxies={'all': next(proxy)}, headers=headers, timeout=10, verify=False)
    html = res.text
    print(url)
    seller_list = re.findall(r"sellerId=(\d+)", html) if re.findall(r"sellerId=(\d+)", html) else \
        re.findall(r'"userId":(\d+)', html)
    return seller_list[0]


# 解析
def parse(d, url):
    data = json.loads(d[d.find("{"):d.rfind("}") + 1])
    result = data['data']['resultList'][0]
    cbid = result.get('couponActivityId', 'null')
    id = result.get('itemId')
    itemUrl = 'https://detail.m.tmall.com/item.htm?id={}'.format(id)
    shopId = seller(itemUrl)
    needAmount = result.get('couponStartFee', 'null')[0: -3]
    rebate = result.get('couponAmount', 'null')
    couponDis = '满{}减{}'.format(needAmount, rebate)
    status = True
    if not needAmount and not rebate:
        status = False
    # 有的优惠券失效了, 起止时间是None
    try:
        couponStime = time.strftime('%Y-%m-%d %H:%M:%S',
                                    time.localtime(int(result.get('couponEffectiveStartTime', '0')[0: 10])))
        couponEtime = time.strftime('%Y-%m-%d %H:%M:%S',
                                    time.localtime(int(result.get('couponEffectiveEndTime', '0')[0: 10])))
    except TypeError:
        couponStime = 'null'
        couponEtime = 'null'
    couponUrl = g_url
    crawlTime = time.strftime('%Y-%m-%d %H:%M:%S')
    couponType = result.get('couponType')
    shopTitle = result['shop']['shopTitle']
    nCouponInfoMap = result['nCouponInfoMap']
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
    if nCouponInfoMap:
        couponDis = '满{}减{}'.format(nCouponInfoMap['couponStartFees'], int(nCouponInfoMap['everySaveAmounts'][0: -3])*int(nCouponInfoMap['nNum']))
        final2 = {
            "CouponBatchID": nCouponInfoMap['couponActivityIds'],
            "CouponDescription": 'couponDis',
            "CouponName": shopTitle,
            "NeedAmount": nCouponInfoMap['couponStartFees'],
            "Discount": '',
            "MaxRebate": "",
            "CouponImage": "",
            "Rebate": int(nCouponInfoMap['everySaveAmounts'][0: -3])*int(nCouponInfoMap['nNum']),
            "StartTime": nCouponInfoMap['couponEffectiveStartTimes'],
            "EndTime": nCouponInfoMap['couponEffectiveEndTimes'],
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
        res2 = json.dumps(final2, ensure_ascii=False)
        return res, res2
    print(res)
    return res


if __name__ == '__main__':
    app.run()
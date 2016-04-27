# -*- coding: utf-8 -*-

import json
import requests

def check_car_policy(policy_series, policy_number, timeout=20.0):
    headers = {
        'User-Agent': u'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0',
        'Accept': u'application/json',
        'Accept-Language': u'en-US,en;q=0.5',
        'Accept-Encoding': u'gzip, deflate',
        'Content-Type': u'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': u'XMLHttpRequest',
        'Referer': u'http://dkbm-web.autoins.ru/dkbm-web-1.0/bsostate.htm',
    }

    response = requests.post('http://dkbm-web.autoins.ru/dkbm-web-1.0/bsostate.htm', data={
        'answer': u'Введите текст',                                                         # БГГ, это капча
        'bsonumber': policy_number,
        'bsoseries': policy_series
    }, headers=headers, timeout=timeout)

    if response.status_code != 200:
        return

    return json.loads(response.text)

    #typical response: {
    # "policyCreateDate":"17.10.2013",
    # "bsoSeries":"ССС",
    # "bsoNumber":"0307897277",
    # "changeDate":"06.02.2014",
    # "policyBeginDate":"20.10.2013",
    # "policyEndDate":"19.10.2014",
    # "insCompanyName":"РЕСО-ГАРАНТИЯ",
    # "bsoStatusName":"Находится у страхователя",
    # "validCaptcha":true,
    # "errorMessage":null
    # }
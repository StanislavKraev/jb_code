# -*- coding: utf-8 -*-

import json
import requests
from flask import current_app


def prepare_key(key):
    return filter(lambda c: c.isalnum(), key).encode('utf-8')


def get_detailed_address(address):

    if not address or not isinstance(address, basestring):
        return u""
    # dd_api_key = "90ca299132f2c9b4c09f7a907ef0dc7abcc9c374 "
    dd_api_key = "3dc7eb747eb6ac11509b941b40df1b582de68f2b"
    #dd_secret_key = "4647c2967a9d365160ca87d233b2fc6061655a7a "
    url = u"https://dadata.ru/api/v2/suggest/address"

    cache_key = prepare_key('dadata/s/addr' + address)
    result_text = current_app.external_tools.cache.get(cache_key)
    if not result_text:
        headers = {
            u'Content-Type': u'application/json',
            u'Accept': u'application/json',
            u'Authorization': u'Token %s' % dd_api_key
        }

        r = requests.post(url, data=json.dumps({"query": address}), headers=headers, timeout=5)
        if r.status_code != 200:
            return
        result_text = r.text
        current_app.external_tools.cache.set(cache_key, result_text, 3600 * 24)
    try:
        result = json.loads(result_text)
    except Exception:
        return
    return result


def dadata_standardize_address(address):
    if not address or not isinstance(address, basestring):
        return {}

    dd_api_key = "3dc7eb747eb6ac11509b941b40df1b582de68f2b"
    dd_secret_key = "0affb032f2563b4c2bb6a66d7ee4f9c8fef48240"

    url = u"https://dadata.ru/api/v2/clean/address"

    cache_key = prepare_key('dadata/s/clean' + address)
    result_text = current_app.external_tools.cache.get(cache_key)
    if not result_text:
        headers = {
            u'Content-Type': u'application/json',
            u'Accept': u'application/json',
            u'Authorization': u'Token %s' % dd_api_key,
            u'X-Secret': dd_secret_key
        }

        r = requests.post(url, data=json.dumps([address]), headers=headers, timeout=5)
        if r.status_code != 200:
            return
        result_text = r.text
        current_app.external_tools.cache.set(cache_key, result_text, 3600 * 24)

    try:
        result = json.loads(result_text)
        if not result or not isinstance(result, list):
            raise Exception()
        result = result[0]
    except Exception:
        return

    return result

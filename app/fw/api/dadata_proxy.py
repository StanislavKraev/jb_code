# -*- coding: utf-8 -*-
import hashlib
import json
import shlex
import subprocess
import requests
from flask import current_app

api_key = "Token 3dc7eb747eb6ac11509b941b40df1b582de68f2b" # todo: move to configuration
secret_key = "0affb032f2563b4c2bb6a66d7ee4f9c8fef48240"
DADATA_TIMEOUT_SECONDS = 20

def make_key(key):
    m = hashlib.md5()
    m.update(key)
    return m.hexdigest()

def dadata_clean(method, data):
    key = make_key('dadata/clean' + method + unicode(data))
    result_text = current_app.external_tools.cache.get(key)

    if not result_text:
        current_app.logger.debug(u'ddc: cache miss')
        result = requests.post('https://dadata.ru/api/v2/clean/%s' % method,
            data = json.dumps(data),
            headers = {
                "Content-Type": "application/json",
                "Authorization": api_key,
                "X-Secret": secret_key
            }, timeout=DADATA_TIMEOUT_SECONDS)

        if result.status_code == 200:
            result_text = result.text
        else:
            current_app.logger.error(u'invalid response code: %s (%s)' % (result.status_code, result.text))
            return
        current_app.external_tools.cache.set(key, result_text, 1800)
    else:
        current_app.logger.debug(u'ddc: cache hit')

    if result_text:
        try:
            items = json.loads(result_text)
            for item in items:
                if 'house' in item and item['house'] and 'block_type' in item and item['block_type'] is None:
                    if len(item['house']) > 1 and item['house'][0].isdigit() and item['house'][-1].isalpha():
                        item['block_type'] = u'литер'
                        item['block'] = item['house'][-1]
                        item['house'] = item['house'][:-1]

            try:
                cmd = 'zabbix_sender -c /etc/zabbix/zabbix_agentd.conf -k %s -o 1' % 'dadata_clean'     # todo: make quick!
                p = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate()
            except Exception:
                pass
            return items
        except Exception:
            current_app.logger.exception(u'error during response processing')
            pass


def dadata_suggest(method, data):
    if method not in ('fio', 'address', 'party') or not data:
        current_app.logger.error('invalid input data')
        return

    try:
        result = requests.post('https://dadata.ru/api/v2/suggest/%s/' % method,
            data = json.dumps(data),
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": api_key,
                "X-Secret": secret_key
            }, timeout=20)
    except Exception:
        current_app.logger.error('error during suggestion request')
        return

    if result.status_code == 200:
        try:
            data = result.json()
            suggestions = data['suggestions']
            for sugg in suggestions:
                item = sugg['data']
                if 'house' in item and item['house'] and 'block_type' in item and item['block_type'] is None:
                    if len(item['house']) > 1 and item['house'][0].isdigit() and item['house'][-1].isalpha():
                        item['block_type'] = u'литер'
                        item['block'] = item['house'][-1]
                        item['house'] = item['house'][:-1]
                if 'city' in item and item['city'] in  [u"Москва", u"Санкт-Петербург", u"Севастополь"] and 'city_type' in item and item['city_type'] == u"г":
                    item['city'] = None
                    item['city_type'] = None
                    item['city_type_full'] = None

            return data
        except Exception:
            current_app.logger.exception(u'error during suggestion processing')
            pass
    current_app.logger.error('invalid response code')

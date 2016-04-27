# -*- coding: utf-8 -*-

import json
from urllib import urlencode
from tornado import httputil, gen
from tornado.httpclient import AsyncHTTPClient
from utils import make_cache_key

class AsyncDadataProvider(object):

    @staticmethod
    @gen.coroutine
    def get_detailed_address(address, cache):
        if not address or not isinstance(address, basestring):
            raise gen.Return(None)


        cache_key = make_cache_key('dadata/s/addr' + address)
        #result_text = cache.get(cache_key)
        result_text = ""
        if not result_text:
            headers = httputil.HTTPHeaders({
                u'Content-Type': u'application/json',
                u'Accept': u'application/json',
                u'Authorization': u'Token %s' % dd_api_key
            })
            http_client = AsyncHTTPClient()
            body = json.dumps({"query" : address})
            response = yield http_client.fetch(url, method = 'POST', headers = headers, request_timeout=5, body = body, follow_redirects=False)
            if response.code != 200:
                raise gen.Return(None)
            result_text = response.body

            cache.set(cache_key, result_text, 3600 * 24)
        try:
            result = json.loads(result_text)
        except Exception:
            raise gen.Return(None)
        raise gen.Return(result)

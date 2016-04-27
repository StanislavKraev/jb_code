# -*- coding: utf-8 -*-

import memcache


class CacheWrapper(object):

    def __init__(self):
        self._cache = None

    def _call(self, f, *args, **kwargs):
        from flask import current_app
        try:
            return f(*args, **kwargs)
        except Exception, ex:
            print(u"Failed to call memcached function %s with" % unicode(f))
            self._cache = memcache.Client(['%s:11211' % current_app.config['MEMCACHED_HOST']], debug=0)
            raise

    def get(self, key):
        from flask import current_app
        if not self._cache:
            self._cache = memcache.Client(['%s:11211' % current_app.config['MEMCACHED_HOST']], debug=0)
        return self._call(self._cache.get, key)

    def set(self, key, val, time=0, min_compress_len=0):
        from flask import current_app
        if not self._cache:
            self._cache = memcache.Client(['%s:11211' % current_app.config['MEMCACHED_HOST']], debug=0)
        return self._call(self._cache.set, key, val, time=time, min_compress_len=min_compress_len)

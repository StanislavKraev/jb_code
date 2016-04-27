# -*- coding: utf-8 -*-
import asyncmongo

from importlib import import_module
import logging
from logging.handlers import SocketHandler, DEFAULT_TCP_LOGGING_PORT
import tornado.web
import tornado.ioloop
from tornado.options import options, define
from tornado.httpserver import HTTPServer
from fw.cache.cache_wrapper import CacheWrapper
from fw.db.db_wrapper import DbWrapper
from jb_config import JBConfiguration

SERVICE_DESCRIPTION = 'JurBureau'
DEFAULT_CONFIG_PATH = '/etc/jurbureau/config.cfg'

def init_logging(config):

    logger = logging.getLogger('jb_async')
    socketHandler = SocketHandler('localhost', DEFAULT_TCP_LOGGING_PORT)
    socketHandler.setLevel(config['LOG_LEVEL'])
    socketHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    logger.addHandler(socketHandler)
    logger.setLevel(config['LOG_LEVEL'])
    return logger

class Application(tornado.web.Application):
    def __init__(self, config, db = None, cache_client = None,
                 file_manager = None, init_pool=True, logger = None, **settings):
        self.config = config or JBConfiguration(SERVICE_DESCRIPTION, DEFAULT_CONFIG_PATH)
        api_module_urls = import_module('async.urls')
        self.sync_db = DbWrapper(self.config)
        self.cache = CacheWrapper(self.config)

        self.logger = logger or init_logging(self.config)
        super(Application, self).__init__(api_module_urls.url_patterns, **settings)


def main():
    config = JBConfiguration(SERVICE_DESCRIPTION, DEFAULT_CONFIG_PATH)

    define("port", default="9876", help="HTTP service port")
    define("host", default="127.0.0.1", help="HTTP service address")
    tornado.options.parse_command_line()
    http_server = HTTPServer(Application(config))
    http_server.bind(int(options.port), options.host)
    http_server.start(1)

    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()

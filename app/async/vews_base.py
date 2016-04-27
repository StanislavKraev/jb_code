# -*- coding: utf-8 -*-
from bson.objectid import ObjectId

from tornado import escape
import traceback
from tornado.web import HTTPError
from tornado import gen
from tornado.web import asynchronous

import tornado.web

class AsyncConnectionRequestHandler(tornado.web.RequestHandler):

    def initialize(self):
        logger = self.application.logger
        logger.debug(u"Request data: \n%s" % unicode(self.request))
        logger.debug(u"Arguments data: \n%s" % unicode(self.request.arguments))

    def _process_response(self, content):
        return content

    @asynchronous
    @gen.coroutine
    def get(self, *args, **kwargs):
        yield self.get_content_on_method(self._get_content_on_get, *args, **kwargs)

    @asynchronous
    @gen.coroutine
    def post(self, *args, **kwargs):
        yield self.get_content_on_method(self._get_content_on_post, *args, **kwargs)

    @asynchronous
    @gen.coroutine
    def patch(self, *args, **kwargs):
        yield self.get_content_on_method(self._get_content_on_patch, *args, **kwargs)

    @gen.coroutine
    def get_content_on_method(self, method, *args, **kwargs):
        config = self.application.config
        try:
            content = yield method(*args, **kwargs)
            self.set_header('Access-Control-Allow-Credentials', 'true')
            self.set_header('Access-Control-Allow-Origin', "http://%s" % config['site_domain'])
            content = self._process_response(content)
        except errors.ServerUnavailable, exc:
            self.application.logger.exception(u"Server Unavaliable error")
            trbk = traceback.format_exc()
            self.application.logger.exception(trbk)
            raise HTTPError(503, str(exc))
        except errors.ApiBaseError, exc:
            api_error_code = exc.get_error_code()
            http_error_code = exc.get_http_error_code()
            api_error_msg = exc.get_error_message()
            data_json = escape.json_encode({"error" : {"code" : api_error_code, "message" : api_error_msg}})
            self.set_header('Content-Type', 'application/json')
            self.set_header('Access-Control-Allow-Credentials', 'true')
            self.set_header('Access-Control-Allow-Origin', "http://%s" % config['site_domain'])

            self.write(data_json)
            self.set_status(http_error_code, reason=api_error_msg)
            self.finish()
            if self.application.settings.get('debug'):
                self.application.logger.debug(
                    "API ERROR " + str(exc.get_error_code()) + ": "+ exc.get_error_message().encode("utf8")
                )
            else:
                self.application.logger.exception(
                    "API ERROR " + str(exc.get_error_code()) + ": "+ exc.get_error_message().encode("utf8")
                )
            return
        except NotImplementedError:
            raise HTTPError(405)
        except Exception, exc:
            trbk = traceback.format_exc()
            self.application.logger.error(trbk)
            raise HTTPError(500, trbk)

        self.write(content)
        self.finish()

    @gen.coroutine
    def _get_content_on_get(self, *args, **kwargs):
        result = yield self.get_content_on_get(*args, **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def get_content_on_get(self, *args, **kwargs):
        raise NotImplementedError()

    @gen.coroutine
    def _get_content_on_post(self, *args, **kwargs):
        result = yield self.get_content_on_post(*args, **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def get_content_on_post(self, *args, **kwargs):
        raise NotImplementedError()

    @gen.coroutine
    def _get_content_on_patch(self, *args, **kwargs):
        result = yield self.get_content_on_patch(*args, **kwargs)
        raise gen.Return(result)

    @gen.coroutine
    def get_content_on_patch(self, *args, **kwargs):
        raise NotImplementedError()

class SessionRequestHandler(AsyncConnectionRequestHandler):

    def __init__(self, *args, **kwargs): # BLOCKING
        super(SessionRequestHandler, self).__init__(*args, **kwargs)

        config = self.application.config
        session_interface = MongoSessionInterface(
            None,
            self.application.sync_db,
            'sessions',
            config['cookie_name'],
            config['PERMANENT_SESSION_LIFETIME'], False, False)
        session = session_interface.open_session(None, self) # BLOCKING

        if 'user_id' in session:
            user =  AuthUser.find_one(self.application.sync_db, {'_id' : ObjectId(session['user_id'])}) # BLOCKING
        else:
            user = AnonymousUser()
        self.user = user


class JsonRequestHandler(SessionRequestHandler):

    def _process_response(self, content):
        self.set_header('Content-Type', 'text/javascript')
        return escape.json_encode(content)

def authorized(func):
    def wrapper(self, *args, **kwargs):
        if self.user.is_anonymous:
            raise errors.NotAuthorized()
        return func(self, *args, **kwargs)
    return wrapper

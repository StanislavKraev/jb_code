# -*- coding: utf-8 -*-
from functools import wraps
import traceback
from flask import json, current_app, abort, redirect, Response, request
from werkzeug.wrappers import Response as WResponse
from fw.api import errors

RESTRICTED_LOG_URLS = (
    '/account/create/', '/account/login/', '/account/password_change/', '/account/by/code/', '/account/login/external/',
    '/account/login/external-url/')


def log_request():
    for url in RESTRICTED_LOG_URLS:
        if url in request.url:
            current_app.logger.debug(u'%s: %s {arguments hidden}' % (request.method, request.url))
            return
    try:
        headers = {}
        skip_headers = {'PRAGMA', 'CONNECTION', 'HOST', 'CACHE-CONTROL',
                        'ACCEPT', 'ACCEPT-LANGUAGE', 'ACCEPT-ENCODING', 'REFERER'}
        for k, v in request.headers.items():
            if k.upper() in skip_headers:
                continue
            headers[k] = v

        args = unicode(request.args).strip()
        if args == u"ImmutableMultiDict([])":
            args = u""
        else:
            args = args.replace(u"ImmutableMultiDict", u"")

        form = unicode(request.form).strip()
        if form == u"ImmutableMultiDict([])":
            form = u""
        else:
            form = form.replace(u"ImmutableMultiDict", u"")

        current_app.logger.debug(u'%s: %s Arguments: %s Form data: %s\n%s' % (
            request.method, request.url, args, form, unicode(headers)))
    except Exception:
        current_app.logger.exception(u"Failed to log request data")


def error_tree_to_list(error_tree, cur_name=u"", fields=None):
    items = []
    fields = fields if (fields is not None) else set()
    for i in error_tree:
        if cur_name:
            name = cur_name + ((u"." + i['field']) if i['field'] else "")
        else:
            name = i['field']

        if 'inner_exception' in i:
            items.extend(error_tree_to_list(i["inner_exception"], name, fields))
        else:
            if name not in fields:
                items.append({
                    'field': name,
                    'error_code': i['error_code']
                })
                fields.add(name)
    return items


def api_view(func):
    @wraps(func)
    def view_wrapper(*args, **kwargs):
        try:
            log_request()
            result = func(*args, **kwargs)
        except errors.ServerUnavailable, exc:
            current_app.logger.critical("Server Unavaliable error")
            trbk = traceback.format_exc()
            current_app.logger.exception(trbk)
            return unicode(exc), 503
        except errors.ApiBaseError, exc:
            api_error_code = exc.get_error_code()
            http_error_code = exc.get_http_error_code()
            api_error_msg = exc.get_error_message()
            exc_ext_data = getattr(exc, 'ext_data', None)
            if exc_ext_data is not None:
                data_json = json.dumps({
                    "error": {
                        "code": api_error_code,
                        "message": api_error_msg
                    },
                    "error_ext": error_tree_to_list(exc_ext_data)
                })
            else:
                data_json = json.dumps({"error": {"code": api_error_code, "message": api_error_msg}})
            if current_app.config.get('debug'):
                current_app.logger.debug(
                    "API ERROR " + str(exc.get_error_code()) + ": " + exc.get_error_message().encode(
                        "utf8") + ": " + data_json
                )
            else:
                current_app.logger.exception(
                    "API ERROR " + str(exc.get_error_code()) + ": " + exc.get_error_message().encode(
                        "utf8") + ": " + data_json
                )
            result = Response(data_json, mimetype='application/json', status=http_error_code)
            result.headers.add('Access-Control-Allow-Credentials', "true")
            result.headers.add('Access-Control-Allow-Origin', "http://%s" % current_app.config['site_domain'])
            return result
        except errors.SocialServiceRedirect, exc:
            resp = redirect(exc.url)
            resp.headers.add('Access-Control-Allow-Credentials', "true")
            resp.headers.add('Access-Control-Allow-Origin', "http://%s" % current_app.config['site_domain'])
            return resp
        except NotImplementedError:
            abort(405)
            return
        except Exception, exc:
            current_app.logger.exception(u"Unhandled exception")
            abort(500)
            return

        if isinstance(result, WResponse):
            result.headers.add('Access-Control-Allow-Credentials', "true")
            result.headers.add('Access-Control-Allow-Origin', "http://%s" % current_app.config['site_domain'])
            return result

        try:
            result_str = json.dumps(result, default=lambda x: unicode(x), indent=1)
        except Exception, ex:
            current_app.logger.exception(u"Failed to jsonify result")
            abort(500)
            return
        response = Response(result_str, mimetype='application/json')
        response.headers.add('Access-Control-Allow-Credentials', "true")
        response.headers.add('Access-Control-Allow-Origin', "http://%s" % current_app.config['site_domain'])
        return response

    return view_wrapper

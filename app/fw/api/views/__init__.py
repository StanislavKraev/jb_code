# -*- coding: utf-8 -*-
import json

from flask import Response

from fw.api import errors


def not_authorized(site_domain=None):
    api_error_code = errors.NotAuthorized.ERROR_CODE
    http_error_code = errors.NotAuthorized.HTTP_ERROR_CODE
    api_error_msg = errors.NotAuthorized.ERROR_MESSAGE
    data_json = json.dumps({"error": {"code": api_error_code, "message": api_error_msg}})

    result = Response(data_json, mimetype='application/json', status=http_error_code)
    if site_domain:
        result.headers.add('Access-Control-Allow-Credentials', "true")
        result.headers.add('Access-Control-Allow-Origin', "http://%s" % site_domain)
    return result


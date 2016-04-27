# -*- coding: utf-8 -*-

from flask import current_app, json, abort, Response, request, Blueprint
from flask_login import current_user
from fw.api import geoip_utils, errors
from fw.api.args_validators import validate_arguments
from fw.api.args_validators import ArgumentValidator

from fw.api.base_handlers import api_view
from fw.api.views import not_authorized
from fw.documents.address_enums import RFRegionsEnum

general_bp = Blueprint('general', __name__)


def _set_cors_headers(response):
    response.headers.add('Access-Control-Allow-Credentials', "true")
    response.headers.add('Access-Control-Allow-Origin', "http://%s" % current_app.config['site_domain'])


@general_bp.route('/dadata.ru/api/v2/clean/<method>', methods=['POST'])
def dadata_v2_clean(method):
    if not current_user.is_authenticated:
        return not_authorized(current_app.config['site_domain'])
    if method not in ('address', 'birthdate', 'email', 'name', 'phone'):
        abort(404)
    xdata = request.form
    if not xdata:
        abort(400)

    data = {}
    for item in xdata:
        # noinspection PyBroadException
        try:
            item_data = json.loads(item)
            if isinstance(item_data, dict):
                data.update(item_data)
        except Exception:
            pass

    current_app.logger.debug(u"clean query: %s" % unicode(data))
    resp_data = current_app.external_tools.dadata_clean(method, [data['query']])
    current_app.logger.debug(u"clean request finished")
    resp = Response(json.dumps(resp_data), mimetype='application/json') \
        if resp_data else Response("[]", mimetype='application/json')
    _set_cors_headers(resp)
    return resp


@general_bp.route('/dadata.ru/api/v2/suggest/<method>', methods=['POST'])
def dadata_v2_suggest(method):
    if not current_user.is_authenticated:
        return not_authorized(current_app.config['site_domain'])
    if method not in ('fio', 'address', 'party'):
        abort(404)
    try:
        data = request.form
        if not data:
            abort(400)
        for item in data:
            data = json.loads(item)
        current_app.logger.debug(u"suggest query: %s" % json.dumps(data, ensure_ascii=False))

        result_data = current_app.external_tools.dadata_suggest(method, data)
        if not result_data:
            raise Exception(u"Failed to get suggestions")

    except Exception:
        current_app.logger.exception(u"Failed to send request")
        resp = Response(json.dumps({'suggestions': []}), status=200)
        _set_cors_headers(resp)
        return resp

    if result_data:
        try:
            data = result_data
            str_result = json.dumps(result_data, ensure_ascii=False)[:200]
            # noinspection PyStringFormat
            current_app.logger.debug(u"suggest result data: %s..." % str_result)
            suggestions = data['suggestions']
            for sugg in suggestions:
                item = sugg['data']
                if 'house' in item and item['house'] and 'block_type' in item and item['block_type'] is None:
                    if len(item['house']) > 1 and item['house'][0].isdigit() and item['house'][-1].isalpha():
                        item['block_type'] = u'литер'
                        item['block'] = item['house'][-1]
                        item['house'] = item['house'][:-1]
                if 'city' in item and item['city'] in [u"Москва", u"Санкт-Петербург",
                                                       u"Севастополь"] and 'city_type' in item and item[
                    'city_type'] == u"г":
                    item['city'] = None
                    item['city_type'] = None
                    item['city_type_full'] = None

            resp = Response(json.dumps(data), mimetype='application/json')
            _set_cors_headers(resp)
            current_app.logger.debug(u"suggest finished")
            return resp
        except Exception:
            pass

    resp = Response('[]', mimetype='application/json')
    _set_cors_headers(resp)
    return resp


@general_bp.route('/geoip/', methods=['GET'])
@api_view
@validate_arguments(ip=ArgumentValidator(required=False))
def geo_ip(ip=None):
    ip = ip or request.remote_addr
    try:
        result = geoip_utils.GeoIpLocator.get_location(ip)
        if not result:
            raise Exception()
    except Exception:
        current_app.logger.exception(u"Failed to get location")
        return {'result': {'region': RFRegionsEnum.RFR_SPB}}
    return {'result': result}

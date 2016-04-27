# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import email
from email.header import decode_header
from services.ifns.ifns_manager import IfnsDescription

SERVICES = [{
                'id': 180,
                'title': u'Гос. регистрация юридических и физическил лиц. Сведения из гос. реестров. Информирование. (Регистрационный центр)',
                'check': 0,
                'subservices': [{
                                    'id': 181,
                                    'title': u'Прием документов при регистрации от гос. предприятий и учреждений',
                                }, {
                                    'id': 182,
                                    'title': u'Прием документов при регистрации лично от заявителя',
                                }, {
                                    'id': 275,
                                    'title': u'Прием документов  при регистрации создания  (1-но ЮЛ)',
                                }, {
                                    'id': 276,
                                    'title': u'Прием документов при регистрации изменений (1-но ЮЛ)*',
                                }, {
                                    'id': 277,
                                    'title': u'Прием документов при регистрации изменений (не более 3-х ЮЛ)*',
                                }, {
                                    'id': 278,
                                    'title': u'Прием документов при регистрации реорганизации и ликвидации (1-но ЮЛ)',
                                }, {
                                    'id': 188,
                                    'title': u'Выдача документов при регистрации гос. предприятий и учреждений',
                                }, {
                                    'id': 186,
                                    'title': u'Выдача документов при регистрации лично заявителю',
                                }, {
                                    'id': 189,
                                    'title': u'Выдача документов при регистрации по доверенности',
                                }, {
                                    'id': 279,
                                    'title': u'Прием по записи онлайн на подачу документов при регистрации ЮЛ',
                                }, {
                                    'id': 282,
                                    'title': u'Прием по записи через портал государственных услуг на подачу документов при регистрации ЮЛ',
                                }, {
                                    'id': 191,
                                    'title': u'Прием заявлений на предоставление сведений из ЕГРЮЛ/ЕГРИП от гос. предприятий и учреждений',
                                }, {
                                    'id': 190,
                                    'title': u'Прием заявлений на предоставление сведений из ЕГРЮЛ/ЕГРИП лично от заявителя',
                                }, {
                                    'id': 246,
                                    'title': u'Прием заявлений на предоставление сведений из ЕГРЮЛ/ЕГРИП по доверенности',
                                }, {
                                    'id': 285,
                                    'title': u'Выдача документов при регистрации создания (1-но ЮЛ)',
                                }, {
                                    'id': 286,
                                    'title': u'Выдача документов при регистрации создания (более 1-го ЮЛ)',
                                }, {
                                    'id': 193,
                                    'title': u'Прием заявлений на предоставление сведений из ЕГРЮЛ (в отношении 1-го ЮЛ)',
                                }, {
                                    'id': 192,
                                    'title': u'Прием заявлений на предоставление сведений из ЕГРЮЛ (в отношении более 1-го ЮЛ)',
                                }, {
                                    'id': 287,
                                    'title': u'Выдача документов при регистрации изменений / реорганизации / ликвидации (1-но ЮЛ)',
                                }, {
                                    'id': 288,
                                    'title': u'Выдача документов при регистрации изменений / реорганизации / ликвидации (более 1-го ЮЛ)',
                                }, {
                                    'id': 195,
                                    'title': u'Выдача сведений из ЕГРЮЛ/ЕГРИП гос. предприятиям и учреждениям',
                                }, {
                                    'id': 194,
                                    'title': u'Выдача сведений из ЕГРЮЛ/ЕГРИП лично заявителю',
                                }, {
                                    'id': 199,
                                    'title': u'Прием заявлений на исправление технической ошибки в ЕГРЮЛ',
                                }, {
                                    'id': 200,
                                    'title': u'Выдача документов после исправления технической ошибки в ЕГРЮЛ',
                                }, {
                                    'id': 249,
                                    'title': u'Информирование по порядку регистрации',
                                }, {
                                    'id': 250,
                                    'title': u'Прием обращений (жалоб, предложений, заявлений)',
                                }, {
                                    'id': 295,
                                    'title': u'Прием заявлений на повторную выдачу документа о регистрации и повторная выдача документа о регистрации',
                                }, {
                                    'id': 300,
                                    'title': u'Выдача сведений из ЕГРЮЛ (в отношении 1-го лица)',
                                }, {
                                    'id': 303,
                                    'title': u'Выдача сведений из ЕГРЮЛ (в отношении более 1-го лица)',
                                }, {
                                    'id': 309,
                                    'title': u'Информирование по исправлению тех. ошибок в ЕГРЮЛ/ЕГРИП',
                                }]
            }]

KNOWN_FSN_INTERNAL_ID_MAP = {
    1001: 95,
}

MONTHS = {
    u'Январь': 1,
    u'Февраль': 2,
    u'Март': 3,
    u'Апрель': 4,
    u'Май': 5,
    u'Июнь': 6,
    u'Июль': 7,
    u'Август': 8,
    u'Сентябрь': 9,
    u'Октябрь': 10,
    u'Ноябрь': 11,
    u'Декабрь': 12,
}


def get_detailed_address(address):
    return {
        "suggestions": [
            {
                "value": "Хабаровский край",
                "unrestricted_value": "Хабаровский край",
                "data": {
                    "qc_complete": None,
                    "qc_house": None,
                    "postal_code": "",
                    "postal_box": None,
                    "country": "Россия",
                    "region_type": "край",
                    "region_type_full": "край",
                    "region": "Хабаровский",
                    "area_type": None,
                    "area_type_full": None,
                    "area": None,
                    "city_type": None,
                    "city_type_full": None,
                    "city": None,
                    "settlement_type": None,
                    "settlement_type_full": None,
                    "settlement": None,
                    "street_type": None,
                    "street_type_full": None,
                    "street": None,
                    "house_type": None,
                    "house_type_full": None,
                    "house": None,
                    "block_type": None,
                    "block": None,
                    "flat_area": None,
                    "flat_type": None,
                    "flat": None,
                    "tax_office": "2700",
                    "kladr_id": "2700000000000",
                    "okato": "8000000000",
                    "oktmo": None,
                    "unparsed_parts": None,
                    "qc": None
                }
            }
        ]
    }


def get_ifns_by_address(address, service_nalog_ru_url):
    ifns = IfnsDescription({
        'kod': 1001,
        'naimk': u'отделение ифнс',
        'plat': {
        },
        'rof': {
            'code': 10012,
            'naimk': u'Межрайонная инспекция Федеральной налоговой службы №15 по Санкт-Петербургу'
        },
        'rou': {
            'code': 10011,
            'naimk': u'Межрайонная инспекция Федеральной налоговой службы №15 по Санкт-Петербургу'
        }
    })

    return ifns


def get_ifns_by_code(code, service_nalog_ru_url):
    ifns = IfnsDescription({
        'kod': 7726,
        'naimk': u'отделение ифнс',
        'plat': {
        },
        'rof': {
            'code': 10012,
            'naimk': u'Межрайонная инспекция Федеральной налоговой службы №15 по Санкт-Петербургу'
        },
        'rou': {
            'code': 10011,
            'naimk': u'Межрайонная инспекция Федеральной налоговой службы №15 по Санкт-Петербургу'
        }
    })

    return ifns


def morph_with_morpher(word_or_phrase):
    from fw.documents.morpher_tools import morph_with_morpher as _morpher
    return _morpher(word_or_phrase)


def get_nalog_ru_time_slots(person_data, company_data, internal_ifns_number, internal_ifns_service, IFNS_LOGGER):
    day_info = [{
                    'date': (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                    'time_slots': [{
                                       'slot_start': u'10:30',
                                       'slot_end': u'11:00'
                                   }, {
                                       'slot_start': u'11:30',
                                       'slot_end': u'12:00'
                                   }]
                }]
    return day_info


def book_ifns(person_data, company_data, internal_ifns_number, internal_ifns_service, dt, logger):
    return {
        "ifns": u'Межрайонная ИФНС №10000000',
        "service": u'Регистрация ООО',
        "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%S"),
        "window": u"-1",
        "address": u"село Гадюкино, ул. Разъезжая 2",
        "phone": u"322223233",
        "how_to_get": u"неизвестно",
        "code": u"111"
    }


def get_registration_ifns(service_nalog_ru_url, address_ifns=None):
    return {'adres': "село Гадюкино, ул. Разъезжая 2", 'rou': {'naimk': u'Межрайонная ИФНС №10000000'}}


class TestMailer(object):
    def __init__(self):
        self.mails = []

    def send_email(self, addr_from, addr_to, message):
        if message:
            msg = email.message_from_string(message)
            if msg:
                headers = dict(msg.items())
                new_headers = {}
                for header_name in headers:
                    header_val = headers[header_name]
                    if header_val:
                        d = decode_header(header_val)
                        if d:
                            d = d[0]
                            if d:
                                d = d[0]
                                if d:
                                    header_val = d.decode('utf-8')
                    new_headers[header_name] = header_val
                parts = [part.get_payload(decode=True) for part in msg.walk() if not part.is_multipart()]

                subject = new_headers.get('Subject', '')
                message = {
                    'headers': headers,
                    'subject': subject,
                    'parts': parts
                }

        self.mails.append({
            'from': addr_from,
            'to': addr_to,
            'message': message
        })


class TestSmsSender(object):
    def __init__(self, *args, **kwargs):
        self.sms = []

    def get_sms_cost(self, data):
        return 0.5

    def send(self, data):
        self.sms.append(data)


class Cache(object):
    def set(self, key, val, time=0, min_compress_len=0):
        pass

    def add(self, key, val, time=0, min_compress_len=0):
        pass

    def replace(self, key, val, time=0, min_compress_len=0):
        pass

    def set_multi(self, mapping, time=0, key_prefix='', min_compress_len=0):
        pass

    def get(self, key):
        pass

    def get_multi(self, keys, key_prefix=''):
        pass

    def incr(self, key, delta=1):
        pass

    def decr(self, key, delta=1):
        pass

    def delete(self, key, time=0):
        pass

    def delete_multi(self, keys, time=0, key_prefix=''):
        pass


def dadata_clean(method, data):
    return [{
                u'city_type': None,
                u'settlement_type': None,
                u'settlement_type_full': None,
                u'qc_complete': 0,
                u'flat': u'705',
                u'flat_type': u'\u043e\u0444',
                u'house': u'44',
                u'unparsed_parts': None,
                u'okato': u'40273563000',
                u'region_type': u'\u0433',
                u'postal_box': None,
                u'street': u'\u0421\u0432\u0435\u0440\u0434\u043b\u043e\u0432\u0441\u043a\u0430\u044f',
                u'postal_code': u'195027',
                u'oktmo': u'40330000',
                u'qc_geo': 1,
                u'timezone': u'UTC+4',
                u'geo_lon': u'30.405708993',
                u'settlement': None,
                u'city_type_full': None,
                u'kladr_id': u'7800000000012500139',
                u'city': None,
                u'flat_area': None,
                u'area': None,
                u'area_type_full': None,
                u'country': u'\u0420\u043e\u0441\u0441\u0438\u044f',
                u'region': u'\u0421\u0430\u043d\u043a\u0442-\u041f\u0435\u0442\u0435\u0440\u0431\u0443\u0440\u0433',
                u'block_type': u'\u043b\u0438\u0442\u0435\u0440',
                u'geo_lat': u'59.9614399',
                u'area_type': None,
                u'source': u'\u0421\u0430\u043d\u043a\u0442-\u041f\u0435\u0442\u0435\u0440\u0431\u0443\u0440\u0433, \u0421\u0432\u0435\u0440\u0434\u043b\u043e\u0432\u0441\u043a\u0430\u044f \u043d\u0430\u0431 44\u042e \u043e\u0444 705',
                u'qc': 0,
                u'street_type': u'\u043d\u0430\u0431',
                u'qc_house': 3,
                u'tax_office': u'7804',
                u'street_type_full': u'\u043d\u0430\u0431\u0435\u0440\u0435\u0436\u043d\u0430\u044f',
                u'house_type': u'\u0434',
                u'region_type_full': u'\u0433\u043e\u0440\u043e\u0434',
                u'block': u'\u042e'
            }]


def get_ifns_registrations(name, date_from=None, date_to=None, ifns=None, service_nalog_ru_url=None, logger=None):
    result_items = []
    if name == u"ЮРБЮРО ОНЛАЙН":
        result_item = {'full_name': u"ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ \"ЮРБЮРО ОНЛАЙН\"",
                       'ogrn': "1147847331367", 'status': 'registered', 'reg_date': "29.09.2014"}
        result_items.append(result_item)
    elif name == u"ЮРБЮРО ОФФЛАЙН":
        result_item = {'full_name': u"ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ \"ЮРБЮРО ОФФЛАЙН\"",
                       'status': 'registration_declined', 'reg_date': "29.09.2014"}
        result_items.append(result_item)
    elif name == u"ЮРБЮРО ПАЙПЛАЙН":
        result_item = {'full_name': u"ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ \"ЮРБЮРО ПАЙПЛАЙН\"",
                       'status': 'progress', 'reg_date': "29.09.2014"}
        result_items.append(result_item)
    return result_items

def check_car_policy(policy_series, policy_number, timeout=5.0):
    return {
        "policyCreateDate": u"17.10.2013",
        "bsoSeries": policy_series,
        "bsoNumber": policy_number,
        "changeDate": u"06.02.2014",
        "policyBeginDate": u"20.10.2013",
        "policyEndDate": u"19.10.2014",
        "insCompanyName": u"РЕСО-ГАРАНТИЯ",
        "bsoStatusName": u"Находится у страхователя",
        "validCaptcha": True,
        "errorMessage": None
    }

cache = Cache()



# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import hashlib
import json
from bson.objectid import ObjectId
import re
import html5lib
from lxml.cssselect import CSSSelector
from tornado import httputil, gen
from tornado.httpclient import AsyncHTTPClient, HTTPError
from urllib import urlencode
from custom_exceptions import CacheMiss
from fw.db.address_enums import RFRegionsEnum
from utils import make_cache_key, MONTHS, int_to_ifns

REGION_ID_INTERNAL_IDS = {
    1 : 1,  # адыгея
    2 : 5,  # башкортостан
    3 : 26, # бурятия
    4 : 48, # алтай
    5: 53,  # дагестан
    6: 74,  # ингушетия
    7: 1755,    # кабардино-балкарская
    8: 85,      # калмыкия
    9: 90,      # карачаево-черкесская
    10: 94,     # карелия
    11: 101,    # коми
    12: 113,    # марий эл
    13: 120,    # мордовия
    14: 130,    # саха
    15: 168,    # сев. осетия - алания
    16: 1278,   # татарстан
    17: 170,    # тыва
    18: 175,    # удмуртская
    19: 186,    # хакассия
    20: 190,    # чеченская
    21: 196,    # чувашская
    22: 207,    # алтайскийц
    23: 224,    # краснодарский
    24: 268,    # красноярский
    25: 275,    # приморский
    26: 297,    # ставропольский
    27: 1727,   # хабаровский
    28: 333,    # амурская
    29: 341,    # архангельская
    30: 367,    # астраханская
    31: 373,    # белгородская
    32: 383,    # брянская
    33: 395,    # владимирская
    34: 408,    # волгоградская
    35: 429,    # вологодская
    36: 1794,   # воронежская
    37: 440,    # ивановская
    38: 445,    # иркутская
    39: 2090,   # калининградская
    40: 463,    # калужская
    41: 473,    # камчатский
    42: 476,    # кемеровская
    43: 493,    # кировская
    44: 506,    # костромская
    45: 515,    # курганская
    46: 524,    # курская
    47: 553,    # ленинградская
    48: 566,    # липецкая
    49: 591,    # магаданская
    50: 595,    # московская
    51: 634,    # мурманская
    52: 650,    # нижегородская
    53: 673,    # новгородская
    54: 679,    # новосибирская
    55: 696,    # омская
    56: 713,    # оренбургская
    57: 730,    # орловская
    58: 737,    # пензенская
    59: 771,    # пермский
    60: 795,    # псковская
    61: 804,    # ростовская
    62: 825,    # рязанская
    63: 835,    # самарская
    64: 856,    # саратовская
    65: 901,    # сахалинская
    66: 909,    # свердловская
    67: 930,    # смоленская
    68: 958,    # тамбовская
    69: 964,    # тверская
    70: 974,    # томская
    71: 984,    # тульская
    72: 996,    # тюменская
    73: 1008,   # ульяновская
    74: 1020,   # челябинская
    75: 1043,   # забайкальский
    76: 1077,   # ярославская
    77: 1234,   # москва
    78: 1088,   # Санкт-Петербург
    79: 1114,   # еврейская
    86: 1117,   # югра
    87: 1132,   # чукотская
    89: 1135,   # ямало-ненецкий
    91: 2793,   # крым
    92: 2792    # севастополь
}

PP_REGION_REG_SERVICES = {
    47: 327,
    77: 281,
    78: 281
}

COMPANY_REGION_REG_SERVICES = {
    47: 139,
    77: 282,
    78: 182 # 275
}

class FailedToGetAppointmentData(Exception):
    def __init__(self, *args, **kwargs):
        super(FailedToGetAppointmentData, self).__init__(*args, **kwargs)

class AsyncIfnsProvider(object):

    @staticmethod
    @gen.coroutine
    def get_ifns_internal_id_by_ifns_name(region_name, ifns_name, is_private_person, headers, cache, logger):
        logger.debug(u"get_ifns_internal_id_by_ifns_name: region_name: %s, ifns_name: %s, is_private_person: %s" % (unicode(region_name), unicode(ifns_name), unicode(is_private_person)))

        region_id = RFRegionsEnum.get_number(region_name)
        internal_region_id = REGION_ID_INTERNAL_IDS[region_id]
        cb_param = u"c0:LECC|%d;%d;LBCRI|4;0:99;" % (len(unicode(internal_region_id)), internal_region_id)
        data = {
            "__CALLBACKID" : "ctl00$ifns",
            "__CALLBACKPARAM" : cb_param,
            "__VIEWSTATE" : ""
        }
        http_client = AsyncHTTPClient()
        body = urlencode(data)
        try:
            response = yield http_client.fetch('http://order.nalog.ru/fns_service/', method='POST', body=body, headers=headers, request_timeout=5)
        except HTTPError, ex:
            logger.exception(u"order.nalog.ru вернул неожиданный ответ")
            raise errors.IfnsServiceUnavailable()

        response_body = response.body.decode('utf-8')

        if response.code != 200 or u's/*DX*/({' not in response_body:
            logger.error(u"Failed to get internal ifns number. Request was: %s. Response text: %s" % (json.dumps(data), response_body))
            raise errors.IfnsServiceUnavailable()

        try:
            json_str = response_body.split(u"'result':'")[1][:-3]
            data = json.loads(json_str)
            i = 0
            ifns_service_name_id_map = {}
            while i < len(data):
                ifns_id = int(data[i])
                i += 1
                ifns_service_name_id_map[data[i].replace(' ', '')] = ifns_id
                i += 1

            ifns_name = ifns_name.replace(' ', '')
        except Exception:
            logger.error(u"Failed to get internal ifns number. Request was: %s. Response text: %s" % (json.dumps(data), response_body))
            raise errors.IfnsServiceUnavailable()

        if ifns_name in ifns_service_name_id_map:
            raise gen.Return((ifns_service_name_id_map[ifns_name], PP_REGION_REG_SERVICES[region_id] if is_private_person else COMPANY_REGION_REG_SERVICES[region_id]))

        match = re.search(ur'(\d+)', ifns_name)
        if not match:
            logger.error(u"Failed to get internal ifns number. Ifns name: %s" % ifns_name)
            raise gen.Return((None, None))

        ifns_id = match.groups(0)[0]
        for name, cur_ifns_id in ifns_service_name_id_map.items():
            match = re.search(ur'(\d+)', name)
            if match:
                if match.groups(0)[0] == ifns_id:
                    yield gen.Return((cur_ifns_id, PP_REGION_REG_SERVICES[region_id] if is_private_person else COMPANY_REGION_REG_SERVICES[region_id]))

        logger.error(u"Failed to get internal ifns number.")
        raise errors.IfnsServiceUnavailable()

    @staticmethod
    @gen.coroutine
    def start_ifns_session(person_data, company_data, reg_ifns_name, service, region_name, cache, logger):
        if int(service) != IfnsServiceEnum.IS_REG_COMPANY:
            raise errors.InvalidParameterValue("service")

        headers = httputil.HTTPHeaders({
            'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:33.0) Gecko/20100101 Firefox/33.0',
            'Accept-Encoding' : 'gzip, deflate',
            'Accept-Language' : 'en-US,en;q=0.5',
            'Connection' : 'keep-alive',
            'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer' : 'http://order.nalog.ru/'
        })
        http_client = AsyncHTTPClient()

        response = None
        if company_data:
            data = {
                "ctl00$LastName" : company_data['name'].encode('utf-8'),
                "ctl00$inn"	: str(company_data['inn']),
                "ctl00$phone"	: company_data['phone'].encode('utf-8'),
                "ctl00$email"	: company_data['email'].encode('utf-8'),
                "__VIEWSTATE"  : "",
                "ctl00$face"   : "0",
                "ctl00$btNext" : ""
            }
            # start session
            body = urlencode(data)
            ok = False
            for x in range(4):
                try:
                    response = yield http_client.fetch('http://order.nalog.ru/details/', method='POST', body=body, headers = headers, request_timeout=20, follow_redirects=False)
                    logger.error(u"order.nalog.ru вернул неожиданный код: %s" % unicode(response.code))
                    raise errors.IfnsServiceUnavailable()
                except HTTPError, ex:
                    error_code = ex.code
                    if error_code == 302:
                        ok = True
                        response = ex.response
                        break
                    elif error_code == 599:
                        raise errors.IfnsServiceUnavailable()
                    else:
                        logger.exception(u"order.nalog.ru вернул неожиданный ответ")
                        raise errors.ServerUnavailable()
            if not ok:
                raise errors.IfnsServiceUnavailable()

        elif person_data:
            data = {
                "ctl00$LastName"	: person_data['surname'].encode('utf-8'),
                "ctl00$FirstName"	: person_data['name'].encode('utf-8'),
                "ctl00$SecondName"  : person_data['patronymic'].encode('utf-8') or "",
                "ctl00$inn"	: str(person_data['inn']),
                "ctl00$phone"	: person_data['phone'].encode('utf-8'),
                "ctl00$email"	: person_data['email'].encode('utf-8'),
                "__VIEWSTATE"  : "",
                "ctl00$face"   : "1",
                "ctl00$btNext" : ""
            }
            body = urlencode(data)
            ok = False
            for x in range(4):
                try:
                    response = yield http_client.fetch('http://order.nalog.ru/details/', method='POST', body=body, headers = headers, request_timeout=20, follow_redirects=False)
                    logger.error(u"order.nalog.ru вернул неожиданный код: %s" % unicode(response.code))
                    raise errors.IfnsServiceUnavailable()
                except HTTPError, ex:
                    error_code = ex.code
                    if error_code == 302:
                        ok = True
                        response = ex.response
                        break
                    elif error_code == 599:
                        logger.exception(u"order.nalog.ru недоступен")
                        raise errors.IfnsServiceUnavailable()
                    else:
                        logger.exception(u"order.nalog.ru вернул неожиданный ответ")
                        raise errors.ServerUnavailable()
            if not ok:
                raise errors.IfnsServiceUnavailable()
        else:
            logger.error(u"Invalid parameters")
            raise errors.ServerError()

        cookies = response.headers["set-cookie"] if "set-cookie" in response.headers else None
        if cookies:
            headers.add('Cookie', cookies)

        try:
            fns, sub_service = yield AsyncIfnsProvider.get_ifns_internal_id_by_ifns_name(region_name, reg_ifns_name, not company_data, headers, cache, logger)
            if fns is None or sub_service is None:
                raise Exception()
        except errors.IfnsServiceUnavailable, ex:
            raise
        except Exception:
            logger.exception(u"Failed to get internal ids for ifns")
            raise errors.ServerUnavailable()

        service = 0
        is_multi_sub_service = 0

        session_data = {
            'service' : service,
            'is_multi_sub_service' : is_multi_sub_service,
            'sub_service' : sub_service,
            'fns' : fns,
            'cookies' : cookies
        }
        new_id = str(ObjectId())
        session_data_str = json.dumps(session_data).encode('utf-8')
        cache.set(new_id, session_data_str, time=1800)
        raise gen.Return(new_id)

    @staticmethod
    def get_ifns_days_cache_key(reg_ifns_name, service, is_private_person, region_name):
        m = hashlib.md5()
        m.update((u"%s-%s-%s-%s" % (reg_ifns_name, unicode(service), unicode(is_private_person), region_name)).encode('utf-8'))
        return m.hexdigest()

    @staticmethod
    def get_ifns_day_slots_cache_key(reg_ifns_name, service, is_private_person, region_name, day_datetime):
        m = hashlib.md5()
        m.update((u"%s-%s-%s-%s-%s" % (reg_ifns_name, unicode(service), unicode(is_private_person), region_name, day_datetime.strftime("%Y-%m-%d"))).encode('utf-8')    )
        return m.hexdigest()

    @staticmethod
    @gen.coroutine
    def get_nalog_ru_time_slots(person_data, company_data, reg_ifns_name, service, region_name, cache, logger):
        session_id = yield AsyncIfnsProvider.start_ifns_session(person_data, company_data, reg_ifns_name, service, region_name, cache, logger)

        session_data_str = cache.get(session_id)
        if not session_data_str:
            raise errors.ServerUnavailable()
        try:
            session_data = json.loads(session_data_str)
            cookies = session_data['cookies']
            is_multi_sub_service = session_data['is_multi_sub_service']
            sub_service = session_data['sub_service']
            fns = session_data['fns']
        except Exception:
            logger.exception(u"Failed to load ifns session data")
            raise errors.ServerUnavailable()

        headers = httputil.HTTPHeaders({'Cookie' : cookies})

        if is_multi_sub_service is None:
            logger.error(u"Услуга не поддерживается: %s" % (unicode(service)))
            raise errors.InvalidParameterValue("service")

        days, simple_days = yield AsyncIfnsProvider._get_days(service, sub_service, is_multi_sub_service, fns, headers, logger)

        ifns_days_cache_key = AsyncIfnsProvider.get_ifns_days_cache_key(reg_ifns_name, service, not company_data, region_name)
        days_str = json.dumps(simple_days)
        cache.set(ifns_days_cache_key, days_str)

        # ban check
        d = days[0]

        is_banned = yield AsyncIfnsProvider.check_ban(session_id, d, cache, logger)
        if is_banned:
            raise MaximumRegistrationsExceeded()

        day_info = []
        # get time slots
        for d in days:
            res = yield AsyncIfnsProvider.get_day_slots(session_id, d, cache, logger)
            if res:
                day_info.append(res)
                cache_key = AsyncIfnsProvider.get_ifns_day_slots_cache_key(reg_ifns_name, service, not company_data, region_name, d)
                value_str = json.dumps(res)
                cache.set(cache_key, value_str)

        raise gen.Return(day_info)

    @staticmethod
    @gen.coroutine
    def get_day_slots(ifns_session_id, day_datetime, cache, logger):
        session_data_str = cache.get(ifns_session_id)
        if not session_data_str:
            raise errors.IfnsSessionExpired()
        try:
            session_data = json.loads(session_data_str)
            service = session_data['service']
            is_multi_sub_service = session_data['is_multi_sub_service']
            sub_service = session_data['sub_service']
            fns = session_data['fns']
            cookies = session_data['cookies']
        except Exception:
            logger.exception(u"Failed to load ifns session data")
            raise errors.IfnsSessionExpired()

        headers = httputil.HTTPHeaders({'Cookie' : cookies})
        http_client = AsyncHTTPClient()

        part = u"%d.%d.%d;%d;%d;%d;%d" % (day_datetime.year, day_datetime.month, day_datetime.day,
                                          service if is_multi_sub_service else sub_service, fns, is_multi_sub_service, sub_service)
        part2 = u"14|CUSTOMCALLBACK%d|" % len(part) + part
        cb_param = u"c0:KV|2;[];GB|%d;" % len(part2) + part2 + ";"

        data = {
            "__CALLBACKID" : u"ctl00$gvTime",
            "__CALLBACKPARAM" : cb_param,
            "__EVENTARGUMENT" : u"",
            "__EVENTTARGET" : u"",
            "__VIEWSTATE" : u"",
            }

        body = urlencode(data)
        response = yield http_client.fetch('http://order.nalog.ru/fns_service/', method='POST', body=body, headers=headers, request_timeout=5)
        response_body = response.body
        if response.code != 200 or not response_body:
            logger.error(u"order.nalog.ru вернул неожиданный ответ")
            raise errors.IfnsServiceUnavailable()

        text_parts = response_body.split('cpFS_ID\':')
        if len(text_parts) < 2:
            logger.error(u"order.nalog.ru вернул неожиданный ответ")
            raise errors.IfnsServiceUnavailable()
        sub_service_fs_id = filter(lambda x: x.isdigit(), text_parts[1])

        data_str = response_body[19:].decode('string_escape').replace('!-\\-', '!--').replace('/-\\-', '/--').replace('\\/script', '/script')
        content = u"<!DOCTYPE html><html><head><title></title></head><body>%s</body></html>" % data_str.decode('utf-8')
        root = html5lib.parse(content, treebuilder='lxml', namespaceHTMLElements=False)

        time_slots = []
        #noinspection PyCallingNonCallable
        for item in CSSSelector('#ctl00_gvTime_DXMainTable tr')(root):
            #noinspection PyCallingNonCallable
            tds = CSSSelector('td')(item)
            if len(tds) > 1:
                time_str = tds[0].text
                #noinspection PyCallingNonCallable
                spans = CSSSelector('span')(tds[1])
                if len(spans):
                    span_style = spans[0].attrib['style']
                    available = 'block' not in span_style
                    #print(time_str, available)
                    if available:
                        hour, minutes = time_str.strip().replace('00', '0').split(':')
                        dt = datetime(2014, 1, 1, int(hour), int(minutes))

                        time_slots.append({
                            "slot_start" : dt.strftime("%H:%M"),
                            "slot_end" : (dt + timedelta(seconds = 1800)).strftime("%H:%M"),
                            })

        if time_slots:
            raise gen.Return({
                'date' : day_datetime.strftime("%Y-%m-%d"),
                'time_slots' : time_slots,
                'sub_service_fs_id' : sub_service_fs_id
            })
        raise gen.Return(None)

    @staticmethod
    @gen.coroutine
    def check_ban(ifns_session_id, day_datetime, cache, logger):
        session_data_str = cache.get(ifns_session_id)
        if not session_data_str:
            raise errors.IfnsSessionExpired()
        try:
            session_data = json.loads(session_data_str)
            fns = session_data['fns']
            cookies = session_data['cookies']
        except Exception:
            logger.exception(u"Failed to load ifns session data")
            raise errors.IfnsSessionExpired()

        data = {
            "__CALLBACKID" : "ctl00$clBanCheck",
            "__CALLBACKPARAM" : "c0:%s.%s.%s;%s;%s;0" % (unicode(day_datetime.year), unicode(day_datetime.month), unicode(day_datetime.day), unicode(180), unicode(fns)),
            "__EVENTARGUMENT" : "",
            "__EVENTTARGET" : "",
            "__VIEWSTATE" : ""
        }
        body = urlencode(data)
        http_client = AsyncHTTPClient()
        headers = httputil.HTTPHeaders({'Cookie' : cookies})
        response = yield http_client.fetch('http://order.nalog.ru/fns_service/', method='POST', body=body, headers = headers, request_timeout=20, follow_redirects=False)
        response_body = response.body

        if response.code != 200 or not response_body:
            logger.error(u"order.nalog.ru вернул неожиданный ответ")
            raise errors.ServerUnavailable()

        if "'data':'0'" in response_body:
            raise gen.Return(True)

        raise gen.Return(False)

    @staticmethod
    @gen.coroutine
    def get_nalog_ru_time_slots_cached(is_person, reg_ifns_name, service, region_name, cache, logger):
        ifns_days_cache_key = AsyncIfnsProvider.get_ifns_days_cache_key(reg_ifns_name, service, is_person, region_name)

        days_cache_str = cache.get(ifns_days_cache_key)
        if not days_cache_str:
            raise CacheMiss()

        try:
            days_cache = json.loads(days_cache_str)
            if not days_cache:
                raise Exception("Empty cache")
        except Exception:
            raise CacheMiss()

        days = [datetime(d[0], d[1], d[2]) for d in days_cache]

        result = []
        for day in days:
            cache_key = AsyncIfnsProvider.get_ifns_day_slots_cache_key(reg_ifns_name, service, is_person, region_name, day)
            day_cache_str = cache.get(cache_key)
            if not day_cache_str:
                continue
            try:
                day_cache = json.loads(day_cache_str)
                result.append(day_cache)
            except Exception:
                pass
        raise gen.Return(result)

    @staticmethod
    def get_nalog_ru_default_time_slots(region_name, reg_ifns_name, is_private_person, first_day = None, days_to_get = None):
        next_day = first_day or (datetime.now() + timedelta(days = 1))
        weekend = {5, 6}
        result = []
        days_to_get = days_to_get or 10
        while len(result) < days_to_get:
            if next_day.weekday() not in weekend:
                result.append({
                    "date" : next_day.strftime("%Y-%m-%d"),
                    "time_slots" : [[{"slot_end": "09:30", "slot_start": "09:00"}, {"slot_end": "10:00", "slot_start": "09:30"}, {"slot_end": "10:30", "slot_start": "10:00"}, {"slot_end": "11:00", "slot_start": "10:30"}, {"slot_end": "11:30", "slot_start": "11:00"}, {"slot_end": "12:00", "slot_start": "11:30"}, {"slot_end": "12:30", "slot_start": "12:00"}, {"slot_end": "13:00", "slot_start": "12:30"}, {"slot_end": "13:30", "slot_start": "13:00"}, {"slot_end": "14:00", "slot_start": "13:30"}, {"slot_end": "14:30", "slot_start": "14:00"}, {"slot_end": "15:00", "slot_start": "14:30"}, {"slot_end": "15:30", "slot_start": "15:00"}, {"slot_end": "16:00", "slot_start": "15:30"}, {"slot_end": "16:30", "slot_start": "16:00"}, {"slot_end": "17:00", "slot_start": "16:30"}, {"slot_end": "17:30", "slot_start": "17:00"}, {"slot_end": "18:00", "slot_start": "17:30"}, {"slot_end": "18:30", "slot_start": "18:00"}, {"slot_end": "19:00", "slot_start": "18:30"}, {"slot_end": "19:30", "slot_start": "19:00"}]],
                    "default" : True
                })

            next_day += timedelta(days = 1)

        return result

    @staticmethod
    @gen.coroutine
    def get_company_person_data_for_ifns(founder_applicant, email, db):
        person_data = None
        company_data = None
        person_col = PrivatePersonDbObject.get_collection(db)
        company_col = CompanyDbObject.get_collection(db)

        if FounderTypeEnum.TYPE_CLS(founder_applicant['founder_type']) == FounderTypeEnum.FT_PERSON:
            r, error = yield gen.Task(person_col.find_one, {'_id' : ObjectId(founder_applicant['person']['id'])})
            person_obj = r[0]
            if not person_obj:
                raise errors.InvalidParameterValue("founder_applicant")
            name = person_obj['name'] if 'name' in person_obj else ''
            surname = person_obj['surname'] if 'surname' in person_obj else ''
            patronymic = person_obj['patronymic'] if 'patronymic' in person_obj else ''
            #noinspection PyTypeChecker
            person_data = {
                "name" : name['nom'] if name and isinstance(name, dict) else name,
                "surname" : surname['nom'] if surname and isinstance(surname, dict) else surname,
                "patronymic" : patronymic.get('nom', u'') if patronymic and isinstance(patronymic, dict) else patronymic,
                "phone" : person_obj.get('phone', ''),
                "email" : email,
                "inn" : person_obj.get('inn', '')
            }
        else:
            r, error = yield gen.Task(company_col.find_one, {'_id' : ObjectId(founder_applicant['company']['id'])})
            company_obj = r[0]
            r, error = yield gen.Task(person_col.find_one, {'_id' : ObjectId(company_obj['general_manager'])})
            general_manager = r[0]
            if not general_manager or not company_obj:
                raise errors.InvalidParameterValue("founder_applicant")
            company_data = {
                "name" : company_obj['full_name'],
                "phone" : general_manager['phone'],
                "email" : email,
                "inn" : company_obj['inn']
            }
        raise gen.Return((company_data, person_data))

    @staticmethod
    @gen.coroutine
    def get_registration_ifns(address_ifns, cache, service_nalog_ru_url):
        if not address_ifns or not isinstance(address_ifns, basestring):
            raise errors.IfnsNotFound()

        cache_key = make_cache_key(address_ifns)
        result_text = cache.get(cache_key)
        if not result_text:
            headers = httputil.HTTPHeaders({
                'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:33.0) Gecko/20100101 Firefox/33.0',
                'Accept-Encoding' : 'gzip, deflate',
                'Accept-Language' : 'en-US,en;q=0.5',
                'Connection' : 'keep-alive',
                'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer' : 'http://order.nalog.ru/'
            })
            http_client = AsyncHTTPClient()

            response = yield http_client.fetch('%s/addrno.do?l=6&g=%s' % (service_nalog_ru_url, address_ifns), method = 'GET', headers = headers, request_timeout=20, follow_redirects=False)
            if response.code != 200:
                raise errors.IfnsNotFound()
            result_text = response.body
            cache.set(cache_key, result_text, 3600 * 24)

        data = None
        try:
            data = json.loads(result_text)
        except Exception:
            pass
        if data:
            raise gen.Return(data["res"])
        raise errors.IfnsNotFound()

    @staticmethod
    @gen.coroutine
    def _get_days(service, sub_service, is_multi_sub_service, fns, headers, logger):
        cb_param = 'c0:%d;%d;%d;%d' % (sub_service, is_multi_sub_service, (service if is_multi_sub_service else sub_service), fns)
        data = {
            "__CALLBACKID":"ctl00$cpday",
            "__CALLBACKPARAM":cb_param,
            "__EVENTTARGET":"",
            "__EVENTARGUMENT":"",
            "__VIEWSTATE" : ""
        }

        body = urlencode(data)
        http_client = AsyncHTTPClient()
        try:
            response = yield http_client.fetch('http://order.nalog.ru/fns_service/', method='POST', body=body, headers = headers, request_timeout=20, follow_redirects=False)
        except HTTPError, ex:
            logger.exception(u"order.nalog.ru вернул ошибку")
            raise errors.IfnsServiceUnavailable()
        except Exception:
            logger.exception(u"Failed to get internal ids for ifns")
            raise errors.ServerUnavailable()

        response_body = response.body
        if response.code != 200 or not response_body:
            logger.error(u"order.nalog.ru вернул неожиданный ответ")
            raise errors.IfnsServiceUnavailable()

        str_data = response_body[26:-3].decode('string_escape').replace('!-\\-', '!--').replace('/-\\-', '/--').replace('\\/script', '/script')
        content = u"<!DOCTYPE html><html><head><title></title></head><body>%s</body></html>" % str_data.decode('utf-8')
        root = html5lib.parse(content, treebuilder='lxml', namespaceHTMLElements=False)

        year = None
        month = None
        #noinspection PyCallingNonCallable
        for item in CSSSelector('#ctl00_cpday_day_T')(root):
            item_text_parts = item.text.split(' ')
            if len(item_text_parts) < 2:
                logger.error(u"Ожидалась дата, получили %s" % item.text)
                raise errors.IfnsServiceUnavailable(u"Invalid nalog.ru service return content")
            try:
                month = MONTHS[item_text_parts[0].strip()]
                year = int(item_text_parts[1].strip())
                break
            except Exception:
                logger.exception(u"Не удалось распарсить дату: %s" % item.text)
                raise errors.IfnsServiceUnavailable(u"Invalid nalog.ru service return content")

        if not month or not year:
            logger.error(u"Дату так и не получили")
            raise Exception(u"Invalid nalog.ru service return content")

        day_prev = -1
        days = []
        simple_days = []
        #noinspection PyCallingNonCallable
        for item in CSSSelector('#ctl00_cpday_day_mt td.dxeCalendarDay')(root):
            classes = filter(lambda x: not not x, [i.strip() for i in item.attrib['class'].split(' ')])
            if 'dxeCalendarOutOfRange' in classes  or 'dxeCalendarToday' in classes:
                continue

            try:
                day = int(item.text)
            except Exception:
                logger.exception(u"Invalid nalog.ru service response: %s" % unicode(item.text))
                raise errors.IfnsServiceUnavailable(u"Invalid nalog.ru service response: %s" % unicode(item.text))
            if day_prev > day:
                month += 1
                if month > 12:
                    year += 1
                    month = 1
            day_prev = day
            d = datetime(year, month, day)
            days.append(d)
            simple_days.append((year, month, day))
        if not days:
            logger.error(u"Invalid nalog.ru service response: no days returned")
            raise errors.IfnsServiceUnavailable(u"Invalid nalog.ru service response: no days returned")
        raise gen.Return((days, simple_days))


    @staticmethod
    @gen.coroutine
    def book_ifns(person_data, company_data, reg_ifns_name, service, region_name, reg_date, reg_responsible_person, cache, logger):
        session_id = yield AsyncIfnsProvider.start_ifns_session(person_data, company_data, reg_ifns_name, service, region_name, cache, logger)

        session_data_str = cache.get(session_id)
        if not session_data_str:
            raise errors.ServerUnavailable()
        try:
            session_data = json.loads(session_data_str)
            cookies = session_data['cookies']
            is_multi_sub_service = session_data['is_multi_sub_service']
            sub_service = session_data['sub_service']
            fns = session_data['fns']
        except Exception:
            logger.exception(u"Failed to load ifns session data")
            raise errors.ServerUnavailable()

        headers = httputil.HTTPHeaders({'Cookie' : cookies})

        days, simple_days = yield AsyncIfnsProvider._get_days(service, sub_service, is_multi_sub_service, fns, headers, logger)

        ifns_days_cache_key = AsyncIfnsProvider.get_ifns_days_cache_key(reg_ifns_name, service, not company_data, region_name)
        days_str = json.dumps(simple_days)
        cache.set(ifns_days_cache_key, days_str)

        # ban check
        d = days[0]

        is_banned = yield AsyncIfnsProvider.check_ban(session_id, d, cache, logger)
        if is_banned:
            raise errors.MaximumRegistrationsExceeded()

        # get time slots
        time_slots = yield AsyncIfnsProvider.get_day_slots(session_id, reg_date, cache, logger)
        if not time_slots:
            raise errors.DayBusyOrHolliday(reg_date)

        found = False
        slot_search_str = reg_date.strftime("%H:%M")
        for slot in time_slots['time_slots']:
            if slot["slot_start"] == slot_search_str:
                found = True
                break

        if not found:
            raise errors.DayBusyOrHolliday(reg_date)

        sub_service_fs_id = time_slots['sub_service_fs_id']
        cb_param = "c0:" + str(reg_date.year) + "." + str(reg_date.month) + "." + str(reg_date.day) + " " + reg_date.strftime("%H:%M:00") +\
                   ";" + str(sub_service_fs_id) + ";" + str(fns) + ";" + str(sub_service) + ";" + str(is_multi_sub_service)

        data = {
            "__CALLBACKID" : "ctl00$clRegister",
            "__CALLBACKPARAM" : cb_param,
            "__EVENTARGUMENT" : "",
            "__EVENTTARGET" : "",
            "__VIEWSTATE" : ""
        }
        body = urlencode(data)
        http_client = AsyncHTTPClient()
        try:
            response = yield http_client.fetch('http://order.nalog.ru/fns_service/', method='POST', body=body, headers = headers, request_timeout=20, follow_redirects=False)
        except HTTPError, ex:
            logger.exception(u"order.nalog.ru вернул ошибку")
            raise errors.IfnsServiceUnavailable()
        except Exception:
            logger.exception(u"Failed to get internal ids for ifns")
            raise errors.ServerUnavailable()

        response_body = response.body
        if response.code != 200 or not response_body:
            logger.error(u"order.nalog.ru вернул неожиданный ответ")
            raise errors.ServerUnavailable()

        if "'DoubleTime'" in response_body:
            raise errors.DuplicateBookingAtTheSameTime()

        result = response_body.decode('utf-8')

        parts = result.split("'data':'")
        if len(parts) < 2:
            logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result)
            raise errors.IfnsServiceUnavailable()
        parts = parts[1].split("'")
        if len(parts) < 2:
            logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result)
            raise errors.IfnsServiceUnavailable()
        code = parts[0].strip()
        logger.debug(u'booking url: http://order.nalog.ru/appointment/R%s/' % code)

        try:
            response = yield http_client.fetch('http://order.nalog.ru/appointment/R%s/' % code, method='GET', request_timeout=20, follow_redirects=False)
        except HTTPError, ex:
            logger.exception(u"order.nalog.ru вернул ошибку")
            raise FailedToGetAppointmentData()
        except Exception:
            logger.exception(u"Failed to get appointment data")
            raise errors.ServerUnavailable()

        if response.code == 302:
            logger.error(u"appointment not found")
            raise errors.IfnsServiceUnavailable()

        response_body = response.body
        if response.code != 200 or not response_body:
            logger.error(u"order.nalog.ru вернул неожиданный ответ")
            raise FailedToGetAppointmentData()

        root = html5lib.parse(response_body.decode('utf-8'), treebuilder='lxml', namespaceHTMLElements=False)

        #noinspection PyCallingNonCallable
        if not len(CSSSelector("#ctl00_pnlDetails")(root)):
            logger.error(result.text)
            raise errors.DuplicateBookingAtTheSameTime()

        if len(CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)) < 18:
            logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result.text)
            raise errors.ServerUnavailable()
        #noinspection PyCallingNonCallable
        ifns =      CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[3].text
        #noinspection PyCallingNonCallable
        address =   CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[5].text
        #noinspection PyCallingNonCallable
        map =       CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[7].text
        #noinspection PyCallingNonCallable
        phone =     CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[9].text
        #noinspection PyCallingNonCallable
        service =   CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[11].text
        #noinspection PyCallingNonCallable
        data_str =  CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[13].text
        #noinspection PyCallingNonCallable
        time_str =  CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[15].text
        #noinspection PyCallingNonCallable
        window =    CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[17].text

        try:
            dt = datetime.strptime(data_str + 'T' + time_str, "%d.%m.%YT%H:%M")
        except Exception:
            raise errors.ServerError(u"Invalid datetime format")

        raise gen.Return({
            "ifns" : ifns,
            "service" : service,
            "date" : dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "window" : window,
            "address" : address,
            "phone" : phone,
            "how_to_get" : map,
            "code" : code
        })

    @staticmethod
    @gen.coroutine
    def get_ifns_by_code(tax_office, service_nalog_ru_url, cache, logger):
        cache_key = make_cache_key('ifns_no_' + unicode(tax_office))
        result_text = cache.get(cache_key)
        if not result_text:
            url = u"%s/addrno.do?l=6&g=%s" % (service_nalog_ru_url, int_to_ifns(tax_office))
            headers = {
                u"Referer" : u"%s/addrno.do" % service_nalog_ru_url,
                u"Accept" : "application/json, text/javascript, */*; q=0.01"
            }
            httputil.HTTPHeaders(headers)
            http_client = AsyncHTTPClient()
            r = yield http_client.fetch(url, method='GET', headers = headers, request_timeout=20, follow_redirects=False)
            if r.code != 200:
                logger.error(u"Invalid response code while requesting ifns %s data" % unicode(tax_office))
                raise gen.Return(None)
            result_text = r.body.decode('utf-8')
            cache.set(cache_key, result_text, 3600 * 24)

        result = None
        try:
            result = json.loads(result_text)
            result = IfnsDescription(result["res"])
        except Exception:
            logger.exception(u"Invalid response (%s) while requesting ifns %s data" % (result_text, unicode(tax_office)))

        raise gen.Return(result)
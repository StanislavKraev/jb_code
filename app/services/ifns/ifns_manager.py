# -*- coding: utf-8 -*-
from copy import deepcopy
from datetime import datetime, timedelta
import json
import logging

from lxml import etree
import requests
import html5lib
from lxml.cssselect import CSSSelector
from flask import current_app

from common_utils import MONTHS, int_to_ifns
from fw.db.sql_base import db as sqldb
from fw.utils import address_utils
from fw.utils.address_utils import prepare_key
from fw.api import errors
from services.ifns.data_model.models import IfnsBookingObject, IfnsCatalogObject


def discard_booking(batch, logger):
    try:
        batch_id = batch.id
        for booking in IfnsBookingObject.query.filter_by(batch_id=batch_id, _discarded=False):
            if not booking.reg_info or 'status' not in booking.reg_info or booking.reg_info['status'] == "registered":
                continue
            booking._discarded = True
            ifns_reg_info = (batch.result_fields or {}).get('ifns_reg_info', None)
            if ifns_reg_info:
                res_fields = batch.result_fields
                del res_fields['ifns_reg_info']
                batch.result_fields = res_fields
                sqldb.session.commit()
            break
    except Exception:
        logger.exception(u"Failed to discard ifns booking")


def get_ifns_data(ifns_code):
    return IfnsCatalogObject.query.filter_by(code=int(ifns_code)).first()


class IfnsDescription(object):
    def __init__(self, json_data, root=True):
        if root:
            self.code = json_data["kod"]
            self.naimk = json_data["naimk"]
            self.plat = deepcopy(json_data["plat"])
            self.rof = IfnsDescription(json_data["rof"], False)
            self.rou = IfnsDescription(json_data["rou"], False)
        else:
            self.code = json_data["code"]
            self.naimk = json_data["naimk"]


def get_ifns_by_address(address, service_nalog_ru_url):
    if not address or not isinstance(address, basestring):
        return

    address_full = current_app.external_tools.get_detailed_address(address)
    if not address_full:
        return
    # noinspection PyUnresolvedReferences
    suggestions = address_full.get("suggestions", [])
    if not suggestions:
        return

    tax_office = unicode(suggestions[0]['data']["tax_office"])
    if not tax_office:
        return

    return get_ifns_by_code(tax_office, service_nalog_ru_url)


def get_ifns_by_code(tax_office, service_nalog_ru_url):
    cache_key = address_utils.prepare_key('ifns_no_' + unicode(tax_office))
    result_text = current_app.external_tools.cache.get(cache_key)
    if not result_text:
        url = u"%s/addrno.do?l=6&g=%s" % (service_nalog_ru_url, int_to_ifns(tax_office))
        headers = {
            u"Referer": u"%s/addrno.do" % service_nalog_ru_url,
            u"Accept": "application/json, text/javascript, */*; q=0.01"
        }
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code != 200:
            return u""
        result_text = r.text
        current_app.external_tools.cache.set(cache_key, result_text, 3600 * 24)

    try:
        result = json.loads(result_text)
        return IfnsDescription(result["res"])
    except Exception:
        pass


def get_nalog_ru_time_slots(person_data, company_data, internal_ifns_number, internal_ifns_service, logger):
    s = requests.Session()
    result = s.get(u'http://order.nalog.ru/details/', timeout=20)
    if result.status_code != 200:
        logger.error(u"Невозможно начать сессию с сервером order.nalog.ru")
        raise errors.ServerUnavailable()

    if company_data:
        data = {
            "ctl00$LastName": company_data['name'],
            "ctl00$inn": company_data['inn'],
            "ctl00$phone": company_data['phone'],
            "ctl00$email": company_data['email'],
            "__VIEWSTATE": u"",
            "ctl00$face": u"0",
            "ctl00$btNext": ""
        }
        # start session
        result = s.post(u'http://order.nalog.ru/details/', data=data, timeout=20)
        if result.status_code != 200 or not result.text:
            logger.error(u"order.nalog.ru вернул неожиданный код: %s" % unicode(result.status_code))
            raise errors.ServerUnavailable()
    elif person_data:
        data = {
            "ctl00$LastName": person_data['surname'],
            "ctl00$FirstName": person_data['name'],
            "ctl00$SecondName": person_data['patronymic'] or u"",
            "ctl00$inn": person_data['inn'],
            "ctl00$phone": person_data['phone'] or u"",
            "ctl00$email": person_data['email'],
            "__VIEWSTATE": u"",
            "ctl00$face": u"1",
            "ctl00$btNext": ""
        }
        result = s.post(u'http://order.nalog.ru/details/', data=data, timeout=20)
        if result.status_code != 200 or not result.text:
            logger.error(u"order.nalog.ru вернул неожиданный код: %s" % unicode(result.status_code))
            raise errors.ServerUnavailable()
    else:
        logger.error(u"Invalid parameters")
        raise errors.ServerError()

    fns, sub_service = internal_ifns_number, internal_ifns_service  # get_ifns_internal_id_by_ifns_name(s, region_name, reg_ifns_name, not company_data, logger, service)
    service = 0
    is_multi_sub_service = 0

    cb_param = 'c0:%d;%d;%d;%d' % (
        sub_service, is_multi_sub_service, (service if is_multi_sub_service else sub_service), fns)
    data = {
        "__CALLBACKID": u"ctl00$cpday",
        "__CALLBACKPARAM": cb_param,
        "__EVENTTARGET": u"",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": u"",
    }

    result = s.post(u'http://order.nalog.ru/fns_service/', data=data, timeout=20)
    if result.status_code != 200 or not result.content:
        logger.error(u"order.nalog.ru вернул неожиданный ответ")
        raise errors.ServerUnavailable()

    str_data = result.text[26:-3].encode('utf-8').decode('string_escape').replace('!-\\-', '!--').replace('/-\\-',
                                                                                                          '/--').replace(
        '\\/script', '/script')
    content = u"<!DOCTYPE html><html><head><title></title></head><body>%s</body></html>" % str_data.decode('utf-8')
    root = html5lib.parse(content, treebuilder='lxml', namespaceHTMLElements=False)

    year = None
    month = None
    # noinspection PyCallingNonCallable
    for item in CSSSelector('#ctl00_cpday_day_T')(root):
        item_text_parts = item.text.split(' ')
        if len(item_text_parts) < 2:
            logger.error(u"Ожидалась дата, получили %s" % item.text)
            raise errors.ServerUnavailable(u"Invalid nalog.ru service return content")
        try:
            month = MONTHS[item_text_parts[0].strip()]
            year = int(item_text_parts[1].strip())
            break
        except Exception:
            logger.error(u"Не удалось распарсить дату: %s" % item.text)
            raise errors.ServerUnavailable(u"Invalid nalog.ru service return content")

    if not month or not year:
        logger.error(u"Дату так и не получили")
        raise Exception(u"Invalid nalog.ru service return content")

    day_prev = -1
    days = []
    first = True
    #noinspection PyCallingNonCallable
    for item in CSSSelector('#ctl00_cpday_day_mt td.dxeCalendarDay')(root):
        #logger.info('month: %s, item:%s' % (str(month), stringify_children(item)))
        classes = filter(lambda x: not not x, [i.strip() for i in item.attrib['class'].split(' ')])
        #logger.info('classes:%s' % unicode(classes))

        try:
            day = int(item.text)
            if first and (23 <= day <= 31):
                month -= 1  # (facepalm)
            first = False
        except Exception:
            logger.error(u"Invalid nalog.ru service response: %s" % unicode(item.text))
            raise errors.ServerUnavailable(u"Invalid nalog.ru service response: %s" % unicode(item.text))
        if day_prev > day:
            month += 1
            #logger.info('increase month:%s'%str(month))
            if month > 12:
                year += 1
                month = 1
        day_prev = day
        if 'dxeCalendarOutOfRange' in classes or 'dxeCalendarToday' in classes:
            #logger.info('skip')
            continue
        d = datetime(year, month, day)
        if d not in (datetime(2015, 5, 1), datetime(2015, 5, 2), datetime(2015, 5, 3), datetime(2015, 5, 4),
                     datetime(2015, 5, 9), datetime(2015, 5, 10), datetime(2015, 5, 11)):
            days.append(d)

    if not days:
        logger.error(u"Invalid nalog.ru service response: no days returned")
        raise errors.ServerUnavailable(u"Invalid nalog.ru service response: no days returned")

    # ban check
    d = days[0]
    result = s.post('http://order.nalog.ru/fns_service/', data={
        "__CALLBACKID": u"ctl00$clBanCheck",
        "__CALLBACKPARAM": u"c0:%s.%s.%s;%s;%s;0" % (
            unicode(d.year), unicode(d.month), unicode(d.day), unicode(180), unicode(fns)),
        "__EVENTARGUMENT": u"",
        "__EVENTTARGET": u"",
        "__VIEWSTATE": u"",
    }, timeout=20)

    if result.status_code != 200 or not result.content:
        logger.error(u"order.nalog.ru вернул неожиданный ответ")
        raise errors.ServerUnavailable()

    if "'data':'0'" in result.text:
        raise errors.MaximumRegistrationsExceeded()

    day_info = []
    # get time slots
    for d in days:
        part = u"%d.%d.%d;%d;%d;%d;%d" % (
            d.year, d.month, d.day, service if is_multi_sub_service else sub_service, fns, is_multi_sub_service,
            sub_service)
        part2 = u"14|CUSTOMCALLBACK%d|" % len(part) + part
        cb_param = u"c0:KV|2;[];GB|%d;" % len(part2) + part2 + ";"

        data = {
            "__CALLBACKID": u"ctl00$gvTime",
            "__CALLBACKPARAM": cb_param,
            "__EVENTARGUMENT": u"",
            "__EVENTTARGET": u"",
            "__VIEWSTATE": u"",
        }

        result = s.post('http://order.nalog.ru/fns_service/', data=data, timeout=20)
        if result.status_code != 200 or not result.content:
            logger.error(u"order.nalog.ru вернул неожиданный ответ")
            raise errors.ServerUnavailable()

        data_str = result.text[19:].encode('utf-8').decode('string_escape').replace('!-\\-', '!--').replace('/-\\-',
                                                                                                            '/--').replace(
            '\\/script', '/script')
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
                            "slot_start": dt.strftime("%H:%M"),
                            "slot_end": (dt + timedelta(seconds=1800)).strftime("%H:%M"),
                        })

        if time_slots:
            day_info.append({
                'date': d.strftime("%Y-%m-%d"),
                'time_slots': time_slots
            })
    return day_info


def book_ifns(person_data, company_data, internal_ifns_number, internal_ifns_service, dt, logger):
    s = requests.Session()
    result = s.get(u'http://order.nalog.ru/details/')
    if result.status_code != 200:
        logger.error(u"Невозможно начать сессию с сервером order.nalog.ru")
        raise errors.ServerUnavailable()

    test_str = u"Укажите параметры для записи на посещение ИФНС России"
    ok = False
    if company_data:
        for x in range(4):
            result = s.post(u'http://order.nalog.ru/details/', data={
                "ctl00$LastName": company_data['name'],
                "ctl00$inn": company_data['inn'],
                "ctl00$phone": company_data['phone'],
                "ctl00$email": company_data['email'],
                "__VIEWSTATE": u"",
                "ctl00$face": u"0",
                "ctl00$btNext": ""
            }, timeout=20)
            if result.status_code != 200:
                logger.error(u"order.nalog.ru вернул неожиданный код: %s" % unicode(result.status_code))
                raise errors.ServerUnavailable()
            content = result.content.decode('utf-8')

            if test_str in content:
                ok = True
                break
        if not ok:
            logger.error(u"Не удалось начать работу с order.nalog.ru")
            raise errors.ServerUnavailable()
    elif person_data:
        for x in range(4):
            result = s.post(u'http://order.nalog.ru/details/', data={
                "ctl00$LastName": person_data['surname'],
                "ctl00$FirstName": person_data['name'],
                "ctl00$SecondName": person_data['patronymic'] or u"",
                "ctl00$inn": person_data['inn'],
                "ctl00$phone": person_data['phone'],
                "ctl00$email": person_data['email'],
                "__VIEWSTATE": u"",
                "ctl00$face": u"1",
                "ctl00$btNext": ""
            }, timeout=20)
            if result.status_code != 200:
                logger.error(u"order.nalog.ru вернул неожиданный код: %s" % unicode(result.status_code))
                raise errors.ServerUnavailable()
            content = result.content.decode('utf-8')

            if test_str in content:
                ok = True
                break
        if not ok:
            logger.error(u"Не удалось начать работу с order.nalog.ru")
            raise errors.ServerUnavailable()

    fns, sub_service = internal_ifns_number, internal_ifns_service  # get_ifns_internal_id_by_ifns_name(s, region_name, reg_ifns_name, not company_data, logger)

    service = None
    is_multi_sub_service = 0

    cb_param = 'c0:%d;%d;%d;%d' % (
        sub_service, is_multi_sub_service, (service if is_multi_sub_service else sub_service), fns)
    result = s.post(u'http://order.nalog.ru/fns_service/', data={
        "__CALLBACKID": u"ctl00$cpday",
        "__CALLBACKPARAM": cb_param,
        "__EVENTTARGET": u"",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": u"",
    }, timeout=20)
    if result.status_code != 200:
        logger.error(u"order.nalog.ru вернул неожиданный код: %s" % unicode(result.status_code))
        raise errors.ServerUnavailable()

    str_data = result.text[26:-3].encode('utf-8').decode('string_escape').replace('!-\\-', '!--').replace('/-\\-',
                                                                                                          '/--').replace(
        '\\/script', '/script')
    content = u"<!DOCTYPE html><html><head><title></title></head><body>%s</body></html>" % str_data.decode('utf-8')
    root = html5lib.parse(content, treebuilder='lxml', namespaceHTMLElements=False)

    year = None
    month = None
    # noinspection PyCallingNonCallable
    for item in CSSSelector('#ctl00_cpday_day_T')(root):
        item_text_parts = item.text.split(' ')
        if len(item_text_parts) < 2:
            logger.error(u"Ожидалась дата, получили %s" % item.text)
            raise errors.ServerUnavailable(u"Invalid nalog.ru service return content")
        try:
            month = MONTHS[item_text_parts[0].strip()]
            year = int(item_text_parts[1].strip())
            break
        except Exception:
            logger.error(u"Не удалось распарсить дату: %s" % item.text)
            raise errors.ServerUnavailable(u"Invalid nalog.ru service return content")

    if not month or not year:
        logger.error(u"Дату так и не получили")
        raise Exception(u"Invalid nalog.ru service return content")

    day_prev = -1
    days = []
    first = True
    #noinspection PyCallingNonCallable
    for item in CSSSelector('#ctl00_cpday_day_mt td.dxeCalendarDay')(root):
        classes = filter(lambda x: not not x, [i.strip() for i in item.attrib['class'].split(' ')])

        day = int(item.text)
        if first and (23 <= day <= 31):
            month -= 1
        first = False
        if day_prev > day:
            month += 1
            if month > 12:
                year += 1
                month = 1
        day_prev = day
        if 'dxeCalendarOutOfRange' in classes or 'dxeCalendarToday' in classes:
            continue
        d = datetime(year, month, day)
        if d not in (
                datetime(2015, 5, 1), datetime(2015, 5, 2), datetime(2015, 5, 3), datetime(2015, 5, 4), datetime(2015, 5, 9),
                datetime(2015, 5, 10), datetime(2015, 5, 11)):
            days.append(d)

    # ban check
    d = days[0]
    result = s.post('http://order.nalog.ru/fns_service/', data={
        "__CALLBACKID": u"ctl00$clBanCheck",
        "__CALLBACKPARAM": u"c0:%s.%s.%s;%s;%s;0" % (
            unicode(d.year), unicode(d.month), unicode(d.day), unicode(180), unicode(fns)),
        "__EVENTARGUMENT": u"",
        "__EVENTTARGET": u"",
        "__VIEWSTATE": u"",
    }, timeout=20)

    if result.status_code != 200 or not result.content:
        logger.error(u"order.nalog.ru вернул неожиданный ответ")
        raise errors.ServerUnavailable()

    if u"'data':'0'" in result.text:
        raise errors.MaximumRegistrationsExceeded()

    # get time slots
    part = u"%d.%d.%d;%d;%d;%d;%d" % (
        dt.year, dt.month, dt.day, service if is_multi_sub_service else sub_service, fns, is_multi_sub_service,
        sub_service)
    part2 = u"14|CUSTOMCALLBACK%d|" % len(part) + part
    cb_param = u"c0:KV|2;[];GB|%d;" % len(part2) + part2 + ";"
    result = s.post('http://order.nalog.ru/fns_service/', data={
        "__CALLBACKID": u"ctl00$gvTime",
        "__CALLBACKPARAM": cb_param,
        "__EVENTARGUMENT": u"",
        "__EVENTTARGET": u"",
        "__VIEWSTATE": u"",
    }, timeout=20)
    if result.status_code != 200 or not result.content:
        logger.error(u"order.nalog.ru вернул неожиданный ответ")
        raise errors.ServerUnavailable()

    if u"К сожалению, на указанную Вами услугу и дату полная запись. Предлагаем  выбрать другую удобную для Вас дату." in result.text:
        raise errors.DayBusyOrHolliday(dt)
    text_parts = result.text.split('cpFS_ID\':')
    if len(text_parts) < 2:
        logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result.text)
        raise errors.ServerUnavailable()

    sub_service_fs_id = filter(lambda x: x.isdigit(), text_parts[1])
    cb_param = u"c0:" + unicode(dt.year) + u"." + unicode(dt.month) + u"." + unicode(dt.day) + u" " + dt.strftime(
        "%H:%M:00") + \
               ";" + unicode(sub_service_fs_id) + u";" + unicode(fns) + u";" + unicode(sub_service) + ";" + unicode(
        is_multi_sub_service)

    result = s.post('http://order.nalog.ru/fns_service/', data={
        "__CALLBACKID": u"ctl00$clRegister",
        "__CALLBACKPARAM": cb_param,
        "__EVENTARGUMENT": u"",
        "__EVENTTARGET": u"",
        "__VIEWSTATE": u"",
    }, timeout=20)

    if result.status_code != 200 or not result.content:
        logger.error(u"order.nalog.ru вернул неожиданный ответ")
        raise errors.ServerUnavailable()

    if "'DoubleTime'" in result:
        raise errors.DuplicateBookingAtTheSameTime()

    logger.error(result.text)
    result = result.content.decode('utf-8')

    parts = result.split("'data':'")
    if len(parts) < 2:
        logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result)
    parts = parts[1].split("'")
    if len(parts) < 2:
        logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result)
    code = parts[0].strip()
    logger.debug(u'booking url: http://order.nalog.ru/appointment/R%s/' % code)

    result = requests.get(u'http://order.nalog.ru/appointment/R%s/' % code, timeout=20)
    if result.status_code != 200 or not result.content:
        logger.error(u"order.nalog.ru вернул неожиданный ответ")
        raise errors.ServerUnavailable()
    root = html5lib.parse(result.text, treebuilder='lxml', namespaceHTMLElements=False)

    #noinspection PyCallingNonCallable
    if not len(CSSSelector("#ctl00_pnlDetails")(root)):
        logger.error(result.text)
        raise errors.DuplicateBookingAtTheSameTime()

    if len(CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)) < 18:
        logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result.text)
        raise errors.ServerUnavailable()
    #noinspection PyCallingNonCallable
    ifns = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[3].text
    #noinspection PyCallingNonCallable
    address = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[5].text
    #noinspection PyCallingNonCallable
    map = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[7].text
    #noinspection PyCallingNonCallable
    phone = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[9].text
    #noinspection PyCallingNonCallable
    service = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[11].text
    #noinspection PyCallingNonCallable
    data_str = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[13].text
    #noinspection PyCallingNonCallable
    time_str = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[15].text
    #noinspection PyCallingNonCallable
    window = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[17].text

    try:
        dt = datetime.strptime(data_str + 'T' + time_str, "%d.%m.%YT%H:%M")
    except Exception:
        raise errors.ServerError(u"Invalid datetime format")

    return {
        "ifns": ifns,
        "service": service,
        "date": dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "window": window,
        "address": address,
        "phone": phone,
        "how_to_get": map,
        "code": code
    }


def get_registration_ifns(service_nalog_ru_url, address_ifns=None):
    if not address_ifns or not isinstance(address_ifns, basestring):
        raise errors.IfnsNotFound()

    result_text = current_app.external_tools.cache.get(prepare_key(address_ifns))
    if not result_text:
        result = requests.get('%s/addrno.do?l=6&g=%s' % (service_nalog_ru_url, address_ifns), headers={
            'Referer': '%s/addrno.do' % service_nalog_ru_url
        }, timeout=5)
        if not result or result.status_code != 200:
            raise errors.IfnsNotFound()
        result_text = result.text
        current_app.external_tools.cache.set(prepare_key(address_ifns), result_text, 3600 * 24)

    try:
        data = json.loads(result_text)
        return data["res"]
    except Exception:
        pass
    raise errors.IfnsNotFound()


def stringify_children(node):
    s = node.text
    if s is None:
        s = ''
    for child in node:
        s += etree.tostring(child, encoding='unicode')
    return s


def get_ifns_registrations(name, company_type=u'ooo', date_from=None, date_to=None,
                           service=None, ifns=None, service_nalog_ru_url=None, logger=None):
    from services.llc_reg.documents.enums import IfnsServiceEnum
    service = service or IfnsServiceEnum.IS_REG_COMPANY

    logger = logger or logging.getLogger()
    if service == IfnsServiceEnum.IS_REG_COMPANY:
        service_str = u"Р11001"
    elif service == IfnsServiceEnum.IS_REG_IP:
        service_str = u"P21001"
    else:
        return

    try:
        s = requests.Session()
        s.get('%s/uwsfind.do' % service_nalog_ru_url, timeout=20)
        reg_ifns = ifns
        req_data = {
            "dtfrom": date_from.strftime("%d.%m.%Y") if date_from else u"",  # 06.06.2014
            "dtto": date_to.strftime("%d.%m.%Y") if date_to else u"",  # 27.10.2014
            "frm": service_str,  #
            "frmip": u"",
            "ifns": reg_ifns,  # 78086
            "name": name,
            "nptype": u"ul",
            "ogrn": u"",
            "ogrnip": u""
        }
        result = s.post('%s/uwsfind.do' % service_nalog_ru_url, data=req_data, timeout=20)
        if not result or result.status_code != 200:
            raise Exception(u"Unexpected result")
        data = result.text
    except Exception, ex:
        logger.exception(u"Failed to get reservations")
        return

    root = html5lib.parse(data, treebuilder='lxml', namespaceHTMLElements=False)

    found_registries = CSSSelector("#uwsfound span")(root)
    if not len(found_registries):
        return
    try:
        results_count = int(found_registries[0].text.strip())
        if not results_count:
            raise Exception(u"Not found")
    except Exception, ex:
        return

    table = CSSSelector("#uwsdata tbody tr")(root)
    if not table or not len(table):
        return

    result_items = []
    upper_name = name.upper()
    while '  ' in upper_name:
        upper_name = upper_name.replace('  ', ' ')
    for item in table:
        result_item = {}
        reshenie = False
        for td in CSSSelector("td")(item):
            td_str = stringify_children(td)
            if not td_str:
                continue

            td_str = td_str.strip()
            td_str = td_str.replace('<br>', '<br/>')
            for part in td_str.split('<br/>'):
                part = part.strip()
                if u"Наименование:" in part:
                    result_item['full_name'] = part.split('</strong>')[1].strip()
                if u"ОГРН:" in part:
                    result_item['ogrn'] = part.split('</strong>')[1].strip()
                if u"ОГРНИП:" in part:
                    result_item['ogrnip'] = part.split('</strong>')[1].strip()
                if u"ФИО::" in part:
                    result_item['fio'] = part.split('</strong>')[1].strip()

                if u"Вид решения:" in part:
                    reshenie = True
                    res = part.split('</strong>')[1].strip()
                    if u'Решение о государственной регистрации' in res:
                        result_item['status'] = 'registered'
                    elif u'Решение об отказе в государственной регистрации' in res:
                        result_item['status'] = 'registration_declined'
                    else:
                        result_item['status'] = 'unknown'

                if u"Дата готовности документов:" in part:
                    res = part.split('</strong>')[1].strip()
                    result_item['reg_date'] = res
        if 'reg_date' in result_item and not reshenie:
            result_item['status'] = 'progress'

        if 'full_name' in result_item:
            res_full_name = result_item['full_name'].upper()
            if not res_full_name:
                continue
            while '  ' in res_full_name:
                res_full_name = res_full_name.replace('  ', ' ')
            if res_full_name == u"ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ \"%s\"" % upper_name or \
               res_full_name == u"ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ %s" % upper_name or \
               res_full_name == u"ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ «%s»" % upper_name or \
               res_full_name == u"ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ ‹‹%s››" % upper_name:
                result_items.append(result_item)
        elif 'fio' in result_item:
            result_items.append(result_item)
    return result_items

def if_gp_pay_working():
    data = {
        "addrFl": "117105,77,,,,ВАРШАВСКОЕ Ш,17,,25",
        "addrFl_ifns": "7726",
        "addrFl_okatom": "45296561000",
        "addrUl": "117105,77,,,,ВАРШАВСКОЕ Ш,17,,24",
        "addrUl_ifns": "7726",
        "addrUl_okatom": "45296561000",
        "bank": "",
        "c": "",
        "fam": "Долгов",
        "gp": "11|18210807010011000110|13|ul|4000",
        "inn": "772900273375",
        "nam": "Центр",
        "otch": "Иванович",
        "payKind": "on",
        "region": "",
        "sum": "4000"
    }
    response = requests.post('https://service.nalog.ru/gp-pay.do', data, timeout=20)
    return response.status_code == 200 and 'application/pdf' == response.headers['content-type']

# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging

from celery import current_task, current_app as celery


celery.config_from_envvar('CELERY_CONFIG_MODULE')


def _is_task_expired(dt):
    return dt - datetime > timedelta(seconds=2 * 3600)


def _get_ifns_logger():
    logger = logging.getLogger("IFNS")
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('/var/log/jb/ifns.log')  # todo: config
    file_handler.setLevel(logging.DEBUG)
    _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(_formatter)
    logger.addHandler(file_handler)
    return logger


@celery.task()
def book_ifns(task_id):
    request = current_task.request
    config = celery.conf.get('config')
    db = celery.conf.get('db')
    logger = _get_ifns_logger()
    ifns_admin_email = config['ifns_admin_email']

# task_data = IfnsBookingTaskDbObject.find_one(db, {'_id' : ObjectId(task_id)})
#    if not task_data:
#        logger.error(u"Invalid task id: %s" % task_id)
#        return False
#
#    person_data = task_data["person_data"]
#    company_data = task_data["company_data"]
#    reg_ifns_name = task_data["reg_ifns_name"]
#    service_id = task_data["service"]
#    region_name = task_data["region_name"]
#    dt = datetime.strptime(task_data["reg_date"], "%Y-%m-%dT%H:%M:%S")
#    batch_id = task_data["batch_id"]
#    user_email = task_data["user_email"]
#    status = task_data["status"]
#    _update_task(task_id, {
#        'status' : IfnsBookingTaskStatus.BTS_PROGRESS,
#        'task_id' : request.id
#    })
#
#    if status != IfnsBookingTaskStatus.BTS_NEW:
#        logger.error(u"Invalid task status: %s" % status)
#        return False
#
#    with TaskFileIdHolder(request.id, config) as task_file:
#        s = requests.Session()
#        try:
#            test_str = u"Укажите параметры для записи на посещение ИФНС России"
#            ok = False
#            if company_data:
#                for x in range(4):
#                    result = s.post(u'http://order.nalog.ru/details/', data={
#                        "ctl00$LastName"	: company_data['name'],
#                        "ctl00$inn"	: company_data['inn'],
#                        "ctl00$phone"	: company_data['phone'],
#                        "ctl00$email"	: company_data['email'],
#                        "__VIEWSTATE" : u"",
#                        "ctl00$face"	: u"0",
#                        "ctl00$btNext" : ""
#                    }, timeout=20)
#                    if result.status_code != 200:
#                        logger.error(u"order.nalog.ru вернул неожиданный код: %s" % unicode(result.status_code))
#                        raise errors.IfnsServiceUnavailable()
#                    content = result.content.decode('utf-8')
#
#                    if test_str in content:
#                        ok = True
#                        break
#                if not ok:
#                    logger.error(u"Не удалось начать работу с order.nalog.ru")
#                    raise errors.IfnsServiceUnavailable()
#            elif person_data:
#                for x in range(4):
#                    result = s.post(u'http://order.nalog.ru/details/', data={
#                        "ctl00$LastName"	: person_data['surname'],
#                        "ctl00$FirstName"	: person_data['name'],
#                        "ctl00$SecondName"  : person_data['patronymic'] or u"",
#                        "ctl00$inn"	: person_data['inn'],
#                        "ctl00$phone"	: person_data['phone'],
#                        "ctl00$email"	: person_data['email'],
#                        "__VIEWSTATE" : u"",
#                        "ctl00$face"	: u"1",
#                        "ctl00$btNext" : ""
#                    }, timeout=20)
#                    if result.status_code != 200:
#                        logger.error(u"order.nalog.ru вернул неожиданный код: %s" % unicode(result.status_code))
#                        raise errors.IfnsServiceUnavailable()
#                    content = result.content.decode('utf-8')
#
#                    if test_str in content:
#                        ok = True
#                        break
#                if not ok:
#                    logger.error(u"Не удалось начать работу с order.nalog.ru")
#                    raise errors.IfnsServiceUnavailable()
#
#            try:
#                fns, sub_service = get_ifns_internal_id_by_ifns_name(s, region_name, reg_ifns_name, not company_data, logger)
#            except Exception, ex:
#                logger.exception(u"Failed to get internal ids for ifns")
#                send_email.send_email(ifns_admin_email, 'failed_to_book_ifns')
#                _update_task(task_id, {
#                    'status' : IfnsBookingTaskStatus.BTS_FAIL,
#                    'error_info' : {
#                        "tag" : "get_ifns_internal_id_by_ifns_name",
#                        "exc" : unicode(ex)
#                    }
#                })
#                return False
#
#            service = None
#            is_multi_sub_service = 0
#
#            cb_param = 'c0:%d;%d;%d;%d' % (sub_service, is_multi_sub_service, (service if is_multi_sub_service else sub_service), fns)
#            result = s.post(u'http://order.nalog.ru/fns_service/', data = {
#                "__CALLBACKID":u"ctl00$cpday",
#                "__CALLBACKPARAM":cb_param,
#                "__EVENTTARGET":u"",
#                "__EVENTARGUMENT":"",
#                "__VIEWSTATE" : u"",
#                }, timeout=20)
#            if result.status_code != 200:
#                logger.error(u"order.nalog.ru вернул неожиданный код: %s" % unicode(result.status_code))
#                raise errors.IfnsServiceUnavailable()
#
#            str_data = result.text[26:-3].encode('utf-8').decode('string_escape').replace('!-\\-', '!--').replace('/-\\-', '/--').replace('\\/script', '/script')
#            content = u"<!DOCTYPE html><html><head><title></title></head><body>%s</body></html>" % str_data.decode('utf-8')
#            root = html5lib.parse(content, treebuilder='lxml', namespaceHTMLElements=False)
#
#            year = None
#            month = None
#            #noinspection PyCallingNonCallable
#            for item in CSSSelector('#ctl00_cpday_day_T')(root):
#                item_text_parts = item.text.split(' ')
#                if len(item_text_parts) < 2:
#                    logger.error(u"Ожидалась дата, получили %s" % item.text)
#                    raise errors.IfnsServiceUnavailable(u"Invalid nalog.ru service return content")
#                try:
#                    month = MONTHS[item_text_parts[0].strip()]
#                    year = int(item_text_parts[1].strip())
#                    break
#                except Exception:
#                    logger.error(u"Не удалось распарсить дату: %s" % item.text)
#                    raise errors.IfnsServiceUnavailable(u"Invalid nalog.ru service return content")
#
#            if not month or not year:
#                logger.error(u"Дату так и не получили")
#                raise errors.IfnsServiceUnavailable(u"Invalid nalog.ru service return content")
#
#            day_prev = -1
#            days = []
#            #noinspection PyCallingNonCallable
#            for item in CSSSelector('#ctl00_cpday_day_mt td.dxeCalendarDay')(root):
#                classes = filter(lambda x: not not x, [i.strip() for i in item.attrib['class'].split(' ')])
#                if 'dxeCalendarOutOfRange' in classes  or 'dxeCalendarToday' in classes:
#                    continue
#
#                day = int(item.text)
#                if day_prev > day:
#                    month += 1
#                    if month > 12:
#                        year += 1
#                        month = 1
#                day_prev = day
#                d = datetime(year, month, day)
#                days.append(d)
#
#            # ban check
#            d = days[0]
#            result= s.post('http://order.nalog.ru/fns_service/', data = {
#                "__CALLBACKID" : u"ctl00$clBanCheck",
#                "__CALLBACKPARAM" : u"c0:%s.%s.%s;%s;%s;0" % (unicode(d.year), unicode(d.month), unicode(d.day), unicode(180), unicode(fns)),
#                "__EVENTARGUMENT" : u"",
#                "__EVENTTARGET" : u"",
#                "__VIEWSTATE" : u"",
#                }, timeout=20)
#
#            if result.status_code != 200 or not result.content:
#                logger.error(u"order.nalog.ru вернул неожиданный ответ")
#                raise errors.IfnsServiceUnavailable()
#
#            if u"'data':'0'" in result.text:
#                send_email.send_email(user_email, 'ifns_maximum_registrations_exceeded')
#                _update_task(task_id, {
#                    'status' : IfnsBookingTaskStatus.BTS_SUCCESS,
#                    'error_info' : {
#                        "tag" : "MaximumRegistrationsExceeded"
#                    }
#                })
#                return False
#
#            # get time slots
#            part = u"%d.%d.%d;%d;%d;%d;%d" % (dt.year, dt.month, dt.day, service if is_multi_sub_service else sub_service, fns, is_multi_sub_service,sub_service)
#            part2 = u"14|CUSTOMCALLBACK%d|" % len(part) + part
#            cb_param = u"c0:KV|2;[];GB|%d;" % len(part2) + part2 + ";"
#            result= s.post('http://order.nalog.ru/fns_service/', data = {
#                "__CALLBACKID" : u"ctl00$gvTime",
#                "__CALLBACKPARAM" : cb_param,
#                "__EVENTARGUMENT" : u"",
#                "__EVENTTARGET" : u"",
#                "__VIEWSTATE" : u"",
#                }, timeout=20)
#            if result.status_code != 200 or not result.content:
#                logger.error(u"order.nalog.ru вернул неожиданный ответ")
#                raise errors.IfnsServiceUnavailable()
#
#            if u"К сожалению, на указанную Вами услугу и дату полная запись. Предлагаем  выбрать другую удобную для Вас дату." in result.text:
#                send_email.send_email(user_email, 'ifns_no_free_slots')
#                _update_task(task_id, {
#                    'status' : IfnsBookingTaskStatus.BTS_SUCCESS,
#                    'error_info' : {
#                        "tag" : "no_free_slots"
#                    }
#                })
#                return False
#
#            text_parts = result.text.split('cpFS_ID\':')
#            if len(text_parts) < 2:
#                logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result.text)
#                raise errors.IfnsServiceUnavailable()
#
#            sub_service_fs_id = filter(lambda x: x.isdigit(), text_parts[1])
#            cb_param = u"c0:" + unicode(dt.year) + u"." + unicode(dt.month) + u"." + unicode(dt.day) + u" " + dt.strftime("%H:%M:00") +\
#                       ";" + unicode(sub_service_fs_id) + u";" + unicode(fns) + u";" + unicode(sub_service) + ";" + unicode(is_multi_sub_service)
#
#            result= s.post('http://order.nalog.ru/fns_service/', data = {
#                "__CALLBACKID" : u"ctl00$clRegister",
#                "__CALLBACKPARAM" : cb_param,
#                "__EVENTARGUMENT" : u"",
#                "__EVENTTARGET" : u"",
#                "__VIEWSTATE" : u"",
#                }, timeout=20)
#
#            if result.status_code != 200 or not result.content:
#                logger.error(u"order.nalog.ru вернул неожиданный ответ")
#                raise errors.IfnsServiceUnavailable()
#
#            if "'DoubleTime'" in result.content:
#                send_email.send_email(user_email, 'ifns_duplicate_booking')
#                _update_task(task_id, {
#                    'status' : IfnsBookingTaskStatus.BTS_SUCCESS,
#                    'error_info' : {
#                        "tag" : "DuplicateBookingAtTheSameTime"
#                    }
#                })
#                return False
#
#            result = result.content.decode('utf-8')
#
#            parts = result.split("'data':'")
#            if len(parts) < 2:
#                logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result)
#                raise errors.IfnsServiceUnavailable()
#
#            parts = parts[1].split("'")
#            if len(parts) < 2:
#                logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result)
#                raise errors.IfnsServiceUnavailable()
#
#            code = parts[0].strip()
#            #logger.debug(u'booking url: http://order.nalog.ru/appointment/R%s/' % code)
#
#            result = requests.get(u'http://order.nalog.ru/appointment/R%s/' % code, timeout=20)
#            if result.status_code != 200 or not result.content:
#                logger.error(u"order.nalog.ru вернул неожиданный ответ")
#                raise errors.IfnsServiceUnavailable()
#
#            root = html5lib.parse(result.text, treebuilder='lxml', namespaceHTMLElements=False)
#
#            #noinspection PyCallingNonCallable
#            if not len(CSSSelector("#ctl00_pnlDetails")(root)):
#                send_email.send_email(user_email, 'ifns_duplicate_booking')
#                _update_task(task_id, {
#                    'status' : IfnsBookingTaskStatus.BTS_SUCCESS,
#                    'error_info' : {
#                        "tag" : "DuplicateBookingAtTheSameTime"
#                    }
#                })
#                return False
#
#            if len(CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)) < 18:
#                logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result.text)
#                raise errors.IfnsServiceUnavailable()
#                #noinspection PyCallingNonCallable
#            ifns =      CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[3].text
#            #noinspection PyCallingNonCallable
#            address =   CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[5].text
#            #noinspection PyCallingNonCallable
#            map =       CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[7].text
#            #noinspection PyCallingNonCallable
#            phone =     CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[9].text
#            #noinspection PyCallingNonCallable
#            service =   CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[11].text
#            #noinspection PyCallingNonCallable
#            data_str =  CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[13].text
#            #noinspection PyCallingNonCallable
#            time_str =  CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[15].text
#            #noinspection PyCallingNonCallable
#            window =    CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[17].text
#
#            try:
#                dt = datetime.strptime(data_str + 'T' + time_str, "%d.%m.%YT%H:%M")
#            except Exception:
#                raise errors.IfnsServiceUnavailable(u"Invalid datetime format")
#
#            send_email.send_email(user_email, 'ifns_booking_success')
#            _update_task(task_id, {
#                'status' : IfnsBookingTaskStatus.BTS_SUCCESS,
#            })
#
#            booking = IfnsBooking.parse_raw_value({
#                'ifns' : ifns,
#                'service' : service,
#                'service_id' : service_id,
#                'date' : dt.strftime("%Y-%m-%dT%H:%M:%S"),
#                'window' : window,
#                'address' : address,
#                'phone' : phone,
#                'how_to_get' : map,
#                'code' : code,
#                '_discarded' : False
#            }, api_data = True)
#            booking_db_obj = booking.get_db_object()
#            booking_db_obj.update_attr('batch_id', batch_id)
#            booking_db_obj.insert(db)
#            return True
#        except errors.IfnsServiceUnavailable, exc:
#            if not _is_task_expired(dt):
#                _update_task(task_id, {
#                    'status' : IfnsBookingTaskStatus.BTS_NEW,
#                    'task_id' : None
#                })
#                raise book_ifns.retry(countdown=3500 + randint(200), exc=exc)
#            send_email.send_email(ifns_admin_email, 'failed_to_book_ifns')
#            _update_task(task_id, {
#                'status' : IfnsBookingTaskStatus.BTS_FAIL,
#                'error_info' : {
#                    "tag" : "task_expired"
#                }
#            })
#            return False
#        except Exception, ex:
#            send_email.send_email(ifns_admin_email, 'failed_to_book_ifns')
#            _update_task(task_id, {
#                'status' : IfnsBookingTaskStatus.BTS_FAIL,
#                'error_info' : {
#                    "tag" : "get_ifns_internal_id_by_ifns_name",
#                    "exc" : unicode(ex)
#                }
#            })
#            return False
#
#@celery.task()
#def find_appointment_data(apt_code, batch_id, reg_date_str, user_email, service_id):
#    request = current_task.request
#    config = celery.conf.get('config')
#    ifns_admin_email = config['ifns_admin_email']
#    db = celery.conf.get('db')
#    logger = _get_ifns_logger()
#    reg_date = datetime.strptime(reg_date_str, "%Y-%m-%dT%H:%M:%S")
#    with TaskFileIdHolder(request.id, config) as task_file:
#        try:
#            result = requests.get(u'http://order.nalog.ru/appointment/R%s/' % apt_code, timeout=20)
#            if result.status_code != 200 or not result.content:
#                logger.error(u"order.nalog.ru вернул неожиданный ответ")
#                raise errors.IfnsServiceUnavailable()
#
#            root = html5lib.parse(result.text, treebuilder='lxml', namespaceHTMLElements=False)
#
#            #noinspection PyCallingNonCallable
#            if not len(CSSSelector("#ctl00_pnlDetails")(root)):
#                send_email.send_email(user_email, 'ifns_duplicate_booking')
#                return False
#
#            if len(CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)) < 18:
#                logger.error(u"order.nalog.ru вернул неожиданный ответ: %s" % result.text)
#                raise errors.IfnsServiceUnavailable()
#                #noinspection PyCallingNonCallable
#            ifns =      CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[3].text
#            #noinspection PyCallingNonCallable
#            address =   CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[5].text
#            #noinspection PyCallingNonCallable
#            map =       CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[7].text
#            #noinspection PyCallingNonCallable
#            phone =     CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[9].text
#            #noinspection PyCallingNonCallable
#            service =   CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[11].text
#            #noinspection PyCallingNonCallable
#            data_str =  CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[13].text
#            #noinspection PyCallingNonCallable
#            time_str =  CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[15].text
#            #noinspection PyCallingNonCallable
#            window =    CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[17].text
#
#            try:
#                dt = datetime.strptime(data_str + 'T' + time_str, "%d.%m.%YT%H:%M")
#            except Exception:
#                raise errors.IfnsServiceUnavailable(u"Invalid datetime format")
#
#            send_email.send_email(user_email, 'ifns_booking_success')
#
#            booking = IfnsBooking.parse_raw_value({
#                'ifns' : ifns,
#                'service' : service,
#                'service_id' : service_id,
#                'date' : dt.strftime("%Y-%m-%dT%H:%M:%S"),
#                'window' : window,
#                'address' : address,
#                'phone' : phone,
#                'how_to_get' : map,
#                'code' : apt_code,
#                '_discarded' : False
#            }, api_data = True)
#            booking_db_obj = booking.get_db_object()
#            booking_db_obj.update_attr('batch_id', batch_id)
#            booking_db_obj.insert(db)
#            return True
#        except errors.IfnsServiceUnavailable, exc:
#            if not _is_task_expired(reg_date):
#                raise find_appointment_data.retry(countdown=3500 + randint(200), exc=exc)
#            send_email.send_email(ifns_admin_email, 'failed_to_book_ifns')
#            return False
#        except Exception, ex:
#            send_email.send_email(ifns_admin_email, 'failed_to_book_ifns')
#            return False

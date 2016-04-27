# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import json
from tornado import gen
from async.async_dadata_provider import AsyncDadataProvider
from async.async_ifns_provider import AsyncIfnsProvider, FailedToGetAppointmentData
from async.vews_base import JsonRequestHandler, authorized
from common_utils import int_to_ifns
from custom_exceptions import CacheMiss
from fw.api import errors
from fw.api.args_validators import validate_arguments_tornado, IntValidator, EnumValidator, DateTypeValidator, \
    JsonValidator, DateTimeValidator, ObjectIdValidator
from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject
from fw.documents.enums import DocumentTypeEnum
from services.ifns.async_tasks import ifns_booking_tasks
from services.ifns.data_model.models import IfnsBookingObject, IfnsBookingTaskStatus
from services.llc_reg.documents.enums import IfnsServiceEnum


class IfnsGetScheduleView(JsonRequestHandler):
    @gen.coroutine
    @authorized
    @validate_arguments_tornado(
        ifns=IntValidator(required=True),
        service=EnumValidator(enum_cls=IfnsServiceEnum, required=True),
        datetime=DateTypeValidator(required=True),
        founder_applicant=JsonValidator(required=True)
    )
    def get_content_on_post(self, arguments=None, *args, **kwargs):

        logger = self.application.logger  # todo: ifns logger!
        cache = self.application.cache

        ifns = arguments['ifns']
        service = arguments['service']
        dt = arguments['datetime']
        founder_applicant = arguments['founder_applicant']
        service_nalog_ru_url = self.application.config['SERVICE_NALOG_RU_URL']

        try:
            company_data, person_data = yield AsyncIfnsProvider.get_company_person_data_for_ifns(founder_applicant,
                                                                                                 self.user.email,
                                                                                                 self.application.db)
        except Exception:
            logger.exception(u"Failed to collect data")
            raise errors.InvalidParameterValue("founder_applicant")

        try:
            reg_ifns = yield AsyncIfnsProvider.get_registration_ifns(int_to_ifns(ifns), cache,
                                                                     service_nalog_ru_url=service_nalog_ru_url)
        except Exception:
            logger.exception(u"Failed to get registration ifns. Address ifns: %s" % unicode(ifns))
            raise

        reg_ifns_name = reg_ifns['rou']['naimk']
        reg_ifns_addr = reg_ifns['adres']
        try:
            address = yield AsyncDadataProvider.get_detailed_address(reg_ifns_addr, cache)
            if not address:
                raise Exception()
        except Exception:
            logger.exception(u"Failed to get detailed address. Reg ifns address: %s" % unicode(reg_ifns_addr))
            raise
        region_name = address['suggestions'][0]['data']['region']

        try:
            result = yield AsyncIfnsProvider.get_nalog_ru_time_slots(person_data, company_data, reg_ifns_name, service,
                                                                     region_name, cache, logger)
        except errors.IfnsServiceUnavailable, ex:
            logger.exception(u"Failed to get schedule from ifns. Trying to get cached value")
            try:
                result = yield AsyncIfnsProvider.get_nalog_ru_time_slots_cached(not company_data, reg_ifns_name,
                                                                                service, region_name, cache, logger)
                if len(result) < 8:
                    last_found_day = datetime.strptime(result[-1]['date'], "%Y-%m-%d")
                    result += AsyncIfnsProvider.get_nalog_ru_default_time_slots(region_name, reg_ifns_name,
                                                                                not company_data,
                                                                                first_day=last_found_day,
                                                                                days_to_get=8 - len(result))
            except CacheMiss, ex:
                logger.exception(u"Nothing in cache: returning defaults")
                result = AsyncIfnsProvider.get_nalog_ru_default_time_slots(region_name, reg_ifns_name, not company_data)

        all_time_slots = result

        td_min = timedelta(seconds=99999999)
        nearest_time = datetime.strptime(all_time_slots[0]['date'], "%Y-%m-%d")
        slots = all_time_slots[0]['time_slots']

        for slot in all_time_slots:
            cur_date = datetime.strptime(slot['date'], "%Y-%m-%d")
            td_cur = cur_date - dt if (cur_date > dt) else (dt - cur_date)
            if td_cur < td_min:
                td_min = td_cur
                nearest_time = cur_date
                slots = slot['time_slots']

        logger.debug(u"Ifns schedule - succeeded. Nearest time: %s, Slots: %s" % (
            nearest_time.strftime("%Y-%m-%d"), json.dumps(slots)))
        raise gen.Return({'result': {
            'nearest_time': nearest_time.strftime("%Y-%m-%d"),
            'slots': slots
        }})


class IfnsMakeBookingView(JsonRequestHandler):
    @gen.coroutine
    @authorized
    @validate_arguments_tornado(
        ifns=IntValidator(required=True),
        service=EnumValidator(enum_cls=IfnsServiceEnum, required=True),
        datetime=DateTimeValidator(required=True),
        founder_applicant=JsonValidator(required=True),
        batch_id=ObjectIdValidator(required=True),
        reg_responsible_person=ObjectIdValidator(required=False)
    )
    def get_content_on_post(self, arguments=None, *args, **kwargs):

        logger = self.application.logger  # todo: ifns logger!
        cache = self.application.cache

        ifns = arguments['ifns']
        service = arguments['service']
        dt = arguments['datetime']
        founder_applicant = arguments['founder_applicant']
        batch_id = arguments['batch_id']
        reg_responsible_person = arguments.get('reg_responsible_person', None)
        service_nalog_ru_url = self.application.config['SERVICE_NALOG_RU_URL']

        try:
            company_data, person_data = yield AsyncIfnsProvider.get_company_person_data_for_ifns(founder_applicant,
                                                                                                 self.user.email,
                                                                                                 self.application.db)
        except Exception:
            logger.exception(u"Failed to collect data")
            raise errors.InvalidParameterValue("founder_applicant")

        try:
            reg_ifns = yield AsyncIfnsProvider.get_registration_ifns(int_to_ifns(ifns), cache,
                                                                     service_nalog_ru_url=service_nalog_ru_url)
        except Exception:
            logger.exception(u"Failed to get registration ifns. Address ifns: %s" % unicode(ifns))
            raise

        reg_ifns_name = reg_ifns['rou']['naimk']
        reg_ifns_addr = reg_ifns['adres']
        try:
            address = yield AsyncDadataProvider.get_detailed_address(reg_ifns_addr, cache)
            if not address:
                raise Exception()
        except Exception:
            logger.exception(u"Failed to get detailed address. Reg ifns address: %s" % unicode(reg_ifns_addr))
            raise
        region_name = address['suggestions'][0]['data']['region']

        # todo: remove booking tasks with the same batch_id:service. (remove objects (in statuses new & progress) & cancel tasks)
        try:
            result = yield AsyncIfnsProvider.book_ifns(person_data, company_data, reg_ifns_name, service, region_name,
                                                       dt, reg_responsible_person, cache, logger)
        except errors.IfnsServiceUnavailable, ex:
            logger.exception(u"Failed to book ifns")
            booking_obj = IfnsBookingObject(**{
                "batch_id": batch_id,
                "person_data": person_data,
                "company_data": company_data,
                "reg_ifns_name": reg_ifns_name,
                "service": service,
                "region_name": region_name,
                "reg_date": dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "reg_responsible_person": reg_responsible_person,
                "status": IfnsBookingTaskStatus.BTS_NEW,
                "error_info": None,
                "user_email": self.user.email
            })
            sqldb.session.add(booking_obj)
            sqldb.session.commit()
            ifns_booking_task_id = booking_obj.id
            ifns_booking_tasks.book_ifns(str(ifns_booking_task_id))
            raise gen.Return({
                'error': True,
                'error_type': "booking_queued"
            })
        except FailedToGetAppointmentData, ex:
            ifns_booking_tasks.find_appointment_data(ex.apt_code, str(batch_id), dt.strftime("%Y-%m-%dT%H:%M:%S"),
                                                     self.user.email, service)
            raise gen.Return({
                'error': True,
                'error_type': "reserved_but_no_data"
            })

        result_value = None
        if result:
            try:
                booking = IfnsBookingObject(
                    ifns=result['ifns'],
                    service=result['service'],
                    service_id=service,
                    date=result['date'],
                    window=result['window'],
                    address=result['address'],
                    phone=result['phone'],
                    how_to_get=result['how_to_get'],
                    code=result['code'],
                    _discarded=False,
                    batch_id=batch_id
                )
                sqldb.session.add(booking)
                sqldb.session.commit()

                logger.debug(u"Reserverd ifns. ")
                result_value = {
                    'result': {
                        "ifns": result['ifns'],
                        "id": booking.id,
                        "service": result['service'],
                        "service_id": service,
                        "date": result['date'],
                        "window": result['window'],
                        "address": result['address'],
                        "phone": result['phone'],
                        "how_to_get": result['how_to_get'],
                        "code": result['code']
                    }
                }
            except Exception:
                logger.exception(u"Failed to save booking!")
                raise errors.ServerError()

        if result_value:
            raise gen.Return(result_value)
        logger.error(u"Failed to reserve ifns due to unknown reason.")
        raise errors.ServerError()


class IfnsBookingView(JsonRequestHandler):
    @gen.coroutine
    @authorized
    @validate_arguments_tornado(
        batch_id=ObjectIdValidator(required=True)
    )
    def get_content_on_get(self, arguments=None, *args, **kwargs):
        result_values = []
        logger = self.application.logger  # todo: ifns logger!
        batch_id = arguments['batch_id']

        booking_col = None # todo: IfnsBookingDbModel.get_collection(self.application.db)
        r, error = yield gen.Task(booking_col.find, {
            'batch_id': batch_id,
            '_discarded': {
                "$ne": True}
        })
        booking_cursor = r[0]
        for book in booking_cursor:
            result_values.append({
                'id': unicode(book['_id']),
                'ifns': book['ifns'],
                'service': book['service'],
                'service_id': book['service_id'],
                'date': book['date'],
                'window': book['window'],
                'address': book['address'],
                'phone': book['phone'],
                'how_to_get': book['how_to_get'],
                'code': book['code']
            })
        raise gen.Return({'result': result_values})


class IfnsNameView(JsonRequestHandler):
    @gen.coroutine
    @authorized
    @validate_arguments_tornado(
        batch_id=ObjectIdValidator(required=True)
    )
    def get_content_on_get(self, arguments=None, *args, **kwargs):
        logger = self.application.logger  # todo: ifns logger!
        cache = self.application.cache
        batch_id = arguments['batch_id']
        config = self.application.config

        null_res = {'result': ""}

        db = self.application.db
        batch_col = DocumentBatchDbObject.get_collection(db)

        r, error = yield gen.Task(batch_col.find_one, {'_id': batch_id})
        batch_db = r[0]

        if not batch_db:
            logger.error(u"No such batch %s" % unicode(batch_id))
            raise gen.Return(null_res)
        docs = batch_db.get('documents', [])
        if not docs:
            logger.error(u"No documents in batch %s" % unicode(batch_id))
            raise gen.Return(null_res)

        address = None
        for doc in docs:
            if 'document_type' not in doc:
                continue
            if doc['document_type'] == DocumentTypeEnum.DT_ARTICLES:
                address = doc['data'].get('address', None)
                break

        if not address:
            logger.error(u"Failed to get address")
            raise gen.Return(null_res)

        ifns = address.get('ifns', None)
        if not ifns:
            address_string = address.get('address_string')
            if not address_string:
                logger.error(u"Empty address string")
                raise gen.Return(null_res)
            detailed_address = yield AsyncDadataProvider.get_detailed_address(address_string, cache)
            if not detailed_address:
                logger.error(u"Failed to get detailed address from address string %s" % address_string)
                raise gen.Return(null_res)

            suggestions = detailed_address.get("suggestions", [])
            if not suggestions:
                logger.error(u"Empty suggestions")
                raise gen.Return(null_res)
            ifns = suggestions[0]['data'].get("tax_office", None)
        if not ifns:
            logger.error(u"Null ifns")
            raise gen.Return(null_res)

        ifns_data = yield AsyncIfnsProvider.get_ifns_by_code(ifns, config['SERVICE_NALOG_RU_URL'], cache, logger)
        if not ifns_data:
            logger.error(u"Failed to get ifns %s data" % unicode(ifns))
            raise gen.Return(null_res)

        raise gen.Return({'result': ifns_data.rou.naimk})


class IfnsDiscardBookingView(JsonRequestHandler):
    @gen.coroutine
    @authorized
    @validate_arguments_tornado(
        booking_id=ObjectIdValidator(required=True)
    )
    def get_content_on_post(self, arguments=None, *args, **kwargs):
        logger = self.application.logger  # todo: ifns logger!
        booking_id = arguments['booking_id']
        logger.debug(u"Trying to cancel ifns booking %s" % unicode(booking_id))

        booking_col = None # todo: IfnsBookingDbModel.get_collection(self.application.db)
        r, error = yield gen.Task(booking_col.update, {
            '_id': booking_id,
            '_discarded': {
                "$ne": True
            }
        }, {'$set': {
            '_discarded': True
        }})
        # result = r[0]
        #
        #        if not result:
        #            logger.debug(u"Ifns booking %s was not found" % unicode(booking_id))
        #            raise errors.IfnsBookingNotFound()

        logger.debug(u"Ifns booking %s canceled" % unicode(booking_id))
        raise gen.Return({'result': True})

# -*- coding: utf-8 -*-
from datetime import datetime
import json
from random import randint
import re
from datetime import timedelta
from flask import Blueprint, current_app
from flask_login import login_required, current_user
from common_utils import int_to_ifns

from fw.api import errors
from fw.api.args_validators import validate_arguments, IntValidator, EnumValidator, DateTypeValidator, DateTimeValidator
from fw.api.args_validators import ArgumentValidator
from fw.api.base_handlers import api_view
from fw.api.errors import BatchNotFound
from fw.auth.social_services import SocialServiceBackends
from fw.catalogs.models import OkvadObject, OkvedCatalogObject
from fw.db.sql_base import db as sqldb
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import DocumentBatchDbObject, CompanyDbObject, PrivatePersonDbObject
from fw.documents.enums import DocumentBatchTypeEnum, BatchStatusEnum
from fw.documents.fields.doc_fields import as_dumpable

from services.ifns import ifns_manager
from services.ifns.data_model.fields import IfnsBooking
from services.ifns.data_model.models import IfnsBookingObject, IfnsCatalogObject
from services.ifns.utils.ifns_logger import IFNS_LOGGER

from services.llc_reg.documents.enums import IfnsServiceEnum, FounderTypeEnum

ifns_bp = Blueprint('ifns', __name__)


_okvad_to_json = lambda x: {
    '_id': x.id,
    'okved': x.okved,
    'caption': x.caption,
    'nalog': x.nalog,
    'parent': x.parent
}

@ifns_bp.route('/get_okvad/', methods=['POST'])
@api_view
@validate_arguments(
    parent=ArgumentValidator(required=False),
    batch_type=ArgumentValidator(required=False),
    search=ArgumentValidator(required=False)
)
def get_okvad(parent=None, batch_type=None, search=None):
    search = search or ""
    make_okvad = lambda x: x['class'] + (
        ('.%s' % x['group'] + ('.%s' % x['kind'] if 'kind' in x else '')) if 'group' in x else '')

    query = OkvadObject.query.filter()
    if parent:
        query = query.filter_by(parent=parent)
        if search:
            query = query.filter(OkvadObject.caption.ilike(u'%%%s%%' % search))

        result = [_okvad_to_json(item) for item in query]
    else:
        query = OkvadObject.query.filter_by(parent=None)
        query2 = OkvadObject.query.filter(OkvadObject.parent.__ne__(None))
        if search:
            query = query.filter(OkvadObject.caption.ilike(u'%%%s%%' % search))
            query2 = query2.filter(OkvadObject.caption.ilike(u'%%%s%%' % search))

        result = [_okvad_to_json(item) for item in query.order_by(OkvadObject.caption.asc())] + [
            _okvad_to_json(item) for item in query2]

    from services.ip_reg.okvad_utils import is_restricted_for_ip_okvad
    if batch_type == DocumentBatchTypeEnum.DBT_NEW_IP:
        result = filter(lambda item: not is_restricted_for_ip_okvad(make_okvad(item)), result)
    return {'result': result}


def sort_okvads(search_term, okvad_list):
    term_len = len(search_term)
    for i in okvad_list:
        cap = i['caption']
        if cap == search_term:
            i['w'] += 200
        else:
            try:
                pattern = ur'\W(%s\w*)' % search_term
                m = re.search(pattern, cap, flags=re.I | re.U)
                word = m.group(1)
                i['w'] += 100 - abs(len(word) - term_len) * 10
            except Exception:
                pass
    result = sorted(okvad_list, key=lambda x: x['w'], reverse=True)
    return [{
        '_id': r['_id'],
        'caption': r['caption'],
        'code': r['code'],
        'parent': r['parent'],
    } for r in result]


@ifns_bp.route('/search_okvad/', methods=['GET'])
@api_view
@validate_arguments(title=ArgumentValidator(required=True, min_length=3))
def search_okvad(title=u""):
    result = []

    for r in OkvadObject.query.filter(OkvadObject.caption.ilike('%%%s%%' % title)):
        result.append(as_dumpable({
            '_id': r.id,
            'caption': r.caption,
            'code': r.okved,
            'parent': r.parent,
            'w': 0
        }))

    result = sort_okvads(title, result)

    return {'result': result[:20]}


@ifns_bp.route('/get_okvad_skeleton/', methods=['POST'])
@api_view
@validate_arguments(
    batch_type=ArgumentValidator(required=False),
    search=ArgumentValidator(required=False)
)
def get_okvad_skeleton(batch_type=None, search=None):
    search = search or ""

    from services.ip_reg.okvad_utils import is_restricted_for_ip_okvad

    result = OkvadObject.query.filter_by(parent=None)
    all_roots_list = [i.id for i in result]
    all_roots = set(all_roots_list)

    query = OkvadObject.query.filter(OkvadObject.parent!=None)
    if search:
        query = query.filter(OkvadObject.caption.ilike(u'%%%s%%' % search))
    total_items = [i for i in query]

    if batch_type == DocumentBatchTypeEnum.DBT_NEW_IP:
        total_items = filter(lambda x: not is_restricted_for_ip_okvad(x.okved or ''), total_items)

    first_level = filter(lambda x: x.parent in all_roots, total_items)  # подходящие по поиску
    first_level_ids = set([i.id for i in first_level])

    all_first_level = [i for i in OkvadObject.query.filter(OkvadObject.parent.in_(all_roots_list))]
    if batch_type == DocumentBatchTypeEnum.DBT_NEW_IP:
        all_first_level = filter(lambda x: not is_restricted_for_ip_okvad(x.okved or ''), all_first_level)
    all_first_level_map = {}
    for item in all_first_level:
        item_id = item.id
        all_first_level_map[item_id] = item

    #all_roots.add(None)

    second_level = filter(lambda x: x.parent not in all_roots, total_items)

    for item in second_level:
        item_code = item.okved
        item_id = item.id
        if not item_code:
            continue
        if item_id not in first_level_ids and item_id in all_first_level_map:
            first_level.append(item)
            first_level_ids.add(item_id)

    zero_level = set([x.parent for x in first_level])

    zero_level_full = [i.id for i in OkvadObject.query.filter(OkvadObject.parent==None).order_by(OkvadObject.okved.asc())]
    zero_level = filter(lambda i: i in all_roots, zero_level_full)

    result2 = [{
                   '_id': str(i),
                   'parent': None
               } for i in zero_level]

    first_level = sorted(first_level, key=lambda x: x.okved)
    result2.extend([{
                        '_id': i.id,
                        'code': i.okved,
                        'parent': i.parent
                    } for i in first_level])

    second_level = sorted(second_level, key=lambda x: x.okved)
    result2.extend([{
                        '_id': i.id,
                        'code': i.okved,
                        'parent': i.parent
                    } for i in second_level])

    return {'result': result2}


@ifns_bp.route('/get_okvad_items_data/', methods=['POST'])
@api_view
@validate_arguments(
    ids=ArgumentValidator(required=True),
    batch_type=ArgumentValidator(required=False)
)
def get_okvad_items_data(ids=None, batch_type=None):
    if not ids:
        return {'result': []}

    items = json.loads(ids)
    result = [_okvad_to_json(item) for item in OkvadObject.query.filter(OkvadObject.id.in_(items))]
    result2 = []
    from services.ip_reg.okvad_utils import is_restricted_for_ip_okvad
    for r in result:
        if batch_type == DocumentBatchTypeEnum.DBT_NEW_IP and is_restricted_for_ip_okvad(r['okved']):
            continue
        result2.append({
            '_id': r['_id'],
            'caption': r['caption'],
            'parent': r['parent'],
            'code': r['okved'],
            'description': u"",
            'nalog': r['nalog']
        })

    return {'result': result2}


@ifns_bp.route('/get_okvad_catalog/', methods=['GET'])
@api_view
@validate_arguments(batch_type=ArgumentValidator(required=False))
def get_okvad_catalog(batch_type=None):
    result = []
    query = OkvedCatalogObject.query.filter().order_by(OkvedCatalogObject.name.asc())
    from services.ip_reg.okvad_utils import is_restricted_for_ip_okvad
    for item in query:
        new_item = {
            'name': item.name,
            '_id': item.id,
        }
        deps = []

        for dep in item.departments:
            main_okvad = dep['main_okvad']
            if batch_type == DocumentBatchTypeEnum.DBT_NEW_IP and is_restricted_for_ip_okvad(main_okvad):
                continue
            deps.append({
                "_id": dep['id'],
                "name": dep['name'],
                "main_okvad": main_okvad
            })
        deps = sorted(deps, key=lambda x: x['name'])
        new_item['departments'] = deps
        result.append(new_item)

    return {'result': result}


@ifns_bp.route('/get_department_okvads/', methods=['GET'])
@api_view
@validate_arguments(
    department_id=ArgumentValidator(required=True),
    batch_type=ArgumentValidator(required=False)
)
def get_dep_okvads(department_id=None, batch_type=None):
    from services.ip_reg.okvad_utils import is_restricted_for_ip_okvad
    for c in OkvedCatalogObject.query.filter():
        if not c.departments:
            continue
        for dep in c.departments:
            if dep['id'] == department_id:
                okvad_list = dep['okvads']
                if not okvad_list:
                    continue
                result = [_okvad_to_json(item) for item in OkvadObject.query.filter(OkvadObject.okved.in_(okvad_list))]
                for i in xrange(len(result)):
                    result[i]['description'] = ""
                    code = result[i]['okved']
                    result[i]['code'] = code
                    del result[i]['okved']
                if batch_type == DocumentBatchTypeEnum.DBT_NEW_IP:
                    result = filter(lambda x: not is_restricted_for_ip_okvad(x['code']), result)
                return {'result': result}

    raise errors.InvalidParameterValue('department_id')


def get_company_person_data_for_ifns(founder_applicant, reg_responsible_object, email):
    person_data = None
    company_data = None

    reg_responsible_person = None
    try:
        if reg_responsible_object and '_id' in reg_responsible_object and 'type' in reg_responsible_object:
            obj_id = reg_responsible_object['_id']
            obj_type = reg_responsible_object['type']
            if obj_type == 'person':
                reg_responsible_person = obj_id
            else:
                reg_responsible_company = CompanyDbObject.query.filter_by(id=obj_id).scalar()
                if reg_responsible_company and reg_responsible_company.general_manager:
                    reg_responsible_person = reg_responsible_company.general_manager['_id']
    except Exception:
        pass

    if reg_responsible_person:
        person_obj = PrivatePersonDbObject.query.filter_by(id=reg_responsible_person).scalar()
        if not person_obj:
            raise errors.InvalidParameterValue("reg_responsible_person")
        person_data = {
            "name": person_obj.name or u"",
            "surname": person_obj.surname or u"",
            "patronymic": person_obj.patronymic or u"",
            "phone": person_obj.phone,
            "email": email,
            "inn": person_obj.inn
        }
        return None, person_data

    if FounderTypeEnum.TYPE_CLS(founder_applicant['founder_type']) == FounderTypeEnum.FT_PERSON:
        person_obj = PrivatePersonDbObject.query.filter_by(id=founder_applicant['person']['_id']).scalar()
        if not person_obj:
            raise errors.InvalidParameterValue("founder_applicant")
        person_data = {
            "name": person_obj.name or u"",
            "surname": person_obj.surname or u"",
            "patronymic": person_obj.patronymic or u"",
            "phone": person_obj.phone,
            "email": email,
            "inn": person_obj.inn
        }
    else:
        company_obj = CompanyDbObject.query.filter_by(id=founder_applicant['company']['_id']).scalar()
        general_manager = company_obj.general_manager
        if not general_manager or not company_obj:
            raise errors.InvalidParameterValue("founder_applicant")
        company_data = {
            "name": company_obj.full_name,
            "phone": general_manager.phone,
            "email": email,
            "inn": company_obj.inn
        }
    return company_data, person_data


def _make_fake_company_data():
    return {
        "name": u"Ромашка " + str(randint(1000000, 9999999)),
        "phone": "+7900" + str(randint(1000000, 9999999)),
        "email": "check" + str(randint(1000000, 9999999)) + "@mail.ru",
        "inn": "0000000000"
    }


RECEIVE_REG_DOCS_INTERNAL_SERVICE_ID_MAP = {
    '78086': (285, 1112),  # 'agent' : (189, 1112)
    '77066': (285, 2586),
    '47029': (77, 557),
    '47026': (71, 554),
    '47027': (71, 555),
    '47028': (71, 556),
    '47031': (71, 559),
    '47100': (71, 1633),
    '47030': (71, 558),
    '47035': (71, 561),
    '47098': (71, 565),
    '47034': (71, 560),
    '47036': (71, 562),
    '47039': (71, 563),
    '47040': (71, 564)
}

LLC_REG_INTERNAL_SERVICE_ID_MAP = {
    '78086': {
        'company': (182, 1112),
        'person': (281, 1112)
    },
    '77066': {
        'company': (275, 1265),
        'person': (281, 2813)
    }
}


@ifns_bp.route('/meeting/ifns/schedule/', methods=['POST'])
@api_view
@login_required
@validate_arguments(ifns=IntValidator(required=True),
                    service=EnumValidator(enum_cls=IfnsServiceEnum, required=True),
                    datetime=DateTypeValidator(required=True),
                    batch_id=ArgumentValidator(required=True)
                    )
def ifns_schedule(ifns=None, service=None, batch_id=None, **kwargs):
    dt = kwargs['datetime']
    service = int(service)

    batch_db = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).scalar()
    if not batch_db:
        raise errors.InvalidParameterValue('batch_id')

    # todo: check batch type (new llc)

    from services.llc_reg.llc_reg_manager import LlcRegBatchManager
    founder_applicant = LlcRegBatchManager.get_founder_applicant(batch_db, logger=current_app.logger)

    if not founder_applicant:
        raise errors.InvalidParameterValue("batch_id")

    IFNS_LOGGER.debug(
        u"Trying to get ifns schedule. ifns:%d, service:%s, dt:%s" % (int(ifns), unicode(service), unicode(dt)))

    all_time_slots = []

    ifns_data = ifns_manager.get_ifns_data(ifns)
    if not ifns_data or not ifns_data.rou:
        raise errors.InvalidParameterValue("ifns")

    rou = ifns_data.rou
    if 'code' not in rou:
        raise errors.InvalidParameterValue("ifns")

    code = rou['code']

    if service == IfnsServiceEnum.IS_REG_COMPANY:
        if code not in LLC_REG_INTERNAL_SERVICE_ID_MAP:
            raise errors.InvalidParameterValue("ifns")

        # noinspection PyTypeChecker
        company_data, person_data = get_company_person_data_for_ifns(founder_applicant, None, current_user.email)

        obj_type = "person" if person_data is not None else "company"
        internal_ifns_service, internal_ifns_number = LLC_REG_INTERNAL_SERVICE_ID_MAP[code][obj_type]

        try:
            all_time_slots = current_app.external_tools.get_nalog_ru_time_slots(person_data,
                                                                                company_data,
                                                                                internal_ifns_number,
                                                                                internal_ifns_service, IFNS_LOGGER)
            if not all_time_slots:
                raise Exception()
        except Exception:
            IFNS_LOGGER.exception(u"Failed to get_nalog_ru_time_slots")
            raise

    elif service == IfnsServiceEnum.IS_RECEIVE_REG_DOCS:
        if code not in RECEIVE_REG_DOCS_INTERNAL_SERVICE_ID_MAP:
            raise errors.InvalidParameterValue("ifns")
        internal_ifns_service, internal_ifns_number = RECEIVE_REG_DOCS_INTERNAL_SERVICE_ID_MAP[code]

        company_data = _make_fake_company_data()

        try:
            all_time_slots = current_app.external_tools.get_nalog_ru_time_slots(None,
                                                                                company_data,
                                                                                internal_ifns_number,
                                                                                internal_ifns_service, IFNS_LOGGER)
            if not all_time_slots:
                raise Exception()
        except Exception:
            IFNS_LOGGER.exception(u"Failed to get_nalog_ru_time_slots")
            raise

    if not all_time_slots:
        return {
            'result': {
                'nearest_time': None,
                'slots': []
            }
        }

    td_min = timedelta(seconds=99999999)
    nearest_time = datetime.strptime(all_time_slots[0]['date'], "%Y-%m-%d")
    slots = all_time_slots[0]['time_slots']

    actual_slots = []

    dt_str = dt.strftime("%Y-%m-%d")
    for slot in all_time_slots:
        cur_date = datetime.strptime(slot['date'], "%Y-%m-%d")
        if slot['date'] == dt_str:
            actual_slots = slot['time_slots']
        td_cur = cur_date - dt if (cur_date > dt) else (dt - cur_date)
        if td_cur < td_min:
            td_min = td_cur
            nearest_time = cur_date
            slots = slot['time_slots']

    # IFNS_LOGGER.debug(u"Ifns schedule - succeeded. Nearest time: %s, Slots: %s" % (nearest_time.strftime("%Y-%m-%d"), json.dumps(slots)))
    return {'result': {
        'nearest_time': dt_str,
        'slots': actual_slots
    }}


@ifns_bp.route('/meeting/ifns/create/', methods=['POST'])
@api_view
@login_required
@validate_arguments(ifns=IntValidator(required=True),
                    service=EnumValidator(enum_cls=IfnsServiceEnum, required=True),
                    datetime=DateTimeValidator(required=True),
                    batch_id=ArgumentValidator(required=True)
                    )
def ifns_reserve(ifns=None, service=None, batch_id=None, **kwargs):
    dt = kwargs['datetime']
    service = int(service)

    result = None

    batch_db = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).scalar()
    if not batch_db:
        raise errors.InvalidParameterValue('batch_id')

    from services.llc_reg.llc_reg_manager import LlcRegBatchManager
    founder_applicant = LlcRegBatchManager.get_founder_applicant(batch_db, logger=current_app.logger)
    if not founder_applicant:
        raise errors.InvalidParameterValue("batch_id")

    reg_responsible_object = LlcRegBatchManager.get_reg_responsible_object(batch_db, logger=current_app.logger)

    if not batch_db.data:
        raise errors.InvalidParameterValue('batch_id')

    batch_data_data = batch_db.data
    if 'full_name' not in batch_data_data or not batch_data_data['full_name']:
        raise errors.InvalidParameterValue('batch_id')
    company_full_name = batch_data_data['full_name']

    ifns_data = ifns_manager.get_ifns_data(ifns)
    if not ifns_data or not ifns_data.rou:
        raise errors.InvalidParameterValue("ifns")

    rou = ifns_data.rou
    if 'code' not in rou:
        raise errors.InvalidParameterValue("ifns")

    code = rou['code']

    if service == IfnsServiceEnum.IS_REG_COMPANY:
        if code not in LLC_REG_INTERNAL_SERVICE_ID_MAP:
            raise errors.InvalidParameterValue("ifns")

        IFNS_LOGGER.debug(
            u"Trying to reserve ifns. ifns:%d, service:%s, dt:%s" % (int(ifns), unicode(service), unicode(dt)))
        company_data, person_data = get_company_person_data_for_ifns(founder_applicant, reg_responsible_object,
                                                                     current_user.email)

        obj_type = "person" if person_data is not None else "company"
        internal_ifns_service, internal_ifns_number = LLC_REG_INTERNAL_SERVICE_ID_MAP[code][obj_type]
        try:
            result = current_app.external_tools.book_ifns(person_data, company_data, internal_ifns_number,
                                                          internal_ifns_service, dt, IFNS_LOGGER)
        except Exception:
            IFNS_LOGGER.exception(u"Failed to reserve ifns.")
            raise
    elif service == IfnsServiceEnum.IS_RECEIVE_REG_DOCS:
        try:
            if code not in RECEIVE_REG_DOCS_INTERNAL_SERVICE_ID_MAP:
                raise errors.InvalidParameterValue("ifns")
            general_manager = batch_data_data.get('general_manager')
            if not general_manager or '_id' not in general_manager:
                raise errors.InvalidParameterValue("batch_id")
            general_manager_id = general_manager['_id']
            general_manager_obj = PrivatePersonDbObject.query.filter_by(id=general_manager_id).scalar()
            if not general_manager_obj:
                raise errors.InvalidParameterValue("batch_id")
            internal_ifns_service, internal_ifns_number = RECEIVE_REG_DOCS_INTERNAL_SERVICE_ID_MAP[code]
            company_data = {
                'inn': '0000000000',
                "name": company_full_name,
                "phone": general_manager_obj.phone,
                "email": current_user.email,
            }
            result = current_app.external_tools.book_ifns(None, company_data, internal_ifns_number,
                                                          internal_ifns_service, dt, IFNS_LOGGER)
        except Exception:
            IFNS_LOGGER.exception(u"Failed to reserve ifns.")
            raise

    if result:
        from fw.async_tasks import send_email
        try:
            booking = IfnsBookingObject(
                batch_id=batch_id,
                code=result['code'],
                date=result['date'],
                service=result['service'],
                phone=result['phone'],
                window=result['window'],
                address=result['address'],
                service_id=service,
                ifns=result['ifns'],
                how_to_get=result['how_to_get']
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            IFNS_LOGGER.debug(u"Reserverd ifns. booking id: %s" % booking.id)

            social_link = SocialServiceBackends.get_user_social_network_profile_url(current_user.id)
            rec_list = current_app.config['YURIST_EMAIL_LIST']
            llc_full_name = batch_db.data.get('full_name', "")
            docs = BatchManager.get_shared_links_to_rendered_docs(batch_db, current_app.config,
                                                                  IFNS_LOGGER)
            for recipient in rec_list:
                send_email.send_email.delay(
                    recipient,
                    'ifns_reservation_notification',
                    email=current_user.email,
                    mobile=current_user.mobile,
                    social_link=social_link,
                    full_name=llc_full_name,
                    ifns=result['ifns'],
                    booking_time=result['date'],
                    docs=docs
                )
            booking_field = IfnsBooking.db_obj_to_field(booking)
            return {'result': booking_field.get_api_structure()}
        except Exception, ex:
            IFNS_LOGGER.exception(u"Failed to save booking!")
            raise errors.ServerError()

    IFNS_LOGGER.error(u"Failed to reserve ifns due to unknown reason.")
    return {'result': False}


@ifns_bp.route('/meeting/ifns/', methods=['GET'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator(required=True))
def ifns_get_booking(batch_id=None):
    result_values = []
    for book in IfnsBookingObject.query.filter(
        IfnsBookingObject.batch_id==batch_id,
        IfnsBookingObject._discarded==False,
        IfnsBookingObject.ifns.__ne__(None),
        IfnsBookingObject.date.__ne__(None),
        IfnsBookingObject.service_id.__ne__(None)):
        try:
            booking = IfnsBooking.db_obj_to_field(book)
            result_values.append(booking.get_api_structure())
        except Exception:
            current_app.logger.exception(u"Failed to parse ifns booking object from db")
            continue
    return {'result': result_values}


@ifns_bp.route('/ifns/reservations/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator(required=True))
def ifns_get_reservations(batch_id=None):
    batch_db = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).scalar()
    if not batch_db:
        raise BatchNotFound()
    if batch_db.status != BatchStatusEnum.BS_FINALISED:
        raise errors.InvalidParameterValue('batch_id')

    booking = IfnsBookingObject.query.filter(
        IfnsBookingObject.batch_id == batch_id,
        IfnsBookingObject._discarded == False,
        IfnsBookingObject.reg_info.__ne__(None)
    ).first()

    try:
        name = batch_db.data['full_name']
        full_name = u"Общество с ограниченной ответственностью \"%s\"" % name
    except Exception:
        current_app.logger.exception(u"Failed to collect data")
        raise errors.InvalidParameterValue('batch_id')

    if not booking:
        return {
            'result': {
                'full_name': full_name,
                'status': "unknown"
            }
        }

    result = {'result': {
        'full_name': full_name,
        'status': booking.reg_info.get('status', 'unknown')
    }}
    reg_date = booking.reg_info.get('reg_date', None)
    ogrn = booking.reg_info.get('ogrn', None)
    if reg_date:
        result['result']['reg_date'] = reg_date
    if ogrn:
        result['result']['ogrn'] = booking.reg_info.get('ogrn', None)
    return result


@ifns_bp.route('/meeting/ifns/discard/', methods=['POST'])
@api_view
@login_required
@validate_arguments(
    booking_id=ArgumentValidator(required=True),
)
def ifns_discard(booking_id=None):
    IFNS_LOGGER.debug(u"Trying to cancel ifns booking %s" % unicode(booking_id))

    IfnsBookingObject.query.filter_by(
        id=booking_id,
        _discarded=False
    ).update({
        '_discarded': True
    })
    sqldb.session.commit()

    IFNS_LOGGER.debug(u"Ifns booking %s canceled" % unicode(booking_id))
    return {'result': True}


@ifns_bp.route('/meeting/ifns/name/', methods=['GET'])
@api_view
@login_required
@validate_arguments(
    ifns=ArgumentValidator(required=True)
)
def ifns_get_name(ifns=None):
    null_res = {'result': {
        'title': "",
        'has_booking': False,
        'address': None
    }}
    IFNS_LOGGER.debug("ifns_get_name")

    try:
        ifns = int(ifns)
        if ifns < 1 or ifns > 99999:
            raise ValueError()
    except Exception:
        raise errors.InvalidParameterValue('ifns')

    result = IfnsCatalogObject.query.filter_by(code=ifns).first()
    if not result:
        return null_res

    ifns_item = result
    if not ifns_item.rou:
        return null_res

    rou = ifns_item.rou
    if not rou or 'name' not in rou:
        return null_res

    title = rou['name']
    if not title:
        return null_res

    has_booking = (7700 <= ifns <= 7799) or (7800 <= ifns <= 7899)  # or (4700 <= ifns <= 4799)

    address = (ifns_item.rou or {}).get('address', {})
    if not isinstance(address, dict):
        address = {}

    return {'result': {
        "title": title,
        "has_booking": has_booking,
        "address": address
    }}

@ifns_bp.route('/structures/ifns/search/', methods=['GET'])
@api_view
@validate_arguments(
    region=ArgumentValidator(required=False),
    search_string=ArgumentValidator(required=False),
    limit=IntValidator(required=False, min_val=1, max_val=100500),
    offset=IntValidator(required=False, min_val=0, max_val=100500)
)
def search_ifns(region=None, search_string=None, limit=20, offset=0):
    query = IfnsCatalogObject.query
    if region:
        query = query.filter_by(region=region)

    if search_string:
        reserved_symbols = '.\\$^*/[]()|+'
        for s in reserved_symbols:
            search_string = search_string.replace(s, '').strip()
            if not search_string:
                break
        if search_string:
            try:
                code_int = int(search_string)
                if 100 <= code_int < 10000:
                    query = query.filter_by(code=code_int)
            except Exception:
                query = query.filter(IfnsCatalogObject.name.ilike(u'%%%s%%' % search_string))

    total = query.count()
    if offset:
        query = query.skip(offset)
    if limit:
        query = query.limit(limit)

    query = query.order_by(IfnsCatalogObject.code.asc())
    return {
        'total': total,
        'count': query.count(),
        'ifns': [db_ifns_to_api(item) for item in query]
    }

@ifns_bp.route('/structures/ifns/', methods=['GET'])
@api_view
@validate_arguments(
    id=ArgumentValidator(required=True),
)
def get_ifns(**kwargs):
    id_val = kwargs.get('id', None)
    if not id_val:
        raise errors.MissingRequiredParameter('id')

    item = IfnsCatalogObject.query.filter_by(id=id_val).first()
    if not item:
        raise errors.IfnsNotFound()

    return db_ifns_to_api(item)


def db_ifns_to_api(item):
    result_item = {
        'id': item.id,
        'ifns_code': int_to_ifns(item.code),
        'caption': item.name or u'',
        'address': item.address or u'',
        'phones': [phone.replace('(', '').replace(')', '') for phone in (item.tel or [])],
        'additional_info': item.comment or u''
    }
    if 'address_string' in result_item['address']:
        try:
            address = json.loads(result_item['address'])
            result_item['address'] = address.get('address_string', u'')
        except Exception:
            pass
    plat = item.plat or {}
    if plat:
        result_item['payment_details'] = {
            'payment_recipient_caption': plat.get('recipient_name', u''),
            'inn': plat.get('recipient_inn', u''),
            'kpp': plat.get('recipient_kpp', u''),
            'bank_caption': plat.get('bank_name', u''),
            'bik': plat.get('bik', u''),
            'account': plat.get('recipient_account', u'')
        }
    if item.rou:
        rou = item.rou
        result_item['llc_registration_ifns'] = {
            'ifns_reg_code': str(rou['code']),
            'caption': rou.get('name', u""),
            'address': rou.get('address', {}).get('address_string', u''),
            'phones': [phone.replace('(', '').replace(')', '') for phone in rou.get('tel', [])]
        }

    if item.rof:
        rof = item.rof
        result_item['ip_registration_ifns'] = {
            'ifns_reg_code': str(rof['code']),
            'caption': rof.get('name', u""),
            'address': rof.get('address', {}).get('address_string', u''),
            'phones': [phone.replace('(', '').replace(')', '') for phone in (rof or {}).get('tel', [])]
        }
    return result_item


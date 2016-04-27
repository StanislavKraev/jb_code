# -*- coding: utf-8 -*-

import copy
from datetime import datetime
import json

from flask import Blueprint
from bson import ObjectId
from flask import current_app
from flask_login import login_required, current_user
import requests
from sqlalchemy import or_
from sqlalchemy.dialects.postgresql import ARRAY

from custom_exceptions import MissingRequiredFieldException, InvalidFieldValueException
from fw.api.args_validators import BoolTypeValidator
from fw.api.base_handlers import error_tree_to_list
from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import SPECIAL_CITY_REGIONS
from fw.documents.db_fields import DocumentBatchDbObject
from fw.documents.enums import DocumentBatchTypeEnum
from fw.documents.fields.doc_fields import DocumentBatch
from fw.documents.schema.conditions import Condition
from fw.api import errors
from fw.api.args_validators import validate_arguments, ArgumentValidator
from fw.api.base_handlers import api_view
from fw.documents.batch_manager import BatchManager
from services.partners.models import AccountantPartnersObject, BankPartnersObject, BankPartnerRequestObject, \
    BankPartnersServiceObject, StampPartnersObject

partners_bp = Blueprint('partners', __name__)

@partners_bp.route('/partners/accounts/', methods=['GET'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator())
def get_accountant_partners(batch_id=None):
    accountant_partner_list = []

    try:
        region = BatchManager.get_batch_region(batch_id)
    except Exception, ex:
        current_app.logger.exception(u"Failed to get batch region")
        raise errors.BatchNotFound()

    partners = AccountantPartnersObject.query.filter_by(enabled=True)
    if region:
        partners = partners.filter(or_(AccountantPartnersObject.region.contains([region]),
                                       AccountantPartnersObject.region == None))
    for item in partners.order_by(AccountantPartnersObject.sort_index.asc()):
        accountant_partner_list.append({
            "id": item.id,
            "link": item.link,
            "banner": item.banner,
            "title": item.title,
            "type": item.type
        })

    return {"result": {"accounts_partners": accountant_partner_list}}


@partners_bp.route('/partners/banks/', methods=['GET'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator())
def get_bank_partners(batch_id=None):
    bank_partner_list = []

    try:
        address = BatchManager.get_batch_address(batch_id)
        city = address['region'] if address['region'] in SPECIAL_CITY_REGIONS else address.get('city', address.get('village', u""))
    except Exception:
        raise errors.BatchNotFound()

    banks = BankPartnersObject.query.filter_by(enabled=True)
    if city:
        banks = banks.filter(or_(BankPartnersObject.city.contains([city]),
                                 BankPartnersObject.city == None))

    for item in banks.order_by(BankPartnersObject.sort_index.asc()):
        bank_partner_list.append({
            "id": item.id,
            "link": item.link,
            "banner": item.banner,
            "title": item.title,
            "conditions": item.conditions or []
        })

    return {"result": {"banks_partners": bank_partner_list}}


@partners_bp.route('/partners/banks/send/', methods=['POST'])
@api_view
@login_required
@validate_arguments(
    bank_id=ArgumentValidator(),
    batch_id=ArgumentValidator(),
    bank_contact_phone_general_manager=BoolTypeValidator(required=False),
    bank_contact_phone=ArgumentValidator(required=False),
    send_private_data=BoolTypeValidator()
)
def request_bank_partner(bank_id=None, batch_id=None, bank_contact_phone_general_manager=False,
                         bank_contact_phone="", send_private_data=None):

    if not bank_contact_phone_general_manager and not bank_contact_phone:
        raise errors.MissingRequiredParameter('bank_contact_phone')

    batch = DocumentBatchDbObject.query.filter_by(id=batch_id,
                                                  _owner=current_user,
                                                  deleted=False,
                                                  batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC).scalar()
    if not batch or not batch.data:
        raise errors.BatchNotFound()
    current_batch = DocumentBatch.db_obj_to_field(batch)

    partner = BankPartnersObject.query.filter_by(id=bank_id).first()
    if not partner:
        raise errors.InvalidParameterValue('partner_id')

    svc_data = BankPartnersServiceObject.query.filter_by(bank_partner_id=partner.id).first()
    if not svc_data:
        raise errors.ServerError()

    current_bank_request = BankPartnerRequestObject.query.filter_by(bank_partner_id=partner.id, batch_id=batch_id).first()
    if current_bank_request and current_bank_request.status in ('sending', 'success'):
        struct = current_batch.get_api_structure()
        return {'result': struct}

    if current_bank_request and abs((datetime.utcnow() - current_bank_request.sent_date).total_seconds()) > 60:
        BankPartnerRequestObject.query.filter_by(id=current_bank_request.id).delete()
        sqldb.session.commit()
        current_bank_request = None

    svc_type = svc_data.type

    fields = svc_data.fields
    extra_context = {
        'bank_contact_phone_general_manager': bank_contact_phone_general_manager,
        'bank_contact_phone': bank_contact_phone,
        'send_private_data': send_private_data,
        'bank_title': partner.title
    }
    field_list = BatchManager.make_fields_from_data(batch_id, fields, current_app.config, extra_context=extra_context)

    context = {}
    errors_list = []
    for name in field_list:
        field = field_list[name]
        try:
            if not field.initialized:
                if field.required:
                    raise MissingRequiredFieldException(name)
            else:
                field.validate()
        except (InvalidFieldValueException, MissingRequiredFieldException), ex:
            if hasattr(field, "suppress_validation_errors"):
                suppress_validation_errors = field.suppress_validation_errors
                if isinstance(suppress_validation_errors, dict):
                    suppress_validation_condition = Condition(suppress_validation_errors)
                    context = copy.copy(batch.data)
                    context.update(extra_context)
                    suppress_validation_errors = suppress_validation_condition.check(context)
                if suppress_validation_errors:
                    continue

            if getattr(ex, 'ext_data', None):
                err_list = error_tree_to_list(ex.ext_data)
                error_field_paths = [{'field': name + '.' + i['field'], 'error_code': i['error_code']} for i in err_list]
                errors_list.extend(error_field_paths)
            else:
                errors_list.append({
                    'field': name,
                    'error_code': ex.ERROR_CODE
                })
            current_app.logger.exception(u"Field %s validation error" % name)
            continue
        if field_list[name].initialized:
            context[name] = field_list[name]

    if errors_list:
        current_app.logger.exception(u"Failed to construct email context")
        if current_bank_request:
            current_bank_request.sent_date = datetime.utcnow()
            current_bank_request.status = "failed"
            current_bank_request.bank_contact_phone_general_manager = bank_contact_phone_general_manager
            current_bank_request.bank_contact_phone = bank_contact_phone
            current_bank_request.send_private_data = send_private_data
        else:
            new_item = BankPartnerRequestObject(
                bank_partner_id=partner.id,
                batch_id=batch_id,
                bank_partner_caption=partner.title,
                sent_date=datetime.utcnow(),
                status="failed",
                bank_contact_phone_general_manager=bank_contact_phone_general_manager,
                bank_contact_phone=bank_contact_phone,
                send_private_data=send_private_data
            )
            sqldb.session.add(new_item)
        sqldb.session.commit()

        batch.error_info = {
            'error_ext': errors_list
        }
        sqldb.session.commit()
        current_batch.error_info.value = {
            'error_ext': errors_list
        }
        current_batch.error_info.initialized = True
        struct = current_batch.get_api_structure()
        return {'result': struct}
    else:
        batch.error_info = None
        sqldb.session.commit()
        current_batch.error_info.value = None
        current_batch.error_info.initialized = False

    if context is None or not isinstance(context, dict):
        raise errors.ServerError()

    from flask.templating import render_template
    if svc_type == 'email':
        target_address = svc_data.email
        if current_app.config['STAGING'] or current_app.config['DEBUG']:
            target_address = current_app.config['ADMIN_EMAIL_LIST']
        template_name = svc_data.template_name
        if not target_address or not template_name:
            raise errors.ServerError()

        context['send_private_data'] = send_private_data
        html_text = render_template('email/%s.html' % template_name, **context)
        plain_text = render_template('email/%s.text' % template_name, **context)
        subject_text = render_template('email/%s.subject' % template_name, **context)

        from fw.async_tasks import send_email
        if current_bank_request:
            current_bank_request.sent_date = datetime.utcnow()
            current_bank_request.status = "sending"
            current_bank_request.bank_contact_phone_general_manager = bank_contact_phone_general_manager
            current_bank_request.bank_contact_phone = bank_contact_phone
            current_bank_request.send_private_data = send_private_data
        else:
            new_item = BankPartnerRequestObject(
                bank_partner_id=bank_id,
                batch_id=batch_id,
                bank_partner_caption=partner.title,
                sent_date=datetime.utcnow(),
                status="sending",
                bank_contact_phone_general_manager=bank_contact_phone_general_manager,
                bank_contact_phone=bank_contact_phone,
                send_private_data=send_private_data
            )
            sqldb.session.add(new_item)
        sqldb.session.commit()
        send_email.send_email_to_partner_and_set_result.delay(target_address, template_name, batch_id,
                                                              bank_id, bank_contact_phone_general_manager,
                                                              bank_contact_phone, send_private_data,
                                                              html_text=html_text, plain_text=plain_text,
                                                              subject_text=subject_text)
    elif svc_type == 'web':
        config = svc_data.config
        url = config['url']
        method = config['method']
        template_name = svc_data.template_name

        context['send_private_data'] = send_private_data
        json_str = render_template('%s.json' % template_name, **context)
        data = json.loads(json_str)
        new_data = {}
        for k, v in data.items():
            if isinstance(v, basestring):
                new_data[k] = v.encode('cp1251')
            else:
                new_data[k] = v

        try:
            if method == 'get':
                response = requests.get(url, params=new_data, timeout=3)
            elif method == 'post':
                response = requests.post(url, data=new_data, timeout=3)
            else:
                raise NotImplementedError()
        except Exception:
            current_app.logger.exception(u"Failed to send request to partner")
            return {"result": current_batch.get_api_structure()}

        if response.status_code == 200:
            if current_bank_request:
                current_bank_request.sent_date = datetime.utcnow()
                current_bank_request.status = "success"
                current_bank_request.bank_contact_phone_general_manager = bank_contact_phone_general_manager
                current_bank_request.bank_contact_phone = bank_contact_phone
                current_bank_request.send_private_data = send_private_data
            else:
                new_item = BankPartnerRequestObject(
                    bank_partner_id=bank_id,
                    batch_id=batch_id,
                    bank_partner_caption=partner.title,
                    sent_date=datetime.utcnow(),
                    status="success",
                    bank_contact_phone_general_manager=bank_contact_phone_general_manager,
                    bank_contact_phone=bank_contact_phone,
                    send_private_data=send_private_data
                )
                sqldb.session.add(new_item)
        else:
            if current_bank_request:
                current_bank_request.sent_date = datetime.utcnow()
                current_bank_request.status = "failed"
                current_bank_request.bank_contact_phone_general_manager = bank_contact_phone_general_manager
                current_bank_request.bank_contact_phone = bank_contact_phone
                current_bank_request.send_private_data = send_private_data
            else:
                new_item = BankPartnerRequestObject(
                    bank_partner_id=bank_id,
                    batch_id=batch_id,
                    bank_partner_caption=partner.title,
                    sent_date=datetime.utcnow(),
                    status="failed",
                    bank_contact_phone_general_manager=bank_contact_phone_general_manager,
                    bank_contact_phone=bank_contact_phone,
                    send_private_data=send_private_data
                )
                sqldb.session.add(new_item)
        sqldb.session.commit()

    else:
        raise errors.ServerError()

    return {"result": current_batch.get_api_structure()}


@partners_bp.route('/partners/banks/status/', methods=['GET'])
@api_view
@login_required
@validate_arguments(bank_id=ArgumentValidator(), batch_id=ArgumentValidator())
def get_bank_partner_request_status(bank_id=None, batch_id=None):
    try:
        bank_id = ObjectId(bank_id)
    except Exception:
        raise errors.InvalidParameterValue('bank_id')
    try:
        ObjectId(batch_id)
    except Exception:
        raise errors.InvalidParameterValue('batch_id')

    current_bank_request = BankPartnerRequestObject.query.filter_by(bank_partner_id=bank_id, batch_id=batch_id).first()
    if not current_bank_request:
        raise errors.BatchNotFound()

    if current_bank_request and current_bank_request.status == 'sending' and \
       abs((datetime.utcnow() - current_bank_request.sent_date).total_seconds()) > 60:

        sqldb.session.delete(current_bank_request)
        sqldb.session.commit()
        raise errors.BatchNotFound()

    return {"result": current_bank_request['status']}


@partners_bp.route('/partners/stamps/', methods=['GET'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator())
def get_stamp_partners(batch_id=None):
    stamp_partner_list = []

    try:
        region = BatchManager.get_batch_region(batch_id)
    except Exception:
        raise errors.BatchNotFound()

    stamps = StampPartnersObject.query.filter_by(enabled=True)
    if region:
        stamps = stamps.filter(or_(StampPartnersObject.region.contains([region]), StampPartnersObject.region == None))
    for item in stamps.order_by(StampPartnersObject.sort_index.asc()):
        stamp_partner_list.append({
            "id": item.id,
            "link": item.link,
            "banner": item.banner,
            "title": item.title
        })

    return {"result": {"stamp_partners": stamp_partner_list}}

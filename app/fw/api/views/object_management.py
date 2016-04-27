# -*- coding: utf-8 -*-
from flask import current_app, Blueprint

from flask_login import login_required, current_user

from fw.api import errors
from fw.api.args_validators import validate_arguments, ObjectRefValidator, IntValidator
from fw.api.args_validators import JsonValidator
from fw.api.base_handlers import api_view
from fw.documents.db_fields import PrivatePersonDbObject, CompanyDbObject
from fw.documents.fields.doc_fields import PrivatePerson, CompanyObject
from fw.db.sql_base import db as sqldb

domain_objects_bp = Blueprint('domain_objects', __name__)


@domain_objects_bp.route('/entity/person/create/', methods=['POST'])
@api_view
@login_required
@validate_arguments(person=JsonValidator())
def create_person(person=None):
    try:
        person_doc = PrivatePerson.parse_raw_value(person, api_data=True)
        if not person_doc:
            raise Exception()
    except Exception, ex:
        raise errors.InvalidParameterValue('person')

    try:
        person_doc.validate(strict=False)
    except Exception, ex:
        raise errors.InvalidParameterValue('person')

    person = person_doc.get_db_object()
    person._owner = current_user

    sqldb.session.add(person)
    sqldb.session.commit()

    result = person_doc.get_api_structure()
    result['id'] = person.id + "_person"
    return {"result": result}


@domain_objects_bp.route('/entity/person/', methods=['GET'])
@api_view
@login_required
@validate_arguments(person_id=ObjectRefValidator(required=False),
                    count=IntValidator(min_val=1, required=False),
                    offset=IntValidator(min_val=0, required=False))
def get_persons(person_id=None, count=None, offset=None):
    result_list = []
    person_id = str(person_id) if person_id else ''

    if person_id:
        person = PrivatePersonDbObject.query.filter_by(id=person_id, deleted=False, _owner=current_user,
                                                       _batch=None, _copy_id=None).first()
        if not person:
            raise errors.EntityNotFound('person_id')
        person_doc = PrivatePerson.db_obj_to_field(person)
        result_list.append(person_doc.get_api_structure())

        result_count = 1
        result_total = 1
    else:
        cur = PrivatePersonDbObject.query.filter_by(deleted=False, _owner=current_user, _batch=None, _copy_id=None).order_by(
            PrivatePersonDbObject.id.asc())
        result_total = cur.count()
        cur = PrivatePersonDbObject.query.filter_by(deleted=False, _owner=current_user, _batch=None, _copy_id=None).order_by(
            PrivatePersonDbObject.id.asc())

        if count is not None:
            cur = cur.limit(offset)
        if offset is not None:
            cur = cur.offset(offset)

        result_count = cur.count()
        for person in cur:
            person_doc = PrivatePerson.db_obj_to_field(person)
            result_list.append(person_doc.get_api_structure())

    return {'result': {
        'persons': result_list,
        'total': result_total,
        'count': result_count
    }}


@domain_objects_bp.route('/entity/person/update/', methods=['POST'])
@api_view
@login_required
@validate_arguments(person_id=ObjectRefValidator(), person=JsonValidator())
def update_person(person_id=None, person=None):
    person_db_obj = PrivatePersonDbObject.query.filter_by(id=unicode(person_id), _owner=current_user,
                                                          _batch=None).first()
    if not person_db_obj:
        raise errors.EntityNotFound()

    PrivatePerson.update_db_obj(person_db_obj, person, api_data=True)

    # validator = IsMyObjectVisitor(current_user._id) # todo:!!!
    # try:
    # validator.process(old_person_doc)
    # except NotMineException:
    # raise InvalidParameterValue('person')

    sqldb.session.commit()
    person_doc = PrivatePerson.db_obj_to_field(person_db_obj)
    return {"result": person_doc.get_api_structure()}


@domain_objects_bp.route('/entity/person/remove/', methods=['POST'])
@api_view
@login_required
@validate_arguments(person_id=ObjectRefValidator())
def delete_person(person_id=None):
    person_db_obj = PrivatePersonDbObject.query.filter_by(id=unicode(person_id), _owner=current_user,
                                                          _batch=None).first()
    if not person_db_obj:
        raise errors.EntityNotFound()

    person_db_obj.deleted = True
    sqldb.session.commit()

    return {"result": True}


@domain_objects_bp.route('/entity/company/create/', methods=['POST'])
@api_view
@login_required
@validate_arguments(company=JsonValidator())
def create_company(company=None):
    try:
        company_doc = CompanyObject.parse_raw_value(company, api_data=True)
        if not company_doc:
            raise Exception()
    except Exception:
        current_app.logger.exception(u"Failed to validate company data")
        raise errors.InvalidParameterValue('company')

    try:
        company_doc.validate(strict=False)
    except Exception, ex:
        raise errors.InvalidParameterValue('company')

    company_db_obj = company_doc.get_db_object()
    company_db_obj._owner = current_user

    sqldb.session.add(company_db_obj)
    sqldb.session.commit()

    result = company_doc.get_api_structure()
    result['id'] = company_db_obj.id + "_company"
    return {"result": result}


@domain_objects_bp.route('/entity/company/', methods=['GET'])
@api_view
@login_required
@validate_arguments(company_id=ObjectRefValidator(required=False),
                    count=IntValidator(min_val=1, required=False),
                    offset=IntValidator(min_val=0, required=False))
def get_companies(company_id=None, count=None, offset=None):
    result_list = []
    company_id = str(company_id) if company_id else ''
    if company_id:
        company = CompanyDbObject.query.filter_by(id=company_id, deleted=False, _owner=current_user,
                                                  _batch=None, _copy_id=None).first()

        if not company:
            raise errors.EntityNotFound()
        company_doc = CompanyObject.db_obj_to_field(company)
        result_list.append(company_doc.get_api_structure())
        result_count = 1
        result_total = 1
    else:
        cur = CompanyDbObject.query.filter_by(deleted=False, _owner=current_user, _batch=None, _copy_id=None).order_by(
            CompanyDbObject.id.asc())
        result_total = cur.count()
        cur = CompanyDbObject.query.filter_by(deleted=False, _owner=current_user, _batch=None, _copy_id=None).order_by(
            CompanyDbObject.id.asc())
        if count is not None:
            cur = cur.limit(offset)
        if offset is not None:
            cur = cur.offset(offset)
        result_count = cur.count()
        for company in cur:
            company_doc = CompanyObject.db_obj_to_field(company)
            result_list.append(company_doc.get_api_structure())
    return {'result': {
        'companies': result_list,
        'total': result_total,
        'count': result_count
    }}


@domain_objects_bp.route('/entity/company/update/', methods=['POST'])
@api_view
@login_required
@validate_arguments(company_id=ObjectRefValidator(), company=JsonValidator())
def update_company(company_id=None, company=None):
    company_id = str(company_id) if company_id else None
    company_db_obj = CompanyDbObject.query.filter_by(id=company_id, _owner=current_user, _batch=None).first()
    if not company_db_obj:
        raise errors.EntityNotFound()

    old_company_doc = CompanyObject.db_obj_to_field(company_db_obj)
    old_company_doc.update(company)

    CompanyObject.update_db_obj(company_db_obj, company, api_data=True)

    sqldb.session.commit()
    company_doc = CompanyObject.db_obj_to_field(company_db_obj)

    return {"result": company_doc.get_api_structure()}


@domain_objects_bp.route('/entity/company/remove/', methods=['POST'])
@api_view
@login_required
@validate_arguments(company_id=ObjectRefValidator())
def delete_company(company_id=None):
    company_id = str(company_id) if company_id else None
    company_db_obj = CompanyDbObject.query.filter_by(id=company_id, _owner=current_user, _batch=None).first()
    if not company_db_obj:
        raise errors.EntityNotFound()

    company_db_obj.deleted = True
    sqldb.session.commit()

    return {"result": True}

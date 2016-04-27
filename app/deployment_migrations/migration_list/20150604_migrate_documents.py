# -*- coding: utf-8 -*-
from datetime import datetime
import logging
from tempfile import TemporaryFile, NamedTemporaryFile
from bson import ObjectId
import requests
from fw.auth.models import AuthUser
from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject, CompanyDbObject, PrivatePersonDbObject
from fw.documents.enums import PersonTypeEnum, IncorporationFormEnum, CompanyTypeEnum
from fw.storage.models import FileObject


def replace_all_objectid_with_str(obj):
    if isinstance(obj, dict):
        val = {}
        for k, v in obj.items():
            val[replace_all_objectid_with_str(k)] = replace_all_objectid_with_str(v)
        return val
    elif isinstance(obj, list):
        return [replace_all_objectid_with_str(i) for i in obj]
    else:
        if isinstance(obj, ObjectId):
            return str(obj)
    return obj


def migrate_document(new_batch, old_doc, rendered_docs):
    data = replace_all_objectid_with_str(old_doc.get('data', {}))

    doc_id = str(old_doc['id'])
    found_docs = filter(lambda d: 'document_id' in d and str(d['document_id']) == doc_id, rendered_docs)
    caption = ""
    file_obj = None
    if found_docs:
        file_id = found_docs[0]['file_id']
        file_obj = FileObject.query.filter_by(id=str(file_id)).scalar()
        caption = found_docs[0].get('caption', "")

    # rendered docs:
    # {
    #     "caption" : "Квитанция на уплату госпошлины",
    #     "document_type" : "reg_fee_invoice",
    #     "file_link" : "/api/storage/54e1d5b5e64bcf5977867c80/%D0%9A%D0%B2%D0%B8%D1%82%D0%B0%D0%BD%D1%86%D0%B8%D1%8F%20%D0%BD%D0%B0%20%D0%BE%D0%BF%D0%BB%D0%B0%D1%82%D1%83%20%D1%80%D0%B5%D0%B3%D0%B8%D1%81%D1%82%D1%80%D0%B0%D1%86%D0%B8%D0%BE%D0%BD%D0%BD%D0%BE%D0%B9%20%D0%BF%D0%BE%D1%88%D0%BB%D0%B8%D0%BD%D1%8B%20%D0%9E%D0%9E%D0%9E.pdf",
    #     "file_id" : ObjectId("54e1d5b5e64bcf5977867c80"),
    #     "document_id" : ObjectId("54e1d5afe64bcf599525a6f2")
    # }

    new_doc = BatchDocumentDbObject(
        id=doc_id,
        _owner=new_batch._owner,
        creation_date=old_doc.get('creation_date', datetime.utcnow()),
        document_type=old_doc['document_type'],
        file=file_obj,
        batch=new_batch,
        data=data,
        status=old_doc['status'],
        caption=caption,
        _celery_task_id=None,
        _celery_task_started=None
    )
    sqldb.session.add(new_doc)
    sqldb.session.commit()

broken_batches = set()
missing_users = set()
broken_persons = set()
broken_companies = set()
incomplete_companies = set()
incomplete_persons = set()
failed_paid_bathes_of_real_users = set()

detailed_logger = logging.getLogger(__name__)
detailed_logger.setLevel(logging.DEBUG)

t = NamedTemporaryFile(prefix="migration_details_%s" % datetime.now().strftime("%Y-%m-%dT%H:%M"), suffix='.log', delete=False)

fh = logging.FileHandler(t.name)
fh.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

detailed_logger.addHandler(fh)

def migrate_batch(batch):
    detailed_logger.info(u"Migrating batch %s" % str(batch['_id']))
    required_fields = ('_owner', 'data')
    for rf in required_fields:
        if rf not in batch:
            detailed_logger.error(u"Invalid batch %s: missing required field %s" % (str(batch['_id']), rf))
            broken_batches.add(str(batch['_id']))
            return
    data = replace_all_objectid_with_str(batch['data'] or {})
    _owner = batch['_owner']
    try:
        _owner = int(_owner)
    except Exception:
        detailed_logger.exception(u"Invalid _owner type")
        detailed_logger.error(u"Invalid batch %s: ObjectId in _owner field instead of int" % str(batch['_id']))
        broken_batches.add(str(batch['_id']))
        return
    if not isinstance(_owner, int):
        detailed_logger.error(u"Invalid batch %s: ObjectId in _owner field instead of int" % str(batch['_id']))
        broken_batches.add(str(batch['_id']))
        return

    owner = AuthUser.query.filter_by(id=_owner).first()
    if not owner:
        missing_users.add(owner)
        detailed_logger.error(u"Failed to find user with id %s" % _owner)
        broken_batches.add(str(batch['_id']))
        detailed_logger.error(u"Invalid batch %s: Failed to find owner user")
        return

    new_batch = DocumentBatchDbObject(
        id=str(batch['_id']),
        _owner_id=owner.id,
        batch_type=batch['batch_type'],
        creation_date=batch.get('creation_date', datetime.utcnow()),
        finalisation_date=batch.get('finalisation_date', None),
        status=batch['status'],
        deleted=False,
        data=data,
        result_fields=replace_all_objectid_with_str(batch.get('result_fields', None)),

        error_info=batch.get('error_info', None),
        current_task_id=None,
        batch_rendering_start=None,
        _metadata=batch.get('metadata', None),

        pay_info=batch.get('pay_info', None),
        paid=batch.get('paid', False),
        last_change_dt=batch.get('last_change_dt', None),
        _broken=False
    )
    sqldb.session.add(new_batch)
    sqldb.session.commit()

    old_documents = batch.get('_documents', [])
    for old_doc in old_documents:
        migrate_document(new_batch, old_doc, batch.get('rendered_docs', []))

def fix_name(name):
    if not name:
        return None
    if isinstance(name, dict):
        return name.get("nom", "")
    return str(name)

def migrate_person(person):
    detailed_logger.info(u"Migrating person %s" % str(person['_id']))
    required_fields = ('name', 'surname')
    for rf in required_fields:
        if rf not in person:
            detailed_logger.error(u"Invalid person %s: missing required field %s" % (str(person['_id']), rf))
            broken_persons.add(str(person['_id']))
            return

    batch_id = person.get('_batch', None)
    if batch_id:
        batch_id = str(batch_id)

        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).scalar()
        if not batch:
            detailed_logger.error(u"Incomplete person %s: failed to find batch with id %s. Resetting to null" % (str(person['_id']), batch_id))
            incomplete_persons.add(str(person['_id']))
            batch_id = None

    copy_id = person.get('_copy', None)
    if copy_id:
        copy_id = str(copy_id)

    _owner = person['_owner']
    try:
        _owner = int(_owner)
    except Exception:
        detailed_logger.exception(u"Invalid _owner type")
        detailed_logger.error(u"Invalid person %s: Owner id is not int" % str(person['_id']))
        broken_persons.add(str(person['_id']))
        return

    if not isinstance(_owner, int):
        detailed_logger.error(u"Invalid person %s: Owner id is not int" % str(person['_id']))
        broken_persons.add(str(person['_id']))
        return

    owner = AuthUser.query.filter_by(id=_owner).first()
    if not owner:
        detailed_logger.error(u"Invalid person %s: failed to find person owner with id %s" % (str(person['_id']), _owner))
        missing_users.add(str(person['_owner']))
        broken_persons.add(str(person['_id']))
        return

    new_person = PrivatePersonDbObject(
        id=str(person['_id']),
        _owner_id=owner.id,
        _batch_id=batch_id,
        deleted=False,
        caption=None,
        name=fix_name(person['name']),
        surname=fix_name(person['surname']),
        patronymic=fix_name(person.get('patronymic', None)),
        birthdate=person.get('birthdate', None),
        sex=person.get('sex', "male"),
        birthplace=person.get('birthplace', None),
        inn=person.get('inn', None),
        phone=person.get('phone', None),
        passport=person.get('passport', None),
        address=person.get('address', None),
        living_address=person.get('living_address', None),
        living_country_code=person.get('living_country_code', None),
        ogrnip=person.get('ogrnip', None),
        email=person.get('email', None),
        spouse=None,
        _copy_id=copy_id,
        person_type=PersonTypeEnum.PT_RUSSIAN
    )
    sqldb.session.add(new_person)
    sqldb.session.commit()


def migrate_company(company):
    detailed_logger.info(u"Migrating company %s" % str(company['_id']))
    batch_id = company.get('_batch', None)
    if batch_id:
        batch_id = str(batch_id)

        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).scalar()
        if not batch:
            detailed_logger.error(u"Incomplete company %s: failed to find batch with id %s. Resetting to null" % (str(company['_id']), batch_id))
            incomplete_companies.add(str(company['_id']))
            batch_id = None

    copy_id = company.get('_copy', None)
    if copy_id:
        copy_id = str(copy_id)

    general_manager_id = company.get('general_manager', {}).get('_id', None)
    if general_manager_id:
        general_manager_id = str(general_manager_id)

        gen_man = PrivatePersonDbObject.query.filter_by(id=general_manager_id).scalar()
        if not gen_man:
            detailed_logger.error(u"Incomplete company %s: failed to find general manager with id %s. "
                                  u"Resetting to null" % (str(company['_id']), general_manager_id))
            incomplete_companies.add(str(company['_id']))
            general_manager_id = None

    _owner = company['_owner']
    try:
        _owner = int(_owner)
    except Exception:
        detailed_logger.exception(u"Invalid _owner type")
        detailed_logger.error(u"Invalid company %s: Owner id is not int" % str(company['_id']))
        broken_companies.add(str(company['_id']))
        return

    if not isinstance(_owner, int):
        detailed_logger.error(u"Invalid company %s: Owner id is not int" % str(company['_id']))
        broken_companies.add(str(company['_id']))
        return

    owner = AuthUser.query.filter_by(id=_owner).first()
    if not owner:
        missing_users.add(str(_owner))
        broken_companies.add(str(company['_id']))
        detailed_logger.error(u"Invalid company %s: failed to find company owner with id %s" % (str(company['_id']), _owner))
        return

    new_company = CompanyDbObject(
        id=str(company['_id']),
        _owner_id=company['_owner'],
        _copy_id=copy_id,
        _batch_id=batch_id,
        deleted=False,
        inn=company.get('inn', None),
        ogrn=company.get('ogrn', None),
        kpp=company.get('kpp', None),
        registration_date=company.get('registration_date', None),
        registration_depart=company.get('registration_depart', None),
        registration_number=company.get('registration_number', None),
        full_name=company.get('full_name', None),
        short_name=company.get('short_name', None),
        incorporation_form=IncorporationFormEnum.IF_LLC,
        country_code=company.get('country_code', None),
        address=company.get('address', None),
        generic_address=company.get('generic_address', None),
        phone=company.get('phone', None),
        general_manager=general_manager_id,
        general_manager_caption=company.get('general_manager_caption', None),
        base_general_manager_document=company.get('base_general_manager_document', None),
        company_type=CompanyTypeEnum.CT_RUSSIAN
    )
    sqldb.session.add(new_company)
    sqldb.session.commit()

def find_id_in_data(data, obj_id):
    if isinstance(data, dict):
        if len(data) == 2 and '_id' in data and 'type' in data:
            if data['_id'] == obj_id:
                print("Found dropped object's id %s" % obj_id)
                return True
        else:
            for k, v in data.items():
                if find_id_in_data(k, obj_id):
                    return True
                if find_id_in_data(v, obj_id):
                    return True
    elif isinstance(data, list):
        for i in data:
            if find_id_in_data(i, obj_id):
                return True
    else:
        if obj_id == data:
            print("Found dropped object's id %s" % obj_id)
            return True


def pull_id_or_ref_from_data(data, obj_id):
    if isinstance(data, dict):
        if len(data) == 2 and '_id' in data and 'type' in data:
            if data['_id'] == obj_id:
                return
            return data
        else:
            res = {}
            for k, v in data.items():
                res_v = pull_id_or_ref_from_data(v, obj_id)
                if res_v:
                    res[k] = res_v
            return res
    elif isinstance(data, list):
        res = []
        for i in data:
            res_i = pull_id_or_ref_from_data(i, obj_id)
            if res_i:
                res.append(res_i)
        return res
    else:
        if obj_id == data:
            return
    return data

def forward(config, logger):
    logger.debug(u"migrate documents, companies, persons")

    logger.info("Drop company, person, document, batch tables")
    try:
        CompanyDbObject.__table__.drop(sqldb.engine)
    except Exception:
        pass

    try:
        PrivatePersonDbObject.__table__.drop(sqldb.engine)
    except Exception:
        pass

    try:
        BatchDocumentDbObject.__table__.drop(sqldb.engine)
    except Exception:
        pass

    try:
        DocumentBatchDbObject.__table__.drop(sqldb.engine)
    except Exception:
        pass

    DocumentBatchDbObject.__table__.create(sqldb.engine)
    BatchDocumentDbObject.__table__.create(sqldb.engine)
    PrivatePersonDbObject.__table__.create(sqldb.engine)
    CompanyDbObject.__table__.create(sqldb.engine)

    batch_col = db['doc_batch']
    company_object_col = db['company_object']
    private_person_col = db['private_person']

    batch_query = {'deleted': {'$ne': True}, '_broken': {'$ne': True}, 'batch_type': {'$ne': None}}

    logger.info(u"Calculating metrics")

    batch_status_count_map = {}
    batch_type_count_map = {}
    test_users_list = []
    for user in AuthUser.query.filter_by(is_tester=True):
        test_users_list.append(user.id)

    paid_batch_count = batch_col.find({'deleted': {'$ne': True}, '_broken': {'$ne': True}, 'paid':True}).count()
    real_user_paid_batch_count = batch_col.find({'deleted': {'$ne': True},
                                                 '_broken': {'$ne': True},
                                                 'paid': True,
                                                 '_owner': {'$nin': test_users_list}}).count()
    documents_count = 0

    total_batches = batch_col.find(batch_query).count()
    for batch in batch_col.find(batch_query):
        batch_status = batch['status']
        if batch_status not in batch_status_count_map:
            batch_status_count_map[batch_status] = 1
        else:
            batch_status_count_map[batch_status] += 1

        batch_type = batch['batch_type']
        if batch_type not in batch_type_count_map:
            batch_type_count_map[batch_type] = 1
        else:
            batch_type_count_map[batch_type] += 1

        if 'rendered_docs' in batch:
            documents_count += len(batch['rendered_docs'])

    persons_count = private_person_col.find({'deleted': {'$ne': True}}).count()
    companies_count = company_object_col.find({'deleted': {'$ne': True}}).count()

    logger.info("Batches")
    for batch in batch_col.find(batch_query):
        migrate_batch(batch)

    logger.info("Persons")
    for person in private_person_col.find({'deleted': {'$ne': True}, '_copy': None}):
        migrate_person(person)

    # logger.info("Person copies")
    # for person in private_person_col.find({'deleted': {'$ne': True}, '_copy': {'$ne': None}}):
    #     migrate_person(person)

    logger.info("Companies")
    for company in company_object_col.find({'deleted': {'$ne': True}, '_copy': None}):
        migrate_company(company)

    # logger.info("Company copies")
    # for company in company_object_col.find({'deleted': {'$ne': True}, '_copy': {'$ne': None}}):
    #     migrate_company(company)

    logger.info("\n  Summary\n==================================================================================\n\n")
    logger.info("Initial batch count: %s" % total_batches)
    logger.info("Rendered document count: %s" % documents_count)
    logger.info("batches by type: %s" % ", ".join(["%s: %s" % (t, c) for t, c in batch_type_count_map.items()]))
    logger.info("batches by status: %s" % ", ".join(["%s: %s" % (s, c) for s, c in batch_status_count_map.items()]))
    logger.info("paid batches: %s. real user paid batches: %s" % (paid_batch_count, real_user_paid_batch_count))
    logger.info("Persons count: %s" % persons_count)
    logger.info("Companies count: %s" % companies_count)

    batch_type_count_map = {}
    batch_status_count_map = {}
    for batch_obj in DocumentBatchDbObject.query.filter_by():
        if batch_obj.status not in batch_status_count_map:
            batch_status_count_map[batch_obj.status] = 1
        else:
            batch_status_count_map[batch_obj.status] += 1

        if batch_obj.batch_type not in batch_type_count_map:
            batch_type_count_map[batch_obj.batch_type] = 1
        else:
            batch_type_count_map[batch_obj.batch_type] += 1

    logger.info("New batch count: %s" % DocumentBatchDbObject.query.count())
    logger.info("Rendered document count: %s" % BatchDocumentDbObject.query.count())
    logger.info("batches by type: %s" % ", ".join(["%s: %s" % (t, c) for t, c in batch_type_count_map.items()]))
    logger.info("batches by status: %s" % ", ".join(["%s: %s" % (s, c) for s, c in batch_status_count_map.items()]))
    logger.info("paid batches: %s. real user paid batches: %s" % (DocumentBatchDbObject.query.filter_by(paid=True).count(),
                DocumentBatchDbObject.query.filter(DocumentBatchDbObject.paid==True).join(AuthUser).filter(AuthUser.is_tester == False).count()))
    logger.info("Persons count: %s" % PrivatePersonDbObject.query.count())
    logger.info("Companies count: %s" % CompanyDbObject.query.count())

    if broken_batches:
        logger.info("broken batches: %d out of %d\n%s" % (len(broken_batches), total_batches, '\n'.join(broken_batches)))

    if missing_users:
        logger.info("missing users: \n%s" % ('\n'.join(missing_users)))

    if broken_persons:
        logger.info("broken persons: \n%s" % ('\n'.join(broken_persons)))

    if broken_companies:
        logger.info("broken companies: \n%s" % ('\n'.join(broken_companies)))

    if incomplete_companies:
        logger.info("incomplete companies: \n%s" % ('\n'.join(incomplete_companies)))

    if incomplete_persons:
        logger.info("incomplete persons: \n%s" % ('\n'.join(incomplete_persons)))

    logger.warn("real person's paid batches that failed to migrate:")
    for batch in batch_col.find({'deleted': {'$ne': True},
                                 '_broken': {'$ne': True},
                                 'batch_type': {'$ne': None},
                                 'paid': True,
                                 '_owner': {'$nin': test_users_list}
                                 }):
        if not DocumentBatchDbObject.query.filter_by(id=str(batch['_id'])).count():
            msg = u"[%s] type=%s status=%s data.full_name=%s" % (batch['_id'], batch['batch_type'], batch['status'], batch['data'].get('full_name', '<empty full_name field>'))
            logger.warn(msg)
            detailed_logger.warn(msg)

    save = False
    for batch in DocumentBatchDbObject.query.filter_by():
        if not batch.data:
            continue
        for person_id in broken_persons:
            if find_id_in_data(batch.data, person_id):
                batch.data = pull_id_or_ref_from_data(batch.data, person_id)
                save = True
        for company_id in broken_companies:
            if find_id_in_data(batch.data, company_id):
                batch.data = pull_id_or_ref_from_data(batch.data, company_id)
                save = True
    if save:
        sqldb.session.commit()

    ifns_booking_col = db['ifns_booking']
    notarius_booking_col = db['notarius_booking']
    yurist_batch_check_col = db['yurist_batch_check']
    bank_partners_request_col = db['bank_partners_request']

    ids = set()
    for booking in ifns_booking_col.find():
        if 'batch_id' in booking and booking['batch_id']:
            ids.add(booking['batch_id'])

    for _id in ids:
        ifns_booking_col.update({'batch_id': _id}, {'$set': {'batch_id': str(_id)}}, multi=True)

    ids = set()
    for booking in notarius_booking_col.find():
        if 'batch_id' in booking and booking['batch_id']:
            ids.add(booking['batch_id'])

    for _id in ids:
        notarius_booking_col.update({'batch_id': _id}, {'$set': {'batch_id': str(_id)}}, multi=True)

    ids = set()
    for ybc in yurist_batch_check_col.find():
        if 'batch_id' in ybc and ybc['batch_id']:
            ids.add(ybc['batch_id'])

    for _id in ids:
        yurist_batch_check_col.update({'batch_id': _id}, {'$set': {'batch_id': str(_id)}}, multi=True)

    ids = set()
    for bpr in bank_partners_request_col.find():
        if 'batch_id' in bpr and bpr['batch_id']:
            ids.add(bpr['batch_id'])

    for _id in ids:
        bank_partners_request_col.update({'batch_id': _id}, {'$set': {'batch_id': str(_id)}}, multi=True)


def rollback(config, logger):
    logger.debug(u"Rolling back migration")

    CompanyDbObject.__table__.drop(sqldb.engine)
    PrivatePersonDbObject.__table__.drop(sqldb.engine)
    BatchDocumentDbObject.__table__.drop(sqldb.engine)
    DocumentBatchDbObject.__table__.drop(sqldb.engine)

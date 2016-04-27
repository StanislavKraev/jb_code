# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from flask import json
from fw.catalogs.models import BikCatalog

from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentBatchTypeEnum, DocumentTypeEnum
from fw.documents.schema.schema_transform import transform_with_schema
from services.osago.documents.enums import OsagoDocTypeEnum, PretensionResultEnum, InsuranceLawsuitEnum, \
    OsagoRefusalReasonEnum
from services.pay.models import PayInfoObject, PurchaseServiceType
from test_api import authorized
from test_pack.base_batch_test import BaseBatchTestCase


class OsagoTestCase(BaseBatchTestCase):

    @authorized()
    def test_docs_claim(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_OSAGO]['doc_types'] = [DocumentTypeEnum.DT_OSAGO_DOCUMENTS_CLAIM]

        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user)
            victim_car_owner = self.create_person(self.user, batch.id, phone="")
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22, phone="")

            batch_json = json.dumps({
                "data": {
                    'policy_called': True,
                    'victim_owner': victim_car_owner.id + "_person",
                    'responsible_person': responsible_person.id + '_person',
                    'docs_got': [OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                #OsagoDocTypeEnum.ODT_INSURANCE_DENIAL,
                #OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE,
                OsagoDocTypeEnum.ODT_POLICE_STATEMENT,
                OsagoDocTypeEnum.ODT_POLICE_PROTOCOL,
                OsagoDocTypeEnum.ODT_CASE_INITIATION_REFUSAL],
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'police_case': True,
                    'independent_expertise_sum': 1500000,
                    'independent_expertise_cost': 200000,
                    'compensation_sum': 10000,
                    'problem_type': 'refusal',
                    "submission_way": "responsible_person",
                    'obtain_way': 'responsible_person',
                    'own_insurance_company': True,
                    'obtain_address_type': 'responsible_person_address',
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': batch.id,
                'document_type': json.dumps([DocumentTypeEnum.DT_OSAGO_DOCUMENTS_CLAIM])
            })
            self.assertEqual(result.status_code, 200)
            doc = BatchDocumentDbObject.query.filter().scalar()
            print (json.dumps(doc.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

    @authorized()
    def test_pretesion(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_OSAGO]['doc_types'] = [DocumentTypeEnum.DT_OSAGO_PRETENSION]

        with self.app.app_context():
            assurance = self.addCarAssurance(u"РЕСО-ГАРАНТИЯ")
            assurance_branch = self.addCarAssuranceBranch(assurance=assurance)
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user)

            batch_payment = PayInfoObject(
                user=self.user,
                batch=batch,
                pay_record_id=0,
                payment_provider=1,
                service_type=PurchaseServiceType.OSAGO_PART1
            )
            sqldb.session.add(batch_payment)
            sqldb.session.commit()

            victim_car_owner = self.create_person(self.user, batch.id, phone="345345")
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22, phone="1231313")
            victim_driver = self.create_person(self.user, batch.id, name=u"Полина",
                                               surname=u"Ступицина", patronymic=u"Араровна", age=18, phone="1231313")
            guilty_driver = self.create_person(self.user, batch.id, name=u"Прохор",
                                               surname=u"Иванов", patronymic=u"Иванович", age=88, phone="123123")
            guilty_owner = self.create_person(self.user, batch.id, name=u"Бобр",
                                              surname=u"Лесной", age=31, phone="123123")

            bik = BikCatalog(
                id="040173745",
                name=u"банк",
                okpo="12323",
                bik="040173745",
                phone="",
                address="",
                kor_account='2342342'
            )
            sqldb.session.add(bik)
            sqldb.session.commit()

            ppid = lambda x: x.id + '_person'
            batch_json = json.dumps({
                "data": {
                    'victim_owner': ppid(victim_car_owner),
                    'got_cash': True,
                    'have_osago': 'victim',
                    'obtain_way': 'responsible_person',
                    'other_date': False,
                    'responsible_person': ppid(responsible_person),
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'obtain_address_type': 'responsible_person_address',
                    'owner_as_victim_driver': True,
                    'use_other_submission_address': False,
                    'other_insurance': True,
                    'victim_driver': ppid(victim_driver),
                    'guilty_driver': ppid(guilty_driver),
                    'guilty_car_brand': u'Белаз',
                    'guilty_car_number': u'М100Е50',
                    'policy_series': u'ССС',
                    'policy_number': u'123456789',
                    'problem_type': 'underpay',
                    'compensation_sum': 1111.1,
                    'bik_account': u'040173745',
                    'account_number': u'12345678901234567890',
                    'independent_expertise_number': u'1111111',
                    'independent_expertise_sum': '0',
                    'independent_expertise_cost': '0',
                    'guilty_owner': ppid(guilty_owner),
                    'submission_branch_id': assurance_branch.id,
                    "submission_way": "oneself",
                    #'submission_branch_id': "",
                    'insurance_company_region': u"Санкт-Петербург",
                    'owner_as_guilty_driver': False,
                    #'submission_address': u'Какой-то адрес',
                    'obtain_address': u"Обтейн адрес",
                    'insurance_name': u"Суперстраховая №1",
                    'police_case': True,
                    'policy_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'own_insurance_company': True,
                    'add_person_to_claim': True,
                    'first_claim_date': datetime.utcnow().strftime("%Y-%m-%d"),
                    'court_include': False
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': batch.id,
                'document_type': json.dumps([DocumentTypeEnum.DT_OSAGO_PRETENSION])
            })
            self.assertEqual(result.status_code, 200)
            doc = BatchDocumentDbObject.query.filter().scalar()
            print (json.dumps(doc.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

    @authorized()
    def test_mail_list(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_OSAGO]['doc_types'] = [DocumentTypeEnum.DT_OSAGO_MAIL_LIST]

        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status='pretension')
            batch_json = json.dumps({
                "data": {
                    'other_insurance': True,
                    'insurance_name': u'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ РОССИЙСКАЯ ГОСУДАРСТВЕННАЯ КОМПАНИЯ ПО ОЧИСТКЕ СТОЧНЫХ ВОД',
                    'use_other_submission_address': True,
                    'submission_address': u"197342, Санкт-Петербург, Ушаковская наб., д. 5",
                    'submission_way': "mail",
                    'docs_got': [
                        OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                        OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                        OsagoDocTypeEnum.ODT_INSURANCE_DENIAL,
                        OsagoDocTypeEnum.ODT_POLICE_STATEMENT,
                        OsagoDocTypeEnum.ODT_POLICE_PROTOCOL
                    ],
                    'policy_called': True,
                    'court_include': True
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': batch.id,
                'document_type': json.dumps([DocumentTypeEnum.DT_OSAGO_MAIL_LIST])
            })
            self.assertEqual(result.status_code, 200)

    @authorized()
    def test_trust_submission_docs(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_OSAGO]['doc_types'] = [DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISSION_DOCS]

        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user)
            victim_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)

            batch_json = json.dumps({
                "data": {
                    'victim_owner': victim_car_owner.id + "_person",
                    'responsible_person': responsible_person.id + '_person',
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    "submission_way": "responsible_person",
                    'obtain_way': 'mail',
                    'insurance_name': u'ООО ААА ОАО АОА',
                    'court_include': True
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': batch.id,
                'document_type': json.dumps([DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISSION_DOCS])
            })
            self.assertEqual(result.status_code, 200)

    @authorized()
    def test_trust_obtain_docs(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_OSAGO]['doc_types'] = [DocumentTypeEnum.DT_OSAGO_TRUST_OBTAIN_DOCS]

        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user)
            victim_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)

            batch_json = json.dumps({
                "data": {
                    'victim_owner': victim_car_owner.id + "_person",
                    'responsible_person': responsible_person.id + '_person',
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    "submission_way": "mail",
                    'obtain_way': 'responsible_person',
                    'insurance_name': u'ООО ААА ОАО АОА'
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': batch.id,
                'document_type': json.dumps([DocumentTypeEnum.DT_OSAGO_TRUST_OBTAIN_DOCS])
            })
            self.assertEqual(result.status_code, 200)

    @authorized()
    def test_trust_submission_and_obtain_docs(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_OSAGO]['doc_types'] = [DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISION_OBTAIN_DOCS]

        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user)
            victim_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Ивановна", age=22)

            batch_json = json.dumps({
                "data": {
                    'victim_owner': victim_car_owner.id + "_person",
                    'responsible_person': responsible_person.id + '_person',
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    "submission_way": "responsible_person",
                    'obtain_way': 'responsible_person',
                    'insurance_name': u'ООО ААА ОАО АОА',
                    'court_include': True
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': batch.id,
                'document_type': json.dumps([DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISION_OBTAIN_DOCS])
            })
            self.assertEqual(result.status_code, 200)

    @authorized()
    def test_find_osago_policy_on_id_change(self):
        with self.app.app_context():
            assurance = self.addCarAssurance(u"РЕСО-ГАРАНТИЯ")
            DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_OSAGO]['doc_types'] = [DocumentTypeEnum.DT_OSAGO_MAIL_LIST]
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user)
            batch_json = json.dumps({
                "data": {
                    'policy_series': u'ААА',
                    'policy_number': '123111'
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            del data['result']['creation_date']
            del data['result']['id']
            del data['result']['name']
            self.assertEqual(data,  {
                u'result': {
                    u'all_docs': [],
                    u'batch_type': u'osago',
                    u'data': {u'policy_number': u'123111',
                              u'policy_series': u'ААА'},
                    u'metadata': {},
                    u'paid': u'false',
                    u'result_fields': {
                        u'insurance_id': assurance.id,
                        u'insurance_name': assurance.full_name,
                        u'policy_date': u'2013-10-20',
                        u'region_prepositional': u'',
                        u'responsible_person_dative': u'',
                        u'underpay_sum': u'50000',
                        u'above_limits_sum': u'50000'
                    },
                    u'status': u'pretension',
                    u'status_data': {u'finalisation_count': u'0'}}
            })
            batch = DocumentBatchDbObject.query.filter_by(id=batch.id).scalar()
            self.assertEqual(batch.result_fields, {
                u'insurance_id': assurance.id,
                u'insurance_name': assurance.full_name,
                u'policy_date': u"2013-10-20",
                u'region_prepositional': u'',
                u'responsible_person_dative': u'',
                u'underpay_sum': u'50000',
                u'above_limits_sum': u'50000'
            })
            batch_json = json.dumps({
                "data": {
                    'insurance_name': u'CCC',
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

    @authorized()
    def test_underpay_sum(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_OSAGO]['doc_types'] = [DocumentTypeEnum.DT_OSAGO_MAIL_LIST]

        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status='pretension')
            batch_json = json.dumps({
                "data": {
                    'policy_called': True,
                    'crash_date': datetime.utcnow().strftime("%Y-%m-%d"),
                    'independent_expertise_sum': 500000,
                    'problem_type': 'refusal',
                    'compensation_sum': 100
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.result_fields['underpay_sum'], u'400000')

            batch_json = json.dumps({
                "data": {
                    'policy_called': False,
                    'crash_date': datetime.utcnow().strftime("%Y-%m-%d"),
                    'independent_expertise_sum': 100500,
                    'problem_type': 'refusal',
                    'compensation_sum': 100
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.result_fields['underpay_sum'], u'50000')

            batch_json = json.dumps({
                "data": {
                    'policy_called': True,
                    'crash_date': datetime.utcnow().strftime("%Y-%m-%d"),
                    'independent_expertise_sum': 100500,
                    'problem_type': 'underpay',
                    'compensation_sum': 100
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.result_fields['underpay_sum'], u'100400')

            batch_json = json.dumps({
                "data": {
                    'policy_called': False,
                    'crash_date': datetime.utcnow().strftime("%Y-%m-%d"),
                    'independent_expertise_sum': 100500,
                    'problem_type': 'underpay',
                    'compensation_sum': 100
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.result_fields['underpay_sum'], u'49900')

            batch_json = json.dumps({
                "data": {
                    'policy_called': True,
                    'crash_date': datetime(2013, 1, 1).strftime("%Y-%m-%d"),
                    'independent_expertise_sum': 300000,
                    'problem_type': 'refusal',
                    'compensation_sum': 100
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.result_fields['underpay_sum'], u'120000')

            batch_json = json.dumps({
                "data": {
                    'policy_called': False,
                    'crash_date': datetime(2013, 1, 1).strftime("%Y-%m-%d"),
                    'independent_expertise_sum': 100500,
                    'problem_type': 'refusal',
                    'compensation_sum': 100
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.result_fields['underpay_sum'], u'25000')

            batch_json = json.dumps({
                "data": {
                    'policy_called': True,
                    'crash_date': datetime(2013, 1, 1).strftime("%Y-%m-%d"),
                    'independent_expertise_sum': 10500,
                    'problem_type': 'underpay',
                    'compensation_sum': 100
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.result_fields['underpay_sum'], u'10400')

            batch_json = json.dumps({
                "data": {
                    'policy_called': False,
                    'crash_date': datetime(2013, 1, 1).strftime("%Y-%m-%d"),
                    'independent_expertise_sum': 100500,
                    'problem_type': 'underpay',
                    'compensation_sum': 100
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.result_fields['underpay_sum'], u'24900')

            batch_json = json.dumps({
                "data": {
                    'policy_called': True,
                    'policy_case': False,
                    'crash_date': datetime(2014, 10, 2).strftime("%Y-%m-%d"),
                    'independent_expertise_sum': 120001,
                    'independent_expertise_cost': 1000,
                    'problem_type': 'underpay',
                    'compensation_sum': 2222227
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.result_fields['above_limits_sum'], u'0')

    @authorized()
    def test_go_ahead_in_pretesion(self):
        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status="pretension")
            victim_car_owner = self.create_person(self.user, batch.id, name=u"ЖЖ", surname=u"ЖЖ", patronymic=u"ЖЖ")
            guilty_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)

            batch_json = json.dumps({
                "data": {
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'policy_called': True,
                    'all_have_osago': True,
                    'own_insurance_company': True,
                    'have_osago': 'both',
                    'problem_type': 'refusal',
                    'refusal_reason': 'wrong_docs',
                    'notice_has_mistakes': False,
                    'got_cash': False,
                    'victim_owner': victim_car_owner.id + "_person",
                    'owner_as_victim_driver': True,
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'guilty_owner': guilty_car_owner.id + "_person",
                    'owner_as_guilty_driver': True,
                    'guilty_car_brand': u'Рено',
                    'guilty_car_number': u'В000ВВ50',
                    'other_victims': None,
                    'insurance_company_region': u'Санкт-Петербург',
                    'policy_series': u'ААА',
                    'policy_number': '0123456789',
                    'other_insurance': True,
                    'insurance_name': u"РоСгосСтраХ",
                    'insurance_id': None,
                    'other_date': True,
                    'policy_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'first_claim_date': (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                    'independent_expertise_number': u'01234567890123456789',
                    'independent_expertise_sum': '222000.50',
                    'independent_expertise_cost': 1000,
                    'compensation_sum': 1000.9,
                    'add_person_to_claim': True,
                    'docs_got': [OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                                OsagoDocTypeEnum.ODT_BANK_STATEMENT],
                    'insurance_case_number': '01234567890123456789',
                    'submission_way': 'oneself',
                    'submission_branch_id': '',
                    'use_other_submission_address': True,
                    'submission_address': u'сабмишн адрес',
                    'obtain_way': 'responsible_person',
                    'responsible_person': responsible_person.id + '_person',
                    'court_include': True,
                    'obtain_address_type': 'other_address',
                    'obtain_address': 'аптейн адрес',
                    'bik_account': '012345678',
                    'account_number': '01234567890123456789',
                    'police_case': True
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/go_ahead/', data={
                'batch_id': batch.id,
            })
            self.assertEqual(result.status_code, 200)
            self.assertEqual(BatchDocumentDbObject.query.count(), 3)
            self.assertEqual(BatchDocumentDbObject.query.filter_by(status="rendered").count(), 3)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.status, "claim")

    @authorized()
    def test_go_ahead_in_pretesion_wrong_data(self):
        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status="pretension")
            victim_car_owner = self.create_person(self.user, batch.id)
            guilty_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)

            batch_json = json.dumps({
                "data": {
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'policy_called': True,
                    'all_have_osago': True,
                    'own_insurance_company': True,
                    'have_osago': 'both',
                    'problem_type': 'refusal',
                    'refusal_reason': 'wrong_docs',
                    'notice_has_mistakes': False,
                    'got_cash': False,
                    'victim_owner': victim_car_owner.id + "_person",
                    'owner_as_victim_driver': True,
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'guilty_owner': guilty_car_owner.id + "_person",
                    'owner_as_guilty_driver': True,
                    'guilty_car_brand': u'Рено',
                    'guilty_car_number': u'В000ВВ50',
                    'other_victims': None,
                    'insurance_company_region': u'Санкт-Петербург',
                    'policy_series': u'ААА',
                    'policy_number': '0123456789',
                    'other_insurance': True,
                    'insurance_name': u"РоСгосСтраХ",
                    'insurance_id': None,
                    'other_date': True,
                    'policy_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'first_claim_date': (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                    'independent_expertise_number': u'01234567890123456789',
                    'independent_expertise_sum': 1500000,
                    'independent_expertise_cost': 200000,
                    'compensation_sum': 0,
                    'add_person_to_claim': True,
                    'docs_got': [OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                                 OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                                 OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE],
                    'insurance_case_number': '01234567890123456789',
                    'submission_way': 'responsible_person',
                    'submission_branch_id': '',
                    'use_other_submission_address': True,
                    'submission_address': u'сабмишн адрес',
                    'obtain_way': 'responsible_person',
                    'responsible_person': responsible_person.id + '_person',
                    'court_include': True,
                    'obtain_address_type': 'other_address',
                    'bik_account': '012345678',
                    'account_number': '01234567890123456789'
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/go_ahead/', data={
                'batch_id': batch.id,
            })
            self.assertEqual(result.status_code, 200)
            self.assertEqual(BatchDocumentDbObject.query.count(), 3)
            self.assertEqual(BatchDocumentDbObject.query.filter_by(status="rendered").count(), 2)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).scalar()
            self.assertEqual(db_batch.status, "pretension")
            self.assertEqual(db_batch.error_info, {
                u'error_ext': [{u'error_code': 5, u'field': u'obtain_address'}]
            })

    @authorized()
    def test_go_ahead_in_generating_pretension(self):
        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status="generating_pretension")
            victim_car_owner = self.create_person(self.user, batch.id)
            guilty_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)
            doc = self.create_document(DocumentTypeEnum.DT_OSAGO_PRETENSION, batch, data={})

            batch_json = json.dumps({
                "data": {
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'policy_called': True,
                    'all_have_osago': True,
                    'own_insurance_company': True,
                    'have_osago': 'both',
                    'problem_type': 'refusal',
                    'refusal_reason': 'wrong_docs',
                    'notice_has_mistakes': False,
                    'got_cash': False,
                    'victim_owner': victim_car_owner.id + "_person",
                    'owner_as_victim_driver': True,
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'guilty_owner': guilty_car_owner.id + "_person",
                    'owner_as_guilty_driver': True,
                    'guilty_car_brand': u'Рено',
                    'guilty_car_number': u'В000ВВ50',
                    'other_victims': None,
                    'insurance_company_region': u'Санкт-Петербург',
                    'policy_series': u'ААА',
                    'policy_number': '0123456789',
                    'other_insurance': True,
                    'insurance_name': u"РоСгосСтраХ",
                    'insurance_id': None,
                    'other_date': True,
                    'policy_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'first_claim_date': (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                    'independent_expertise_number': u'01234567890123456789',
                    'independent_expertise_sum': 1500000,
                    'independent_expertise_cost': 200000,
                    'compensation_sum': 0,
                    'add_person_to_claim': True,
                    'docs_got': [OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                                 OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                                 OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE],
                    'insurance_case_number': '01234567890123456789',
                    'submission_way': 'responsible_person',
                    'submission_branch_id': '',
                    'use_other_submission_address': True,
                    'submission_address': u'сабмишн адрес',
                    'obtain_way': 'responsible_person',
                    'responsible_person': responsible_person.id + '_person',
                    'court_include': True,
                    'obtain_address_type': 'other_address',
                    'obtain_address': 'аптейн адрес',
                    'bik_account': '012345678',
                    'account_number': '01234567890123456789'
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/go_ahead/', data={
                'batch_id': batch.id,
            })
            self.assertEqual(result.status_code, 200)
            self.assertEqual(BatchDocumentDbObject.query.count(), 1)
            self.assertEqual(BatchDocumentDbObject.query.filter_by(status="rendered").count(), 0)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.status, "generating_pretension")

    @authorized()
    def test_update_in_claim(self):
        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status="pretension")
            victim_car_owner = self.create_person(self.user, batch.id)
            guilty_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)

            batch_json = json.dumps({
                "data": {
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'policy_called': True,
                    'all_have_osago': True,
                    'own_insurance_company': True,
                    'have_osago': 'both',
                    'problem_type': 'refusal',
                    'refusal_reason': 'wrong_docs',
                    'notice_has_mistakes': False,
                    'got_cash': False,
                    'victim_owner': victim_car_owner.id + "_person",
                    'owner_as_victim_driver': True,
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'guilty_owner': guilty_car_owner.id + "_person",
                    'owner_as_guilty_driver': True,
                    'guilty_car_brand': u'Рено',
                    'guilty_car_number': u'В000ВВ50',
                    'other_victims': None,
                    'insurance_company_region': u'Санкт-Петербург',
                    'policy_series': u'ААА',
                    'policy_number': '0123456789',
                    'other_insurance': True,
                    'insurance_name': u"РоСгосСтраХ",
                    'insurance_id': None,
                    'other_date': True,
                    'policy_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'first_claim_date': (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                    'independent_expertise_number': u'01234567890123456789',
                    'independent_expertise_sum': 1500000,
                    'independent_expertise_cost': 200000,
                    'compensation_sum': 0,
                    'add_person_to_claim': True,
                    'docs_got': [OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                                 OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                                 OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE],
                    'insurance_case_number': '01234567890123456789',
                    'submission_way': 'responsible_person',
                    'submission_branch_id': '',
                    'use_other_submission_address': True,
                    'submission_address': u'сабмишн адрес',
                    'obtain_way': 'responsible_person',
                    'responsible_person': responsible_person.id + '_person',
                    'court_include': True,
                    'obtain_address_type': 'other_address',
                    'obtain_address': 'аптейн адрес',
                    'bik_account': '012345678',
                    'account_number': '01234567890123456789'
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/go_ahead/', data={
                'batch_id': batch.id,
            })
            self.assertEqual(result.status_code, 200)
            self.assertEqual(BatchDocumentDbObject.query.count(), 0)
            self.assertEqual(BatchDocumentDbObject.query.filter_by(status="rendered").count(), 3)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.status, "claim")

            batch_json = json.dumps({
                "data": {
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'policy_called': False,
                    'all_have_osago': False,
                    'own_insurance_company': True,
                    'have_osago': 'both',
                    'problem_type': 'refusal',
                    'refusal_reason': 'wrong_docs',
                    'notice_has_mistakes': False,
                    'got_cash': False,
                    'victim_owner': victim_car_owner.id + "_person",
                    'owner_as_victim_driver': True,
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'guilty_owner': guilty_car_owner.id + "_person",
                    'owner_as_guilty_driver': True,
                    'guilty_car_brand': u'Рено',
                    'guilty_car_number': u'В000ВВ50',
                    'other_victims': None,
                    'insurance_company_region': u'Санкт-Петербург',
                    'policy_series': u'ААА',
                    'policy_number': '0123456789',
                    'other_insurance': True,
                    'insurance_name': u"РоСгосСтраХ",
                    'insurance_id': None,
                    'other_date': True,
                    'policy_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'first_claim_date': (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                    'independent_expertise_number': u'01234567890123456789',
                    'independent_expertise_sum': 1500000,
                    'independent_expertise_cost': 200000,
                    'compensation_sum': 0,
                    'add_person_to_claim': True,
                    'docs_got': [OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                                 OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                                 OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE],
                    'insurance_case_number': '01234567890123456789',
                    'submission_way': 'responsible_person',
                    'submission_branch_id': '',
                    'use_other_submission_address': True,
                    'submission_address': u'сабмишн адрес2',
                    'obtain_way': 'responsible_person',
                    'responsible_person': responsible_person.id + '_person',
                    'court_include': True,
                    'obtain_address_type': 'other_address',
                    'obtain_address': 'аптейн адрес',
                    'bik_account': '012345678',
                    'account_number': '01234567890123456789'
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.status, "claim")

            self.assertEqual(BatchDocumentDbObject.query.count(), 3)
            self.assertEqual(BatchDocumentDbObject.query.filter(
                BatchDocumentDbObject.status=="rendered",
                BatchDocumentDbObject.file_id!=None
            ).count(), 3)

    @authorized()
    def test_update_in_generating_pretension(self):
        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status="pretension")
            victim_car_owner = self.create_person(self.user, batch.id)
            guilty_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)

            batch_json = json.dumps({
                "data": {
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'policy_called': True,
                    'all_have_osago': True,
                    'own_insurance_company': True,
                    'have_osago': 'both',
                    'problem_type': 'refusal',
                    'refusal_reason': 'wrong_docs',
                    'notice_has_mistakes': False,
                    'got_cash': False,
                    'victim_owner': victim_car_owner.id + "_person",
                    'owner_as_victim_driver': True,
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'guilty_owner': guilty_car_owner.id + "_person",
                    'owner_as_guilty_driver': True,
                    'guilty_car_brand': u'Рено',
                    'guilty_car_number': u'В000ВВ50',
                    'other_victims': None,
                    'insurance_company_region': u'Санкт-Петербург',
                    'policy_series': u'ААА',
                    'policy_number': '0123456789',
                    'other_insurance': True,
                    'insurance_name': u"РоСгосСтраХ",
                    'insurance_id': None,
                    'other_date': True,
                    'policy_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'first_claim_date': (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                    'independent_expertise_number': u'01234567890123456789',
                    'independent_expertise_sum': 1500000,
                    'independent_expertise_cost': 200000,
                    'compensation_sum': 0,
                    'add_person_to_claim': True,
                    'docs_got': [OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                                 OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                                 OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE],
                    'insurance_case_number': '01234567890123456789',
                    'submission_way': 'responsible_person',
                    'submission_branch_id': '',
                    'use_other_submission_address': True,
                    'submission_address': u'сабмишн адрес',
                    'obtain_way': 'responsible_person',
                    'responsible_person': responsible_person.id + '_person',
                    'court_include': True,
                    'obtain_address_type': 'other_address',
                    'obtain_address': 'аптейн адрес',
                    'bik_account': '012345678',
                    'account_number': '01234567890123456789'
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/go_ahead/', data={
                'batch_id': batch.id,
            })
            self.assertEqual(result.status_code, 200)
            self.assertEqual(BatchDocumentDbObject.query.count(), 3)
            self.assertEqual(BatchDocumentDbObject.query.filter_by(status="rendered").count(), 3)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.status, "claim")

            DocumentBatchDbObject.query.filter_by(id=batch.id).update({
                'status': 'generating_pretension'
            })
            sqldb.session.commit()

            batch_json = json.dumps({
                "data": {
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'policy_called': False,
                    'all_have_osago': False,
                    'own_insurance_company': True,
                    'have_osago': 'both',
                    'problem_type': 'refusal',
                    'refusal_reason': 'wrong_docs',
                    'notice_has_mistakes': False,
                    'got_cash': False,
                    'victim_owner': victim_car_owner.id + "_person",
                    'owner_as_victim_driver': True,
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'guilty_owner': guilty_car_owner.id + "_person",
                    'owner_as_guilty_driver': True,
                    'guilty_car_brand': u'Рено',
                    'guilty_car_number': u'В000ВВ50',
                    'other_victims': None,
                    'insurance_company_region': u'Санкт-Петербург',
                    'policy_series': u'ААА',
                    'policy_number': '0123456789',
                    'other_insurance': True,
                    'insurance_name': u"РоСгосСтраХ",
                    'insurance_id': None,
                    'other_date': True,
                    'policy_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'first_claim_date': (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                    'independent_expertise_number': u'01234567890123456789',
                    'independent_expertise_sum': 1500000,
                    'independent_expertise_cost': 200000,
                    'compensation_sum': 0,
                    'add_person_to_claim': True,
                    'docs_got': [OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                                 OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                                 OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE],
                    'insurance_case_number': '01234567890123456789',
                    'submission_way': 'responsible_person',
                    'submission_branch_id': '',
                    'use_other_submission_address': True,
                    'submission_address': u'сабмишн адрес2',
                    'obtain_way': 'responsible_person',
                    'responsible_person': responsible_person.id + '_person',
                    'court_include': True,
                    'obtain_address_type': 'other_address',
                    'obtain_address': 'аптейн адрес',
                    'bik_account': '012345678',
                    'account_number': '01234567890123456789'
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.status, "generating_pretension")

            self.assertEqual(BatchDocumentDbObject.query.count(), 3)
            self.assertEqual(BatchDocumentDbObject.query.filter(
                BatchDocumentDbObject.status=="rendered",
                BatchDocumentDbObject.file_id!=None
            ).count(), 3)

    @authorized()
    def test_go_back_in_claim(self):
        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status="pretension")
            victim_car_owner = self.create_person(self.user, batch.id)
            guilty_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)

            batch_json = json.dumps({
                "data": {
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'policy_called': True,
                    'all_have_osago': True,
                    'own_insurance_company': True,
                    'have_osago': 'both',
                    'problem_type': 'refusal',
                    'refusal_reason': 'wrong_docs',
                    'notice_has_mistakes': False,
                    'got_cash': False,
                    'victim_owner': victim_car_owner.id + "_person",
                    'owner_as_victim_driver': True,
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'guilty_owner': guilty_car_owner.id + "_person",
                    'owner_as_guilty_driver': True,
                    'guilty_car_brand': u'Рено',
                    'guilty_car_number': u'В000ВВ50',
                    'other_victims': None,
                    'insurance_company_region': u'Санкт-Петербург',
                    'policy_series': u'ААА',
                    'policy_number': '0123456789',
                    'other_insurance': True,
                    'insurance_name': u"РоСгосСтраХ",
                    'insurance_id': None,
                    'other_date': True,
                    'policy_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'first_claim_date': (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d"),
                    'independent_expertise_number': u'01234567890123456789',
                    'independent_expertise_sum': 1500000,
                    'independent_expertise_cost': 200000,
                    'compensation_sum': 0,
                    'add_person_to_claim': True,
                    'docs_got': [OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                                 OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                                 OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE],
                    'insurance_case_number': '01234567890123456789',
                    'submission_way': 'responsible_person',
                    'submission_branch_id': '',
                    'use_other_submission_address': True,
                    'submission_address': u'сабмишн адрес',
                    'obtain_way': 'responsible_person',
                    'responsible_person': responsible_person.id + '_person',
                    'court_include': True,
                    'obtain_address_type': 'other_address',
                    'obtain_address': 'аптейн адрес',
                    'bik_account': '012345678',
                    'account_number': '01234567890123456789'
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/go_ahead/', data={
                'batch_id': batch.id,
            })
            self.assertEqual(result.status_code, 200)
            self.assertEqual(BatchDocumentDbObject.query.count(), 3)
            self.assertEqual(BatchDocumentDbObject.query.filter_by(status="rendered").count(), 3)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.status, "claim")

            result = self.test_client.post('/batch/go_back/', data={
                'batch_id': batch.id,
            })
            self.assertEqual(result.status_code, 200)
            self.assertEqual(BatchDocumentDbObject.query.count(), 0)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.status, "pretension")

    @authorized()
    def test_result_fields_3_4_stage(self):
        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status="pretension")
            victim_car_owner = self.create_person(self.user, batch.id, name=u"виктим", surname=u"пострадашко", patronymic=u"потерпешевич")
            guilty_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)

            batch_json = json.dumps({
                "data": {
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'all_have_osago': True,
                    'own_insurance_company': True,
                    'have_osago': 'both',
                    'refusal_reason': 'wrong_docs',
                    'notice_has_mistakes': False,
                    'got_cash': False,
                    'victim_owner': victim_car_owner.id + "_person",
                    'owner_as_victim_driver': True,
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'guilty_owner': guilty_car_owner.id + "_person",
                    'owner_as_guilty_driver': True,
                    'guilty_car_brand': u'Рено',
                    'guilty_car_number': u'В000ВВ50',
                    'other_victims': None,
                    'insurance_company_region': u'Санкт-Петербург',
                    'policy_series': u'ААА',
                    'policy_number': '0123456789',
                    'other_insurance': True,
                    'insurance_name': u"РоСгосСтраХ",
                    'insurance_id': None,
                    'other_date': True,
                    'independent_expertise_number': u'01234567890123456789',
                    'independent_expertise_sum': '10.0',
                    'independent_expertise_cost': 1000,
                    'add_person_to_claim': True,
                    'docs_got': [OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                                 OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                                 OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE],
                    'insurance_case_number': '01234567890123456789',
                    'submission_way': 'responsible_person',
                    'submission_branch_id': '',
                    'use_other_submission_address': True,
                    'submission_address': u'сабмишн адрес',
                    'obtain_way': 'responsible_person',
                    'responsible_person': responsible_person.id + '_person',
                    'court_include': True,
                    'obtain_address_type': 'other_address',
                    'obtain_address': 'аптейн адрес',
                    'bik_account': '012345678',
                    'account_number': '01234567890123456789',
                    'police_case': True,

                    'policy_called': True,
                    'problem_type': 'refusal',
                    'policy_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'compensation_sum': 1000.9,

                    'lawsuit_date': datetime(2014, 5, 1).strftime("%Y-%m-%d"),
                    'first_claim_date': datetime(2014, 1, 1).strftime("%Y-%m-%d"),
                    'compensation_date': datetime(2015, 1, 1).strftime("%Y-%m-%d"),
                    'compensation_got': "9.0"
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            # формула для проверки: (0.01 * underpay_sum * ((lawsuit_date if lawsuit_date else datetime.now()) - first_claim_date - timedelta(days=20)).days)
            #                       if compensation_got is None
            #                       else (0.01 * underpay_sum * ((compensation_date if compensation_date else datetime.today()) - first_claim_date - timedelta(days=20)).days +
            #                            0.01 * (underpay_sum - compensation_got) * ((lawsuit_date if lawsuit_date else datetime.today()) - compensation_date if compensation_date else datetime.today()).days)

            self.assertEqual(db_batch.result_fields, {
                u'above_limits_sum': u'0',
                u'attached_to_lawsuit_docs': [u'case_init_refusal', u'expertise_report'],
                u'insufficient_docs': [u'police_protocol', u'act_insurance_case'],
                u'insurance_penalty': u'50',
                u'lawsuit_cost': u'500000.5',
                u'legal_fee': u'1000.5',
                u'limits_sum': u'400000',
                u'region': u'Санкт-Петербург',
                u'region_prepositional': u'Санкт-Петербург',
                u'responsible_person_dative': u'Поганкина Арина Мстиславовна',
                u'underpay_sum': u'10.0'
            })

    @authorized()
    def test_trust_court(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_OSAGO]['doc_types'] = [DocumentTypeEnum.DT_OSAGO_TRUST_COURT_REPRESENTATION]

        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user)
            victim_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Ивановна", age=22)

            batch_json = json.dumps({
                "data": {       # todo: add fields
                    'victim_owner': victim_car_owner.id + "_person",
                    'lawsuit_submission_responsible_person': responsible_person.id + '_person',
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    "submission_way": "responsible_person",
                    'obtain_way': 'responsible_person',
                    'insurance_name': u'ООО ААА ОАО АОА',
                    'court_include': True
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': batch.id,
                'document_type': json.dumps([DocumentTypeEnum.DT_OSAGO_TRUST_COURT_REPRESENTATION])
            })
            self.assertEqual(result.status_code, 200)

    @authorized()
    def test_trust_court_absence_claim(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_OSAGO]['doc_types'] = [DocumentTypeEnum.DT_OSAGO_CLAIM_COURT_ABSENT]

        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user)
            victim_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Ивановна", age=22)

            batch_json = json.dumps({
                "data": {
                    'victim_owner': victim_car_owner.id + "_person",
                    'lawsuit_submission_responsible_person': responsible_person.id + '_person',
                    'responsible_person': responsible_person.id + '_person',
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    "submission_way": "responsible_person",
                    'obtain_way': 'responsible_person',
                    'insurance_name': u'ООО ААА ОАО АОА',
                    'court_include': True,
                    'first_claim_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    "court_name": u'Наш суд, самый гуманный суд в мире',
                    "court_address": u'Планета Обезьян',
                    "add_person_to_claim": True,
                    'lawsuit_submission_way': 'oneself'
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': batch.id,
                'document_type': json.dumps([DocumentTypeEnum.DT_OSAGO_CLAIM_COURT_ABSENT])
            })
            self.assertEqual(result.status_code, 200)

    @authorized()
    def test_go_ahead_in_claim(self):
        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status="claim")

            batch_payment = PayInfoObject(
                user=self.user,
                batch=batch,
                pay_record_id=0,
                payment_provider=1,
                service_type=PurchaseServiceType.OSAGO_PART1
            )
            sqldb.session.add(batch_payment)
            batch_payment = PayInfoObject(
                user=self.user,
                batch=batch,
                pay_record_id=1,
                payment_provider=1,
                service_type=PurchaseServiceType.OSAGO_PART2
            )
            sqldb.session.add(batch_payment)
            sqldb.session.commit()

            victim_car_owner = self.create_person(self.user, batch.id, name=u"ЖЖ", surname=u"ЖЖ", patronymic=u"ЖЖ")
            guilty_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)

            batch_json = json.dumps({
                "data": {
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'all_have_osago': True,
                    'own_insurance_company': True,
                    'have_osago': 'both',
                    'notice_has_mistakes': False,
                    'got_cash': True,
                    'victim_owner': victim_car_owner.id + "_person",
                    'owner_as_victim_driver': True,
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'guilty_owner': guilty_car_owner.id + "_person",
                    'owner_as_guilty_driver': True,
                    'guilty_car_brand': u'Рено',
                    'guilty_car_number': u'В000ВВ50',
                    'other_victims': None,
                    'insurance_company_region': u'Санкт-Петербург',
                    'policy_series': u'ААА',
                    'policy_number': '0123456789',
                    'other_insurance': True,
                    'insurance_name': u"РоСгосСтраХ",
                    'insurance_id': None,
                    'first_claim_date': (datetime(2014,5,1) - timedelta(days=90)).strftime("%Y-%m-%d"),
                    'independent_expertise_number': u'01234567890123456789',
                    'independent_expertise_cost': 1000,
                    'add_person_to_claim': True,
                    'docs_got': [
                        OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                        OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                        OsagoDocTypeEnum.ODT_INSURANCE_DENIAL,
                    ],
                    'insurance_case_number': '01234567890123456789',
                    'submission_branch_id': '',
                    'use_other_submission_address': True,
                    'submission_address': u'сабмишн адрес',
                    'obtain_way': 'responsible_person',
                    'responsible_person': responsible_person.id + '_person',
                    'obtain_address_type': 'other_address',
                    'obtain_address': 'аптейн адрес',
                    'bik_account': '012345678',
                    'account_number': '01234567890123456789',
                    'police_case': False,
                    'refusal_reason': OsagoRefusalReasonEnum.ORR_WRONG_DOCS,

                    'court_name': u"Наименование суда",
                    'court_address': u'Адрес суда',
                    'lawsuit_submission_way': 'mail',

                    'court_include': True,
                    'submission_way': 'responsible_person',

                    'lawsuit_submission_responsible_person': responsible_person.id + '_person',

                    # --------------------------------------------------------------------------------------------------
                    'policy_called': True,          # gibdd/euro
                    'other_date': True,
                    'policy_date': "2015-01-01",

                    'independent_expertise_sum': '500000',

                    'problem_type': 'refusal',
                    'compensation_sum': 10000,     # до претензии
                    "pretension_result": "success",
                    "compensation_got": 5000,       # после претензии

                    # --------------------------------------------------------------------------------------------------
                    "compensation_date": (datetime.utcnow() - timedelta(days=50)).strftime("%Y-%m-%d"),
                    "insurance_returned_docs": [
                        OsagoDocTypeEnum.ODT_POLICE_PROTOCOL,
                        OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE,
                        OsagoDocTypeEnum.ODT_POLICE_STATEMENT,
                        OsagoDocTypeEnum.ODT_CASE_INITIATION_REFUSAL
                    ],
                    "pretension_answer_got": True,
                    "lawsuit_date": (datetime.utcnow() - timedelta(days=20)).strftime("%Y-%m-%d"),
                    "make_lawsuit": True,
                    "insurance_lawsuit": [
                        InsuranceLawsuitEnum.ILS_EXPERTISE_COST,
                        InsuranceLawsuitEnum.ILS_FINE,
                        InsuranceLawsuitEnum.ILS_PENALTY,
                        InsuranceLawsuitEnum.ILS_UNDERPAY
                    ],
                    "notary_costs": 100000.12,
                    "moral_damages": 2000000.34,
                    'court_attendance': 'responsible_person',
                    "attached_to_lawsuit_docs_pagecount": [
                    {
                        "page": OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_INSURANCE_DENIAL,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_POLICE_STATEMENT,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_POLICE_PROTOCOL,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_CASE_INITIATION_REFUSAL,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_EXPERTISE_REPORT,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_EXPERTISE_CONTRACT,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_PRETENSION_ANSWER_COPY,
                        "pagecount": 123
                    },{
                        "page": OsagoDocTypeEnum.ODT_NOTARY_PAY_ACT,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_POLICY_OSAGO,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_BANK_STATEMENT,
                        "pagecount": 321
                    }]
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/go_ahead/', data={
                'batch_id': batch.id,
            })
            self.assertEqual(result.status_code, 200)
            self.assertEqual(BatchDocumentDbObject.query.count(), 3)
            self.assertEqual(BatchDocumentDbObject.query.filter_by(status="rendered").count(), 3)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.status, "court")

    def test_fields_order(self):
        field_values = {
            'a': 'a',
            'b': 'b'
        }
        schema = {
            'fields': [{
                'name': 'd',
                'field_type': 'DocTextField',
                'type': 'calculated',
                'depends_on': ['b', 'c'],
                'value': {
                    '#sum': [{
                        '#field': 'b'
                    }, {
                        "#value": " + "
                    }, {
                        '#field': 'c'
                    }]
                }
            }, {
                'name': 'e',
                'field_type': 'DocTextField',
                'type': 'calculated',
                'depends_on': ['a', 'd'],
                'value': {
                    '#sum': [{
                        '#field': 'a'
                    }, {
                        "#value": " + "
                    }, {
                        '#field': 'd'
                    }]
                }
            }, {
                'name': 'f',
                'field_type': 'DocTextField',
                'type': 'calculated',
                'depends_on': ['b'],
                'value': {
                    '#field': 'b'
                }
            }, {
                'name': 'a',
                'type': 'DocTextField'
            }, {
                'name': 'c',
                'field_type': 'DocTextField',
                'type': 'calculated',
                'depends_on': ['a'],
                'value': {
                    '#field': 'a'
                }
            }, {
                'name': 'b',
                'type': 'DocTextField'
            }]
        }

        result = transform_with_schema(field_values, schema)
        for i in result:
            print(i + '=' + result[i].db_value())

    @authorized()
    def test_go_ahead_in_court(self):
        with self.app.app_context():
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status="court")
            victim_car_owner = self.create_person(self.user, batch.id, name=u"ЖЖ", surname=u"ЖЖ", patronymic=u"ЖЖ")
            guilty_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)

            batch_json = json.dumps({
                "data": {
                    'crash_date': (datetime.utcnow() - timedelta(days=100)).strftime("%Y-%m-%d"),
                    'all_have_osago': True,
                    'own_insurance_company': True,
                    'have_osago': 'both',
                    'notice_has_mistakes': False,
                    'got_cash': True,
                    'victim_owner': victim_car_owner.id + "_person",
                    'owner_as_victim_driver': True,
                    'victim_car_brand': u"Форд Фокус в кредит",
                    'victim_car_number': u"А000ОО98",
                    'guilty_owner': guilty_car_owner.id + "_person",
                    'owner_as_guilty_driver': True,
                    'guilty_car_brand': u'Рено',
                    'guilty_car_number': u'В000ВВ50',
                    'other_victims': None,
                    'insurance_company_region': u'Санкт-Петербург',
                    'policy_series': u'ААА',
                    'policy_number': '0123456789',
                    'other_insurance': True,
                    'insurance_name': u"РоСгосСтраХ",
                    'insurance_id': None,
                    'first_claim_date': (datetime(2014,5,1) - timedelta(days=90)).strftime("%Y-%m-%d"),
                    'independent_expertise_number': u'01234567890123456789',
                    'independent_expertise_cost': 1000,
                    'add_person_to_claim': True,
                    'docs_got': [
                        OsagoDocTypeEnum.ODT_INQUIRE_CRASH
                    ],
                    'insurance_case_number': '01234567890123456789',
                    'submission_branch_id': '',
                    'use_other_submission_address': True,
                    'submission_address': u'сабмишн адрес',
                    'obtain_way': 'responsible_person',
                    'responsible_person': responsible_person.id + '_person',
                    'obtain_address_type': 'other_address',
                    'obtain_address': 'аптейн адрес',
                    'bik_account': '012345678',
                    'account_number': '01234567890123456789',
                    'police_case': False,
                    'refusal_reason': OsagoRefusalReasonEnum.ORR_WRONG_DOCS,

                    'court_name': u"Наименование суда",
                    'court_address': u'Адрес суда',
                    'lawsuit_submission_way': 'oneself',

                    'court_include': True,
                    'submission_way': 'responsible_person',

                    'lawsuit_submission_responsible_person': responsible_person.id + '_person',
                    'lawsuit_number': '1234567890',

                    # --------------------------------------------------------------------------------------------------
                    'policy_called': True,          # gibdd/euro
                    'other_date': True,
                    'policy_date': "2013-01-01",

                    'independent_expertise_sum': '1200000',

                    'problem_type': 'refusal',
                    'compensation_sum': 10000,     # до претензии
                    "pretension_result": "refuse",
                    "compensation_got": 10000,       # после претензии

                    # --------------------------------------------------------------------------------------------------
                    "compensation_date": (datetime.utcnow() - timedelta(days=20)).strftime("%Y-%m-%d"),
                    "insurance_returned_docs": [OsagoDocTypeEnum.ODT_POLICE_PROTOCOL],
                    "pretension_answer_got": True,
                    "lawsuit_date": (datetime.utcnow() - timedelta(days=50)).strftime("%Y-%m-%d"),
                    "make_lawsuit": True,
                    "insurance_lawsuit": [
                        InsuranceLawsuitEnum.ILS_EXPERTISE_COST,
                        InsuranceLawsuitEnum.ILS_FINE,
                        InsuranceLawsuitEnum.ILS_PENALTY,
                        InsuranceLawsuitEnum.ILS_UNDERPAY
                    ],
                    "notary_costs": 100000.12,
                    "moral_damages": 2000000.34,
                    'court_attendance': 'responsible_person',

                    'insurance_execution_act_responsible_person': True,
                    'insurance_execution_act_obtain_way': 'no_obtain',

                    'guilty_execution_act_responsible_person': False,
                    'guilty_execution_act_obtain_way': 'no_obtain',

                    "attached_to_lawsuit_docs_pagecount": [
                    {
                        "page": OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_INSURANCE_DENIAL,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_POLICE_STATEMENT,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_POLICE_PROTOCOL,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_CASE_INITIATION_REFUSAL,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_EXPERTISE_REPORT,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_EXPERTISE_CONTRACT,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_PRETENSION_ANSWER_COPY,
                        "pagecount": 123
                    },{
                        "page": OsagoDocTypeEnum.ODT_NOTARY_PAY_ACT,
                        "pagecount": 123
                    }, {
                        "page": OsagoDocTypeEnum.ODT_POLICY_OSAGO,
                        "pagecount": 123
                    }]
                }
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/go_ahead/', data={
                'batch_id': batch.id,
            })
            self.assertEqual(result.status_code, 200)
            self.assertEqual(BatchDocumentDbObject.query.count(), 3)
            self.assertEqual(BatchDocumentDbObject.query.filter_by(status="rendered").count(), 3)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch.id).first()
            self.assertEqual(db_batch.status, "court")

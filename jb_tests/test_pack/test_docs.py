# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import urllib

from flask import json, current_app

from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import (RFRegionsEnum, StreetTypeEnum, HouseTypeEnum)
from fw.documents.db_fields import (DocumentBatchDbObject, CompanyDbObject,
                                    PrivatePersonDbObject, BatchDocumentDbObject)
from fw.documents.enums import DocumentBatchTypeEnum, BatchStatusEnum, PersonDocumentTypeEnum, UserDocumentStatus
from fw.documents.enums import DocumentTypeEnum
from fw.documents.fields.doc_fields import UserDocument
from fw.documents.fields.simple_doc_fields import DocTextField
from fw.storage.file_storage import FileStorage
from fw.storage.models import FileObject
from services.llc_reg.documents.enums import CompanyStarterCapitalTypeEnum
from services.llc_reg.documents.enums import FounderTypeEnum
from services.test_svc import TestSvcManager
from test_api import authorized
from test_pack.base_batch_test import BaseBatchTestCase


class DocsTestCase(BaseBatchTestCase):
    def setUp(self):
        super(DocsTestCase, self).setUp()
        self.maxDiff = None

    @authorized()
    def test_delete_batch_document(self):
        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                data={
                    "a": 1
                },
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()

            batch2 = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                data={
                    "a": 2
                },
                _owner=self.user
            )
            sqldb.session.add(batch2)
            sqldb.session.commit()
            batch2_id = batch2.id

            batch3 = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                data={
                    "a": 3
                },
                _owner=self.user
            )
            sqldb.session.add(batch3)
            sqldb.session.commit()

            result = self.test_client.post('/batch/delete/', data={'batch_id': batch2.id})
            self.assertEqual(result.status_code, 200)

            data = json.loads(result.data)
            self.assertEqual(data['result'], True)

            self.assertEqual(DocumentBatchDbObject.query.filter_by(deleted=False).count(), 2)
            self.assertIsNotNone(DocumentBatchDbObject.query.filter_by(id=batch.id).first())
            self.assertIsNone(DocumentBatchDbObject.query.filter_by(id=batch2_id, deleted=False).first())
            self.assertIsNotNone(DocumentBatchDbObject.query.filter_by(id=batch3.id).first())

    @authorized()
    def test_delete_batch_document(self):
        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                data={
                    "a": 1
                },
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()

            result = self.test_client.get('/batch/')
            self.assertEqual(result.status_code, 200)

            data = json.loads(result.data)
            a = 1

    @authorized()
    def test_make_docs_from_data(self):
        batch_manager = TestSvcManager()

        short_name = DocTextField()
        short_name.parse_raw_value(u"Наименование")
        current_batch_data_fields = {
            'short_name': short_name
        }

        new_short_name = DocTextField()
        new_short_name.parse_raw_value(u"Наименование 2")
        new_batch_fields = {
            'short_name': new_short_name
        }

        current_batch_db_model = DocumentBatchDbObject(
            _owner=self.user,
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
        )

        new_field_set, docs_list, changed_field_names = batch_manager.make_docs_for_new_data(
            current_batch_data_fields,
            new_batch_fields,
            current_batch_db_model
        )

        self.assertEqual(changed_field_names, {"short_name"})

        self.assertIn('short_name', new_field_set)
        self.assertIsInstance(new_field_set['short_name'], DocTextField)
        self.assertEqual(new_field_set['short_name'], u"Наименование 2")

        self.assertEqual(len(docs_list), 1)
        doc = docs_list[0]
        self.assertIsInstance(doc, UserDocument)
        fields = doc.data.value
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields['short_name'], u"Наименование 2")

    def test_make_docs_from_unchanged(self):
        batch_manager = TestSvcManager()

        short_name = DocTextField()
        short_name.parse_raw_value(u"Наименование")
        current_batch_data_fields = {
            'short_name': short_name
        }

        new_short_name = DocTextField()
        new_short_name.parse_raw_value(u"Наименование")
        new_batch_fields = {
            'short_name': new_short_name
        }

        current_batch_db_model = DocumentBatchDbObject(
            _owner=self.user,
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
        )

        new_field_set, docs_list, changed_field_names = batch_manager.make_docs_for_new_data(
            current_batch_data_fields,
            new_batch_fields,
            current_batch_db_model
        )

        self.assertEqual(changed_field_names, set())

        self.assertIn('short_name', new_field_set)
        self.assertIsInstance(new_field_set['short_name'], DocTextField)
        self.assertEqual(new_field_set['short_name'], u"Наименование")

        self.assertEqual(len(docs_list), 1)
        doc = docs_list[0]
        self.assertIsInstance(doc, UserDocument)
        fields = doc.data.value
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields['short_name'], u"Наименование")

    @authorized()
    def test_update_batch(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)
        sqldb.session.commit()

        data = {
            "short_name": u"Новое наименование"
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data,
                "metadata": {
                    u"some": "data"
                },
            })
        })
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(new_batch._documents), 1)
        doc = new_batch._documents[0]
        self.assertEqual(doc.data, {
            "short_name": u"Новое наименование"
        })
        self.assertEqual(doc.status, UserDocumentStatus.DS_NEW)

    @authorized()
    def test_add_docs_on_update(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        data = {
            "short_name": u"создай второй документ"
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data
            })
        })
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(new_batch._documents), 2)
        doc = new_batch._documents[0]
        self.assertEqual(doc.data, {
            "short_name": u"создай второй документ"
        })
        self.assertEqual(doc.status, UserDocumentStatus.DS_NEW)

        doc = new_batch._documents[1]
        self.assertEqual(doc.data, {
            "short_name": u"создай второй документ"
        })
        self.assertEqual(doc.status, UserDocumentStatus.DS_NEW)

    @authorized()
    def test_remove_docs_on_update(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"создай второй документ"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            data={
                "short_name": u"создай второй документ"
            }
        )
        sqldb.session.add(first_doc)

        second_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_2,
            data={
                "short_name": u"создай второй документ"
            }
        )
        sqldb.session.add(second_doc)
        sqldb.session.commit()

        data = {
            "short_name": u"не создавай второй документ"
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data
            })
        })
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(new_batch._documents), 1)
        doc = new_batch._documents[0]
        self.assertEqual(doc.data, {
            "short_name": u"не создавай второй документ"
        })
        self.assertEqual(doc.status, UserDocumentStatus.DS_NEW)

    @authorized()
    def test_update_docs_on_update(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()
        obj_id = first_doc.id

        data = {
            "short_name": u"Новое наименование"
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data
            })
        })
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(new_batch._documents), 1)
        doc = new_batch._documents[0]
        self.assertEqual(doc.data, {
            "short_name": u"Новое наименование"
        })
        self.assertEqual(doc.status, UserDocumentStatus.DS_NEW)
        self.assertEqual(doc.id, obj_id)

    @authorized()
    def test_update_edited_batch(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_EDITED,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        data = {
            "short_name": u"Новое наименование"
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data
            })
        })
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(new_batch._documents), 1)
        doc = new_batch._documents[0]
        self.assertEqual(doc.data, {
            "short_name": u"Новое наименование"
        })
        self.assertEqual(doc.status, UserDocumentStatus.DS_NEW)

    @authorized()
    def test_validation_errors_during_update_edited_batch(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_EDITED,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        data = {
            "short_name": u"Новое наименование, но очень очень длинное"
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data
            })
        })
        self.assertEqual(result.status_code, 200)

        self.assertEqual(new_batch.error_info, {
            u'error_ext': [{
                u'error_code': 5,
                u'field': u'short_name'
            }]
        })
        self.assertEqual(len(new_batch._documents), 1)
        doc = new_batch._documents[0]
        self.assertEqual(doc.data, {
            "short_name": u"Новое наименование, но очень очень длинное"
        })
        self.assertEqual(doc.status, UserDocumentStatus.DS_NEW)

    @authorized()
    def test_finalize(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_EDITED,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            _owner=self.user,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id,
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']
        self.assertTrue(data)

    @authorized()
    def test_render_deferred_docs(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"создай второй документ"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            _owner=self.user,
            data={
                "short_name": u"создай второй документ"
            }
        )
        sqldb.session.add(first_doc)

        second_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_2,
            _owner=self.user,
            data={
                "short_name": u"создай второй документ"
            }
        )
        sqldb.session.add(second_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id,
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']
        self.assertTrue(data)

    @authorized()
    def test_render_with_finalized_entities(self):
        # todo: 1. create entities
        person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя",
            surname=u"СтараяФамилия",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='male',
            birthplace=u"Неизвестно где"
        )
        sqldb.session.add(person)

        company_person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя2",
            surname=u"СтараяФамилия2",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='female',
            birthplace=u"Неизвестно где2"
        )
        sqldb.session.add(company_person)
        sqldb.session.commit()

        company = CompanyDbObject(
            _owner=self.user,
            inn=u"6514008400",
            ogrn=u"1086507000029",
            kpp=u"651401001",
            full_name=u"Полное наименование",
            short_name=u"Краткое наименование",
            address={
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4"
            },
            general_manager={
                '_id': company_person.id,
                'type': 'person'
            }
        )
        sqldb.session.add(company)
        sqldb.session.commit()

        pp1_id = person.id
        pp2_id = company_person.id
        co_id = company.id

        # todo: 2. finalize

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        data = {
            "short_name": u"Новое наименование",
            "general_manager": "%s_person" % person.id,
            "some_db_object": "%s_company" % company.id
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data
            })
        })
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(new_batch._documents), 2)
        doc = new_batch._documents[0]
        self.assertEqual(doc.data, {
            "short_name": u"Новое наименование"
        })
        self.assertEqual(doc.status, UserDocumentStatus.DS_NEW)

        doc = new_batch._documents[1]
        self.assertEqual(doc.data, {
            u'general_manager': {
                u'_id': person.id,
                u'type': u'person'
            },
            u'some_db_object': {
                u'_id': company.id,
                u'type': u'company'
            }
        })
        self.assertEqual(doc.status, UserDocumentStatus.DS_NEW)

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id,
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']
        self.assertTrue(data)

        # todo: 3. change entities

        person.name = u"НовоеИмя"
        company.full_name = u"НовоеНаименование"
        company_person.name = u"НовоеИмя2"

        sqldb.session.commit()

        # todo: 4. get batch
        result = self.test_client.get('/batch/?batch_id=%s' % new_batch.id)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']

        # todo: 5. check that batch data contain original entities
        pp_copy = PrivatePersonDbObject.query.filter_by(_copy_id=pp1_id).first()
        self.assertIsNone(pp_copy)

        pp2_copy = PrivatePersonDbObject.query.filter_by(_copy_id=pp2_id).first()
        self.assertIsNone(pp2_copy)

        cc_copy = CompanyDbObject.query.filter_by(_copy_id=co_id).first()
        self.assertIsNone(cc_copy)


    @authorized()
    def test_definalize(self):
        person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя",
            surname=u"СтараяФамилия",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='male',
            birthplace=u"Неизвестно где"
        )
        sqldb.session.add(person)

        company_person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя2",
            surname=u"СтараяФамилия2",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='female',
            birthplace=u"Неизвестно где2"
        )
        sqldb.session.add(company_person)
        sqldb.session.commit()

        company = CompanyDbObject(
            _owner=self.user,
            inn=u"6514008400",
            ogrn=u"1086507000029",
            kpp=u"651401001",
            full_name=u"Полное наименование",
            short_name=u"Краткое наименование",
            address={
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4"
            },
            general_manager= {
                '_id': company_person.id,
                'type': 'person'
            }
        )
        sqldb.session.add(company)
        sqldb.session.commit()

        pp1_id = person.id
        co_id = company.id

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_EDITED,
            paid=False
        )
        sqldb.session.add(new_batch)
        sqldb.session.commit()

        data = {
            "short_name": u"Новое наименование",
            "general_manager": "%s_person" % person.id,
            "some_db_object": "%s_company" % company.id
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data
            })
        })
        self.assertEqual(result.status_code, 200)

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id,
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']
        self.assertTrue(data)

        self.assertEqual(CompanyDbObject.query.count(), 1)
        self.assertEqual(PrivatePersonDbObject.query.count(), 2)

        result = self.test_client.post('/batch/unfinalise/', data={
            'batch_id': new_batch.id,
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']
        self.assertTrue(data)

        self.assertEqual(CompanyDbObject.query.count(), 1)
        self.assertEqual(PrivatePersonDbObject.query.count(), 2)

        result = self.test_client.get('/batch/?batch_id=%s' % new_batch.id)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']

        for key in ('metadata', 'name', 'all_docs'):
            del data['batches'][0][key]

        self.assertEqual(data, {
            u'batches': [{
                u'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
                u'creation_date': new_batch.creation_date.strftime("%Y-%m-%dT%H:%M:%S"),
                u'data': {
                    u'general_manager': u'%s_person' % pp1_id,
                    u'short_name': u'Новое наименование',
                    u'some_db_object': u'%s_company' % co_id
                },
                u'finalisation_date': new_batch.finalisation_date.strftime("%Y-%m-%dT%H:%M:%S"),
                u'id': new_batch.id,
                u'paid': u'false',
                u'result_fields': {
                    u'name': u'Новое наименование'
                },
                u'status': u'edited'
            }],
            u'count': 1,
            u'total': 1
        })

    @authorized()
    def test_delete_old_files_on_rerender(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_EDITED,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            _owner=self.user,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id,
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']
        self.assertTrue(data)

        self.assertEqual(FileObject.query.count(), 1)
        self.assertEqual(BatchDocumentDbObject.query.count(), 1)

        result = self.test_client.post('/batch/unfinalise/', data={
            'batch_id': new_batch.id,
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']
        self.assertTrue(data)

        self.assertEqual(FileObject.query.count(), 1)
        self.assertEqual(BatchDocumentDbObject.query.count(), 1)

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id,
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']
        self.assertTrue(data)

        self.assertEqual(FileObject.query.count(), 1)
        self.assertEqual(BatchDocumentDbObject.query.count(), 1)

    @authorized()
    def test_get_batch_data_according_to_api(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_EDITED,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            _owner=self.user,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id,
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']
        self.assertTrue(data)

        self.assertEqual(FileObject.query.count(), 1)
        self.assertEqual(BatchDocumentDbObject.query.count(), 1)

        result = self.test_client.get('/batch/')
        result = self.test_client.get('/batch/?batch_id=%s' % new_batch.id)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']

        file_obj = FileObject.query.first()
        file_url = u"http://service.zz/storage/%s" % urllib.quote((unicode(file_obj.id) + '/' + u'Тестовый документ 1.pdf').encode('utf8'))
        self.assertEqual(data, {
            u'batches': [{
                u'id': new_batch.id,
                u'creation_date': new_batch.creation_date.strftime("%Y-%m-%dT%H:%M:%S"),
                u'finalisation_date': new_batch.finalisation_date.strftime("%Y-%m-%dT%H:%M:%S"),
                u'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
                u'status': u'finalised',
                u'paid': u'false',
                u'all_docs': [{
                    u"file_link": file_url,
                    u"document_type": DocumentTypeEnum.DT_TEST_DOC_1,
                    u"document_id": first_doc.id,
                    u"caption": u'Тестовый документ 1'
                }],
                u'data': {
                    u'short_name': u'Старое наименование',
                },
                u'name': u'Тестовый батч',
                u'metadata': {},
                u'result_fields': {}
            }],
            u'count': 1,
            u'total': 1
        })

    @authorized()
    def test_update_metadata(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)
        sqldb.session.commit()

        data = {
            "short_name": u"Новое наименование"
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data,
                "metadata": {
                    "some": "data"
                }
            })
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(new_batch._metadata, {
            "some": "data"
        })

    @authorized()
    def test_update_only_metadata(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)
        sqldb.session.commit()

        data = {
            "short_name": u"Новое наименование"
        }

        result = self.test_client.post('/batch/update_metadata/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data,
                "metadata": {
                    "some": "data"
                }
            })
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(new_batch._metadata, {
            "some": "data"
        })

    @authorized()
    def test_definalize_forced(self):
        person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя",
            surname=u"СтараяФамилия",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='male',
            birthplace=u"Неизвестно где"
        )
        sqldb.session.add(person)

        company_person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя2",
            surname=u"СтараяФамилия2",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='male',
            birthplace=u"Неизвестно где2"
        )
        sqldb.session.add(company_person)
        sqldb.session.commit()

        company = CompanyDbObject(
            _owner=self.user,
            inn=u"6514008400",
            ogrn=u"1086507000029",
            kpp=u"651401001",
            full_name=u"Полное наименование",
            short_name=u"Краткое наименование",
            address={
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4"
            },
            general_manager= {
                '_id': company_person.id,
                'type': 'person'
            }
        )
        sqldb.session.add(company)
        sqldb.session.commit()

        pp1_id = person.id
        co_id = company.id

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_EDITED,
            paid=False
        )
        sqldb.session.add(new_batch)
        sqldb.session.commit()

        data = {
            "short_name": u"Новое наименование",
            "general_manager": "%s_person" % person.id,
            "some_db_object": "%s_company" % company.id
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data
            })
        })
        self.assertEqual(result.status_code, 200)

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id,
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']
        self.assertTrue(data)

        self.assertEqual(CompanyDbObject.query.count(), 1)
        self.assertEqual(PrivatePersonDbObject.query.count(), 2)

        PrivatePersonDbObject.query.filter_by(_copy=None).update({
            'name': u"НовоеИмя"
        })
        sqldb.session.commit()

        result = self.test_client.get('/batch/?batch_id=%s' % new_batch.id)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']

        for key in ('metadata', 'name', 'all_docs'):
            del data['batches'][0][key]

        self.assertEqual(data, {
            u'batches': [{
                u'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
                u'creation_date': new_batch.creation_date.strftime("%Y-%m-%dT%H:%M:%S"),
                u'data': {
                    u'general_manager': u'%s_person' % person.id,
                    u'short_name': u'Новое наименование',
                    u'some_db_object': u'%s_company' % company.id
                },
                u'finalisation_date': new_batch.finalisation_date.strftime("%Y-%m-%dT%H:%M:%S"),
                u'id': new_batch.id,
                u'paid': u'false',
                u'result_fields': {
                    u'name': u'Новое наименование'
                },
                u'status': u'finalised'
            }],
            u'count': 1,
            u'total': 1
        })

        result = self.test_client.post('/batch/unfinalise/', data={
            'batch_id': new_batch.id,
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertIn('result', data)
        self.assertNotIn('error', data)

    @authorized()
    def test_validation_errors_on_update(self):
        person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя",
            surname=u"СтараяФамилия",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='male',
            birthplace=u"Неизвестно где"
        )
        sqldb.session.add(person)

        company_person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя2",
            surname=u"СтараяФамилия2",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='female',
            birthplace=u"Неизвестно где2"
        )
        sqldb.session.add(company_person)
        sqldb.session.commit()

        company = CompanyDbObject(
            _owner=self.user,
            inn=u"6514008400",
            ogrn=u"1086507000029",
            kpp=u"651401001",
            full_name=u"Полное наименование",
            short_name=u"Краткое наименование",
            address={
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4"
            },
            general_manager= {
                '_id': company_person.id,
                'type': 'person'
            }
        )
        sqldb.session.add(company)
        sqldb.session.commit()

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_EDITED,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        person.name = u""
        person.address = {
            "region": u"непонятно какой",
            "street": u"Мотоциклистов",
            "house": "4"
        }

        company.full_name = u""
        company.inn = 123

        sqldb.session.commit()

        data = {
            "short_name": u"Новое наименование, но очень очень очень очень очень очень длинное",
            "general_manager": "%s_person" % person.id,
            "some_db_object": "%s_company" % company.id
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data
            })
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertIn('result', data)
        self.assertNotIn('error', data)
        for key in ('batch_type', 'creation_date', 'id', 'metadata', 'name', 'paid', 'status', 'all_docs'):
            del data['result'][key]
        self.assertEqual(data['result'], {
            u'data': {
                u'general_manager': u'%s_person' % person.id,
                u'short_name': u'Новое наименование, но очень очень очень очень очень очень длинное',
                u'some_db_object': u'%s_company' % company.id
            },
            u'error_info': {
                u'error_ext': [{
                    u'error_code': 5,
                    u'field': u'short_name'
                }, {
                    u'error_code': 5,
                    u'field': u'general_manager.name'
                }, {
                    u'error_code': 4,
                    u'field': u'general_manager.address.index'
                }, {
                    u'error_code': 4,
                    u'field': u'general_manager.address.house_type'
                }, {
                    u'error_code': 4,
                    u'field': u'general_manager.address.region'
                }, {
                    u'error_code': 5,
                    u'field': u'some_db_object.inn'
                }]
            },
            u'result_fields': {
                u'name': u'Новое наименование, но очень очень очень очень очень очень длинное'
            }
        })

    @authorized()
    def test_validation_errors_on_finalise(self):
        person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"",
            surname=u"",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='male',
            birthplace=u"Неизвестно где"
        )
        sqldb.session.add(person)

        company_person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя2",
            surname=u"СтараяФамилия2",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='invalid'
        )
        sqldb.session.add(company_person)
        sqldb.session.commit()

        company = CompanyDbObject(
            _owner=self.user,
            inn=u"6514008400",
            ogrn=u"1086507000029",
            kpp=u"651401001",
            full_name=u"Полное наименование",
            short_name=u"Краткое наименование",
            address={
                "index": 198209,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4"
            },
            general_manager= {
                '_id': company_person.id,
                'type': 'person'
            }
        )
        sqldb.session.add(company)
        sqldb.session.commit()

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование и уже очень очень очень очень очень длинное",
                "general_manager": {
                    "type": "person",
                    "_id": person.id
                },
                "some_db_object": {
                    "type": "company",
                    "_id": company.id
                }
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_EDITED,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            data={
                "short_name": u"Старое наименование и уже очень очень очень очень очень длинное"
            }
        )
        sqldb.session.add(first_doc)

        second_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_3,
            data={
                "general_manager": {
                    "type": "person",
                    "_id": person.id
                },
                "some_db_object": {
                    "type": "company",
                    "_id": company.id
                }
            }
        )
        sqldb.session.add(second_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertIn('result', data)
        self.assertNotIn('error', data)
        self.assertFalse(data['result'])

        result = self.test_client.get('/batch/?batch_id=%s' % new_batch.id)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)['result']
        for key in ('batch_type', 'creation_date', 'id', 'metadata', 'name', 'paid', 'status', 'all_docs'):
            del data['batches'][0][key]
        self.assertEqual(data['batches'][0], {
            u'data': {
                u'general_manager': u'%s_person' % person.id,
                u'short_name': u'Старое наименование и уже очень очень очень очень очень длинное',
                u'some_db_object': u'%s_company' % company.id
            },
            u'error_info': {
                u'error_ext': [{
                    u'error_code': 5,
                    u'field': u'short_name'
                }, {
                    u'error_code': 5,
                    u'field': u'general_manager.surname'
                }, {
                    u'error_code': 5,
                    u'field': u'general_manager.name'
                }, {
                    u'error_code': 4,
                    u'field': u'some_db_object.general_manager.birthplace'
                }, {
                    u'error_code': 4,
                    u'field': u'some_db_object.general_manager.sex'
                }, {
                    u'error_code': 4,
                    u'field': u'some_db_object.address.region'
                }]
            },
            u'result_fields': {}
        })

    @authorized()
    def test_do_not_update_service_fields(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)
        sqldb.session.commit()

        original_creation_date = new_batch.creation_date
        original_finalization_date = new_batch.finalisation_date

        data = {
            "short_name": u"Новое наименование",
            "creation_date": datetime.utcnow(),
            "finalisation_date": datetime.utcnow(),
            "paid": True,
            "error_info": {},
            "deleted": True,
            "batch_type": "invalid"
        }

        result = self.test_client.post('/batch/update/', data={
            'batch_id': new_batch.id,
            'batch': json.dumps({
                "data": data
            })
        })
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(new_batch._documents), 1)
        doc = new_batch._documents[0]
        self.assertEqual(doc.data, {
            "short_name": u"Новое наименование"
        })
        self.assertEqual(doc.status, UserDocumentStatus.DS_NEW)

        new_batch = DocumentBatchDbObject.query.first()
        self.assertEqual(new_batch.creation_date, original_creation_date)
        self.assertEqual(new_batch.finalisation_date, original_finalization_date)
        self.assertEqual(new_batch.paid, False)
        self.assertEqual(new_batch.error_info, None)
        self.assertEqual(new_batch.deleted, False)
        self.assertEqual(new_batch.batch_type, DocumentBatchTypeEnum.DBT_TEST_TYPE)

    @authorized()
    def test_finalize_wrong_batch_status(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_FINALISED,
            paid=False
        )
        sqldb.session.add(new_batch)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertIn('result', data)
        self.assertTrue('result', data)
        self.assertNotIn('error', data)

        new_batch_finalising = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_BEING_FINALISED,
            paid=False
        )
        sqldb.session.add(new_batch_finalising)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch_finalising.id
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertNotIn('result', data)
        self.assertEqual(data['error'], {
            u'message': u'Пакет документов не может быть финализирован',
            u'code': 203
        })

        new_batch_defin = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_DEFINALIZING,
            paid=False
        )
        sqldb.session.add(new_batch_defin)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch_defin.id
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertNotIn('result', data)
        self.assertEqual(data['error'], {
            u'message': u'Пакет документов не может быть финализирован',
            u'code': 203
        })

    @authorized()
    def test_render_single_document(self):
        person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя",
            surname=u"СтараяФамилия",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='male',
            birthplace=u"Неизвестно где"
        )
        sqldb.session.add(person)

        company_person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя2",
            surname=u"СтараяФамилия2",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='female',
            birthplace=u"Неизвестно где2"
        )
        sqldb.session.add(company_person)

        company = CompanyDbObject(
            _owner=self.user,
            inn=u"6514008400",
            ogrn=u"1086507000029",
            kpp=u"651401001",
            full_name=u"Полное наименование",
            short_name=u"Краткое наименование",
            address={
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4"
            },
            general_manager= {
                '_id': company_person.id,
                'type': 'person'
            }
        )
        sqldb.session.add(company)
        sqldb.session.commit()

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование",
                "general_manager": {
                    "type": "person",
                    "_id": person.id
                },
                "some_db_object": {
                    "type": "company",
                    "_id": company.id
                }
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            data={
                "short_name": u"Старое наименование"
            },
            _owner = self.user
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertTrue(data['result'])

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': new_batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_3])
        })
        self.assertEqual(result.status_code, 200)

    @authorized()
    def test_render_single_document_fail_on_make_document(self):
        person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя",
            surname=u"СтараяФамилия",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='male',
            birthplace=u"Неизвестно где",
            living_country_code=0
        )
        sqldb.session.add(person)

        company_person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя2",
            surname=u"СтараяФамилия2",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='female',
            birthplace=u"Неизвестно где2"
        )
        sqldb.session.add(company_person)

        company = CompanyDbObject(
            _owner=self.user,
            inn=u"6514008400",
            ogrn=u"1086507000029",
            kpp=u"651401001",
            full_name=u"Полное наименование",
            short_name=u"Краткое наименование",
            address={
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4"
            },
            general_manager= {
                '_id': company_person.id,
                'type': 'person'
            }
        )
        sqldb.session.add(company)
        sqldb.session.commit()

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование",
                "general_manager": {
                    "type": "person",
                    "_id": person.id
                },
                "some_db_object": {
                    "type": "company",
                    "_id": company.id
                }
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            _owner=self.user,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertTrue(data['result'])

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': new_batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_3])
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        self.assertEqual(BatchDocumentDbObject.query.filter_by(batch=new_batch).count(), 2)
        new_doc = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.id != first_doc.id).one()
        self.assertEqual(new_doc.status, UserDocumentStatus.DS_RENDERING_FAILED)
        self.assertEqual(new_doc._celery_task_id, None)
        self.assertEqual(new_doc._celery_task_started, None)

    @authorized()
    def test_render_single_document_that_can_not_be_created(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование"
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            _owner=self.user,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertTrue(data['result'])

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': new_batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_3])
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        self.assertEqual(BatchDocumentDbObject.query.filter_by(batch=new_batch).count(), 2)
        new_doc = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.id != first_doc.id).one()
        self.assertEqual(new_doc.status, UserDocumentStatus.DS_RENDERING_FAILED)
        self.assertEqual(new_doc._celery_task_id, None)
        self.assertEqual(new_doc._celery_task_started, None)

    @authorized()
    def test_render_single_document_fail_on_validate(self):
        person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя",
            surname=u"СтараяФамилия",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='female',
            birthplace=u"Неизвестно где"
        )
        sqldb.session.add(person)
        sqldb.session.commit()

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование",
                "general_manager": {
                    "type": "person",
                    "_id": person.id
                }
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            _owner=self.user,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertTrue(data['result'])

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': new_batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_3])
        })
        self.assertEqual(result.status_code, 200)
        new_batch = DocumentBatchDbObject.query.filter_by(id=new_batch.id).one()
        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        self.assertEqual(BatchDocumentDbObject.query.filter_by(batch=new_batch).count(), 2)
        new_doc = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.id != first_doc.id).one()
        self.assertEqual(new_doc.status, UserDocumentStatus.DS_RENDERING_FAILED)
        self.assertEqual(new_doc._celery_task_id, None)
        self.assertEqual(new_doc._celery_task_started, None)
        self.assertEqual(new_batch.error_info, {
            u'error_ext': [{
                u'error_code': 5,
                u'field': u'test_doc_validation'
            }]
        })

    @authorized()
    def test_render_single_document_merge_error_info(self):
        person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя",
            surname=u"СтараяФамилия",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='female',
            birthplace=u"Неизвестно где"
        )
        sqldb.session.add(person)
        sqldb.session.commit()

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование",
                "general_manager": {
                    "type": "person",
                    "_id": person.id
                }
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            _owner=self.user,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id
        })

        new_batch.error_info = {
            'error_ext': [{
                'field': 'short_name',
                'error_code': 5
            }]
        }
        sqldb.session.commit()

        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertTrue(data['result'])

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': new_batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_3])
        })
        self.assertEqual(result.status_code, 200)
        new_batch = DocumentBatchDbObject.query.filter_by(id=new_batch.id).one()
        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        self.assertEqual(BatchDocumentDbObject.query.filter_by(batch=new_batch).count(), 2)
        new_doc = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.id != first_doc.id).one()
        self.assertEqual(new_batch.error_info, {
            u'error_ext': [{
                u'error_code': 5,
                u'field': u'short_name'
            }, {
                u'error_code': 5,
                u'field': u'test_doc_validation'
            }]
        })
        self.assertEqual(new_doc.status, UserDocumentStatus.DS_RENDERING_FAILED)
        self.assertEqual(new_doc._celery_task_id, None)
        self.assertEqual(new_doc._celery_task_started, None)

    @authorized()
    def test_get_document_being_rendered(self):
        person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя",
            surname=u"СтараяФамилия",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='male',
            birthplace=u"Неизвестно где"
        )
        sqldb.session.add(person)
        sqldb.session.commit()

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование",
                "general_manager": {
                    "type": "person",
                    "_id": person.id
                }
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            _owner=self.user,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertTrue(data['result'])

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': new_batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_3])
        })
        self.assertEqual(result.status_code, 200)

        result = self.test_client.get('/batch/render_document/state/?batch_id=%s&document_types=["%s"]' %
                                      (new_batch.id, DocumentTypeEnum.DT_TEST_DOC_3))
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        file_obj = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.id != first_doc.id).one().file
        self.assertIsNotNone(file_obj)
        self.assertEqual(data, [{
            u'document_type': u'test_doc_3',
            u'links': {
                u'jpeg': [],
                u'pdf': FileStorage.get_url(file_obj, self.config)
            },
            u'state': u'rendered'
        }])

    @authorized()
    def test_render_single_document_doc_builder_failure(self):
        pass        # todo:

    @authorized()
    def test_render_single_document_soft_time_limit_exceeded(self):
        pass        # todo:

    @authorized()
    def test_regenerate_document(self):
        person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя",
            surname=u"СтараяФамилия",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='male',
            birthplace=u"Неизвестно где"
        )
        sqldb.session.add(person)

        company_person = PrivatePersonDbObject(
            _owner=self.user,
            name=u"СтароеИмя2",
            surname=u"СтараяФамилия2",
            birthdate=datetime.now() - timedelta(days=365 * 30),
            sex='female',
            birthplace=u"Неизвестно где2"
        )
        sqldb.session.add(company_person)
        sqldb.session.commit()

        company = CompanyDbObject(
            _owner=self.user,
            inn=u"6514008400",
            ogrn=u"1086507000029",
            kpp=u"651401001",
            full_name=u"Полное наименование",
            short_name=u"Краткое наименование",
            address={
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4"
            },
            general_manager= {
                '_id': company_person.id,
                'type': 'person'
            }
        )
        sqldb.session.add(company)
        sqldb.session.commit()

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={
                "short_name": u"Старое наименование",
                "general_manager": {
                    "type": "person",
                    "_id": person.id
                },
                "some_db_object": {
                    "type": "company",
                    "_id": company.id
                }
            },
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)

        first_doc = BatchDocumentDbObject(
            batch=new_batch,
            document_type=DocumentTypeEnum.DT_TEST_DOC_1,
            _owner = self.user,
            data={
                "short_name": u"Старое наименование"
            }
        )
        sqldb.session.add(first_doc)
        sqldb.session.commit()

        result = self.test_client.post('/batch/finalise/', data={
            'batch_id': new_batch.id
        })
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertTrue(data['result'])

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': new_batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_3])
        })
        self.assertEqual(result.status_code, 200)

        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        self.assertEqual(BatchDocumentDbObject.query.filter_by(batch=new_batch).count(), 2)
        new_doc = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.id != first_doc.id).one()
        self.assertEqual(new_doc.status, UserDocumentStatus.DS_RENDERED)

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': new_batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_3])
        })
        self.assertEqual(result.status_code, 200)

        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        self.assertEqual(BatchDocumentDbObject.query.filter_by(batch=new_batch).count(), 2)
        new_doc = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.id != first_doc.id).one()
        self.assertEqual(new_doc.status, UserDocumentStatus.DS_RENDERED)

    @authorized()
    def test_render_doc_preview(self):
        pass

    @authorized()
    def test_finalize_not_my_batch(self):
        pass

    @authorized()
    def test_finalize_incomplete_batch(self):
        pass

    @authorized()
    def test_update_batch_in_status_render_failed_(self):
        pass

    @authorized()
    def test_cancel_finalization(self):
        pass

    @authorized()
    def test_generate_new_document_batch_finalised(self):
        pass

    @authorized()
    def test_generate_new_document_already_rendering(self):
        pass

    @authorized()
    def _test_async_render_separate_document(self):
        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "inn": "781108730780",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now(),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
            },
        })
        founder.insert(self.db)

        doc_data = {
            "full_name": u"образовательное учреждение дополнительного образования",
            "short_name": u"Бокс",
            "doc_date": datetime.now(),
            "selected_secretary": founder.id,
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 123131,
                "ifns": 1234
            },
            u"starter_capital": {
                u"capital_type": CompanyStarterCapitalTypeEnum.CSC_USTAVNOY_CAPITAL,
                u"value": {
                    "currency": "RUB",
                    "value": "12312.234234"
                }
            },
            "general_manager": founder.id,
            "general_manager_caption": u"разнорабочий",
            "selected_moderator": founder.id,
            "reg_responsible_person": founder.id,
            "founders": [{
                "founder_type": FounderTypeEnum.FT_PERSON,
                "person": founder.id,
                "share": {
                    "type": "percent",
                    "value": 100
                },
                "nominal_capital": 7466,
            }],
            "founder_applicant": {
                "founder_type": FounderTypeEnum.FT_PERSON,
                "person": founder.id,
                "share": {
                    "type": "percent",
                    "value": 100
                },
                "nominal_capital": 7466,
            }
        }

        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(document_type=DocumentTypeEnum.DT_PROTOCOL, data=doc_data), None, False)

        doc_list = [
            new_user_doc.db_value()
        ]
        new_batch_db_object = DocumentBatchDbObject(documents=doc_list, batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user)
        new_batch_db_object.insert(current_app.db)

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object.id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        del result_data['result']['document_id']
        self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []}}})

        result = self.test_client.post('/batch/document/render/', data={'batch_id': unicode(new_batch_db_object.id),
                                                                        'document_id': unicode(
                                                                            new_user_doc.id.db_value())})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {u'result': True})

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object.id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data['result']['state'], 'rendered')
        self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))

    @authorized()
    def test_fin_defin_cyclic_references(self):
        pass # todo:

    @authorized()
    def test_get_batches_with_prefetched_items(self):
        with self.app.app_context():
            batch = self.create_batch('_test', self.user)
            p1 = self.create_person(self.user, batch_id=batch.id)
            c1 = self.create_company(self.user, batch_id=batch.id)
            data = {
                'general_manager': {
                    '_id': p1.id,
                    'type': 'person'
                },
                'some_db_object': {
                    '_id': c1.id,
                    'type': 'company'
                }
            }
            p2 = self.create_person(self.user, batch_id=batch.id)
            c2 = self.create_company(self.user, batch_id=batch.id)
            data2 = {
                'general_manager': {
                    '_id': p1.id,
                    'type': 'person'
                },
                'some_db_object': {
                    '_id': c1.id,
                    'type': 'company'
                }
            }
            doc1 = self.create_document('test_doc_3', batch, data=data)
            doc2 = self.create_document('test_doc_3', batch, data=data2)

            result = self.test_client.get('/batch/')
            self.assertEqual(result.status_code, 200)


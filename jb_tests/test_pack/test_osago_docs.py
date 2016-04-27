# -*- coding: utf-8 -*-
from datetime import datetime

import json
from datetime import timedelta

from flask import current_app
from fw.async_tasks.models import CeleryScheduledTask

from fw.db.sql_base import db as sqldb
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import (BatchDocumentDbObject, DocumentBatchDbObject)
from fw.documents.enums import DocumentBatchTypeEnum, UserDocumentStatus
from fw.documents.enums import DocumentTypeEnum
from fw.documents.fields.doc_fields import DocumentBatch
from services.osago.documents.enums import OsagoDocTypeEnum
from test_api import authorized
from test_pack.base_batch_test import BaseBatchTestCase

from fw.async_tasks.core_tasks import check_scheduled_tasks

class OsagoDocsTestCase(BaseBatchTestCase):

    @authorized()
    def test_keep_document_instance_on_update(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'Тест нейм'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)
        self.assertEqual(BatchDocumentDbObject.query.count(), 1)
        doc = BatchDocumentDbObject.query.scalar()
        del result['result']['creation_date']
        self.assertEqual(result, {
            'result': {
                'status': u'new',
                'all_docs': [{u'caption': u'Тестовый документ 1', u'document_type': u'test_doc_1', u'file_link': None, u'document_id': doc.id}],
                'name': u'Тестовый батч',
                'paid': 'false',
                'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
                'result_fields': {u'name': u'Тест нейм'},
                'data': {
                    'short_name': u'Тест нейм'
                },
                'id': batch.id,
                'metadata': {},
                'status_data': {'finalisation_count': u'0'}
            }
        })

        new_data['short_name'] = u'создай второй документ'

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)
        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        doc = BatchDocumentDbObject.query.filter_by(id=doc.id).scalar()
        self.assertIsNotNone(doc)
        doc2 = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.id!=doc.id).scalar()
        self.assertIsNotNone(doc2)
        del result['result']['creation_date']
        all_docs = result['result']['all_docs']
        self.assertEqual(len(all_docs), 2)
        del result['result']['all_docs']

        test_docs = [
            {u'caption': u'Тестовый документ 2', u'document_type': u'test_doc_2', u'file_link': None, u'document_id': doc2.id},
            {u'caption': u'Тестовый документ 1', u'document_type': u'test_doc_1', u'file_link': None, u'document_id': doc.id},
        ]
        test_doc_id_set = set()
        for d in all_docs:
            for td in test_docs:
                if d and d == td:
                    test_doc_id_set.add(d['document_id'])

        self.assertEqual(len(test_doc_id_set), len(test_docs))

        self.assertEqual(result, {
            'result': {
                'status': u'new',
                'name': u'Тестовый батч',
                'paid': 'false',
                'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
                'result_fields': {u'name': u'создай второй документ'},
                'data': {
                    'short_name': u'создай второй документ'
                },
                'id': batch.id,
                'metadata': {},
                'status_data': {'finalisation_count': u'0'}
            }
        })

        new_data['short_name'] = u'не создавай второй документ'

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)
        self.assertEqual(BatchDocumentDbObject.query.count(), 1)
        doc = BatchDocumentDbObject.query.filter_by(id=doc.id).scalar()
        self.assertIsNotNone(doc)
        del result['result']['creation_date']
        all_docs = result['result']['all_docs']
        self.assertEqual(len(all_docs), 1)
        del result['result']['all_docs']

        test_docs = [
            {u'caption': u'Тестовый документ 1', u'document_type': u'test_doc_1', u'file_link': None, u'document_id': doc.id},
        ]
        test_doc_id_set = set()
        for d in all_docs:
            for td in test_docs:
                if d and d == td:
                    test_doc_id_set.add(d['document_id'])

        self.assertEqual(len(test_doc_id_set), len(test_docs))

        self.assertEqual(result, {
            'result': {
                'status': u'new',
                'name': u'Тестовый батч',
                'paid': 'false',
                'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
                'result_fields': {u'name': u'не создавай второй документ'},
                'data': {
                    'short_name': u'не создавай второй документ'
                },
                'id': batch.id,
                'metadata': {},
                'status_data': {'finalisation_count': u'0'}
            }
        })

    @authorized()
    def test_keep_document_instance_on_batch_render(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'Тест нейм'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)
        self.assertEqual(BatchDocumentDbObject.query.count(), 1)
        doc = BatchDocumentDbObject.query.scalar()
        del result['result']['creation_date']
        self.assertEqual(result, {
            'result': {
                'status': u'new',
                'all_docs': [{u'caption': u'Тестовый документ 1', u'document_type': u'test_doc_1', u'file_link': None, u'document_id': doc.id}],
                'name': u'Тестовый батч',
                'paid': 'false',
                'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
                'result_fields': {u'name': u'Тест нейм'},
                'data': {
                    'short_name': u'Тест нейм'
                },
                'id': batch.id,
                'metadata': {},
                'status_data': {'finalisation_count': u'0'}
            }
        })

        new_data['short_name'] = u'создай второй документ'

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)

        doc_ids = set()
        for d in BatchDocumentDbObject.query.filter_by():
            doc_ids.add(d.id)

        result = self.test_client.post('/batch/finalise/', data={'batch_id': batch.id})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {'result': True})

        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        new_doc_ids = set()
        for d in BatchDocumentDbObject.query.filter_by():
            new_doc_ids.add(d.id)

        self.assertEqual(doc_ids, new_doc_ids)

    @authorized()
    def test_keep_document_instance_on_document_render(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'Тест нейм',
            'text_field': u'Начальное значение'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)
        self.assertEqual(BatchDocumentDbObject.query.count(), 1)
        doc = BatchDocumentDbObject.query.scalar()
        del result['result']['creation_date']
        self.assertEqual(result, {
            'result': {
                'status': u'new',
                'all_docs': [{u'caption': u'Тестовый документ 1', u'document_type': u'test_doc_1', u'file_link': None, u'document_id': doc.id}],
                'name': u'Тестовый батч',
                'paid': 'false',
                'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
                'result_fields': {u'name': u'Тест нейм'},
                'data': {
                    'short_name': u'Тест нейм',
                    'text_field': u'Начальное значение'
                },
                'id': batch.id,
                'metadata': {},
                'status_data': {'finalisation_count': u'0'}
            }
        })

        new_data['short_name'] = u'создай второй документ'

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)

        doc_ids = set()
        for d in BatchDocumentDbObject.query.filter_by():
            doc_ids.add(d.id)

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_1])
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {'result': True})

        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        new_doc_ids = set()
        for d in BatchDocumentDbObject.query.filter_by():
            new_doc_ids.add(d.id)

        self.assertEqual(doc_ids, new_doc_ids)

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_2])
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {'result': True})

        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        new_doc_ids = set()
        for d in BatchDocumentDbObject.query.filter_by():
            new_doc_ids.add(d.id)

        self.assertEqual(doc_ids, new_doc_ids)

        self.assertEqual(BatchDocumentDbObject.query.filter_by(status=UserDocumentStatus.DS_RENDERED).count(), 2)

        new_data['text_field'] = u"Новое значение"

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)
        self.assertEqual(BatchDocumentDbObject.query.count(), 2)

        new_doc_ids = set()
        for d in BatchDocumentDbObject.query.filter_by():
            new_doc_ids.add(d.id)

        self.assertEqual(doc_ids, new_doc_ids)

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_2])
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {'result': True})

    @authorized()
    def test_filter_errors_in_document(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'Тест нейм' * 30
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)
        self.assertEqual(BatchDocumentDbObject.query.count(), 1)
        doc = BatchDocumentDbObject.query.scalar()
        del result['result']['creation_date']
        self.assertEqual(result, {
            'result': {
                'status': u'new',
                'all_docs': [{
                    u'caption': u'Тестовый документ 1',
                    u'document_type': u'test_doc_1',
                    u'file_link': None,
                    u'document_id': doc.id
                }],
                'name': u'Тестовый батч',
                'paid': 'false',
                'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
                'result_fields': {u'name': u'Тест нейм' * 30},
                'error_info': {'error_ext': [{'error_code': 5,
                                              'field': u'short_name'}]},
                'data': {
                    'short_name': u'Тест нейм' * 30
                },
                'id': batch.id,
                'metadata': {},
                'status_data': {'finalisation_count': u'0'}
            }
        })

        new_data['short_name'] = u'создай второй документ'
        new_data['text_field'] = u'err'

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)
        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        doc = BatchDocumentDbObject.query.filter_by(id=doc.id).scalar()
        self.assertIsNotNone(doc)
        doc2 = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.id!=doc.id).scalar()
        self.assertIsNotNone(doc2)
        del result['result']['creation_date']
        all_docs = result['result']['all_docs']
        self.assertEqual(len(all_docs), 2)
        del result['result']['all_docs']

        test_docs = [
            {u'caption': u'Тестовый документ 2', u'document_type': u'test_doc_2', u'file_link': None, u'document_id': doc2.id},
            {u'caption': u'Тестовый документ 1', u'document_type': u'test_doc_1', u'file_link': None, u'document_id': doc.id},
        ]
        test_doc_id_set = set()
        for d in all_docs:
            for td in test_docs:
                if d and d == td:
                    test_doc_id_set.add(d['document_id'])

        self.assertEqual(len(test_doc_id_set), len(test_docs))

        self.assertEqual(result, {
            'result': {
                'status': u'new',
                'name': u'Тестовый батч',
                'paid': 'false',
                'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
                'result_fields': {u'name': u'создай второй документ'},
                'data': {
                    'short_name': u'создай второй документ',
                    'text_field': 'err'
                },
                'id': batch.id,
                'metadata': {},
                'status_data': {'finalisation_count': u'0'}
            }
        })

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_2])
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(json.loads(result.data), {'result': True})

        doc2 = BatchDocumentDbObject.query.filter_by(document_type = DocumentTypeEnum.DT_TEST_DOC_2).scalar()
        self.assertIsNotNone(doc2)
        self.assertEqual(doc2.status, UserDocumentStatus.DS_RENDERING_FAILED)

        batch = doc2.batch
        self.assertEqual(batch.error_info, {u'error_ext': [{u'error_code': 5, u'field': u'text_field'}]})

        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)
        self.assertEqual(BatchDocumentDbObject.query.count(), 2)
        doc = BatchDocumentDbObject.query.filter_by(id=doc.id).scalar()
        self.assertIsNotNone(doc)
        doc2 = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.id!=doc.id).scalar()
        self.assertIsNotNone(doc2)
        del result['result']['creation_date']
        all_docs = result['result']['all_docs']
        self.assertEqual(len(all_docs), 2)
        del result['result']['all_docs']

        test_docs = [
            {u'caption': u'Тестовый документ 2', u'document_type': u'test_doc_2', u'file_link': None, u'document_id': doc2.id},
            {u'caption': u'Тестовый документ 1', u'document_type': u'test_doc_1', u'file_link': None, u'document_id': doc.id},
        ]
        test_doc_id_set = set()
        for d in all_docs:
            for td in test_docs:
                if d and d == td:
                    test_doc_id_set.add(d['document_id'])

        self.assertEqual(len(test_doc_id_set), len(test_docs))

        self.assertEqual(result, {
            'result': {
                'status': u'finalised2',
                'name': u'Тестовый батч',
                'paid': 'false',
                'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
                'result_fields': {u'name': u'создай второй документ'},
                'data': {
                    'short_name': u'создай второй документ',
                    'text_field': 'err'
                },
                'id': batch.id,
                'metadata': {},
                'error_info': {'error_ext': [{'error_code': 5,
                                              'field': u'text_field'}]},
                'status_data': {'finalisation_count': u'0'}
            }
        })

    @authorized()
    def test_transit_on_data(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'Тест нейм'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps(new_batch.get_api_structure())
        })
        self.assertEqual(result.status_code, 200)
        doc = BatchDocumentDbObject.query.scalar()
        d = json.loads(result.data)
        del d['result']['creation_date']
        self.assertEqual(d, {u'result': {
            u'all_docs': [{
                u'caption': u'Тестовый документ 1',
                u'document_id': doc.id,
                u'document_type': u'test_doc_1',
                u'file_link': None
            }],
            u'batch_type': u'_test',
            u'data': {u'short_name': u'Тест нейм'},
            u'id': batch.id,
            u'metadata': {},
            u'name': u'Тестовый батч',
            u'paid': u'false',
            u'result_fields': {u'name': u'Тест нейм'},
            u'status': u'new',
            u'status_data': {'finalisation_count': u'0'}
        }
        })

        new_data['short_name'] = u'едитыд'
        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps(new_batch.get_api_structure())
        })
        self.assertEqual(result.status_code, 200)
        doc = BatchDocumentDbObject.query.scalar()
        d = json.loads(result.data)
        del d['result']['creation_date']
        self.assertEqual(d, {u'result': {
            u'all_docs': [{
                u'caption': u'Тестовый документ 1',
                u'document_id': doc.id,
                u'document_type': u'test_doc_1',
                u'file_link': None
            }],
            u'batch_type': u'_test',
            u'data': {u'short_name': u'едитыд'},
            u'id': batch.id,
            u'metadata': {},
            u'name': u'Тестовый батч',
            u'paid': u'false',
            u'result_fields': {u'name': u'едитыд'},
            u'status': u'edited',
            u'status_data': {'finalisation_count': u'0'}
        }
        })

        DocumentBatchDbObject.query.filter_by(id=doc.batch_id).update({'status': 'finalised'})

        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps(new_batch.get_api_structure())
        })
        self.assertEqual(result.status_code, 200)
        doc = BatchDocumentDbObject.query.scalar()
        d = json.loads(result.data)
        del d['result']['creation_date']
        self.assertEqual(d, {u'result': {
            u'all_docs': [{
                u'caption': u'Тестовый документ 1',
                u'document_id': doc.id,
                u'document_type': u'test_doc_1',
                u'file_link': None
            }],
            u'batch_type': u'_test',
            u'data': {u'short_name': u'едитыд'},
            u'id': batch.id,
            u'metadata': {},
            u'name': u'Тестовый батч',
            u'paid': u'false',
            u'result_fields': {u'name': u'едитыд'},
            u'status': u'edited',
            u'status_data': {'finalisation_count': u'0'}
        }
        })

    @authorized()
    def test_transit_on_data_and_status(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'Тест нейм'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps(new_batch.get_api_structure())
        })
        self.assertEqual(result.status_code, 200)
        doc = BatchDocumentDbObject.query.scalar()
        d = json.loads(result.data)
        del d['result']['creation_date']
        self.assertEqual(d, {u'result': {
            u'all_docs': [{
                u'caption': u'Тестовый документ 1',
                u'document_id': doc.id,
                u'document_type': u'test_doc_1',
                u'file_link': None
            }],
            u'batch_type': u'_test',
            u'data': {u'short_name': u'Тест нейм'},
            u'id': batch.id,
            u'metadata': {},
            u'name': u'Тестовый батч',
            u'paid': u'false',
            u'result_fields': {u'name': u'Тест нейм'},
            u'status': u'new',
            u'status_data': {'finalisation_count': u'0'}
        }
        })

        new_data['short_name'] = u'финализируйся'
        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps(new_batch.get_api_structure())
        })
        self.assertEqual(result.status_code, 200)
        doc = BatchDocumentDbObject.query.scalar()
        d = json.loads(result.data)
        del d['result']['creation_date']
        self.assertEqual(d, {u'result': {
            u'all_docs': [{
                u'caption': u'Тестовый документ 1',
                u'document_id': doc.id,
                u'document_type': u'test_doc_1',
                u'file_link': None
            }],
            u'batch_type': u'_test',
            u'data': {u'short_name': u'финализируйся'},
            u'id': batch.id,
            u'metadata': {},
            u'name': u'Тестовый батч',
            u'paid': u'false',
            u'result_fields': {u'name': u'финализируйся'},
            u'status': u'finalised',
            u'status_data': {'finalisation_count': u'0'}
        }
        })

        DocumentBatchDbObject.query.filter_by(id=doc.batch_id).update({'status': 'edited'})

        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps(new_batch.get_api_structure())
        })
        self.assertEqual(result.status_code, 200)
        doc = BatchDocumentDbObject.query.scalar()
        d = json.loads(result.data)
        del d['result']['creation_date']
        self.assertEqual(d, {u'result': {
            u'all_docs': [{
                u'caption': u'Тестовый документ 1',
                u'document_id': doc.id,
                u'document_type': u'test_doc_1',
                u'file_link': None
            }],
            u'batch_type': u'_test',
            u'data': {u'short_name': u'финализируйся'},
            u'id': batch.id,
            u'metadata': {},
            u'name': u'Тестовый батч',
            u'paid': u'false',
            u'result_fields': {u'name': u'финализируйся'},
            u'status': u'edited',
            u'status_data': {'finalisation_count': u'0'}
        }
        })

    @authorized()
    def test_transit_on_event(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'Тест нейм'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps(new_batch.get_api_structure())
        })
        self.assertEqual(result.status_code, 200)
        doc = BatchDocumentDbObject.query.scalar()
        d = json.loads(result.data)
        del d['result']['creation_date']
        self.assertEqual(d, {u'result': {
            u'all_docs': [{
                u'caption': u'Тестовый документ 1',
                u'document_id': doc.id,
                u'document_type': u'test_doc_1',
                u'file_link': None
            }],
            u'batch_type': u'_test',
            u'data': {u'short_name': u'Тест нейм'},
            u'id': batch.id,
            u'metadata': {},
            u'name': u'Тестовый батч',
            u'paid': u'false',
            u'result_fields': {u'name': u'Тест нейм'},
            u'status': u'new',
            u'status_data': {'finalisation_count': u'0'}
        }
        })

        BatchManager.handle_event(batch.id, 'simple_event', {}, current_app.logger, config=self.config)

        doc = DocumentBatchDbObject.query.scalar()
        self.assertEqual(doc.status, 'after_simple_event')

    @authorized()
    def test_transit_on_data_and_event(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'Тест нейм'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps(new_batch.get_api_structure())
        })
        self.assertEqual(result.status_code, 200)
        doc = BatchDocumentDbObject.query.scalar()
        d = json.loads(result.data)
        del d['result']['creation_date']
        self.assertEqual(d, {u'result': {
            u'all_docs': [{
                u'caption': u'Тестовый документ 1',
                u'document_id': doc.id,
                u'document_type': u'test_doc_1',
                u'file_link': None
            }],
            u'batch_type': u'_test',
            u'data': {u'short_name': u'Тест нейм'},
            u'id': batch.id,
            u'metadata': {},
            u'name': u'Тестовый батч',
            u'paid': u'false',
            u'result_fields': {u'name': u'Тест нейм'},
            u'status': u'new',
            u'status_data': {'finalisation_count': u'0'}
        }
        })

        new_data['short_name'] = u'по событию'
        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps(new_batch.get_api_structure())
        })
        self.assertEqual(result.status_code, 200)
        doc = BatchDocumentDbObject.query.scalar()
        d = json.loads(result.data)
        del d['result']['creation_date']
        self.assertEqual(d, {u'result': {
            u'all_docs': [{
                u'caption': u'Тестовый документ 1',
                u'document_id': doc.id,
                u'document_type': u'test_doc_1',
                u'file_link': None
            }],
            u'batch_type': u'_test',
            u'data': {u'short_name': u'по событию'},
            u'id': batch.id,
            u'metadata': {},
            u'name': u'Тестовый батч',
            u'paid': u'false',
            u'result_fields': {u'name': u'по событию'},
            u'status': u'new',
            u'status_data': {'finalisation_count': u'0'}
        }
        })

        result = self.test_client.post('/batch/go_ahead/', data={'batch_id': batch.id})
        self.assertEqual(result.status_code, 200)
        doc = DocumentBatchDbObject.query.scalar()
        self.assertEqual(doc.status, 'after_event')

    @authorized()
    def test_send_email_on_transition(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'Тест нейм'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps(new_batch.get_api_structure())
        })
        self.assertEqual(result.status_code, 200)

        self.assertEqual(len(self.mailer.mails), 0)
        BatchManager.handle_event(batch.id, 'simple_event', None, logger=current_app.logger, config=self.config)

        self.assertEqual(len(self.mailer.mails), 1)

    @authorized()
    def test_fields_modification_restriction(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps({
                "data": {
                    "short_name": u"короткое",
                    "restricted_field": u"начальное значение"
                }
            })
        })
        self.assertEqual(result.status_code, 200)
        batch_db = DocumentBatchDbObject.query.filter_by(id=batch.id).scalar()
        self.assertEqual(batch_db.data, {
            "short_name": u"короткое",
            "restricted_field": u"начальное значение"
        })
        self.assertEqual(batch_db.status, "new")

        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps({
                "data": {
                    "short_name": u"едитыд",
                    "some_text_field": u"шо",
                    "restricted_field": u"значение 2"
                }
            })
        })
        self.assertEqual(result.status_code, 200)
        batch_db = DocumentBatchDbObject.query.filter_by(id=batch.id).scalar()
        self.assertEqual(batch_db.data, {
            "short_name": u"едитыд",
            "restricted_field": u"значение 2",
            "some_text_field": u"шо"
        })
        self.assertEqual(batch_db.error_info, {
            'error_ext': [{'field': "some_text_field", "error_code": 5}]
        })
        self.assertEqual(batch_db.status, "edited")

        result = self.test_client.post('/batch/update/', data={
            'batch_id': batch.id,
            'batch': json.dumps({
                "data": {
                    "short_name": u"едитыд",
                    "restricted_field": u"значение 3",
                    "some_text_field": u"шо11111111111",
                }
            })
        })
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)['result']
        self.assertIn('error_info', result_data)
        batch_db = DocumentBatchDbObject.query.filter_by(id=batch.id).scalar()
        self.assertEqual(batch_db.error_info, {
            'error_ext': [
                {'field': "some_text_field", "error_code": 5},
                {'field': 'restricted_field', 'error_code': 1000}
            ]
        })
        self.assertEqual(batch_db.data, {
            "short_name": u"едитыд",
            "restricted_field": u"значение 2",
            "some_text_field": u"шо",
        })
        self.assertEqual(batch_db.status, "edited")

    @authorized()
    def test_transit_on_docs_group_generated(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'создай второй документ',
            'text_field': u'текстфилд'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_1, DocumentTypeEnum.DT_TEST_DOC_2])
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(self.events), 6)
        sqldb.session.commit()
        batch_db = DocumentBatchDbObject.query.filter_by(id=batch.id).scalar()
        doc1 = BatchDocumentDbObject.query.filter_by(batch_id=batch.id).order_by(BatchDocumentDbObject.creation_date.asc()).first()
        doc2 = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.batch_id==batch.id, BatchDocumentDbObject.id != doc1.id).first()
        self.assertEqual(batch_db.status, 'finalised')
        self.assertEqual(self.events[0]['batch'].id, batch_db.id)
        self.assertEqual(self.events[1]['batch'].id, batch_db.id)
        self.assertEqual(self.events[2]['batch'].id, batch_db.id)
        del self.events[0]['batch']
        del self.events[1]['batch']
        del self.events[2]['batch']
        del self.events[3]['batch']
        del self.events[4]['batch']
        del self.events[5]['batch']
        self.assertEqual(self.events[0], {'event': 'batch_manager.on_field_changed',
                                          'event_data': {'field_name': 'short_name',
                                          'new_value': u'создай второй документ',
                                          'old_value': None}})
        self.assertEqual(self.events[1], {'event': 'batch_manager.on_field_changed',
                                          'event_data': {'field_name': 'text_field',
                                          'new_value': u'текстфилд',
                                          'old_value': None}})
        self.assertEqual(self.events[2], {'event': 'batch_manager.on_fieldset_changed',
                                          'event_data': {'fields': [{'field_name': 'short_name',
                                          'new_value': u'создай второй документ',
                                          'old_value': None}, {'field_name': 'text_field',
                                          'new_value': u'текстфилд',
                                          'old_value': None}]}})
        self.assertEqual(self.events[3], {'event': 'doc_render_success', 'event_data': {'doc_id': doc1.id}})
        self.assertEqual(self.events[4], {'event': 'doc_render_success', 'event_data': {'doc_id': doc2.id}})
        self.assertEqual(self.events[5], {'event': 'doc_group_render_success',
                                          'event_data': {'batch_id': batch_db.id,
                                                         'doc_types': ['test_doc_1', 'test_doc_2']}})

    @authorized()
    def test_transit_on_docs_group_generation_fail(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'создай второй документ',
            'text_field': u'текстфилд'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)

        DocumentBatchDbObject.query.filter_by(id=batch.id).update({
            'data': {
                'short_name': u'создай второй документ',
                'text_field': u'1'
            }
        })

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_1, DocumentTypeEnum.DT_TEST_DOC_2])
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(self.events), 6)
        sqldb.session.commit()
        batch_db = DocumentBatchDbObject.query.filter_by(id=batch.id).scalar()
        doc1 = BatchDocumentDbObject.query.filter_by(batch_id=batch.id).order_by(BatchDocumentDbObject.creation_date.asc()).first()
        doc2 = BatchDocumentDbObject.query.filter(BatchDocumentDbObject.batch_id==batch.id, BatchDocumentDbObject.id != doc1.id).first()
        self.assertEqual(batch_db.status, 'finalised1')
        self.assertEqual(self.events[0]['batch'].id, batch_db.id)
        self.assertEqual(self.events[1]['batch'].id, batch_db.id)
        self.assertEqual(self.events[2]['batch'].id, batch_db.id)
        del self.events[0]['batch']
        del self.events[1]['batch']
        del self.events[2]['batch']
        del self.events[3]['batch']
        del self.events[4]['batch']
        del self.events[5]['batch']
        self.assertEqual(self.events[0], {'event': 'batch_manager.on_field_changed',
                                          'event_data': {'field_name': 'short_name',
                                          'new_value': u'создай второй документ',
                                          'old_value': None}})
        self.assertEqual(self.events[1], {'event': 'batch_manager.on_field_changed',
                                          'event_data': {'field_name': 'text_field',
                                          'new_value': u'текстфилд',
                                          'old_value': None}})
        self.assertEqual(self.events[2], {'event': 'batch_manager.on_fieldset_changed',
                                          'event_data': {'fields': [{'field_name': 'short_name',
                                          'new_value': u'создай второй документ',
                                          'old_value': None}, {'field_name': 'text_field',
                                          'new_value': u'текстфилд',
                                          'old_value': None}]}})
        self.assertEqual(self.events[3], {'event': 'doc_render_success', 'event_data': {'doc_id': doc1.id}})
        self.assertEqual(self.events[4], {'event': 'doc_render_fail', 'event_data': {'doc_id': doc2.id}})
        self.assertEqual(self.events[5], {'event': 'doc_group_render_fail',
                                          'event_data': {'batch_id': batch_db.id,
                                                         'doc_types': ['test_doc_1', 'test_doc_2']}})

    @authorized()
    def test_transit_on_doc_generated(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'создай второй документ',
            'text_field': u'текстфилд'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_1])
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(self.events), 4)
        batch_db = DocumentBatchDbObject.query.filter_by(id=batch.id).scalar()
        doc1 = BatchDocumentDbObject.query.filter_by(batch_id=batch.id).order_by(BatchDocumentDbObject.creation_date.asc()).first()
        self.assertEqual(batch_db.status, 'finalised1')
        self.assertEqual(self.events[0]['batch'].id, batch_db.id)
        del self.events[0]['batch']
        del self.events[1]['batch']
        del self.events[2]['batch']
        del self.events[3]['batch']
        self.assertEqual(self.events[0], {'event': 'batch_manager.on_field_changed',
                                          'event_data': {'field_name': 'short_name',
                                          'new_value': u'создай второй документ',
                                          'old_value': None}})
        self.assertEqual(self.events[1], {'event': 'batch_manager.on_field_changed',
                                          'event_data': {'field_name': 'text_field',
                                          'new_value': u'текстфилд',
                                          'old_value': None}})
        self.assertEqual(self.events[2], {'event': 'batch_manager.on_fieldset_changed',
                                          'event_data': {'fields': [{'field_name': 'short_name',
                                          'new_value': u'создай второй документ',
                                          'old_value': None}, {'field_name': 'text_field',
                                          'new_value': u'текстфилд',
                                          'old_value': None}]}})
        self.assertEqual(self.events[3], {'event': 'doc_render_success', 'event_data': {'doc_id': doc1.id}})

    @authorized()
    def test_transit_on_doc_generation_fail(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_TEST_TYPE, self.user)
        new_data = {
            'short_name': u'создай второй документ',
            'text_field': u'текстфилд'
        }
        new_batch_data = {
            'data': new_data,
            'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            'metadata': {}
        }

        new_batch = DocumentBatch.parse_raw_value(new_batch_data, api_data=False)
        manager = BatchManager.init(batch)
        result = manager.update_batch(batch.id, new_batch, self.user.id, None, self.config, current_app.logger)

        DocumentBatchDbObject.query.filter_by(id=batch.id).update({
            'data': {
                'short_name': u'создай второй документ',
                'text_field': u'1'
            }
        })

        result = self.test_client.post('/batch/render_document/', data={
            'batch_id': batch.id,
            'document_type': json.dumps([DocumentTypeEnum.DT_TEST_DOC_2])
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(self.events), 4)
        batch_db = DocumentBatchDbObject.query.filter_by(id=batch.id).scalar()
        doc1 = BatchDocumentDbObject.query.filter_by(batch_id=batch.id).order_by(BatchDocumentDbObject.creation_date.desc()).first()
        self.assertEqual(batch_db.status, 'finalised2')
        self.assertEqual(self.events[0]['batch'].id, batch_db.id)
        del self.events[0]['batch']
        del self.events[1]['batch']
        del self.events[2]['batch']
        del self.events[3]['batch']
        self.assertEqual(self.events[0], {'event': 'batch_manager.on_field_changed',
                                          'event_data': {'field_name': 'short_name',
                                          'new_value': u'создай второй документ',
                                          'old_value': None}})
        self.assertEqual(self.events[1], {'event': 'batch_manager.on_field_changed',
                                          'event_data': {'field_name': 'text_field',
                                          'new_value': u'текстфилд',
                                          'old_value': None}})
        self.assertEqual(self.events[2], {'event': 'batch_manager.on_fieldset_changed',
                                          'event_data': {'fields': [{'field_name': 'short_name',
                                          'new_value': u'создай второй документ',
                                          'old_value': None}, {'field_name': 'text_field',
                                          'new_value': u'текстфилд',
                                          'old_value': None}]}})
        self.assertEqual(self.events[3], {'event': 'doc_render_fail', 'event_data': {'doc_id': doc1.id}})

    @authorized()
    def test_send_email_on_docs_ready(self):
        with self.app.app_context():
            self.app.db['bik_catalog'].insert({
                'bik': '040173745',
                'address': u'Адрес',
                'name': u'Просто Банк'
            })

            batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user, status="pretension")
            victim_car_owner = self.create_person(self.user, batch.id, name=u"ЖЖ", surname=u"ЖЖ", patronymic=u"ЖЖ")
            guilty_car_owner = self.create_person(self.user, batch.id)
            responsible_person = self.create_person(self.user, batch.id, name=u"Арина",
                                                    surname=u"Поганкина", patronymic=u"Мстиславовна", age=22)

            ddd = {
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
                    'bik_account': '040173745',
                    'account_number': '01234567890123456789',
                    'police_case': True
                }
            }
            batch_json = json.dumps(ddd)
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch.id,
                'batch': batch_json
            })
            # CeleryScheduledTask.query.update({'eta': datetime.utcnow()})
            # sqldb.session.commit()
            # check_scheduled_tasks.delay()

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

            self.assertEqual(len(self.mailer.mails), 1)
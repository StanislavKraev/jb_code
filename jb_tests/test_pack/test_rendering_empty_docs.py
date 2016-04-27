# -*- coding: utf-8 -*-
from datetime import timedelta, datetime

from base_test_case import BaseTestCase
from flask import json
from fw.documents.address_enums import RFRegionsEnum, DistrictTypeEnum, CityTypeEnum, VillageTypeEnum, StreetTypeEnum, \
    HouseTypeEnum, BuildingTypeEnum, FlatTypeEnum
from fw.documents.db_fields import DocumentBatchDbObject, PrivatePersonDbObject, CompanyDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentBatchTypeEnum, BatchStatusEnum, PersonDocumentTypeEnum, DocumentTypeEnum
from fw.documents.fields.doc_fields import DocumentBatch
from fw.documents.fields.general_doc_fields import UserDocument
from test_api import authorized


class RenderingEmptyDocsTestCase(BaseTestCase):
    @authorized()
    def test_async_render_empty_protocol(self):
        DocRequisitiesStorage.get_batch_descriptor(DocumentBatchTypeEnum.DBT_NEW_LLC)['doc_types'] = [DocumentTypeEnum.DT_PROTOCOL]

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user._id
            )
            batch_id = batch.insert(self.db)

            founder_otvetstvennyi = PrivatePersonDbObject(**{
                "_owner": self.user._id,
                "name": u"",
                "surname": u"",
                "patronymic": u"",
                "inn": "781108730780",
                "sex": "male",
                "birthdate": datetime.now() - timedelta(days=365 * 30),
                "birthplace": u"Россия, деревня Гадюкино",
                "passport": {
                    "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                    "series": u"1123",
                    "number": u"192837",
                    "issue_date": datetime.now() - timedelta(days=365 * 14),
                    "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                    "depart_code": u"111987"
                },
                "ogrnip": "123456789012345",
                "address": {
                    "region": RFRegionsEnum.RFR_SPB,
                    "index": 198209,
                    "district_type": DistrictTypeEnum.DIT_DISTRICT,
                    "district": u"Пушкинский",
                    "city_type": CityTypeEnum.CIT_CITY,
                    "city": u"Гадюкино",
                    "village_type": VillageTypeEnum.VIT_HUTOR,
                    "village": u"близ Диканьки",
                    "street_type": StreetTypeEnum.STT_BOULEVARD,
                    "street": u"Мотоциклистов",
                    "house_type": HouseTypeEnum.HOT_HOUSE,
                    "house": "4",
                    "building_type": BuildingTypeEnum.BIT_HOUSING,
                    "building": "2",
                    "flat_type": FlatTypeEnum.FLT_OFFICE,
                    "flat": "705",
                },
                "caption": u"Сантехник",
                "phone": "+79210001122",
                "email": "somebody@domain.zz",
                "living_country_code": 3,
                "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
            })
            founder_otvetstvennyi.insert(self.db)

            company_founder = CompanyDbObject(**{
                "_owner": self.user._id,
                "ogrn": "1234567890123",
                "inn": "781108730780",
                "kpp": "999999999",
                "general_manager_caption": u"генеральный директор",
                "full_name": u"Том и Джери",
                "short_name": u"ТиД",
                "general_manager": {
                },
                "address": {
                    "region": RFRegionsEnum.RFR_SPB,
                    "index": 123131,
                    "street_type": StreetTypeEnum.STT_STREET,
                    "street": u"Седова",
                    "house_type": HouseTypeEnum.HOT_HOUSE,
                    "house": "2",
                    "flat_type": FlatTypeEnum.FLT_OFFICE,
                    "flat": "2",
                },
                "phone": "+7(812)1234567"
            })
            company_founder.insert(self.app.db)

            new_batch_db_object = DocumentBatchDbObject(
                data={
                    u"address_type": u"office_address",
                    u"founders": [
                        {
                            u"founder": {
                                u"_id": company_founder.id,
                                u"type": u"company"
                            },
                            u"nominal_capital": 12312.22,
                            u"share": 85
                        }, {
                            u"founder": {
                                u"_id": founder_otvetstvennyi.id,
                                u"type": u"person"
                            },
                            u"nominal_capital": 1500.5,
                            u"share": 15
                        }
                    ],
                },
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            structure = batch.get_api_structure()
            del structure['batch_type']
            batch_json = json.dumps(structure)
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(batch_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            new_user_doc_id = db_batch._documents[0].id

            result = self.test_client.get(
                '/batch/document/state/?batch_id=%s&document_id=%s' % (batch_id, new_user_doc_id))
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            del result_data['result']['document_id']
            self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []}}})

            result = self.test_client.post('/batch/document/render/',
                                           data={'batch_id': unicode(batch_id), 'document_id': unicode(new_user_doc_id)})
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertEqual(result_data, {u'result': True})

            result = self.test_client.get(
                '/batch/document_preview/state/?batch_id=%s&document_id=%s' % (unicode(batch_id), unicode(new_user_doc_id)))
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertEqual(result_data['result']['state'], 'rendered')
            self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))


    @authorized()
    def test_async_render_empty_articles(self):
        doc_data = {
        }
        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(document_type=DocumentTypeEnum.DT_ARTICLES, data=doc_data), None, False)

        doc_list = [
            new_user_doc.db_value()
        ]
        new_batch_db_object = DocumentBatchDbObject(documents=doc_list, batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user._id)
        new_batch_db_object.insert(self.db)

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        del result_data['result']['document_id']
        self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []}}})

        result = self.test_client.post('/batch/document/render/', data={'batch_id': unicode(new_batch_db_object._id),
                                                                        'document_id': unicode(
                                                                            new_user_doc.id.db_value())})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {u'result': True})

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data['result']['state'], 'rendered')
        self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))

    @authorized()
    def test_async_render_empty_act(self):
        doc_data = {
        }
        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(document_type=DocumentTypeEnum.DT_ACT, data=doc_data), None, False)

        doc_list = [
            new_user_doc.db_value()
        ]
        new_batch_db_object = DocumentBatchDbObject(documents=doc_list, batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user._id)
        new_batch_db_object.insert(self.db)

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []},
                                                   u'document_id': unicode(result_data['result']['document_id'])}})

        result = self.test_client.post('/batch/document/render/', data={'batch_id': unicode(new_batch_db_object._id),
                                                                        'document_id': unicode(
                                                                            new_user_doc.id.db_value())})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {u'result': True})

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data['result']['state'], 'rendered')
        self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))

    @authorized()
    def test_async_render_empty_contract(self):
        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(document_type=DocumentTypeEnum.DT_CONTRACT, data={}), None, False)

        doc_list = [
            new_user_doc.db_value()
        ]
        new_batch_db_object = DocumentBatchDbObject(documents=doc_list, batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user._id)
        new_batch_db_object.insert(self.db)

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        del result_data['result']['document_id']
        self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []}}})

        result = self.test_client.post('/batch/document/render/', data={'batch_id': unicode(new_batch_db_object._id),
                                                                        'document_id': unicode(
                                                                            new_user_doc.id.db_value())})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {u'result': True})

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data['result']['state'], 'rendered')
        self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))

    @authorized()
    def test_async_render_empty_doverennost(self):

        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(document_type=DocumentTypeEnum.DT_DOVERENNOST, data={}), None, False)

        doc_list = [
            new_user_doc.db_value()
        ]
        new_batch_db_object = DocumentBatchDbObject(documents=doc_list, batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user._id)
        new_batch_db_object.insert(self.db)

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        del result_data['result']['document_id']
        self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []}}})

        result = self.test_client.post('/batch/document/render/', data={'batch_id': unicode(new_batch_db_object._id),
                                                                        'document_id': unicode(
                                                                            new_user_doc.id.db_value())})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {u'result': True})

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data['result']['state'], 'rendered')
        self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))

    @authorized()
    def test_async_render_empty_reshenie(self):

        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(document_type=DocumentTypeEnum.DT_DECISION, data={}), None, False)

        doc_list = [
            new_user_doc.db_value()
        ]
        new_batch_db_object = DocumentBatchDbObject(documents=doc_list, batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user._id)
        new_batch_db_object.insert(self.db)

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        del result_data['result']['document_id']
        self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []}}})

        result = self.test_client.post('/batch/document/render/', data={'batch_id': unicode(new_batch_db_object._id),
                                                                        'document_id': unicode(
                                                                            new_user_doc.id.db_value())})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {u'result': True})

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data['result']['state'], 'rendered')
        self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))

    @authorized()
    def test_async_render_empty_r11001(self):
        DocRequisitiesStorage.get_batch_descriptor(DocumentBatchTypeEnum.DBT_NEW_LLC)['doc_types'] = [DocumentTypeEnum.DT_P11001]

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user._id
            )
            batch_id = batch.insert(self.db)

            new_batch_db_object = DocumentBatchDbObject(
                data={},
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            structure = batch.get_api_structure()
            del structure['batch_type']
            batch_json = json.dumps(structure)
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(batch_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            new_user_doc_id = db_batch._documents[0].id
            result = self.test_client.get(
                '/batch/document/state/?batch_id=%s&document_id=%s' % (batch_id, new_user_doc_id))
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            del result_data['result']['document_id']
            self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []}}})

            result = self.test_client.post('/batch/document/render/',
                                           data={'batch_id': unicode(batch_id), 'document_id': new_user_doc_id})
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertEqual(result_data, {u'result': True})

            result = self.test_client.get(
                '/batch/document/state/?batch_id=%s&document_id=%s' % (batch_id, new_user_doc_id))
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertEqual(result_data['result']['state'], 'rendered')
            self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))

    @authorized()
    def test_async_render_empty_usn(self):

        data = {
        }

        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(document_type=DocumentTypeEnum.DT_USN, data=data), None, False)

        doc_list = [
            new_user_doc.db_value()
        ]
        new_batch_db_object = DocumentBatchDbObject(documents=doc_list, batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user._id)
        new_batch_db_object.insert(self.db)

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        del result_data['result']['document_id']
        self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []}}})

        result = self.test_client.post('/batch/document/render/', data={'batch_id': unicode(new_batch_db_object._id),
                                                                        'document_id': unicode(
                                                                            new_user_doc.id.db_value())})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {u'result': True})

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data['result']['state'], 'rendered')
        self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))

    @authorized()
    def test_async_render_empty_soglasie_sobstvennikov(self):

        data = {
        }

        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(document_type=DocumentTypeEnum.DT_SOGLASIE_SOBSTVENNIKOV, data=data), None,
                                     False)

        doc_list = [
            new_user_doc.db_value()
        ]
        new_batch_db_object = DocumentBatchDbObject(documents=doc_list, batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user._id)
        new_batch_db_object.insert(self.db)

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        del result_data['result']['document_id']
        self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []}}})

        result = self.test_client.post('/batch/document/render/', data={'batch_id': unicode(new_batch_db_object._id),
                                                                        'document_id': unicode(
                                                                            new_user_doc.id.db_value())})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {u'result': True})

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data['result']['state'], 'rendered')
        self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))

    @authorized()
    def test_async_render_empty_garant_letter_arenda(self):
        data = {
        }

        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(document_type=DocumentTypeEnum.DT_GARANT_LETTER_ARENDA, data=data), None,
                                     False)

        doc_list = [
            new_user_doc.db_value()
        ]
        new_batch_db_object = DocumentBatchDbObject(documents=doc_list, batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user._id)
        new_batch_db_object.insert(self.db)

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        del result_data['result']['document_id']
        self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []}}})

        result = self.test_client.post('/batch/document/render/', data={'batch_id': unicode(new_batch_db_object._id),
                                                                        'document_id': unicode(
                                                                            new_user_doc.id.db_value())})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {u'result': True})

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data['result']['state'], 'rendered')
        self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))

    @authorized()
    def test_async_render_empty_garant_letter_subarenda(self):
        data = {
        }

        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(document_type=DocumentTypeEnum.DT_GARANT_LETTER_SUBARENDA, data=data), None,
                                     False)

        doc_list = [
            new_user_doc.db_value()
        ]
        new_batch_db_object = DocumentBatchDbObject(documents=doc_list, batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user._id)
        new_batch_db_object.insert(self.db)

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        del result_data['result']['document_id']
        self.assertEqual(result_data, {u'result': {u'state': u'new', u'links': {u'pdf': None, u'jpeg': []}}})

        result = self.test_client.post('/batch/document/render/', data={'batch_id': unicode(new_batch_db_object._id),
                                                                        'document_id': unicode(
                                                                            new_user_doc.id.db_value())})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {u'result': True})

        result = self.test_client.get('/batch/document/state/?batch_id=%s&document_id=%s' % (
            unicode(new_batch_db_object._id), unicode(new_user_doc.id.db_value())))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data['result']['state'], 'rendered')
        self.assertTrue(result_data['result']['links']['pdf'].startswith(u'http://service.zz/storage/'))

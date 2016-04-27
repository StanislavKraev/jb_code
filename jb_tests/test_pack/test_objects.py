# -*- coding: utf-8 -*-
import StringIO
import os

# noinspection PyProtectedMember
from flask import json
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from sqlalchemy.orm import make_transient
from base_test_case import BaseTestCase, authorized
from fw.auth.models import AuthUser
from fw.catalogs.models import OkvedCatalogObject
from fw.documents.address_enums import RFRegionsEnum, HouseTypeEnum, FlatTypeEnum
from fw.documents.address_enums import StreetTypeEnum
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import PrivatePersonDbObject, CompanyDbObject, DocumentBatchDbObject, BatchDocumentDbObject
from fw.documents.enums import CompanyTypeEnum, DocumentTypeEnum, BatchStatusEnum, DocumentBatchTypeEnum, \
    IncorporationFormEnum, PersonDocumentTypeEnum, UserDocumentStatus
from fw.documents.fields.doc_fields import PrivatePerson, CompanyObject, UserDocument
from fw.db.sql_base import db as sqldb
from fw.storage.file_storage import FileStorage
from fw.storage.models import FileObject
from services.ifns.utils.process_okvad import process_okvad


class ObjectsTestCase(BaseTestCase):
    def import_okvad_catalog(self):
        okved_item = OkvedCatalogObject(
            id=str(ObjectId()),
            name="foo",
            departments=[{
                'id': str(ObjectId()),
                'okvads': ['1', '2', '3'],
                'name': 'bar',
                'main_okvad': '1'
            }, {
                'id': str(ObjectId()),
                'okvads': ['1', '3', '5'],
                'name': 'baz',
                'main_okvad': '5'
            }]
        )
        sqldb.session.add(okved_item)
        sqldb.session.commit()

        okved_item = OkvedCatalogObject(
            id=str(ObjectId()),
            name="foo2",
            departments=[{
                'id': str(ObjectId()),
                'okvads': ['11', '12', '13'],
                'name': 'bar2',
                'main_okvad': '11'
            }, {
                'id': str(ObjectId()),
                'okvads': ['11', '13', '15'],
                'name': 'baz2',
                'main_okvad': '15'
            }]
        )
        sqldb.session.add(okved_item)
        sqldb.session.commit()

    @authorized()
    def test_create_person_by_name_then_add_part_of_passport(self):
        with self.app.app_context():
            data = {
                "person": json.dumps({
                    'name': u"Поликарп",
                })
            }
            result = self.test_client.post('/entity/person/create/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            person = result_data['result']
            self.assertIn('id', person)
            person_id, _type = person['id'].split("_")
            real_person = PrivatePersonDbObject.query.filter_by(id=person_id).first()
            self.assertIsNotNone(real_person)
            self.assertEqual(person, PrivatePerson.db_obj_to_field(real_person).get_api_structure())
            self.assertIsInstance(person['name'], basestring)
            self.assertEqual(real_person.name, u"Поликарп")

            data = {
                'person_id': unicode(real_person.id) + "_person",
                'person': json.dumps({
                    'passport': {'document_type': 'internal', 'series': '4111'},
                    'address': {
                        "city_type": "",
                        "city": ""
                    }
                })
            }
            result = self.test_client.post('/entity/person/update/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            person = result_data['result']
            self.assertEqual(person['passport'], {'document_type': 'internal', 'series': '4111'})

    @authorized()
    def test_try_set_empty_fields(self):
        with self.app.app_context():
            data = {
                "person": json.dumps({
                    'name': u"Поликарп"
                })
            }
            result = self.test_client.post('/entity/person/create/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            person = result_data['result']
            self.assertIn('id', person)
            person_id, _type = person['id'].split("_")
            real_person = PrivatePersonDbObject.query.filter_by(id=person_id).first()
            self.assertIsNotNone(real_person)
            self.assertEqual(person, PrivatePerson.db_obj_to_field(real_person).get_api_structure())
            self.assertIsInstance(person['name'], basestring)
            self.assertEqual(real_person.name, u"Поликарп")

            data = {
                'person_id': unicode(real_person.id) + "_person",
                'person': json.dumps({
                    'passport': {'document_type': 'internal', 'series': '4111'},
                    'address': {
                        "city_type": "",
                        "city": ""
                    }
                })
            }
            result = self.test_client.post('/entity/person/update/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            person = result_data['result']
            self.assertEqual(person['passport'], {'document_type': 'internal', 'series': '4111'})
            self.assertEqual(person['address'], {})

    @authorized()
    def test_create_person_null_fields(self):
        with self.app.app_context():
            data = {
                "person": json.dumps({
                    'name': u"Поликарп",
                    'surname': u"Шариков",
                    'patronymic': u"Поликарпович",
                    'passport': {'document_type': None, 'series': None, 'number': None, 'issue_date': None,
                                 'issue_depart': None, 'depart_code': None, 'citizenship': None},
                })
            }
            result = self.test_client.post('/entity/person/create/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            person = result_data['result']
            self.assertIn('id', person)
            person_id, _type = person['id'].split("_")
            real_person = PrivatePersonDbObject.query.filter_by(id=person_id).first()
            self.assertIsNotNone(real_person)
            real_person = PrivatePerson.db_obj_to_field(real_person).get_api_structure()
            self.assertEqual(person, real_person)

    @authorized()
    def test_update_person_name_declension(self):
        with self.app.app_context():
            data = {
                'name': None,
                'surname': None,
                'patronymic': None,
                'caption': None,
                'birthdate': None,
                'sex': None,
                'birthplace': None,
                'inn': None,
                'phone': None,
                'passport': {'document_type': 'internal', 'series': None, 'number': None, 'issue_date': None,
                             'issue_depart': None, 'depart_code': None, 'citizenship': None},
                'address': {"index": None, "region": None, "city": None, "village": None, "street_type": None,
                            "street": None, "house_type": None, "house": None, "building_type": None, "building": None,
                            "flat_type": None, "flat": None},
                'living_address': None,
                'living_country_code': None,
                'ogrnip': None,
                'email': None,
                'spouse': None,
                '_owner_id': self.user.id
            }
            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            data = {
                'person_id': unicode(person.id) + "_person",
                'person': json.dumps({
                    'caption': u"Труляля",
                    "id": u"53b53446a726161b1ab019c0",
                    'name': None,
                    'surname': None,
                    'patronymic': None,
                    'birthdate': u"2010-06-03",
                    'sex': None,
                    'birthplace': None,
                    'inn': None,
                    'phone': None,
                    'passport': {'document_type': 'internal', 'series': None, 'number': None, 'issue_date': None,
                                 'issue_depart': None, 'depart_code': None, 'citizenship': None},
                    'address': {"index": None, "region": None, "city": None, "village": None, "street_type": None,
                                "street": None, "house_type": None, "house": None, "building_type": None,
                                "building": None, "flat_type": None, "flat": None},
                    'living_address': None,
                    'living_country_code': None,
                    'ogrnip': None,
                    'email': None,
                    'spouse': None,
                })
            }
            result = self.test_client.post('/entity/person/update/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            person = result_data['result']
            self.assertEqual(person['caption'], u"Труляля")

    @authorized()
    def test_update_person_name(self):
        with self.app.app_context():
            data = {
                '_owner_id': self.user.id
            }
            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            simple_object = PrivatePersonDbObject.query.filter_by(id=person.id).first()

            # noinspection PyUnresolvedReferences
            real_person = PrivatePerson.db_obj_to_field(
                PrivatePersonDbObject.query.filter_by(id=person.id).first())
            self.assertIsNotNone(real_person)

            data = {
                'person_id': unicode(person.id) + "_person",
                'person': json.dumps({
                    'name': u"Поликарпа"
                })
            }
            result = self.test_client.post('/entity/person/update/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            person = result_data['result']

    @authorized()
    def test_get_person_by_id(self):
        with self.app.app_context():
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                '_owner_id': self.user.id,
                'birthdate': datetime.now()
            }
            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            result = self.test_client.get('/entity/person/?person_id=%s_person' % unicode(person.id))
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            self.assertEqual(len(result_data['result']['persons']), 1)
            self.assertEqual(result_data['result']['count'], 1)
            self.assertEqual(result_data['result']['total'], 1)
            person = result_data['result']['persons'][0]
            self.assertIn('id', person)
            person_id, _type = person['id'].split("_")
            real_person = PrivatePersonDbObject.query.filter_by(id=person_id).first()
            self.assertIsNotNone(real_person)
            self.assertEqual(person, PrivatePerson.db_obj_to_field(real_person).get_api_structure())
            self.assertEqual(real_person.name, data['name'])
            self.assertEqual(real_person.surname, data['surname'])
            self.assertEqual(real_person.patronymic, data['patronymic'])

    @authorized()
    def test_get_all_persons(self):
        with self.app.app_context():
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                '_owner_id': self.user.id
            }
            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            data2 = {
                'name': u"Поликарп2",
                'surname': u"Шариков2",
                'patronymic': u"Поликарпович2",
                '_owner_id': self.user.id
            }
            person2 = PrivatePersonDbObject(**data2)
            sqldb.session.add(person2)
            sqldb.session.commit()

            data3 = {
                'name': u"Поликарп3",
                'surname': u"Шариков3",
                'patronymic': u"Поликарпович3",
                '_owner_id': self.user.id
            }
            person3 = PrivatePersonDbObject(**data3)
            sqldb.session.add(person3)
            sqldb.session.commit()

            result = self.test_client.get('/entity/person/')
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            self.assertEqual(len(result_data['result']['persons']), 3)
            self.assertEqual(result_data['result']['count'], 3)
            self.assertEqual(result_data['result']['total'], 3)
            person = result_data['result']['persons'][0]
            self.assertIn('id', person)
            person_id, _type = person['id'].split("_")
            real_person = PrivatePersonDbObject.query.filter_by(id=person_id).first()
            self.assertIsNotNone(real_person)
            self.assertEqual(person, PrivatePerson.db_obj_to_field(real_person).get_api_structure())
            self.assertEqual(real_person.name, data['name'])
            self.assertEqual(real_person.surname, data['surname'])
            self.assertEqual(real_person.patronymic, data['patronymic'])

    @authorized()
    def test_get_all_persons_limit_offset(self):
        with self.app.app_context():
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                '_owner_id': self.user.id
            }
            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            data2 = {
                'name': u"Поликарп2",
                'surname': u"Шариков2",
                'patronymic': u"Поликарпович2",
                '_owner_id': self.user.id
            }
            person2 = PrivatePersonDbObject(**data2)
            sqldb.session.add(person2)
            sqldb.session.commit()

            data3 = {
                'name': u"Поликарп3",
                'surname': u"Шариков3",
                'patronymic': u"Поликарпович3",
                '_owner_id': self.user.id
            }
            person3 = PrivatePersonDbObject(**data3)
            sqldb.session.add(person3)
            sqldb.session.commit()

            result = self.test_client.get('/entity/person/?offset=1&count=1')
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            self.assertEqual(len(result_data['result']['persons']), 1)
            self.assertEqual(result_data['result']['count'], 1)
            self.assertEqual(result_data['result']['total'], 3)
            person = result_data['result']['persons'][0]
            self.assertIn('id', person)
            person_id, _type = person['id'].split("_")
            real_person = PrivatePersonDbObject.query.filter_by(id=person_id).first()
            self.assertIsNotNone(real_person)
            self.assertEqual(person, PrivatePerson.db_obj_to_field(real_person).get_api_structure())
            self.assertEqual(real_person.name, data2['name'])
            self.assertEqual(real_person.surname, data2['surname'])
            self.assertEqual(real_person.patronymic, data2['patronymic'])

    @authorized()
    def test_update_person(self):
        with self.app.app_context():
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                '_owner_id': self.user.id
            }

            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            data = {
                'person_id': unicode(person.id) + "_person",
                'person': json.dumps({
                    'name': u"Иван",
                    'surname': u"Иванов",
                    'patronymic': u"Иванович",
                    'birthdate': u'2014-02-18'
                })
            }
            result = self.test_client.post('/entity/person/update/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            person = result_data['result']

            person_id, _type = person['id'].split("_")
            real_person = PrivatePersonDbObject.query.filter_by(id=person_id).first()
            self.assertIsNotNone(real_person)
            self.assertEqual(person, PrivatePerson.db_obj_to_field(real_person).get_api_structure())
            self.assertEqual(real_person.name, u"Иван")
            self.assertEqual(real_person.surname, u"Иванов")
            self.assertEqual(real_person.patronymic, u"Иванович")
            # noinspection PyUnresolvedReferences
            person_doc = PrivatePerson.db_obj_to_field(real_person)
            self.assertEqual(unicode(person_doc.name), u"Иван")

    @authorized()
    def test_update_person(self):
        with self.app.app_context():
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                'phone': u"+79001231313",
                '_owner_id': self.user.id
            }

            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            data = {
                'person_id': unicode(person.id) + "_person",
                'person': json.dumps({
                    'name': u"Иван",
                    'surname': u"Иванов",
                    'patronymic': u"Иванович",
                    'phone': u"",
                    'birthdate': u'2014-02-18'
                })
            }
            result = self.test_client.post('/entity/person/update/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            person = result_data['result']

            person_id, _type = person['id'].split("_")
            real_person = PrivatePersonDbObject.query.filter_by(id=person_id).first()
            self.assertIsNotNone(real_person)
            self.assertEqual(person, PrivatePerson.db_obj_to_field(real_person).get_api_structure())
            self.assertEqual(real_person.name, u"Иван")
            self.assertEqual(real_person.surname, u"Иванов")
            self.assertEqual(real_person.patronymic, u"Иванович")
            self.assertEqual(real_person.phone, None)
            # noinspection PyUnresolvedReferences
            person_doc = PrivatePerson.db_obj_to_field(real_person)
            self.assertEqual(unicode(person_doc.name), u"Иван")

    @authorized()
    def test_get_removed_person_by_id(self):
        with self.app.app_context():
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                'deleted': True
            }

            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            result = self.test_client.get('/entity/person/?person_id=%s_person' % unicode(person.id))
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 404)

            result_data = json.loads(result.data)
            self.assertNotIn('result', result_data)
            self.assertIn('error', result_data)
            error = result_data['error']
            self.assertEqual(error['code'], 207)

    @authorized()
    def test_get_persons_after_removal_some_of_them(self):
        with self.app.app_context():
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                'deleted': True,
                '_owner_id': self.user.id
            }
            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            data2 = {
                'name': u"Поликарп2",
                'surname': u"Шариков2",
                'patronymic': u"Поликарпович2",
                '_owner_id': self.user.id
            }
            person2 = PrivatePersonDbObject(**data2)
            sqldb.session.add(person2)
            sqldb.session.commit()

            data3 = {
                'name': u"Поликарп3",
                'surname': u"Шариков3",
                'patronymic': u"Поликарпович3",
                'deleted': True,
                '_owner_id': self.user.id
            }
            person3 = PrivatePersonDbObject(**data3)
            sqldb.session.add(person3)
            sqldb.session.commit()

            result = self.test_client.get('/entity/person/')
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            self.assertEqual(len(result_data['result']['persons']), 1)
            self.assertEqual(result_data['result']['count'], 1)
            self.assertEqual(result_data['result']['total'], 1)
            person = result_data['result']['persons'][0]
            self.assertIn('id', person)
            person_id, _type = person['id'].split("_")
            real_person = PrivatePersonDbObject.query.filter_by(id=person_id).first()
            self.assertIsNotNone(real_person)
            self.assertEqual(person, PrivatePerson.db_obj_to_field(real_person).get_api_structure())
            self.assertEqual(real_person.name, data2['name'])
            self.assertEqual(real_person.surname, data2['surname'])
            self.assertEqual(real_person.patronymic, data2['patronymic'])

    @authorized()
    def test_delete_person(self):
        with self.app.app_context():
            data_person = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                '_owner_id': self.user.id
            }
            person = PrivatePersonDbObject(**data_person)
            sqldb.session.add(person)
            sqldb.session.commit()

            result = self.test_client.post('/entity/person/remove/', data={
                'person_id': unicode(person.id) + "_person"
            })
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertNotIn('error', result_data)
            self.assertIn('result', result_data)
            self.assertTrue(result_data['result'])

    @authorized()
    def test_create_company(self):
        with self.app.app_context():
            data = {
                "company": json.dumps({
                    'full_name': u"ООО Ромашка",
                    'inn': "781108730780"
                })
            }
            result = self.test_client.post('/entity/company/create/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            company = result_data['result']
            self.assertIn('id', company)
            company_id, _type = company['id'].split('_')
            real_company = CompanyDbObject.query.filter_by(id=company_id).first()
            self.assertIsNotNone(real_company)
            self.assertEqual(company, CompanyObject.db_obj_to_field(real_company).get_api_structure())
            self.assertEqual(real_company.full_name, u"ООО Ромашка")
            self.assertEqual(real_company.inn, "781108730780")

    @authorized()
    def test_create_foreign_company(self):
        with self.app.app_context():
            data = {
                "company": json.dumps({
                    'full_name': u"ООО Ромашка",
                    'inn': "781108730780",
                    'company_type': CompanyTypeEnum.CT_FOREIGN
                })
            }
            result = self.test_client.post('/entity/company/create/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            company = result_data['result']
            self.assertIn('id', company)
            company_id, _type = company['id'].split('_')
            real_company = CompanyDbObject.query.filter_by(id=company_id).first()
            self.assertIsNotNone(real_company)
            self.assertEqual(company, CompanyObject.db_obj_to_field(real_company).get_api_structure())
            self.assertEqual(real_company.full_name, u"ООО Ромашка")
            self.assertEqual(real_company.inn, "781108730780")

    @authorized()
    def test_create_company_person_as_empty_string(self):
        with self.app.app_context():
            data = {
                "company": json.dumps({
                    'full_name': u"ООО Ромашка",
                    'inn': "781108730780",
                    'general_manager': "",
                    'registration_date': u""
                })
            }
            result = self.test_client.post('/entity/company/create/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            company = result_data['result']
            self.assertIn('id', company)
            company_id, _type = company['id'].split('_')
            real_company = CompanyDbObject.query.filter_by(id=company_id).first()
            self.assertIsNotNone(real_company)
            self.assertEqual(company, CompanyObject.db_obj_to_field(real_company).get_api_structure())
            self.assertEqual(real_company.full_name, u"ООО Ромашка")
            self.assertEqual(real_company.inn, "781108730780")

    @authorized()
    def test_create_company_with_general_manager(self):
        with self.app.app_context():
            person = PrivatePersonDbObject(
                name=u"Поликарп",
                surname=u"Шариков",
                patronymic=u"Поликарпович",
                _owner=self.user,
                birthdate=datetime.now()
            )
            sqldb.session.add(person)
            sqldb.session.commit()
            data = {
                "company": json.dumps({
                    'full_name': u"ООО Ромашка",
                    'inn': "781108730780",
                    'general_manager': "%s_person" % person.id,
                    'registration_date': u""
                })
            }
            result = self.test_client.post('/entity/company/create/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            company = result_data['result']
            self.assertIn('id', company)
            company_id, _type = company['id'].split('_')
            real_company = CompanyDbObject.query.filter_by(id=company_id).first()
            self.assertIsNotNone(real_company)
            self.assertEqual(company, CompanyObject.db_obj_to_field(real_company).get_api_structure())
            self.assertEqual(real_company.full_name, u"ООО Ромашка")
            self.assertEqual(real_company.inn, "781108730780")

    @authorized()
    def test_update_company(self):
        with self.app.app_context():
            data = {
                'full_name': u"ООО Ромашка",
                'inn': "781108730780",
                '_owner_id': self.user.id
            }
            company = CompanyDbObject(**data)
            sqldb.session.add(company)
            sqldb.session.commit()

            data = {
                'company_id': company.id + "_company",
                'company': json.dumps({
                    'full_name': u"ООО Прогресс",
                    'inn': "781108730780"
                })
            }
            result = self.test_client.post('/entity/company/update/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            company = result_data['result']
            self.assertEqual(company['full_name'], u"ООО Прогресс")
            self.assertEqual(company['inn'], "781108730780")

            company_id, _type = company['id'].split('_')
            real_company = CompanyObject.db_obj_to_field(CompanyDbObject.query.filter_by(id=company_id).first())
            self.assertEqual(unicode(real_company.full_name), u"ООО Прогресс")
            self.assertEqual(real_company.inn, "781108730780")

    @authorized()
    def test_get_company_by_id(self):
        with self.app.app_context():
            data = {
                'full_name': u"ООО Ромашка",
                'inn': "781108730780",
                '_owner_id': self.user.id
            }
            company = CompanyDbObject(**data)
            sqldb.session.add(company)
            sqldb.session.commit()

            result = self.test_client.get('/entity/company/?company_id=%s' % company.id + "_company")
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)

            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            self.assertEqual(len(result_data['result']['companies']), 1)
            self.assertEqual(result_data['result']['count'], 1)
            self.assertEqual(result_data['result']['total'], 1)
            company = result_data['result']['companies'][0]
            self.assertIn('id', company)
            company_id, _type = company['id'].split('_')
            real_company = CompanyDbObject.query.filter_by(id=company_id).first()
            self.assertIsNotNone(real_company)
            self.assertEqual(company, CompanyObject.db_obj_to_field(real_company).get_api_structure())
            self.assertEqual(real_company.full_name, data['full_name'])
            self.assertEqual(real_company.inn, data['inn'])

    @authorized()
    def test_get_all_companies(self):
        with self.app.app_context():
            data = {
                'full_name': u"ООО Ромашка1",
                'inn': '7826120135',
                'kpp': '781701001',
                'ogrn': '1027810273754',
                '_owner_id': self.user.id
            }
            company = CompanyDbObject(**data)
            sqldb.session.add(company)
            sqldb.session.commit()

            data2 = {
                'full_name': u"ООО Ромашка2",
                'inn': "781108730780",
                '_owner_id': self.user.id
            }
            company2 = CompanyDbObject(**data2)
            sqldb.session.add(company2)
            sqldb.session.commit()

            data3 = {
                'full_name': u"ООО Ромашка3",
                'inn': "781108730780",
                '_owner_id': self.user.id
            }
            company3 = CompanyDbObject(**data3)
            sqldb.session.add(company3)
            sqldb.session.commit()

            result = self.test_client.get('/entity/company/')
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            self.assertEqual(len(result_data['result']['companies']), 3)
            self.assertEqual(result_data['result']['count'], 3)
            self.assertEqual(result_data['result']['total'], 3)
            company = result_data['result']['companies'][0]
            self.assertIn('id', company)
            company_id, _type = company['id'].split('_')
            real_company = CompanyDbObject.query.filter_by(id=company_id).order_by(CompanyDbObject.id.asc()).first()
            self.assertIsNotNone(real_company)
            self.assertEqual(company, CompanyObject.db_obj_to_field(real_company).get_api_structure())
            self.assertEqual(real_company.full_name, data['full_name'])
            self.assertEqual(real_company.inn, str(data['inn']))

    @authorized()
    def test_get_all_companies_limit_offset(self):
        with self.app.app_context():
            data = {
                'full_name': u"ООО Ромашка1",
                'inn': "781108730780",
                '_owner_id': self.user.id
            }
            company = CompanyDbObject(**data)
            sqldb.session.add(company)
            sqldb.session.commit()

            data2 = {
                'full_name': u"ООО Ромашка2",
                'inn': "781108730780",
                '_owner_id': self.user.id
            }
            company2 = CompanyDbObject(**data2)
            sqldb.session.add(company2)
            sqldb.session.commit()

            data3 = {
                'full_name': u"ООО Ромашка3",
                'inn': "781108730780",
                '_owner_id': self.user.id
            }
            company3 = CompanyDbObject(**data3)
            sqldb.session.add(company3)
            sqldb.session.commit()

            result = self.test_client.get('/entity/company/?offset=1&count=1')
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            self.assertEqual(len(result_data['result']['companies']), 1)
            self.assertEqual(result_data['result']['count'], 1)
            self.assertEqual(result_data['result']['total'], 3)
            company = result_data['result']['companies'][0]
            self.assertIn('id', company)
            company_id, _type = company['id'].split('_')
            real_company = CompanyDbObject.query.filter_by(id=company_id).first()
            self.assertIsNotNone(real_company)
            self.assertEqual(company, CompanyObject.db_obj_to_field(real_company).get_api_structure())
            self.assertEqual(real_company.full_name, data2['full_name'])
            self.assertEqual(real_company.inn, data2['inn'])

    @authorized()
    def test_delete_company(self):
        with self.app.app_context():
            data = {
                'full_name': u"ООО Ромашка1",
                'inn': "781108730780",
                '_owner_id': self.user.id
            }
            company = CompanyDbObject(**data)
            sqldb.session.add(company)
            sqldb.session.commit()

            result = self.test_client.post('/entity/company/remove/', data={
                'company_id': company.id + "_company"
            })
            company = CompanyDbObject.query.filter_by(id=company.id).first()
            self.assertEqual(company.deleted, True)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertNotIn('error', result_data)
            self.assertIn('result', result_data)
            self.assertTrue(result_data['result'])

    @authorized()
    def test_get_removed_company_by_id(self):
        with self.app.app_context():
            data = {
                'full_name': u"ООО Ромашка1",
                'inn': "781108730780",
                'deleted': True
            }
            company = CompanyDbObject(**data)
            sqldb.session.add(company)
            sqldb.session.commit()

            result = self.test_client.get('/entity/company/?company_id=%s' % company.id + "_company")
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 404)
            result_data = json.loads(result.data)

            self.assertNotIn('result', result_data)
            self.assertIn('error', result_data)
            self.assertEqual(result_data['error']['code'], 207)

    @authorized()
    def test_get_companies_after_removal_some_of_them(self):
        with self.app.app_context():
            data = {
                'full_name': u"ООО Ромашка1",
                'inn': "781108730780",
                'deleted': True,
                '_owner_id': self.user.id
            }
            company = CompanyDbObject(**data)
            sqldb.session.add(company)
            sqldb.session.commit()

            data2 = {
                'full_name': u"ООО Ромашка2",
                'inn': "781108730780",
                '_owner_id': self.user.id
            }
            company2 = CompanyDbObject(**data2)
            sqldb.session.add(company2)
            sqldb.session.commit()

            data3 = {
                'full_name': u"ООО Ромашка3",
                'inn': "781108730780",
                'deleted': True,
                '_owner_id': self.user.id
            }
            company3 = CompanyDbObject(**data3)
            sqldb.session.add(company3)
            sqldb.session.commit()

            result = self.test_client.get('/entity/company/')
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            self.assertEqual(len(result_data['result']['companies']), 1)
            self.assertEqual(result_data['result']['count'], 1)
            self.assertEqual(result_data['result']['total'], 1)
            company = result_data['result']['companies'][0]
            self.assertIn('id', company)
            company_id, _type = company['id'].split('_')
            real_company = CompanyDbObject.query.filter_by(id=company_id).first()
            self.assertIsNotNone(real_company)
            self.assertEqual(company, CompanyObject.db_obj_to_field(real_company).get_api_structure())
            self.assertEqual(real_company.full_name, data2['full_name'])
            self.assertEqual(real_company.inn, data2['inn'])

    @authorized()
    def test_not_my_person(self):
        some_user = AuthUser()
        sqldb.session.add(some_user)
        sqldb.session.commit()
        with self.app.app_context():
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                '_owner': some_user
            }

            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            result = self.test_client.get('/entity/person/?person_id=%s_person' % unicode(person.id))
            self.assertEqual(result.status_code, 404)
            result_data = json.loads(result.data)
            self.assertNotIn('result', result_data)
            self.assertIn('error', result_data)
            self.assertEqual(result_data['error']['code'], 207)

            result = self.test_client.get('/entity/person/')

            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            self.assertEqual(len(result_data['result']['persons']), 0)

    @authorized()
    def test_update_not_my_person(self):
        some_user = AuthUser()
        sqldb.session.add(some_user)
        sqldb.session.commit()
        with self.app.app_context():
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                '_owner': some_user
            }

            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            data = {
                'person_id': unicode(person.id) + "_person",
                'person': json.dumps({
                    'caption': u"Труляля",
                })
            }
            result = self.test_client.post('/entity/person/update/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 404)
            result_data = json.loads(result.data)
            self.assertNotIn('result', result_data)
            self.assertIn('error', result_data)
            self.assertEqual(result_data['error']['code'], 207)

    @authorized()
    def test_remove_not_my_person(self):
        some_user = AuthUser()
        sqldb.session.add(some_user)
        sqldb.session.commit()
        with self.app.app_context():
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                '_owner': some_user
            }

            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            result = self.test_client.post('/entity/person/remove/', data={
                'person_id': unicode(person.id) + "_person"
            })
            self.assertEqual(result.status_code, 404)
            result_data = json.loads(result.data)
            self.assertIn('error', result_data)
            self.assertNotIn('result', result_data)
            self.assertEqual(result_data['error']['code'], 207)

    @authorized()
    def test_not_my_company(self):
        with self.app.app_context():
            some_user = AuthUser()
            sqldb.session.add(some_user)
            sqldb.session.commit()
            data = {
                'full_name': u"ООО Лютик",
                '_owner': some_user
            }

            company = CompanyDbObject(**data)
            sqldb.session.add(company)
            sqldb.session.commit()

            result = self.test_client.get('/entity/company/?company_id=%s_company' % company.id)
            self.assertEqual(result.status_code, 404)
            result_data = json.loads(result.data)
            self.assertNotIn('result', result_data)
            self.assertIn('error', result_data)
            self.assertEqual(result_data['error']['code'], 207)

            result = self.test_client.get('/entity/company/')

            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertIn('result', result_data)
            self.assertNotIn('error', result_data)
            self.assertEqual(len(result_data['result']['companies']), 0)

    @authorized()
    def test_update_not_my_company(self):
        some_user = AuthUser()
        sqldb.session.add(some_user)
        sqldb.session.commit()
        with self.app.app_context():
            data = {
                'full_name': u"ООО Лютик",
                '_owner': some_user
            }

            company = CompanyDbObject(**data)
            sqldb.session.add(company)
            sqldb.session.commit()

            data = {
                'company_id': company.id + "_company",
                'company': json.dumps({
                    'full_name': u"Труляля",
                })
            }
            result = self.test_client.post('/entity/company/update/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 404)
            result_data = json.loads(result.data)
            self.assertNotIn('result', result_data)
            self.assertIn('error', result_data)
            self.assertEqual(result_data['error']['code'], 207)

    @authorized()
    def test_delete_not_my_company(self):
        with self.app.app_context():
            some_user = AuthUser()
            sqldb.session.add(some_user)
            sqldb.session.commit()
            data = {
                'full_name': u"ООО Лютик",
                '_owner': some_user
            }

            company = CompanyDbObject(**data)
            sqldb.session.add(company)
            sqldb.session.commit()

            result = self.test_client.post('/entity/company/remove/', data={
                'company_id': company.id + "_company"
            })
            self.assertEqual(result.status_code, 404)
            result_data = json.loads(result.data)
            self.assertIn('error', result_data)
            self.assertNotIn('result', result_data)
            self.assertEqual(result_data['error']['code'], 207)

    @authorized()
    def test_update_company_set_not_mine_person(self):
        with self.app.app_context():
            data = {
                'full_name': u"ООО Ромашка",
                'inn': "781108730780",
                '_owner_id': self.user.id
            }
            company = CompanyDbObject(**data)
            sqldb.session.add(company)
            sqldb.session.commit()

            real_company = CompanyObject.db_obj_to_field(CompanyDbObject.query.filter_by(id=company.id).first())
            self.assertIsNotNone(real_company)

            some_user = AuthUser()
            sqldb.session.add(some_user)
            sqldb.session.commit()
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                '_owner': some_user
            }

            person = PrivatePersonDbObject(**data)
            sqldb.session.add(person)
            sqldb.session.commit()

            data = {
                'company_id': company.id + "_company",
                'company': json.dumps({
                    'full_name': u"ООО Прогресс",
                    'inn': "781108730780",
                    'general_manager': {
                        "id": unicode(person.id)
                    }
                })
            }
            result = self.test_client.post('/entity/company/update/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 400)
            result_data = json.loads(result.data)
            self.assertNotIn('result', result_data)
            self.assertIn('error', result_data)
            self.assertEqual(result_data['error']['code'], 5)

    @authorized()
    def test_update_person_set_not_mine_person(self):
        with self.app.app_context():
            data = {
                'name': u"Ромашка",
                'inn': "781108730780",
                '_owner_id': self.user.id
            }
            my_person = PrivatePersonDbObject(**data)
            sqldb.session.add(my_person)
            sqldb.session.commit()

            some_user = AuthUser()
            sqldb.session.add(some_user)
            sqldb.session.commit()
            data = {
                'name': u"Поликарп",
                'surname': u"Шариков",
                'patronymic': u"Поликарпович",
                '_owner': some_user
            }

            not_mine_person = PrivatePersonDbObject(**data)
            sqldb.session.add(not_mine_person)
            sqldb.session.commit()

            data = {
                'person_id': unicode(my_person.id) + "_person",
                'person': json.dumps({
                    'name': u"ООО Прогресс",
                    'inn': "781108730780",
                    'spouse': {
                        "id": unicode(not_mine_person.id)
                    }
                })
            }
            result = self.test_client.post('/entity/person/update/', data=data)
            self.assertIsNotNone(result)
            self.assertEqual(result.status_code, 400)
            result_data = json.loads(result.data)
            self.assertNotIn('result', result_data)
            self.assertIn('error', result_data)
            self.assertEqual(result_data['error']['code'], 5)

    @authorized()
    def test_get_batch_status(self):
        batch_db = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
            _owner=self.user
        )
        sqldb.session.add(batch_db)
        sqldb.session.commit()
        batch_id = batch_db.id

        result = self.test_client.get('/batch/status/?batch_id=%s' % batch_id)
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertIn('result', data)
        self.assertEqual(data['result'], {
            u'id': batch_id,
            u'batch_type': u'llc',
            u'creation_date': batch_db.creation_date.strftime('%Y-%m-%dT%H:%M:%S'),
            u"name": u"Создание ООО",
            u"status": u'new',
            u"paid": "false"
        })

    @authorized()
    def test_get_companies_without_copies(self):
        company_founder = CompanyDbObject(**{
            "_owner_id": self.user.id,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "incorporation_form": IncorporationFormEnum.IF_LLC,
            "full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
            "short_name": u"Бокс",
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
        sqldb.session.add(company_founder)
        sqldb.session.commit()
        id1 = company_founder.id

        company_founder2 = CompanyDbObject(**{
            "_owner_id": self.user.id,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "incorporation_form": IncorporationFormEnum.IF_LLC,
            "full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
            "short_name": u"Бокс",
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
        sqldb.session.add(company_founder2)
        sqldb.session.commit()
        id2 = company_founder2.id

        sqldb.session.expunge(company_founder)
        make_transient(company_founder)
        company1_copy = company_founder
        company1_copy.id = None
        sqldb.session.add(company1_copy)
        company1_copy._copy = CompanyDbObject.query.filter_by(id=id1).first()
        sqldb.session.commit()

        sqldb.session.expunge(company_founder2)
        make_transient(company_founder2)
        company2_copy = company_founder2
        company2_copy.id = None
        sqldb.session.add(company2_copy)
        company2_copy._copy = CompanyDbObject.query.filter_by(id=id2).first()
        sqldb.session.commit()

        result = self.test_client.get('/entity/company/')
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)
        self.assertEqual(len(result_data['result']['companies']), 2)
        self.assertEqual(result_data['result']['count'], 2)
        self.assertEqual(result_data['result']['total'], 2)
        person = result_data['result']['companies'][0]
        self.assertIn(person['id'].split('_')[0], (id1, id2))
        person = result_data['result']['companies'][1]
        self.assertIn(person['id'].split('_')[0], (id1, id2))

    @authorized()
    def test_get_persons_without_copies(self):
        founder_person = PrivatePersonDbObject(**{
            "_owner_id": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
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
                "index": 198259,
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Тамбасова",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "38",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "70",
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder_person)
        sqldb.session.commit()
        founder_person_id = founder_person.id

        founder_person2 = PrivatePersonDbObject(**{
            "_owner_id": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
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
                "index": 198259,
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Тамбасова",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "38",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "70",
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder_person2)
        sqldb.session.commit()

        founder_person2_id = founder_person2.id

        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False,
            deleted=True
        )
        sqldb.session.add(new_batch)
        sqldb.session.commit()

        person1_copy = PrivatePersonDbObject.query.filter_by(id=founder_person_id).first()
        sqldb.session.expunge(person1_copy)
        make_transient(person1_copy)
        person1_copy.id = None
        person1_copy._copy = founder_person.id
        person1_copy._batch = new_batch
        sqldb.session.add(person1_copy)
        sqldb.session.commit()

        founder_person = PrivatePersonDbObject.query.filter_by(id=founder_person_id).first()

        person2_copy = PrivatePersonDbObject.query.filter_by(id=founder_person2_id).first()
        sqldb.session.expunge(person2_copy)
        make_transient(person2_copy)
        person2_copy.id = None
        person2_copy._copy = founder_person2.id
        person2_copy._batch = new_batch
        sqldb.session.add(person2_copy)
        sqldb.session.commit()
        founder_person2 = PrivatePersonDbObject.query.filter_by(id=founder_person2_id).first()

        result = self.test_client.get('/entity/person/')
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)
        self.assertEqual(len(result_data['result']['persons']), 2)
        self.assertEqual(result_data['result']['count'], 2)
        self.assertEqual(result_data['result']['total'], 2)
        person = result_data['result']['persons'][0]
        self.assertIn(person['id'].split('_')[0], (unicode(founder_person.id), unicode(founder_person2.id)))
        person = result_data['result']['persons'][1]
        self.assertIn(person['id'].split('_')[0], (unicode(founder_person.id), unicode(founder_person2.id)))

    @authorized()
    def test_upload_file(self):
        strIO = StringIO.StringIO()
        content = "File content"
        strIO.write(content)
        strIO.seek(0)
        result = self.test_client.post('/storage/put/', data={
            "file": (strIO, 'filename.pdf')
        })
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertIn('id', result_data['result'])
        self.assertIn('size', result_data['result'])
        self.assertIn('url', result_data['result'])
        self.assertEqual(result_data['result']['size'], len(content))
        f_obj = FileObject.query.filter_by(id=result_data['result']['id']).first()
        self.assertIsNotNone(f_obj)
        self.assertEqual(f_obj._owner, self.user)
        url = FileStorage.get_url(f_obj, self.config)
        self.assertTrue(url.endswith('/filename.pdf'), url)
        self.assertIn(unicode(f_obj.id), url)
        path = FileStorage.get_path(f_obj, self.config)
        self.assertTrue(os.path.exists(path), u"File %s does not exist" % path)
        with open(path, 'r') as f:
            self.assertEqual(f.read(), content)

    def test_get_okvad_catalog(self):
        self.import_okvad_catalog()
        result = self.test_client.get('/get_okvad_catalog/')
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(len(result_data['result']), 2)

        o1 = result_data['result'][0]
        o2 = result_data['result'][1]

        del o1['_id']
        del o1['departments'][0]['_id']
        del o1['departments'][1]['_id']
        del o2['_id']
        del o2['departments'][0]['_id']
        del o2['departments'][1]['_id']
        self.maxDiff = None
        self.assertEqual(o1, {u'name': u'foo', u'departments': [{u'name': u'bar', u'main_okvad': u'1'},
                                                                {u'name': u'baz', u'main_okvad': u'5'}]})
        self.assertEqual(o2, {u'name': u'foo2', u'departments': [{u'name': u'bar2', u'main_okvad': u'11'},
                                                                 {u'name': u'baz2', u'main_okvad': u'15'}]})

    @authorized()
    def test_send_paid_docs(self):
        data = {
            'name': u"Нейм",
            'surname': u"Сёрнейм",
            'inn': "781108730780",
            'phone': "+79110010203",
            'email': "test@test.email",
            '_owner_id': self.user.id
        }
        person = PrivatePersonDbObject(**data)
        sqldb.session.add(person)
        sqldb.session.commit()
        person_id = person.id

        new_company = CompanyDbObject(**dict({
            "_owner_id": self.user.id,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "full_name": u"Протон",
            "short_name": u"Про",
            "kpp": "999999999",
            "company_type": CompanyTypeEnum.CT_RUSSIAN,
            "general_manager": {
                "_id" : person.id,
                "type": "person"
            }})
                                      )

        sqldb.session.add(new_company)
        sqldb.session.commit()
        new_company_id = new_company.id

        data = {
            u"full_name": u"образовательное учреждение дополнительного образования детей специализированная "
                          u"детско-юношеская спортивная школа олимпийского резерва по боксу",
            u"short_name": u"Парампампам",
            u"doc_date": datetime.now(),
            u"address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 123131,
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Седова",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "2",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "2",
                "ifns": 1234
            },
            u"selected_secretary": {
                "type": "company",
                "_id": new_company_id
            },
        }
        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(document_type=DocumentTypeEnum.DT_GARANT_LETTER_SUBARENDA, data=data), None,
                                     False)
        doc_list = [
            new_user_doc.db_value()
        ]

        file1_id = FileObject(file_path='path', file_name='f.pdf', _owner=self.user)
        sqldb.session.add(file1_id)
        sqldb.session.commit()

        file2_id = FileObject(file_path='path', file_name='f2.pdf', _owner=self.user)
        sqldb.session.add(file2_id)
        sqldb.session.commit()

        new_batch_db_object = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
            status=BatchStatusEnum.BS_NEW,
            _owner=self.user,
            paid=True,
            data=data,
            # rendered_docs=[{
            #                    'document_type': DocumentTypeEnum.DT_ACCOUNTANT_ORDER,
            #                    'file_link': 'http://asdfasdfasdfasdfasdf.ru/a.pdf',
            #                    'caption': u'Приказ о приёме на работу бухгалтера',
            #                    'file_id': file1_id.id,
            #                    'document_id': ObjectId(),
            #                    'status': UserDocumentStatus.DS_RENDERED
            #                }, {
            #                    'document_type': DocumentTypeEnum.DT_ARTICLES,
            #                    'file_link': 'http://asdfhjklasdhfsf.ru/b.pdf',
            #                    'caption': u'Устав',
            #                    'file_id': file2_id.id,
            #                    'document_id': ObjectId(),
            #                    'status': UserDocumentStatus.DS_RENDERED
            #                }]
        )
        sqldb.session.add(new_batch_db_object)
        sqldb.session.commit()

        BatchManager.send_batch_docs_to_user(new_batch_db_object.id, self.config)

        self.assertEqual(len(self.mailer.mails), 1)
        self.assertEqual(self.mailer.mails[0]['message']['subject'], u'Документы для регистрации ООО «Парампампам»')

    @authorized()
    def test_create_batch(self):
        data = {
            "batch_type": DocumentBatchTypeEnum.DBT_TEST_TYPE
        }
        result = self.test_client.post('/batch/create/', data=data)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)

        self.assertEqual(DocumentBatchDbObject.query.count(), 1)
        batch = DocumentBatchDbObject.query.first()
        self.assertEqual(batch.status, BatchStatusEnum.BS_NEW)
        self.assertEqual(batch._owner, self.user)
        self.assertEqual(batch.batch_type, DocumentBatchTypeEnum.DBT_TEST_TYPE)
        self.assertIsNotNone(batch.creation_date)
        self.assertIsNone(batch.finalisation_date)
        self.assertEqual(batch.deleted, False)
        self.assertEqual(batch.data, {})
        self.assertIsNone(batch.error_info)
        self.assertIsNone(batch.result_fields)
        self.assertIsNone(batch._metadata)
        self.assertIsNone(batch.pay_info)
        self.assertEqual(batch.paid, False)
        self.assertIsNone(batch.last_change_dt)

        self.assertEqual(BatchDocumentDbObject.query.count(), 0)

    @authorized()
    def test_get_new_batch(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)
        sqldb.session.commit()

        result = self.test_client.get('/batch/?batch_id=%s' % new_batch.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)

        self.assertIn('total', result_data['result'])
        self.assertIn('count', result_data['result'])
        self.assertIn('batches', result_data['result'])

        self.assertEqual(result_data['result']['total'], 1)
        self.assertEqual(result_data['result']['count'], 1)

        batches = result_data['result']['batches']

        self.assertEqual(len(batches), 1)

        self.assertIn('creation_date', batches[0])
        del batches[0]['creation_date']
        self.assertEqual(batches[0], {
            u'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            u'data': {},
            u'id': new_batch.id,
            u'paid': u'false',
            u'status': UserDocumentStatus.DS_NEW
        })

    @authorized()
    def test_get_batches_2_of_3(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch)
        sqldb.session.commit()

        new_batch2 = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch2)
        sqldb.session.commit()

        new_batch3 = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )
        sqldb.session.add(new_batch3)
        sqldb.session.commit()

        result = self.test_client.get('/batch/?count=2&offset=1')
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)

        self.assertIn('total', result_data['result'])
        self.assertIn('count', result_data['result'])
        self.assertIn('batches', result_data['result'])

        self.assertEqual(result_data['result']['total'], 3)
        self.assertEqual(result_data['result']['count'], 2)

        batches = result_data['result']['batches']

        self.assertEqual(len(batches), 2)

        self.assertIn('creation_date', batches[0])
        self.assertIn('creation_date', batches[1])

        del batches[0]['creation_date']
        del batches[1]['creation_date']

        self.assertEqual(batches[0], {
            u'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            u'data': {},
            u'id': new_batch2.id,
            u'paid': u'false',
            u'status': UserDocumentStatus.DS_NEW
        })

        self.assertEqual(batches[1], {
            u'batch_type': DocumentBatchTypeEnum.DBT_TEST_TYPE,
            u'data': {},
            u'id': new_batch.id,
            u'paid': u'false',
            u'status': UserDocumentStatus.DS_NEW
        })

    @authorized()
    def test_get_deleted_batch(self):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
            data={},
            _owner=self.user,
            status=BatchStatusEnum.BS_NEW,
            paid=False,
            deleted=True
        )
        sqldb.session.add(new_batch)
        sqldb.session.commit()

        result = self.test_client.get('/batch/?batch_id=%s' % new_batch.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 404)

        result = self.test_client.get('/batch/')
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)

        self.assertIn('total', result_data['result'])
        self.assertIn('count', result_data['result'])
        self.assertIn('batches', result_data['result'])

        self.assertEqual(result_data['result']['total'], 0)
        self.assertEqual(result_data['result']['count'], 0)

        batches = result_data['result']['batches']

        self.assertEqual(len(batches), 0)

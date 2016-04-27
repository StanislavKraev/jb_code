# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
import json

from bson.objectid import ObjectId

from base_test_case import BaseTestCase
from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import (RFRegionsEnum, VillageTypeEnum, DistrictTypeEnum, CityTypeEnum, StreetTypeEnum,
                                        HouseTypeEnum, BuildingTypeEnum, FlatTypeEnum)
from fw.documents.db_fields import PrivatePersonDbObject, DocumentBatchDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentBatchTypeEnum, DocumentTypeEnum, PersonDocumentTypeEnum, BatchStatusEnum, TaxType
from fw.documents.fields.doc_fields import DocumentBatch
from services.ifns.data_model.models import IfnsBookingObject, IfnsCatalogObject
from services.ip_reg.documents.enums import IPRegistrationWayEnum
from services.llc_reg.documents.enums import UsnTaxType
from test_api import authorized


class RenderingTestCase(BaseTestCase):
    @authorized()
    def test_ip_P21001(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_IP]['doc_types'] = [DocumentTypeEnum.DT_P21001]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокд",
            "surname": u"Подикарпов",
            "patronymic": u"Подикарпович",
            "inn": "781108730780",
            "sex": "male",
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
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гадчинский",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гадюкино",
                "village_type": VillageTypeEnum.VIT_HUTOR,
                "village": u"близ Диканьки",
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Модоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "2",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сандехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "person_type": 1,
            #"living_country_code" : 643,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder)
        sqldb.session.commit()

        with self.app.app_context():
            data = {
                u"person": {
                    "_id": founder.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1", u"10.01.22"],
                u"doc_obtain_person": {
                    "type": "person",
                    "_id": founder.id
                },
                u"obtain_way": "in_person",
                u"region": u"Санкт-Петербург",
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                status=BatchStatusEnum.BS_NEW,
                data={},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            _id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP
            )

            booking = IfnsBookingObject(
                batch_id=_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            t1 = time.time()
            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(_id)})
            t2 = time.time()
            print(t2 - t1)
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).one()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)

    @authorized()
    def test_ip_state_duty(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_IP]['doc_types'] = [DocumentTypeEnum.DT_IP_STATE_DUTY]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
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
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        founder.insert(self.db)

        with self.app.app_context():
            data = {
                u"person": {
                    "_id": founder.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                u"doc_obtain_person": {
                    "type": "person",
                    "_id": founder.id
                },
                u"obtain_way": "in_person",
                u"region": u"Санкт-Петербург",
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user.id
            )
            _id = batch.insert(self.db)

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP
            )

            booking = IfnsBookingObject(
                batch_id=_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(_id)})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print(json.dumps(db_batch.as_dict(), default=lambda x: unicode(x), ensure_ascii=False, indent=1))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_ip_dov_filing(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_IP]['doc_types'] = [DocumentTypeEnum.DT_IP_DOV_FILING_DOCS]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
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
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        founder.insert(self.db)

        dov_person = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Акакий",
            "surname": u"Тунцов",
            "patronymic": u"Подляченко",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 32),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz"
        })
        dov_person.insert(self.db)

        with self.app.app_context():
            data = {
                u"person": {
                    "_id": founder.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                # u"doc_obtain_person" : {
                #     "type" : "person",
                #     "_id" : founder.id
                # },
                # u"obtain_way" : "in_person",
                u"registration_way": "responsible_person",
                u"region": u"Санкт-Петербург",
                # u"same_obtain_trust_person": False,
                u"reg_responsible_person": {
                    "_id": dov_person.id,
                    "type": "person"
                },
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user.id
            )
            _id = batch.insert(self.db)

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP
            )

            booking = IfnsBookingObject(
                batch_id=_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(_id)})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print(json.dumps(db_batch.as_dict(), default=lambda x: unicode(x), ensure_ascii=False, indent=1))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_ip_dov_filing_receiving_by_same_person(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_IP]['doc_types'] = [DocumentTypeEnum.DT_IP_DOV_FILING_RECEIVING_DOCS, DocumentTypeEnum.DT_IP_DOV_RECEIVING_DOCS]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
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
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        founder.insert(self.db)

        dov_person = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Акакий",
            "surname": u"Тунцов",
            "patronymic": u"Подляченко",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 32),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz"
        })
        dov_person.insert(self.db)

        with self.app.app_context():
            data = {
                u"person": {
                    "_id": founder.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                u"obtain_way": "responsible_person",
                u"registration_way": "in_person",
                u"same_obtain_trust_person": False,
                u"region": u"Санкт-Петербург",
                u"doc_obtain_person": None,
                # u"reg_responsible_person" : {
                #     "_id" : dov_person.id,
                #     "type" : "person"
                # },
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user.id
            )
            _id = batch.insert(self.db)

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP
            )

            booking = IfnsBookingObject(
                batch_id=_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(_id)})
            print result.data
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print(json.dumps(db_batch.as_dict(), default=lambda x: unicode(x), ensure_ascii=False, indent=1))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_ip_dov_filing_receiving_different_persons(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_IP]['doc_types'] = [DocumentTypeEnum.DT_IP_DOV_RECEIVING_DOCS, DocumentTypeEnum.DT_IP_DOV_FILING_DOCS]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
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
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        founder.insert(self.db)

        dov_person = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Акакий",
            "surname": u"Тунцов",
            "patronymic": u"Подляченко",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 32),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz"
        })
        dov_person.insert(self.db)

        dov_person2 = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Марципан",
            "surname": u"Арешкин",
            "patronymic": u"Трофимович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 33),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 1),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Полупроводник",
            "phone": "+79210002233",
            "email": "somebody2@domain.zz"
        })
        dov_person2.insert(self.db)

        with self.app.app_context():
            data = {
                u"person": {
                    "_id": founder.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                u"obtain_way": "responsible_person",
                u"registration_way": "responsible_person",
                u"same_obtain_trust_person": False,
                u"region": u"Санкт-Петербург",
                u"reg_responsible_person": {
                    "_id": dov_person.id,
                    "type": "person"
                },
                u"doc_obtain_person": {
                    "_id": dov_person.id,
                    "type": "person"
                },
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                status=BatchStatusEnum.BS_EDITED,
                _documents=[],
                data={},
                _owner=self.user.id
            )
            _id = batch.insert(self.db)

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP
            )

            booking = IfnsBookingObject(
                batch_id=_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(_id)})
            print result.data
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print(json.dumps(db_batch.as_dict(), default=lambda x: unicode(x), ensure_ascii=False, indent=1))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 2)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_ip_dov_filing_receiving_different_persons2(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_IP]['doc_types'] = [
            DocumentTypeEnum.DT_IP_DOV_RECEIVING_DOCS,
            DocumentTypeEnum.DT_IP_DOV_FILING_DOCS,
            DocumentTypeEnum.DT_IP_DOV_FILING_RECEIVING_DOCS
        ]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 4),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
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
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        founder.insert(self.db)

        dov_person = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Акакий",
            "surname": u"Ивашкин",
            "patronymic": u"Подляченко",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 32),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 1),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz"
        })
        dov_person.insert(self.db)

        dov_person2 = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Марципан",
            #            "surname" : u"Арешкин",
            #            "patronymic" : u"Трофимович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 33),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 1),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Полупроводник",
            "phone": "+79210002233",
            "email": "somebody2@domain.zz"
        })
        dov_person2.insert(self.db)

        with self.app.app_context():
            data = {
                u"person": {
                    "_id": founder.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                u"obtain_way": "responsible_person",
                u"registration_way": "notary",
                u"same_obtain_trust_person": False,
                u"reg_responsible_person": {
                    "_id": dov_person2.id,
                    "type": "person"
                },
                u"doc_obtain_person": None
                #                u"doc_obtain_person" : {
                #                    "_id" : dov_person.id,
                #                    "type" : "person"
                #                },
            }

            data = {
                "doc_obtain_person": "%s_person" % dov_person.id,
                "job_code_array": ["50.30", "50.40", "51.44.4", "52.48.39"],
                "job_main_code": "50.20",
                "obtain_way": "responsible_person",
                "person": "%s_person" % founder.id,
                "reg_responsible_person": "%s_person" % dov_person2.id,
                "registration_way": "responsible_person",
                "same_obtain_trust_person": "false",
                "tax_type": "2",
                "taxation_type": "general"
            }

            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user.id
            )
            _id = batch.insert(self.db)

            #            new_batch_db_object = DocumentBatchDbObject(
            #                data = data,
            #                batch_type = DocumentBatchTypeEnum.DBT_NEW_IP
            #            )

            booking = IfnsBookingObject(
                batch_id=_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            #batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            batch_json = json.dumps({
                "batch_type": DocumentBatchTypeEnum.DBT_NEW_IP,
                "data": data
            })
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(_id)})
            print result.data
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print(json.dumps(db_batch.as_dict(), default=lambda x: unicode(x), ensure_ascii=False, indent=1))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_ip_usn(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_IP]['doc_types'] = [DocumentTypeEnum.DT_IP_USN_CLAIM]

        col = self.db['okvad']
        col.insert({"caption": u"Рыболовство", "okved": "92.31.1", "nalog": "usn",
                    "parent": ObjectId("5478373ee64bcf4ece4a57d8")})

        founder = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 3),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
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
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 643,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        founder.insert(self.db)

        with self.app.app_context():
            data = {
                u"person": {
                    "_id": founder.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1", u"10.01.1"],
                u"doc_obtain_person": {
                    "type": "person",
                    "_id": founder.id
                },
                u"obtain_way": "in_person",
                u"region": u"Санкт-Петербург",
                u"taxation_type": u"usn",
                u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user.id
            )
            _id = batch.insert(self.db)

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP
            )

            booking = IfnsBookingObject(
                batch_id=_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(_id)})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print(json.dumps(db_batch.as_dict(), default=lambda x: unicode(x), ensure_ascii=False, indent=1))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_ip_eshn(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_IP]['doc_types'] = [DocumentTypeEnum.DT_IP_ESHN_CLAIM]

        col = self.db['okvad']
        col.insert({"caption": u"Рыболовство", "okved": "92.31.1", "nalog": "eshn",
                    "parent": ObjectId("5478373ee64bcf4ece4a57d8")})

        founder = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            #"inn" : "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
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
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 643,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        founder.insert(self.db)

        with self.app.app_context():
            data = {
                u"person": {
                    "_id": founder.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1", u"10.01.1"],
                u"doc_obtain_person": {
                    "type": "person",
                    "_id": founder.id
                },
                u"obtain_way": "in_person",
                u"region": u"Санкт-Петербург",
                u"taxation_type": u"eshn",
                # u"tax_type" : UsnTaxType.UT_INCOME_MINUS_EXPENSE,
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user.id
            )
            _id = batch.insert(self.db)

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP
            )

            booking = IfnsBookingObject(
                batch_id=_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(_id)})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print(json.dumps(db_batch.as_dict(), default=lambda x: unicode(x), ensure_ascii=False, indent=1))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_ip_empty_batch(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_IP]['doc_types'] = [DocumentTypeEnum.DT_P21001]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
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
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 643,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        founder.insert(self.db)

        with self.app.app_context():
            data = {
                # u"person" : {
                #             "_id" : founder.id,
                #             "type" : "person"
                # },
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={

                },
                _owner=self.user.id
            )
            _id = batch.insert(self.db)

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP
            )

            booking = IfnsBookingObject(
                batch_id=_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_NEW)

    @authorized()
    def test_ip_full_batch(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_IP]['doc_types'] = [
            DocumentTypeEnum.DT_P21001,
            DocumentTypeEnum.DT_IP_DOV_FILING_DOCS,
            DocumentTypeEnum.DT_IP_ESHN_CLAIM]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
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
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 643,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        founder.insert(self.db)

        with self.app.app_context():
            data = {
                u"person": {
                    "_id": founder.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1", u"10.01.1"],
                u"doc_obtain_person": {
                    "type": "person",
                    "_id": founder.id
                },
                u"obtain_way": "in_person",
                u"region": u"Санкт-Петербург",
                u"taxation_type": u"usn",
                u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
                u"registration_way": "in_person",
                # u"tax_type" : UsnTaxType.UT_INCOME_MINUS_EXPENSE,
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={

                },
                _owner=self.user.id
            )
            _id = batch.insert(self.db)

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP
            )

            booking = IfnsBookingObject(
                batch_id=_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(_id)})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print(json.dumps(db_batch.as_dict(), default=lambda x: unicode(x), ensure_ascii=False, indent=1))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            # self.assertEqual(len(db_batch._documents), 1)
            # self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])


    @authorized()
    def test_ip_letter_inventory(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_IP]['doc_types'] = [DocumentTypeEnum.DT_IP_LETTER_INVENTORY]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
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
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        founder.insert(self.db)

        dov_person = PrivatePersonDbObject(**{
            "_owner": self.user.id,
            "name": u"Акакий",
            "surname": u"Тунцов",
            "patronymic": u"Подляченко",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 32),
            "birthplace": u"Россия, деревня Гадюкино",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "ifns": "7840",
                "okato": "40298566000"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz"
        })
        dov_person.insert(self.db)

        new_item = IfnsCatalogObject(**{
            'name': u"Межрайонная ИФНС России №22 по Санкт-Петербургу",
            'address': {
                "address_string": u",198334,Санкт-Петербург г,,,,Партизана Германа ул,37,,",
            },
            'comment': u"Код ОКПО:39449549 Прием: Понедельник, среда с 09.00 до 18.00. Вторник, четверг с 09.00 до 20.00. Пятница с 09.00 до 16.45. Вторая и четвертая субботы месяца с 10.00 до 15.00. Без перерыва на обед.",
            'code': 7840,
            'rou': {
                "name": u"Межрайонная ИФНС России №15 по Санкт-Петербургу",
                "code": u"78086",
                "tel": ["+7(812)3351403"]
            }
        })
        sqldb.session.add(new_item)
        sqldb.session.commit()

        with self.app.app_context():
            data = {
                u"person": {
                    "_id": founder.id,
                    "type": "person"
                },
                u"taxation_type": TaxType.TT_GENERAL,
                u"registration_way": IPRegistrationWayEnum.IP_RW_MAIL
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                paid=True,
                _owner=self.user.id
            )
            _id = batch.insert(self.db)

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_IP
            )

            booking = IfnsBookingObject(
                batch_id=_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(_id)})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print(json.dumps(db_batch.as_dict(), default=lambda x: unicode(x), ensure_ascii=False, indent=1))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

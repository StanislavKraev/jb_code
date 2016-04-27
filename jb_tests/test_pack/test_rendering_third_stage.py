# -*- coding: utf-8 -*-
from datetime import timedelta, datetime

from bson.objectid import ObjectId
from flask import json

from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import RFRegionsEnum, VillageTypeEnum
from fw.documents.address_enums import DistrictTypeEnum
from fw.documents.address_enums import CityTypeEnum
from fw.documents.address_enums import StreetTypeEnum
from fw.documents.address_enums import HouseTypeEnum
from fw.documents.address_enums import BuildingTypeEnum
from fw.documents.address_enums import FlatTypeEnum
from fw.documents.db_fields import PrivatePersonDbObject, CompanyDbObject, DocumentBatchDbObject, BatchDocumentDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentBatchTypeEnum, DocumentTypeEnum, PersonDocumentTypeEnum, BatchStatusEnum, \
    CurrencyEnum
from fw.documents.fields.doc_fields import DocumentBatch
from services.ifns.data_model.models import IfnsBookingObject
from test_api import authorized
from test_pack.base_batch_test import BaseBatchTestCase


class RenderingTestCase(BaseBatchTestCase):
    @authorized()
    def test_general_manager_contract(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_GENERAL_MANAGER_CONTRACT, DocumentTypeEnum.DT_ARTICLES]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
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
                "issue_date": datetime.now(),
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
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder)
        sqldb.session.commit()

        founder_otvetstvennyi = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Семен",
            "surname": u"Семенчук",
            "patronymic": u"Семейкин",
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
        sqldb.session.add(founder_otvetstvennyi)
        sqldb.session.commit()

        company_founder = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"Том и Джери",
            "short_name": u"ТиД",
            "general_manager": {
                "_id": founder.id,
                "type": "person"
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
        sqldb.session.add(company_founder)
        sqldb.session.commit()

        doc_data = {
            u"full_name": u"Питер-сервис",
            u"short_name": u"Питер-сервис",
            u"inn": "781108730780",
            u"kpp": "999999999",
            u"general_manager_term": 38,
            u"has_general_manager_contract": True,
            u"general_manager_caption": u"повелитель",
            u"general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            u"founders": [
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 12312.22,
                    "share": 100
                }
            ],
            u"general_manager_salary": {
                "currency": CurrencyEnum.CE_RUS_RUBLES,
                "value": "123123.00"
            },
            u"general_manager_fixed_working_hours": True,
            u"general_manager_working_hours": {
                u"start_working_hours": datetime(1900, 1, 1, hour=8),
                u"finish_working_hours": datetime(1900, 1, 1, hour=16, minute=10),
                u"holidays": ["sun", "sat"],
                u"lunch_time": 10
            },
            u"general_manager_trial_period": 24,
            u"general_manager_quit_notify_period": 12,
            u"general_manager_contract_number": "2",
            u"selected_moderator": {
                "type": "company",
                "_id": company_founder.id
            },
            u"general_manager_salary_days": [10, 25],
            u"address": {
                "district_type": u"р-н",
                "city_type": u"г",
                "street_type": u"ул",
                "index": 191186,
                "house": u"4",
                "region": u"Санкт-Петербург",
                "flat": u"12",
                "building_type": u"к",
                "street": u"Большая Морская",
                "address_string": u"г Санкт-Петербург, ул Большая Морская, д 4, кв 12",
                "flat_type": u"кв",
                "house_type": u"д",
                "village_type": u"п",
                "ifns": 7841
            },
            u"address_type": "general_manager_registration_address",
            u"general_manager_contract_date": datetime.now(),
            u"general_manager_has_special_terms": False,
            # u"general_manager_contract_additional_terms" : {
            #                u"rights" : ["Право 1", "Право 2"],
            #                u"responsibility" : ["Респ 1", "Респ 2"],
            #                u"duties" : [u"колоть дрова", "к2"]
            #            },
            u"board_of_directors": True,
            u"registration_date": datetime.now()
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_FINALISED,
                paid=True,
                data={
                    "full_name": u"Пни и Кочки"
                },
                result_fields={
                    'ifns_reg_info': {
                        'ogrn': "1234567890123"
                    }
                },
                _owner=self.user
            )
            sqldb.session.add(batch)

            doc = BatchDocumentDbObject(
                _owner=self.user,
                document_type="articles",
                batch=batch,
                data={
                    "job_main_code": "50.20",
                    "use_national_language_company_name": False,
                    "use_foreign_company_name": False,
                    "pravo_otchuzhdeniya_type": 3,
                    "general_manager_term": 36,
                    "short_name": u"Питер-сервис",
                    "preimusch_pravo_priobreteniya_doli_time_span": 30,
                    "address": {
                        "building": "20",
                        "index": 117105,
                        "street_type": "ш",
                        "house": "12Г",
                        "region": "Москва",
                        "okato": 12122222222,
                        "address_string": "г Москва, Варшавское шоссе, д 12Г стр 20",
                        "building_type": "стр",
                        "street": "Варшавское",
                        "house_type": "д",
                        "ifns": 7726
                    },
                    "perehod_doli_k_naslednikam_soglasie": True,
                    "necessary_votes_for_general_meeting_decisions": {
                        "audit_assignment": 1,
                        "large_deals_approval": 1,
                        "concern_deals_approval": 1,
                        "executives_formation": 1,
                        "other_issues": 1,
                        "articles_change": 1,
                        "branch_establishment": 1,
                        "profit_distribution": 1,
                        "annual_reports_approval": 1,
                        "liquidation_committee_assignment": 1,
                        "auditor_election": 1,
                        "obligations_emission": 1,
                        "reorganization_or_liquidation": 1,
                        "internal_documents_approval": 1,
                        "company_strategy": 1
                    },
                    "starter_capital": {
                        "capital_type": 1,
                        "value": {
                            "currency": "RUB",
                            "value": "10000"
                        }
                    },
                    "general_manager_caption": "Генеральный директор",
                    "doc_date": datetime.now(),
                    "full_name": u"Питер-сервис",
                    "job_code_array": [
                        "52.48.39",
                        "50.30",
                        "50.40",
                        "51.44.4"
                    ],
                    "board_of_directors": False,
                    "founders_count": 2,
                    "board_of_directors_caption": "Совет директоров"
                }
            )
            sqldb.session.add(doc)
            sqldb.session.commit()
            _id = batch.id

            booking = IfnsBookingObject(reg_info={
                'status': 'registered',
                'reg_date': datetime.now(),
                'ogrn': "123456789012345"
            }, batch_id=_id)
            sqldb.session.add(booking)

            # result = self.test_client.post('/batch/update/', data={
            #     'batch_id': _id,
            #     'batch': batch_json
            # })
            # self.assertEqual(result.status_code, 200)

            sqldb.session.commit()
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            doc_data = {
                "inn": u"7811554010", u"kpp": 
                u"781101001",
                 u"address": {"qc": u"0", u"city": u"Петергоф", u"flat": u"15", u"ifns": u"7819", u"house": u"3",
                             u"index": 198510, u"okato": u"40290501000", u"region": u"Санкт-Петербург",
                             u"street": u"Аврова", u"city_type": u"г", u"flat_type": u"кв", u"house_type": u"д",
                             u"qc_complete": u"10", u"street_type": u"пл",
                             u"address_string": u"г Санкт-Петербург, г Петергоф, пл Аврова, д 3, кв 15",
                             u"long_form_mode": False}, 
                u"founders": [{
                    u"share": u"100", 
                    u"founder": {"_id": founder_otvetstvennyi.id, u"type": u"person"},
                    u"nominal_capital": {"value": u"10000", u"currency": u"RUB"}
                }], 
                u"tax_type": 2, u"full_name": u"Питер-сервис",
                             u"obtain_way": u"mail", u"share_type": u"percent", u"short_name": u"Питер-сервис",
                             u"address_type": u"office_address", u"job_main_code": u"05.01", u"taxation_type": u"usn",
                             u"address_person": {"_id": founder_otvetstvennyi.id, u"type": u"person"},
                             u"job_code_array": ["15.20", u"15.41.1", u"51.38.1", u"52.23"],
                             u"general_manager": {"_id": founder_otvetstvennyi.id, u"type": u"person"},
                             u"starter_capital": {"value": u"10000", u"currency": u"RUB"}, u"registration_way": u"notary",
                             u"registration_date": datetime.now(),
                             u"board_of_directors": False, u"address_other_owner": False, u"general_manager_term": 36,
                             u"general_manager_salary": {"value": u"12", u"currency": u"RUB"},
                             u"general_manager_caption": u"Генеральный директор", u"pravo_otchuzhdeniya_type": 1,
                             u"use_foreign_company_name": False, u"has_general_manager_order": True,
                             u"board_of_directors_caption": u"Совет директоров", u"general_manager_salary_days": [10],
                             u"general_manager_order_number": u"01", u"general_manager_trial_period": 6,
                             u"has_general_manager_contract": True,
                             u"general_manager_contract_date": datetime.now(),
                             u"general_manager_contract_number": u"01", u"general_manager_quit_notify_period": 1,
                             u"use_national_language_company_name": False, u"general_manager_fixed_working_hours": False,
                             u"perehod_doli_k_naslednikam_soglasie": True,
                             u"preimusch_pravo_priobreteniya_doli_time_span": 30,
                             u"necessary_votes_for_general_meeting_decisions": {"other_issues": 1, u"articles_change": 1,
                                                                               u"audit_assignment": 1,
                                                                               u"auditor_election": 1,
                                                                               u"company_strategy": 1,
                                                                               u"profit_distribution": 1,
                                                                               u"branch_establishment": 1,
                                                                               u"executives_formation": 1,
                                                                               u"large_deals_approval": 1,
                                                                               u"obligations_emission": 1,
                                                                               u"concern_deals_approval": 1,
                                                                               u"annual_reports_approval": 1,
                                                                               u"internal_documents_approval": 1,
                                                                               u"reorganization_or_liquidation": 1,
                                                                               u"liquidation_committee_assignment": 1}}
            db_batch.result_fields = {"ifns": u"7819", u"ifns_reg_info": {"ogrn": u"1157800121990", u"status": u"registered",
                                                                        u"reg_date": datetime.now(),
                                                                        u"full_name": u"Питер-Сервис"},
                                      u"first_work_day": u"2013-06-17",
                                      u"founder_applicant": u"%s_person" % founder_otvetstvennyi.id,
                                      u"registration_address": {"qc": u"0", u"city": u"Петергоф", u"flat": u"15",
                                                               u"ifns": u"7819", u"house": u"3", u"index": u"198510",
                                                               u"okato": u"40290501000", u"region": u"Санкт-Петербург",
                                                               u"street": u"Аврова", u"city_type": u"г", u"flat_type": u"кв",
                                                               u"house_type": u"д", u"qc_complete": u"10",
                                                               u"street_type": u"пл",
                                                               u"address_string": u"г Санкт-Петербург, г Петергоф, пл Аврова, д 3, кв 15",
                                                               u"long_form_mode": u"False"},
                                      u"general_manager_caption_genitive": u"генерального директора"}
            db_batch.error_info = {"error_ext": [{"field": u"general_manager_term", u"error_code": 4},
                                                   {"field": u"general_manager_contract_number", u"error_code": 4},
                                                   {"field": u"ogrn", u"error_code": 4},
                                                   {"field": u"inn", u"error_code": 4},
                                                   {"field": u"full_name", u"error_code": 4},
                                                   {"field": u"board_of_directors", u"error_code": 4},
                                                   {"field": u"general_manager_fixed_working_hours", u"error_code": 4},
                                                   {"field": u"general_manager_trial_period", u"error_code": 4},
                                                   {"field": u"general_manager_contract_date", u"error_code": 4},
                                                   {"field": u"address_type", u"error_code": 4},
                                                   {"field": u"data", u"error_code": 4},
                                                   {"field": u"short_name", u"error_code": 4},
                                                   {"field": u"general_manager_quit_notify_period", u"error_code": 4},
                                                   {"field": u"general_manager_salary_days", u"error_code": 4},
                                                   {"field": u"kpp", u"error_code": 4},
                                                   {"field": u"general_manager", u"error_code": 4},
                                                   {"field": u"general_manager_caption", u"error_code": 4},
                                                   {"field": u"general_manager_order_number", u"error_code": 4}]} 

            db_batch.data = doc_data
            sqldb.session.commit()

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': _id,
                'document_type': json.dumps([DocumentTypeEnum.DT_GENERAL_MANAGER_CONTRACT])
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            doc_data['inn'] = ''
            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            doc_data['inn'] = u'7811554010'
            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            # self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            # self.assertEqual(len(db_batch._documents), 2)
            #
            # batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            # batch_json = json.dumps(batch.get_api_structure())
            # result = self.test_client.post('/batch/update/', data={
            #     'batch_id': _id,
            #     'batch': batch_json
            # })
            # self.assertEqual(result.status_code, 200)
            #
            # db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            # self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            # self.assertEqual(len(db_batch._documents), 2)
            # # self.assertTrue(not not db_batch.rendered_docs[1]['file_link'])
            #
            # print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

    @authorized()
    def test_general_manager_order(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_GENERAL_MANAGER_ORDER]
        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
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
                "issue_date": datetime.now(),
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
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder)

        founder_otvetstvennyi = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Семен",
            "surname": u"Семенчук",
            "patronymic": u"Семейкин",
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
        sqldb.session.add(founder_otvetstvennyi)

        company_founder = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"Том и Джери",
            "short_name": u"ТиД",
            "general_manager": {
                "_id": founder.id,
                "type": "person"
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
        sqldb.session.add(company_founder)
        sqldb.session.commit()

        doc_data = {
            u"full_name": u"Рога и Копыта",
            u"short_name": u"РиК",
            u"inn": "781108730780",
            u"kpp": "999999999",
            u"general_manager_term": 38,
            u"has_general_manager_contract": True,
            u"has_general_manager_order": True,
            u"general_manager_caption": u"директор",
            u"general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            u"founders": [
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 12312.22,
                    "share": 100
                }
            ],
            u"general_manager_salary": {
                "currency": CurrencyEnum.CE_RUS_RUBLES,
                "value": "123123.00"
            },
            u"general_manager_fixed_working_hours": True,
            # u"general_manager_working_hours" : {
            # u"start_working_hours" : datetime.now(),
            #     u"finish_working_hours" : datetime.now() + timedelta(hours = 8),
            #     u"holidays" : ["mon", "tue", "fri"],
            #     u"lunch_time" : 10
            # },
            u"general_manager_trial_period": 24,
            u"general_manager_quit_notify_period": 12,
            # u"general_manager_contract_number" : "2",
            u"general_manager_order_number": "1",
            u"selected_moderator": {
                "type": "company",
                "_id": company_founder.id
            },
            u"general_manager_salary_days": [1, 2, 3, 4, 5],
            u"address": {
                #"district_type" : u"р-н",
                #"city_type" : u"г",
                "street_type": u"ул",
                "index": 191186,
                "house": u"4",
                "region": u"Санкт-Петербург",
                "flat": u"12",
                #"building_type" : u"к",
                "street": u"Большая Морская",
                "address_string": u"г Санкт-Петербург, ул Большая Морская, д 4, кв 12",
                "flat_type": u"кв",
                "house_type": u"д",
                #"village_type" : u"п",
                "ifns": 7841
            },
            u"address_type": "office_address",
            u"general_manager_contract_date" : datetime.now(),
            # u"general_manager_contract_additional_terms" : {
            #     u"rights" : "",
            #     u"responsibility" : None,
            #     u"duties" : u"колоть дрова"
            # },
            u"board_of_directors": True,
            u"registration_date": datetime.now()
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_FINALISED,
                data={},
                _owner=self.user,
                result_fields={
                    'ifns_reg_info': {
                        'ogrn': "1234567890123"
                    }
                }
            )
            sqldb.session.add(batch)

            doc = BatchDocumentDbObject(
                _owner=self.user,
                document_type="articles",
                batch=batch,
                data={
                    "job_main_code": "50.20",
                    "use_national_language_company_name": False,
                    "use_foreign_company_name": False,
                    "pravo_otchuzhdeniya_type": 3,
                    "general_manager_term": 36,
                    "short_name": "а",
                    "preimusch_pravo_priobreteniya_doli_time_span": 30,
                    "address": {
                        "building": "20",
                        "index": 117105,
                        "street_type": "ш",
                        "house": "12Г",
                        "region": "Москва",
                        "okato": 12122222222,
                        "address_string": "г Москва, Варшавское шоссе, д 12Г стр 20",
                        "building_type": "стр",
                        "street": "Варшавское",
                        "house_type": "д",
                        "ifns": 7726
                    },
                    "perehod_doli_k_naslednikam_soglasie": True,
                    "necessary_votes_for_general_meeting_decisions": {
                        "audit_assignment": 1,
                        "large_deals_approval": 1,
                        "concern_deals_approval": 1,
                        "executives_formation": 1,
                        "other_issues": 1,
                        "articles_change": 1,
                        "branch_establishment": 1,
                        "profit_distribution": 1,
                        "annual_reports_approval": 1,
                        "liquidation_committee_assignment": 1,
                        "auditor_election": 1,
                        "obligations_emission": 1,
                        "reorganization_or_liquidation": 1,
                        "internal_documents_approval": 1,
                        "company_strategy": 1
                    },
                    "starter_capital": {
                        "capital_type": 1,
                        "value": {
                            "currency": "RUB",
                            "value": "10000"
                        }
                    },
                    "general_manager_caption": "Генеральный директор",
                    "doc_date": datetime.now(),
                    "full_name": "аи",
                    "job_code_array": [
                        "52.48.39",
                        "50.30",
                        "50.40",
                        "51.44.4"
                    ],
                    "board_of_directors": False,
                    "founders_count": 2,
                    "board_of_directors_caption": "Совет директоров"
                }
            )
            sqldb.session.add(doc)
            sqldb.session.commit()

            doc = BatchDocumentDbObject(
                _owner=self.user,
                document_type=DocumentTypeEnum.DT_DECISION,
                batch=batch,
                data={
                    "job_main_code": "50.20",
                    "use_national_language_company_name": False,
                    "use_foreign_company_name": False,
                    "pravo_otchuzhdeniya_type": 3,
                    "general_manager_term": 36,
                    "short_name": "а",
                    "preimusch_pravo_priobreteniya_doli_time_span": 30,
                    "address": {
                        "building": "20",
                        "index": 117105,
                        "street_type": "ш",
                        "house": "12Г",
                        "region": "Москва",
                        "okato": 12122222222,
                        "address_string": "г Москва, Варшавское шоссе, д 12Г стр 20",
                        "building_type": "стр",
                        "street": "Варшавское",
                        "house_type": "д",
                        "ifns": 7726
                    },
                    "starter_capital": {
                        "capital_type": 1,
                        "value": {
                            "currency": "RUB",
                            "value": "10000"
                        }
                    },
                    "general_manager_caption": "Генеральный директор",
                    "doc_date": datetime.now(),
                    "full_name": "аи",
                    "job_code_array": [
                        "52.48.39",
                        "50.30",
                        "50.40",
                        "51.44.4"
                    ],
                    "board_of_directors": False,
                    "founders_count": 2,
                    "board_of_directors_caption": "Совет директоров",
                    u"general_manager": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                }
            )
            sqldb.session.add(doc)
            sqldb.session.commit()
            _id = batch.id

            booking = IfnsBookingObject(reg_info={
                'status': 'registered',
                'reg_date': datetime.now(),
                'ogrn': "123456789012345"
            }, batch_id=_id)
            sqldb.session.add(booking)
            sqldb.session.commit()

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': _id,
                'document_type': json.dumps([DocumentTypeEnum.DT_GENERAL_MANAGER_ORDER])
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 3)

    @authorized()
    def test_accountant_contract(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_ACCOUNTANT_CONTRACT]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
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
                "issue_date": datetime.now(),
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
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder)

        founder_otvetstvennyi = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Нарцисса",
            "surname": u"Сизова",
            "patronymic": u"Октаэдровна",
            "inn": "781108730780",
            "sex": "female",
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
        sqldb.session.add(founder_otvetstvennyi)

        company_founder = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"Том и Джери",
            "short_name": u"ТиД",
            "general_manager": {
                "_id": founder.id
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
        sqldb.session.add(company_founder)

        doc_data = {
            u"full_name": u"Рога—Копыт'а №3",
            u"short_name": u"РиК",
            u"inn": "781108730780",
            u"kpp": "999999999",
            u"has_accountant_contract_order": True,
            u"accountant_contract_number": "023",
            u"general_manager_contract_number": "01",
            u"general_manager_caption": u"директор",
            u"general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            u"accountant_person": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            u"founders": [
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 12312.22,
                    "share": 100
                }
            ],
            u"accountant_salary": {
                "currency": CurrencyEnum.CE_RUS_RUBLES,
                "value": "123123.00"
            },
            u"accountant_fixed_working_hours": True,
            u"accountant_working_hours": {
                u"start_working_hours": datetime(1900, 1, 1, hour=8),
                u"finish_working_hours": datetime(1900, 1, 1, hour=16, minute=10),
                u"holidays": ["tue", "fri"],
                u"lunch_time": 10
            },
            u"accountant_trial_period": 24,
            u"accountant_quit_notify_period": 12,
            u"accountant_order_number": "01",
            u"selected_moderator": {
                "type": "company",
                "_id": company_founder
            },
            u"accountant_salary_days": [1, 2, 3, 4, 5],
            u"address": {
                # "district_type" : u"р-н",
                #"city_type" : u"г",
                "street_type": u"ул",
                "index": 191186,
                "house": u"4",
                "region": u"Санкт-Петербург",
                "flat": u"12",
                #"building_type" : u"к",
                "street": u"Большая Морская",
                "address_string": u"г Санкт-Петербург, ул Большая Морская, д 4, кв 12",
                "flat_type": u"кв",
                "house_type": u"д",
                #"village_type" : u"п",
                "ifns": 7841
            },
            u"address_type": "office_address",
            u"accountant_has_special_terms": True,
            u"accountant_contract_additional_terms": {
                u"rights": [],
                u"responsibility": [],
                u"duties": [u"колоть дрова", u"молоть муку"]
            },
            u"board_of_directors": True,
            u"registration_date": datetime.now(),
            u"accountant_start_work": datetime.now(),
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_FINALISED,
                _documents=[{
                    "status": "rendered",
                    "deleted": False,
                    "rendered_docs": [],
                    "document_type": "articles",
                    "data": {
                        "job_main_code": "50.20",
                        "use_national_language_company_name": False,
                        "use_foreign_company_name": False,
                        "pravo_otchuzhdeniya_type": 3,
                        "general_manager_term": 36,
                        "short_name": "а",
                        "preimusch_pravo_priobreteniya_doli_time_span": 30,
                        "address": {
                            "building": "20",
                            "index": 117105,
                            "street_type": "ш",
                            "house": "12Г",
                            "region": "Москва",
                            "okato": 12122222222,
                            "address_string": "г Москва, Варшавское шоссе, д 12Г стр 20",
                            "building_type": "стр",
                            "street": "Варшавское",
                            "house_type": "д",
                            "ifns": 7726
                        },
                        "perehod_doli_k_naslednikam_soglasie": True,
                        "necessary_votes_for_general_meeting_decisions": {
                            "audit_assignment": 1,
                            "large_deals_approval": 1,
                            "concern_deals_approval": 1,
                            "executives_formation": 1,
                            "other_issues": 1,
                            "articles_change": 1,
                            "branch_establishment": 1,
                            "profit_distribution": 1,
                            "annual_reports_approval": 1,
                            "liquidation_committee_assignment": 1,
                            "auditor_election": 1,
                            "obligations_emission": 1,
                            "reorganization_or_liquidation": 1,
                            "internal_documents_approval": 1,
                            "company_strategy": 1
                        },
                        "starter_capital": {
                            "capital_type": 1,
                            "value": {
                                "currency": "RUB",
                                "value": "10000"
                            }
                        },
                        "general_manager_caption": "Генеральный директор",
                        "doc_date": datetime.now(),
                        "full_name": "аи",
                        "job_code_array": [
                            "52.48.39",
                            "50.30",
                            "50.40",
                            "51.44.4"
                        ],
                        "board_of_directors": False,
                        "founders_count": 2,
                        "board_of_directors_caption": "Совет директоров",

                    },
                    "id": ObjectId(),
                    "creation_date": datetime.now()
                }],
                data={},
                _owner=self.user,
                result_fields={
                    'ifns_reg_info': {
                        'ogrn': "1234567890123"
                    }
                }
            )
            _id = sqldb.session.add(batch)

            booking = IfnsBookingObject(reg_info={
                'status': 'registered',
                'reg_date': datetime.now(),
                'ogrn': "123456789012345"
            }, batch_id=_id)
            sqldb.session.add(booking)
            sqldb.session.commit()

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': _id,
                'document_type': json.dumps([DocumentTypeEnum.DT_ACCOUNTANT_CONTRACT])
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print(json.dumps(db_batch.as_dict(), indent=4, sort_keys=True, default=lambda x: unicode(x)))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 2)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_accountant_imposition_order(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_ACCOUNTANT_IMPOSITION_ORDER]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 40),
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
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder)

        founder_otvetstvennyi = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Семен",
            "surname": u"Семенчук",
            "patronymic": u"Семейкин",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
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
        sqldb.session.add(founder_otvetstvennyi)

        company_founder = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"Том и Джери",
            "short_name": u"ТиД",
            "general_manager": {
                "_id": founder.id
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
        sqldb.session.add(company_founder)

        doc_data = {
            u"full_name": u"Рога и Копыта",
            u"short_name": u"РиК",
            u"inn": "781108730780",
            u"kpp": "999999999",
            u"general_manager_term": 38,
            u"has_general_manager_contract": False,
            # u"has_general_manager_order": True,
            # u"has_accountant_contract_order": True,
            u"general_manager_as_accountant": True,
            u"general_manager_caption": u"директор",
            u"general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            u"founders": [
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 12312.22,
                    "share": 100
                }
            ],
            # u"general_manager_salary" : {
            # "currency" : CurrencyEnum.CE_RUS_RUBLES,
            #     "value" : "123123.00"
            # },
            # u"general_manager_fixed_working_hours" : True,
            # u"general_manager_working_hours" : {
            #     u"start_working_hours" : datetime.now(),
            #     u"finish_working_hours" : datetime.now() + timedelta(hours = 8),
            #     u"holidays" : ["mon", "tue", "fri"],
            #     u"lunch_time" : 10
            # },
            # u"general_manager_trial_period" : 24,
            # u"general_manager_quit_notify_period" : 12,
            u"general_manager_as_accountant_order_number": "01К",
            # u"general_manager_order_number": "01",
            # u"selected_moderator" : {
            #     "type" : "company",
            #     "_id" : company_founder._id
            # },
            # u"general_manager_salary_days" : [1,2,3,4,5],
            u"address": {
                #"district_type" : u"р-н",
                #"city_type" : u"г",
                "street_type": u"ул",
                "index": 191186,
                "house": u"4",
                "region": u"Санкт-Петербург",
                "flat": u"12",
                #"building_type" : u"к",
                "street": u"Большая Морская",
                "address_string": u"г Санкт-Петербург, ул Большая Морская, д 4, кв 12",
                "flat_type": u"кв",
                "house_type": u"д",
                #"village_type" : u"п",
                "ifns": 7841
            },
            u"address_type": "office_address",
            #u"general_manager_contract_date" : datetime.now(),
            # u"general_manager_contract_additional_terms" : {
            #     u"rights" : "",
            #     u"responsibility" : None,
            #     u"duties" : u"колоть дрова"
            # },
            u"board_of_directors": True,
            u"registration_date": datetime.now()
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_FINALISED,
                _documents=[{
                                "status": "rendered",
                                "deleted": False,
                                "rendered_docs": [],
                                "document_type": "articles",
                                "data": {
                                    "job_main_code": "50.20",
                                    "use_national_language_company_name": False,
                                    "use_foreign_company_name": False,
                                    "pravo_otchuzhdeniya_type": 3,
                                    "general_manager_term": 36,
                                    "short_name": "а",
                                    "preimusch_pravo_priobreteniya_doli_time_span": 30,
                                    "address": {
                                        "building": "20",
                                        "index": 117105,
                                        "street_type": "ш",
                                        "house": "12Г",
                                        "region": "Москва",
                                        "okato": 12122222222,
                                        "address_string": "г Москва, Варшавское шоссе, д 12Г стр 20",
                                        "building_type": "стр",
                                        "street": "Варшавское",
                                        "house_type": "д",
                                        "ifns": 7726
                                    },
                                    "perehod_doli_k_naslednikam_soglasie": True,
                                    "necessary_votes_for_general_meeting_decisions": {
                                        "audit_assignment": 1,
                                        "large_deals_approval": 1,
                                        "concern_deals_approval": 1,
                                        "executives_formation": 1,
                                        "other_issues": 1,
                                        "articles_change": 1,
                                        "branch_establishment": 1,
                                        "profit_distribution": 1,
                                        "annual_reports_approval": 1,
                                        "liquidation_committee_assignment": 1,
                                        "auditor_election": 1,
                                        "obligations_emission": 1,
                                        "reorganization_or_liquidation": 1,
                                        "internal_documents_approval": 1,
                                        "company_strategy": 1
                                    },
                                    "starter_capital": {
                                        "capital_type": 1,
                                        "value": {
                                            "currency": "RUB",
                                            "value": "10000"
                                        }
                                    },
                                    "general_manager_caption": "Генеральный директор",
                                    "doc_date": datetime.now(),
                                    "full_name": "аи",
                                    "job_code_array": [
                                        "52.48.39",
                                        "50.30",
                                        "50.40",
                                        "51.44.4"
                                    ],
                                    "board_of_directors": False,
                                    "founders_count": 2,
                                    "board_of_directors_caption": "Совет директоров",

                                },
                                "id": ObjectId(),
                                "creation_date": datetime.now()
                            }],
                data={},
                _owner=self.user,
                result_fields={
                    'ifns_reg_info': {
                        'ogrn': "1234567890123"
                    }
                }
            )
            _id = sqldb.session.add(batch)

            booking = IfnsBookingObject(reg_info={
                'status': 'registered',
                'reg_date': datetime.now(),
                'ogrn': "123456789012345"
            }, batch_id=_id)
            sqldb.session.add(booking)
            sqldb.session.commit()

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': _id,
                'document_type': json.dumps([DocumentTypeEnum.DT_ACCOUNTANT_IMPOSITION_ORDER])
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            # print(json.dumps(db_batch.as_dict(), indent=4, sort_keys=True, default=lambda x:unicode(x)))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 2)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_rosstat_claim(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_ROSSTAT_CLAIM]
        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
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
                "issue_date": datetime.now(),
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
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder)

        founder_otvetstvennyi = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Семен",
            "surname": u"Семенчук",
            "patronymic": u"Семейкин",
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
        sqldb.session.add(founder_otvetstvennyi)

        company_founder = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"Том и Джери",
            "short_name": u"ТиД",
            "general_manager": {
                "_id": founder.id
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
        sqldb.session.add(company_founder)

        doc_data = {
            u"full_name": u"Рога и Копыта",
            u"short_name": u"РиК",
            u"inn": "781108730780",
            u"kpp": "999999999",
            u"general_manager_term": 38,
            # u"has_general_manager_contract" : True,
            # u"has_general_manager_order": True,
            # u"has_accountant_contract_order": True,
            # u"general_manager_as_accountant": True,
            u"general_manager_caption": u"директор",
            u"general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            u"founders": [
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 12312.22,
                    "share": 100
                }
            ],
            u"general_manager_salary": {
                "currency": CurrencyEnum.CE_RUS_RUBLES,
                "value": "123123.00"
            },
            u"general_manager_fixed_working_hours": True,
            u"general_manager_working_hours": {
                u"start_working_hours": datetime.now(),
                u"finish_working_hours": datetime.now() + timedelta(hours=8),
                u"holidays": ["mon", "tue", "fri"],
                u"lunch_time": 10
            },
            u"general_manager_trial_period": 24,
            u"general_manager_quit_notify_period": 12,
            # u"general_manager_contract_number" : "2",
            u"general_manager_order_number": "01",
            u"selected_moderator": {
                "type": "company",
                "_id": company_founder
            },
            u"general_manager_salary_days": [1, 2, 3, 4, 5],
            u"address": {
                # "district_type" : u"р-н",
                #"city_type" : u"г",
                "street_type": u"ул",
                "index": 191186,
                "house": u"4",
                "region": u"Санкт-Петербург",
                "flat": u"12",
                #"building_type" : u"к",
                "street": u"Большая Морская",
                "address_string": u"г Санкт-Петербург, ул Большая Морская, д 4, кв 12",
                "flat_type": u"кв",
                "house_type": u"д",
                #"village_type" : u"п",
                "ifns": 7841
            },
            u"address_type": "office_address",
            # u"general_manager_contract_date" : datetime.now(),
            # u"general_manager_contract_additional_terms" : {
            # u"rights" : "",
            #     u"responsibility" : None,
            #     u"duties" : u"колоть дрова"
            # },
            u"board_of_directors": True,
            u"registration_date": datetime.now()
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_FINALISED,
                _documents=[{
                                "status": "rendered",
                                "deleted": False,
                                "rendered_docs": [],
                                "document_type": "articles",
                                "data": {
                                    "job_main_code": "50.20",
                                    "use_national_language_company_name": False,
                                    "use_foreign_company_name": False,
                                    "pravo_otchuzhdeniya_type": 3,
                                    "general_manager_term": 36,
                                    "short_name": "а",
                                    "preimusch_pravo_priobreteniya_doli_time_span": 30,
                                    "address": {
                                        "building": "20",
                                        "index": 117105,
                                        "street_type": "ш",
                                        "house": "12Г",
                                        "region": "Москва",
                                        "okato": 12122222222,
                                        "address_string": "г Москва, Варшавское шоссе, д 12Г стр 20",
                                        "building_type": "стр",
                                        "street": "Варшавское",
                                        "house_type": "д",
                                        "ifns": 7726
                                    },
                                    "perehod_doli_k_naslednikam_soglasie": True,
                                    "necessary_votes_for_general_meeting_decisions": {
                                        "audit_assignment": 1,
                                        "large_deals_approval": 1,
                                        "concern_deals_approval": 1,
                                        "executives_formation": 1,
                                        "other_issues": 1,
                                        "articles_change": 1,
                                        "branch_establishment": 1,
                                        "profit_distribution": 1,
                                        "annual_reports_approval": 1,
                                        "liquidation_committee_assignment": 1,
                                        "auditor_election": 1,
                                        "obligations_emission": 1,
                                        "reorganization_or_liquidation": 1,
                                        "internal_documents_approval": 1,
                                        "company_strategy": 1
                                    },
                                    "starter_capital": {
                                        "capital_type": 1,
                                        "value": {
                                            "currency": "RUB",
                                            "value": "10000"
                                        }
                                    },
                                    "general_manager_caption": "Генеральный директор",
                                    "doc_date": datetime.now(),
                                    "full_name": "аи",
                                    "job_code_array": [
                                        "52.48.39",
                                        "50.30",
                                        "50.40",
                                        "51.44.4"
                                    ],
                                    "board_of_directors": False,
                                    "founders_count": 2,
                                    "board_of_directors_caption": "Совет директоров",

                                },
                                "id": ObjectId(),
                                "creation_date": datetime.now()
                            }],
                data={},
                _owner=self.user,
                result_fields={
                    'ifns_reg_info': {
                        'ogrn': "1234567890123"
                    }
                }
            )
            _id = sqldb.session.add(batch)

            booking = IfnsBookingObject(reg_info={
                'status': 'registered',
                'reg_date': datetime.now(),
                'ogrn': "123456789012345"
            }, batch_id=_id)
            sqldb.session.add(booking)
            sqldb.session.commit()

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': _id,
                'document_type': json.dumps([DocumentTypeEnum.DT_ROSSTAT_CLAIM])
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            # print(json.dumps(db_batch.as_dict(), indent=4, sort_keys=True, default=lambda x:unicode(x)))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 2)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_fss_claim(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_FSS_CLAIM]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
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
                "issue_date": datetime.now(),
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
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder)

        founder_otvetstvennyi = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Семен",
            "surname": u"Семенчук",
            "patronymic": u"Семейкин",
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
        sqldb.session.add(founder_otvetstvennyi)

        company_founder = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"Том и Джери",
            "short_name": u"ТиД",
            "general_manager": {
                "_id": founder.id
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
        sqldb.session.add(company_founder)

        doc_data = {
            u"full_name": u"Рога и Копыта",
            u"short_name": u"РиК",
            u"inn": "781108730780",
            u"kpp": "999999999",
            u"general_manager_term": 38,
            # u"has_general_manager_contract" : True,
            # u"has_general_manager_order": True,
            # u"has_accountant_contract_order": True,
            # u"general_manager_as_accountant": True,
            u"general_manager_caption": u"директор",
            u"general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            u"founders": [
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 12312.22,
                    "share": 100
                }
            ],
            u"general_manager_salary": {
                "currency": CurrencyEnum.CE_RUS_RUBLES,
                "value": "123123.00"
            },
            u"general_manager_fixed_working_hours": True,
            u"general_manager_working_hours": {
                u"start_working_hours": datetime.now(),
                u"finish_working_hours": datetime.now() + timedelta(hours=8),
                u"holidays": ["mon", "tue", "fri"],
                u"lunch_time": 10
            },
            u"general_manager_trial_period": 24,
            u"general_manager_quit_notify_period": 12,
            # u"general_manager_contract_number" : "2",
            u"general_manager_order_number": "01",
            u"selected_moderator": {
                "type": "company",
                "_id": company_founder
            },
            u"general_manager_salary_days": [1, 2, 3, 4, 5],
            u"address": {
                # "district_type" : u"р-н",
                #"city_type" : u"г",
                "street_type": u"ул",
                "index": 191186,
                "house": u"4",
                "region": u"Санкт-Петербург",
                "flat": u"12",
                #"building_type" : u"к",
                "street": u"Большая Морская",
                "address_string": u"г Санкт-Петербург, ул Большая Морская, д 4, кв 12",
                "flat_type": u"кв",
                "house_type": u"д",
                #"village_type" : u"п",
                "ifns": 7841
            },
            u"address_type": "office_address",
            # u"general_manager_contract_date" : datetime.now(),
            # u"general_manager_contract_additional_terms" : {
            # u"rights" : "",
            #     u"responsibility" : None,
            #     u"duties" : u"колоть дрова"
            # },
            u"board_of_directors": True,
            u"registration_date": datetime.now()
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_FINALISED,
                _documents=[{
                                "status": "rendered",
                                "deleted": False,
                                "rendered_docs": [],
                                "document_type": "articles",
                                "data": {
                                    "job_main_code": "50.20",
                                    "use_national_language_company_name": False,
                                    "use_foreign_company_name": False,
                                    "pravo_otchuzhdeniya_type": 3,
                                    "general_manager_term": 36,
                                    "short_name": "а",
                                    "preimusch_pravo_priobreteniya_doli_time_span": 30,
                                    "address": {
                                        "building": "20",
                                        "index": 117105,
                                        "street_type": "ш",
                                        "house": "12Г",
                                        "region": "Москва",
                                        "okato": 12122222222,
                                        "address_string": "г Москва, Варшавское шоссе, д 12Г стр 20",
                                        "building_type": "стр",
                                        "street": "Варшавское",
                                        "house_type": "д",
                                        "ifns": 7726
                                    },
                                    "perehod_doli_k_naslednikam_soglasie": True,
                                    "necessary_votes_for_general_meeting_decisions": {
                                        "audit_assignment": 1,
                                        "large_deals_approval": 1,
                                        "concern_deals_approval": 1,
                                        "executives_formation": 1,
                                        "other_issues": 1,
                                        "articles_change": 1,
                                        "branch_establishment": 1,
                                        "profit_distribution": 1,
                                        "annual_reports_approval": 1,
                                        "liquidation_committee_assignment": 1,
                                        "auditor_election": 1,
                                        "obligations_emission": 1,
                                        "reorganization_or_liquidation": 1,
                                        "internal_documents_approval": 1,
                                        "company_strategy": 1
                                    },
                                    "starter_capital": {
                                        "capital_type": 1,
                                        "value": {
                                            "currency": "RUB",
                                            "value": "10000"
                                        }
                                    },
                                    "general_manager_caption": "Генеральный директор",
                                    "doc_date": datetime.now(),
                                    "full_name": "аи",
                                    "job_code_array": [
                                        "52.48.39",
                                        "50.30",
                                        "50.40",
                                        "51.44.4"
                                    ],
                                    "board_of_directors": False,
                                    "founders_count": 2,
                                    "board_of_directors_caption": "Совет директоров",

                                },
                                "id": ObjectId(),
                                "creation_date": datetime.now()
                            }],
                data={},
                _owner=self.user,
                result_fields={
                    'ifns_reg_info': {
                        'ogrn': "1234567890123"
                    }
                }
            )
            _id = sqldb.session.add(batch)

            booking = IfnsBookingObject(reg_info={
                'status': 'registered',
                'reg_date': datetime.now(),
                'ogrn': "123456789012345"
            }, batch_id=_id)
            sqldb.session.add(booking)
            sqldb.session.commit()

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': _id,
                'document_type': json.dumps([DocumentTypeEnum.DT_FSS_CLAIM])
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            # print(json.dumps(db_batch.as_dict(), indent=4, sort_keys=True, default=lambda x:unicode(x)))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 2)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_pfr_claim(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_PFR_CLAIM]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
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
                "issue_date": datetime.now(),
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
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder)

        founder_otvetstvennyi = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Семен",
            "surname": u"Семенчук",
            "patronymic": u"Семейкин",
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
        sqldb.session.add(founder_otvetstvennyi)

        company_founder = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"Том и Джери",
            "short_name": u"ТиД",
            "general_manager": {
                "_id": founder.id
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
        sqldb.session.add(company_founder)

        doc_data = {
            u"full_name": u"Рога и Копыта",
            u"short_name": u"РиК",
            u"inn": "781108730780",
            u"kpp": "999999999",
            u"general_manager_term": 38,
            # u"has_general_manager_contract" : True,
            # u"has_general_manager_order": True,
            # u"has_accountant_contract_order": True,
            # u"general_manager_as_accountant": True,
            u"general_manager_caption": u"директор",
            u"general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            u"founders": [
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 12312.22,
                    "share": 100
                }
            ],
            # u"general_manager_salary" : {
            # "currency" : CurrencyEnum.CE_RUS_RUBLES,
            #     "value" : "123123.00"
            # },
            # u"general_manager_fixed_working_hours" : True,
            # u"general_manager_working_hours" : {
            #     u"start_working_hours" : datetime.now(),
            #     u"finish_working_hours" : datetime.now() + timedelta(hours = 8),
            #     u"holidays" : ["mon", "tue", "fri"],
            #     u"lunch_time" : 10
            # },
            # u"general_manager_trial_period" : 24,
            # u"general_manager_quit_notify_period" : 12,
            # u"general_manager_contract_number" : "2",
            # u"general_manager_order_number": "01",
            u"selected_moderator": {
                "type": "company",
                "_id": company_founder
            },
            # u"general_manager_salary_days" : [1,2,3,4,5],
            u"address": {
                #"district_type" : u"р-н",
                #"city_type" : u"г",
                "street_type": u"ул",
                "index": 191186,
                "house": u"4",
                "region": u"Санкт-Петербург",
                "flat": u"12",
                #"building_type" : u"к",
                "street": u"Большая Морская",
                "address_string": u"г Санкт-Петербург, ул Большая Морская, д 4, кв 12",
                "flat_type": u"кв",
                "house_type": u"д",
                #"village_type" : u"п",
                "ifns": 7841
            },
            u"address_type": "office_address",
            # u"general_manager_contract_date" : datetime.now(),
            # u"general_manager_contract_additional_terms" : {
            #     u"rights" : "",
            #     u"responsibility" : None,
            #     u"duties" : u"колоть дрова"
            # },
            u"board_of_directors": True,
            u"registration_date": datetime.now()
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_FINALISED,
                _documents=[{
                                "status": "rendered",
                                "deleted": False,
                                "rendered_docs": [],
                                "document_type": "articles",
                                "data": {
                                    "job_main_code": "50.20",
                                    "use_national_language_company_name": False,
                                    "use_foreign_company_name": False,
                                    "pravo_otchuzhdeniya_type": 3,
                                    "general_manager_term": 36,
                                    "short_name": "а",
                                    "preimusch_pravo_priobreteniya_doli_time_span": 30,
                                    "address": {
                                        "building": "20",
                                        "index": 117105,
                                        "street_type": "ш",
                                        "house": "12Г",
                                        "region": "Москва",
                                        "okato": 12122222222,
                                        "address_string": "г Москва, Варшавское шоссе, д 12Г стр 20",
                                        "building_type": "стр",
                                        "street": "Варшавское",
                                        "house_type": "д",
                                        "ifns": 7726
                                    },
                                    "perehod_doli_k_naslednikam_soglasie": True,
                                    "necessary_votes_for_general_meeting_decisions": {
                                        "audit_assignment": 1,
                                        "large_deals_approval": 1,
                                        "concern_deals_approval": 1,
                                        "executives_formation": 1,
                                        "other_issues": 1,
                                        "articles_change": 1,
                                        "branch_establishment": 1,
                                        "profit_distribution": 1,
                                        "annual_reports_approval": 1,
                                        "liquidation_committee_assignment": 1,
                                        "auditor_election": 1,
                                        "obligations_emission": 1,
                                        "reorganization_or_liquidation": 1,
                                        "internal_documents_approval": 1,
                                        "company_strategy": 1
                                    },
                                    "starter_capital": {
                                        "capital_type": 1,
                                        "value": {
                                            "currency": "RUB",
                                            "value": "10000"
                                        }
                                    },
                                    "general_manager_caption": "Генеральный директор",
                                    "doc_date": datetime.now(),
                                    "full_name": "аи",
                                    "job_code_array": [
                                        "52.48.39",
                                        "50.30",
                                        "50.40",
                                        "51.44.4"
                                    ],
                                    "board_of_directors": False,
                                    "founders_count": 2,
                                    "board_of_directors_caption": "Совет директоров",

                                },
                                "id": ObjectId(),
                                "creation_date": datetime.now()
                            }],
                data={},
                _owner=self.user,
                result_fields={
                    'ifns_reg_info': {
                        'ogrn': "1234567890123"
                    }
                }
            )
            _id = sqldb.session.add(batch)

            booking = IfnsBookingObject(reg_info={
                'status': 'registered',
                'reg_date': datetime.now(),
                'ogrn': "123456789012345"
            }, batch_id=_id)
            sqldb.session.add(booking)
            sqldb.session.commit()

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': _id,
                'document_type': json.dumps([DocumentTypeEnum.DT_PFR_CLAIM])
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            # print(json.dumps(db_batch.as_dict(), indent=4, sort_keys=True, default=lambda x:unicode(x)))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 2)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])

    @authorized()
    def test_accountant_order(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_ACCOUNTANT_ORDER]
        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
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
                "issue_date": datetime.now(),
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
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder)

        founder_otvetstvennyi = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Семен",
            "surname": u"Семенчук",
            "patronymic": u"Семейкин",
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
        sqldb.session.add(founder_otvetstvennyi)

        company_founder = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"Том и Джери",
            "short_name": u"ТиД",
            "general_manager": {
                "_id": founder.id
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
        sqldb.session.add(company_founder)

        doc_data = {
            u"full_name": u"Пни и Кочки",
            u"short_name": u"ПиК",
            u"has_accountant_contract_order": True,
            u"general_manager_caption": u"повелитель",
            u"accountant_person": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            u"accountant_salary": {
                "currency": CurrencyEnum.CE_RUS_RUBLES,
                "value": "123123.00"
            },
            u"general_manager_fixed_working_hours": True,
            u"general_manager_working_hours": {
                u"start_working_hours": datetime(1900, 1, 1, hour=8),
                u"finish_working_hours": datetime(1900, 1, 1, hour=19),
                u"holidays": ["mon", "tue", "fri"],
                u"lunch_time": 10
            },
            u"accountant_trial_period": 24,
            u"accountant_contract_number": "c3",
            u"accountant_order_number": "o4",
            u"accountant_start_work": datetime.now()
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_FINALISED,
                rendered_docs=[{
                                   'document_type': DocumentTypeEnum.DT_ARTICLES,
                                   'file_link': 'somefile',
                                   'caption': u"Уставчег",
                                   'file_id': ObjectId(),
                                   'document_id': ObjectId("54b91fe7a726163324353311")
                               }],
                _documents=[
                    {
                        "status": "rendered",
                        "deleted": False,
                        "rendered_docs": [],
                        "creation_date": datetime.now(),
                        "document_type": "articles",
                        "data": {
                            "job_main_code": "50.20",
                            "use_national_language_company_name": False,
                            "use_foreign_company_name": False,
                            "pravo_otchuzhdeniya_type": 3,
                            "general_manager_term": 36,
                            "short_name": "а",
                            "preimusch_pravo_priobreteniya_doli_time_span": 30,
                            "address": {
                                "building": "20",
                                "index": 117105,
                                "street_type": "ш",
                                "house": "12Г",
                                "region": "Москва",
                                "okato": 12122222222,
                                "address_string": "г Москва, Варшавское шоссе, д 12Г стр 20",
                                "building_type": "стр",
                                "street": "Варшавское",
                                "house_type": "д",
                                "ifns": 7726
                            },
                            "perehod_doli_k_naslednikam_soglasie": True,
                            "necessary_votes_for_general_meeting_decisions": {
                                "audit_assignment": 1,
                                "large_deals_approval": 1,
                                "concern_deals_approval": 1,
                                "executives_formation": 1,
                                "other_issues": 1,
                                "articles_change": 1,
                                "branch_establishment": 1,
                                "profit_distribution": 1,
                                "annual_reports_approval": 1,
                                "liquidation_committee_assignment": 1,
                                "auditor_election": 1,
                                "obligations_emission": 1,
                                "reorganization_or_liquidation": 1,
                                "internal_documents_approval": 1,
                                "company_strategy": 1
                            },
                            "starter_capital": {
                                "capital_type": 1,
                                "value": {
                                    "currency": "RUB",
                                    "value": "10000"
                                }
                            },
                            "general_manager_caption": "Генеральный директор",
                            "doc_date": datetime.now(),
                            "full_name": "аи",
                            "job_code_array": [
                                "52.48.39",
                                "50.30",
                                "50.40",
                                "51.44.4"
                            ],
                            "board_of_directors": False,
                            "founders_count": 2,
                            "board_of_directors_caption": "Совет директоров"
                        },
                        "id": ObjectId("54b91fe7a726163324353311")
                    }
                ],
                data={},
                _owner=self.user
            )
            _id = sqldb.session.add(batch)

            booking = IfnsBookingObject(reg_info={
                'status': 'registered',
                'reg_date': datetime.now(),
                'ogrn': "123456789012345"
            }, batch_id=_id)
            sqldb.session.add(booking)
            sqldb.session.commit()

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': _id,
                'document_type': json.dumps([DocumentTypeEnum.DT_ACCOUNTANT_ORDER])
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 2)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])


    @authorized()
    def test_founders_list(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_FOUNDERS_LIST]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
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
                "issue_date": datetime.now(),
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
                "ifns": 7805
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder)

        founder_otvetstvennyi = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Семен",
            "surname": u"Семенчук",
            "patronymic": u"Семейкин",
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
                "ifns": 7805
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder_otvetstvennyi)

        company_founder = CompanyDbObject(**{
            "_owner": self.user.id,
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"Том и Джери",
            "short_name": u"ТиД",
            "general_manager": {
                "_id": founder.id
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
                "ifns": 7805
            },
            "phone": "+7(812)1234567"
        })
        sqldb.session.add(company_founder)

        doc_data = {
            u"full_name": u"Пни и Кочки",
            u"short_name": u"ПиК",
            u"inn": "781108730780",
            u"kpp": "999999999",
            u"general_manager_term": 38,
            u"has_general_manager_contract": False,
            u"general_manager_caption": u"повелитель",
            u"general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            u"founders": [
                {
                    "founder": {
                        "_id": company_founder.id,
                        "type": "company"
                    },
                    "nominal_capital": 12312.22,
                    "share": 100
                }
            ],
            "starter_capital": {
                "currency": "rub",
                "value": "12312.234234"
            },
            u"share_type": "percent",
            # u"general_manager_salary" : {
            # "currency" : CurrencyEnum.CE_RUS_RUBLES,
            #     "value" : "123123.00"
            # },
            # u"general_manager_fixed_working_hours" : True,
            # u"general_manager_working_hours" : {
            #     u"start_working_hours" : datetime(1900, 1, 1, hour=8),
            #     u"finish_working_hours" : datetime(1900, 1, 1, hour=19),
            #     u"holidays" : ["mon", "tue", "fri"],
            #     u"lunch_time" : 10
            # },
            # u"general_manager_trial_period" : 24,
            # u"general_manager_quit_notify_period" : 12,
            # u"general_manager_contract_number" : "2",
            u"selected_moderator": {
                "type": "company",
                "_id": company_founder
            },
            u"general_manager_salary_days": [1, 2, 3, 4, 5],
            u"address": {
                "street_type": u"ул",
                "index": 191186,
                "house": u"4",
                "region": u"Санкт-Петербург",
                "flat": u"12",
                "street": u"Большая Морская",
                "address_string": u"г Санкт-Петербург, ул Большая Морская, д 4, кв 12",
                "flat_type": u"кв",
                "house_type": u"д",
                "village_type": u"п",
                "ifns": 7841
            },
            u"address_type": "general_manager_registration_address",
            u"general_manager_contract_date": datetime.now(),
            # u"general_manager_contract_additional_terms" : {
            #     u"rights" : "",
            #     u"responsibility" : None,
            #     u"duties" : u"колоть дрова"
            # },
            u"board_of_directors": True,
            u"registration_date": datetime.now()
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_FINALISED,
                rendered_docs=[{
                                   'document_type': DocumentTypeEnum.DT_ARTICLES,
                                   'file_link': 'somefile',
                                   'caption': u"Уставчег",
                                   'file_id': ObjectId(),
                                   'document_id': ObjectId("54b91fe7a726163324353311")
                               }],
                _documents=[
                    {
                        "status": "rendered",
                        "deleted": False,
                        "rendered_docs": [],
                        "creation_date": datetime.now(),
                        "document_type": "articles",
                        "data": {
                            "job_main_code": "50.20",
                            "use_national_language_company_name": False,
                            "use_foreign_company_name": False,
                            "pravo_otchuzhdeniya_type": 3,
                            "general_manager_term": 36,
                            "short_name": "а",
                            "preimusch_pravo_priobreteniya_doli_time_span": 30,
                            "address": {
                                "building": "20",
                                "index": 117105,
                                "street_type": "ш",
                                "house": "12Г",
                                "region": "Москва",
                                "okato": 12122222222,
                                "address_string": "г Москва, Варшавское шоссе, д 12Г стр 20",
                                "building_type": "стр",
                                "street": "Варшавское",
                                "house_type": "д",
                                "ifns": 7726
                            },
                            "perehod_doli_k_naslednikam_soglasie": True,
                            "necessary_votes_for_general_meeting_decisions": {
                                "audit_assignment": 1,
                                "large_deals_approval": 1,
                                "concern_deals_approval": 1,
                                "executives_formation": 1,
                                "other_issues": 1,
                                "articles_change": 1,
                                "branch_establishment": 1,
                                "profit_distribution": 1,
                                "annual_reports_approval": 1,
                                "liquidation_committee_assignment": 1,
                                "auditor_election": 1,
                                "obligations_emission": 1,
                                "reorganization_or_liquidation": 1,
                                "internal_documents_approval": 1,
                                "company_strategy": 1
                            },
                            "starter_capital": {
                                "capital_type": 1,
                                "value": {
                                    "currency": "RUB",
                                    "value": "10000"
                                }
                            },
                            "general_manager_caption": "Генеральный директор",
                            "doc_date": datetime.now(),
                            "full_name": "аи",
                            "job_code_array": [
                                "52.48.39",
                                "50.30",
                                "50.40",
                                "51.44.4"
                            ],
                            "board_of_directors": False,
                            "founders_count": 2,
                            "board_of_directors_caption": "Совет директоров"
                        },
                        "id": ObjectId("54b91fe7a726163324353311")
                    }
                ],
                data={},
                _owner=self.user,
                result_fields={
                    'ifns_reg_info': {
                        'ogrn': "1234567890123"
                    }
                }
            )
            _id = sqldb.session.add(batch)

            booking = IfnsBookingObject(reg_info={
                'status': 'registered',
                'reg_date': datetime.now(),
                'ogrn': "123456789012345"
            }, batch_id=_id)
            sqldb.session.add(booking)
            sqldb.session.commit()

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': _id,
                'document_type': json.dumps([DocumentTypeEnum.DT_FOUNDERS_LIST])
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 2)
            self.assertTrue(not not db_batch.rendered_docs[0]['file_link'])


    @authorized()
    def test_company_details(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_COMPANY_DETAILS]
        founder = self.create_person(self.user, name=u"Прокл", surname=u"Поликарпов", patronymic=u"Поликарпович")
        # founder = PrivatePersonDbObject(**{
        #     "_owner": self.user,
        #     "name": u"Прокл",
        #     "surname": u"Поликарпов",
        #     "patronymic": u"Поликарпович",
        #     "inn": "781108730780",
        #     "sex": "male",
        #     "birthdate": datetime.now() - timedelta(days=365 * 30),
        #     "birthplace": u"Россия, деревня Гадюкино",
        #     "passport": {
        #         "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
        #         "series": u"1123",
        #         "number": u"192837",
        #         "issue_date": datetime.now(),
        #         "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
        #         "depart_code": u"111987"
        #     },
        #     "ogrnip": "123456789012345",
        #     "address": {
        #         "region": RFRegionsEnum.RFR_SPB,
        #         "index": 198209,
        #         "district_type": DistrictTypeEnum.DIT_DISTRICT,
        #         "district": u"Гатчинский",
        #         "city_type": CityTypeEnum.CIT_CITY,
        #         "city": u"Гадюкино",
        #         "village_type": VillageTypeEnum.VIT_HUTOR,
        #         "village": u"близ Диканьки",
        #         "street_type": StreetTypeEnum.STT_BOULEVARD,
        #         "street": u"Мотоциклистов",
        #         "house_type": HouseTypeEnum.HOT_HOUSE,
        #         "house": "4",
        #         "building_type": BuildingTypeEnum.BIT_HOUSING,
        #         "building": "2",
        #         "flat_type": FlatTypeEnum.FLT_OFFICE,
        #         "flat": "705",
        #     },
        #     "caption": u"Сантехник",
        #     "phone": "+79210001122",
        #     "email": "somebody@domain.zz",
        #     "living_country_code": 3,
        #     "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        # })
        # sqldb.session.add(founder)

        # founder_otvetstvennyi = PrivatePersonDbObject(**{
        #     "_owner": self.user,
        #     "name": u"Семен",
        #     "surname": u"Семенчук",
        #     "patronymic": u"Семейкин",
        #     "inn": "781108730780",
        #     "sex": "male",
        #     "birthdate": datetime.now() - timedelta(days=365 * 30),
        #     "birthplace": u"Россия, деревня Гадюкино",
        #     "passport": {
        #         "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
        #         "series": u"1123",
        #         "number": u"192837",
        #         "issue_date": datetime.now(),
        #         "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
        #         "depart_code": u"111987"
        #     },
        #     "ogrnip": "123456789012345",
        #     "address": {
        #         "region": RFRegionsEnum.RFR_SPB,
        #         "index": 198209,
        #         "district_type": DistrictTypeEnum.DIT_DISTRICT,
        #         "district": u"Пушкинский",
        #         "city_type": CityTypeEnum.CIT_CITY,
        #         "city": u"Гадюкино",
        #         "village_type": VillageTypeEnum.VIT_HUTOR,
        #         "village": u"близ Диканьки",
        #         "street_type": StreetTypeEnum.STT_BOULEVARD,
        #         "street": u"Мотоциклистов",
        #         "house_type": HouseTypeEnum.HOT_HOUSE,
        #         "house": "4",
        #         "building_type": BuildingTypeEnum.BIT_HOUSING,
        #         "building": "2",
        #         "flat_type": FlatTypeEnum.FLT_OFFICE,
        #         "flat": "705",
        #     },
        #     "caption": u"Сантехник",
        #     "phone": "+79210001122",
        #     "email": "somebody@domain.zz",
        #     "living_country_code": 3,
        #     "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        # })
        # sqldb.session.add(founder_otvetstvennyi)

        founder_otvetstvennyi = self.create_person(self.user, name=u"Семен", surname=u"Семенчук", patronymic=u"Семейкин")

        company_founder = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"Том и Джери",
            "short_name": u"ТиД",
            "general_manager": {
                "_id": founder.id
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
        sqldb.session.add(company_founder)
        sqldb.session.commit()

        self.db['bik_catalog'].insert(
            {'name': 'Банк', 'bik': '000000000', 'address': 'Питер', 'kor_account': '12345678901234567890'})

        doc_data = {
            u"full_name": u"ТестРегистратионФееИнтернетБанк2ПриватеФоюндерс РеспонсиблеПерсонОбтаин-РеспонсиблеПерсонОбтаин",
            u"short_name": u"ТестРегистратионФееИнтернетБанк2ПриватеФоюндерс РеспонсиблеПерсонОбтаин-РеспонсиблеПерсонОбтаин",
            u"inn": "781108730780",
            u"kpp": "999999999",
            u"bank_bik": "000000000",
            u"bank_account": "10101810858050000764",
            u"general_manager_term": 38,
            u"has_general_manager_contract": True,
            u"general_manager_caption": u"повелитель",
            u"general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            u"founders": [
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 12312.22,
                    "share": 100
                }
            ],
            u"general_manager_salary": {
                "currency": CurrencyEnum.CE_RUS_RUBLES,
                "value": "123123.00"
            },
            u"general_manager_fixed_working_hours": True,
            u"general_manager_working_hours": {
                u"start_working_hours": datetime(1900, 1, 1, hour=8),
                u"finish_working_hours": datetime(1900, 1, 1, hour=19),
                u"holidays": ["mon", "tue", "fri"],
                u"lunch_time": 10
            },
            u"general_manager_trial_period": 24,
            u"general_manager_quit_notify_period": 12,
            u"general_manager_contract_number": "2",
            u"selected_moderator": {
                "type": "company",
                "_id": company_founder.id
            },
            u"general_manager_salary_days": [1, 2, 3, 4, 5],
            u"address": {
                "street_type": u"ул",
                "index": 191186,
                "house": u"4",
                "region": u"Санкт-Петербург",
                "flat": u"12",
                "street": u"Большая Морская",
                "address_string": u"г Санкт-Петербург, ул Большая Морская, д 4, кв 12",
                "flat_type": u"кв",
                "house_type": u"д",
                "ifns": 7841
            },
            u"actual_address": {
                "street_type": u"ул",
                "index": 191186,
                "house": u"4",
                "region": u"Санкт-Петербург",
                "flat": u"12",
                "street": u"Большая Морская",
                "address_string": u"г Санкт-Петербург, ул Большая Морская, д 4, кв 12",
                "flat_type": u"кв",
                "house_type": u"д",
                "ifns": 7841
            },
            u"address_type": "general_manager_registration_address",
            u"general_manager_contract_date": datetime.now(),
            u"general_manager_contract_additional_terms": {
                u"rights": "",
                u"responsibility": None,
                u"duties": u"колоть дрова"
            },
            u"board_of_directors": True,
            u"registration_date": datetime.now(),
            u"company_email": "",
            u"company_site": "",
            u"company_phone": "+79111231313"
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_FINALISED,
                data={},
                _owner=self.user,
                result_fields={
                    'ifns_reg_info': {
                        'ogrn': "1234567890123"
                    }
                }
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            _id = batch.id

# rendered_docs=[{
#                                    'document_type': DocumentTypeEnum.DT_ARTICLES,
#                                    'file_link': 'somefile',
#                                    'caption': u"Уставчег",
#                                    'file_id': ObjectId(),
#                                    'document_id': ObjectId("54b91fe7a726163324353311")
#                                }],
            doc = BatchDocumentDbObject(
                status="rendered",
                document_type="articles",
                batch_id=_id,
                data={
                    "job_main_code": "50.20",
                    "use_national_language_company_name": False,
                    "use_foreign_company_name": False,
                    "pravo_otchuzhdeniya_type": 3,
                    "general_manager_term": 36,
                    "short_name": "а",
                    "preimusch_pravo_priobreteniya_doli_time_span": 30,
                    "address": {
                        "building": "20",
                        "index": 117105,
                        "street_type": "ш",
                        "house": "12Г",
                        "region": "Москва",
                        "okato": 12122222222,
                        "address_string": "г Москва, Варшавское шоссе, д 12Г стр 20",
                        "building_type": "стр",
                        "street": "Варшавское",
                        "house_type": "д",
                        "ifns": 7726
                    },
                    "perehod_doli_k_naslednikam_soglasie": True,
                    "necessary_votes_for_general_meeting_decisions": {
                        "audit_assignment": 1,
                        "large_deals_approval": 1,
                        "concern_deals_approval": 1,
                        "executives_formation": 1,
                        "other_issues": 1,
                        "articles_change": 1,
                        "branch_establishment": 1,
                        "profit_distribution": 1,
                        "annual_reports_approval": 1,
                        "liquidation_committee_assignment": 1,
                        "auditor_election": 1,
                        "obligations_emission": 1,
                        "reorganization_or_liquidation": 1,
                        "internal_documents_approval": 1,
                        "company_strategy": 1
                    },
                    "starter_capital": {
                        "capital_type": 1,
                        "value": {
                            "currency": "RUB",
                            "value": "10000"
                        }
                    },
                    "general_manager_caption": "Генеральный директор",
                    "doc_date": datetime.now(),
                    "full_name": "аи",
                    "job_code_array": [
                        "52.48.39",
                        "50.30",
                        "50.40",
                        "51.44.4"
                    ],
                    "board_of_directors": False,
                    "founders_count": 2,
                    "board_of_directors_caption": "Совет директоров"
                })
            sqldb.session.add(doc)
            sqldb.session.commit()

            booking = IfnsBookingObject(reg_info={
                'status': 'registered',
                'reg_date': datetime.now(),
                'ogrn': "123456789012345"
            }, batch_id=_id)
            sqldb.session.add(booking)
            sqldb.session.commit()

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': _id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/render_document/', data={
                'batch_id': _id,
                'document_type': json.dumps([DocumentTypeEnum.DT_COMPANY_DETAILS])
            })
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 2)

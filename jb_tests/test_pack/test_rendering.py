# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import hashlib
import json

from bson.objectid import ObjectId

from base_test_case import authorized
from common_utils.perf import TimeCalculator
from fw.documents.address_enums import (RFRegionsEnum, VillageTypeEnum, DistrictTypeEnum, CityTypeEnum, StreetTypeEnum,
                                        HouseTypeEnum, BuildingTypeEnum, FlatTypeEnum)
from fw.documents.db_fields import PrivatePersonDbObject, CompanyDbObject, DocumentBatchDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentBatchTypeEnum, DocumentTypeEnum, PersonDocumentTypeEnum, PersonTypeEnum, \
    CompanyTypeEnum, BatchStatusEnum, GenderEnum, IncorporationFormEnum
from fw.documents.fields.doc_fields import DocumentBatch
from fw.db.sql_base import db as sqldb
from fw.documents.fields.field_validators import get_uninitialized_field
from fw.metrics.models import UserMetricObject
from services.ifns.data_model.models import IfnsBookingObject
from services.ifns.utils.process_okvad import process_okvad
from services.llc_reg.documents.enums import UsnTaxType, DocumentDeliveryTypeStrEnum, RegistrationWay, AddressType
from services.llc_reg.documents.enums import NecessaryVotesEnum
from test_pack.base_batch_test import BaseBatchTestCase

NECESSARY_VOTES_FOR_GENERAL_MEETING_DECISIONS = {
    u"company_strategy": NecessaryVotesEnum.NV_ALL,
    u"articles_change": NecessaryVotesEnum.NV_3_4,
    u"executives_formation": NecessaryVotesEnum.NV_2_3,
    u"auditor_election": NecessaryVotesEnum.NV_2_3,
    u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
    u"profit_distribution": NecessaryVotesEnum.NV_3_4,
    u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
    u"obligations_emission": NecessaryVotesEnum.NV_ALL,
    u"audit_assignment": NecessaryVotesEnum.NV_2_3,
    u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
    u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
    u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
    u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
    u"branch_establishment": NecessaryVotesEnum.NV_3_4,
    u"other_issues": NecessaryVotesEnum.NV_2_3
}

class RenderingTestCase(BaseBatchTestCase):

    @authorized()
    def test_11001(self):
        a = UserMetricObject()
        #DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_ARTICLES]
        uchreditel_fis_lico_person = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "010101417407",
            "birthdate": datetime(datetime.now().year - 45, datetime.now().month, datetime.now().day,
                                  datetime.now().hour, datetime.now().minute),
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": "male",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,

                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                       datetime.now().hour, datetime.now().minute),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "person_type": PersonTypeEnum.PT_RUSSIAN,
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гадюкино",
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "2",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "long_form_mode": True
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(uchreditel_fis_lico_person)
        sqldb.session.commit()

        uchreditel_fis_lico_person2 = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "010101417407",
            "birthdate": datetime(datetime.now().year - 45, datetime.now().month, datetime.now().day,
                                  datetime.now().hour, datetime.now().minute),
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": "male",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,

                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                       datetime.now().hour, datetime.now().minute),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "person_type": PersonTypeEnum.PT_RUSSIAN,
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гадюкино",
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "2",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "long_form_mode": True
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(uchreditel_fis_lico_person2)
        sqldb.session.commit()

        uchreditel_fis_lico_person3 = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "010101417407",
            "birthdate": datetime(datetime.now().year - 45, datetime.now().month, datetime.now().day,
                                  datetime.now().hour, datetime.now().minute),
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": "male",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,

                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                       datetime.now().hour, datetime.now().minute),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "person_type": PersonTypeEnum.PT_RUSSIAN,
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гадюкино",
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "2",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "long_form_mode": True
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(uchreditel_fis_lico_person3)
        sqldb.session.commit()

        uchreditel_foreign_pp = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Джохн",
            "surname": u"Малковеч",
            "birthdate": datetime(datetime.now().year - 45, datetime.now().month, datetime.now().day,
                                  datetime.now().hour, datetime.now().minute),
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": "male",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_FOREIGN,
                "number": u"995852",
                "issue_date": datetime(datetime.now().year, datetime.now().month, datetime.now().day,
                                       datetime.now().hour, datetime.now().minute),
                "issue_depart": u"Australia",
            },
            "person_type": PersonTypeEnum.PT_FOREIGN,
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гадюкино",
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "2",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705",
                "long_form_mode": True
            },
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705",
            "living_country_code": 72
        })
        sqldb.session.add(uchreditel_foreign_pp)
        sqldb.session.commit()

        general_manager_person = PrivatePersonDbObject(**{
            "_owner": self.user,
            # "name" : u"Марат",
            #            "surname" : u"Кожевников",
            #            "patronymic" : u"Мухамедович",
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",

            "inn": "010101417407",
            "birthdate": datetime.now() - timedelta(days=365 * 19),
            "birthplace": u"неизвестно где",
            "sex": "male",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 30),
                "issue_depart": u"УМВД Гадюкинского района Неизвестной области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012347",
            "person_type": PersonTypeEnum.PT_RUSSIAN,
            "caption": u"Сам техник",
            "phone": "+79110001122",
            "email": "somebody@domain.zz",
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 7",
            "address": {
                "building": u"А",
                "city_type": u"г",
                "qc_complete": "0",
                "street_type": u"ул",
                "index": 420096,
                "address_string": u"Респ Татарстан, г Казань, ул Березовая (Малые Дербышки), д 1А, кв 6",
                "house": "1",
                "region": u"Татарстан",
                "okato": "92401385000",
                "flat": "6",
                "building_type": u"литер",
                "street": u"Березовая (Малые Дербышки)",
                "long_form_mode": False,
                "flat_type": u"кв",
                "house_type": u"д",
                "ifns": "1686",
                "city": u"Казань",
                "qc": "0"
            },
        })
        sqldb.session.add(general_manager_person)
        sqldb.session.commit()

        uchreditel_rus_jur_lico_company = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "full_name": u"Протон",
            "short_name": u"Про",
            "kpp": "999999999",
            "company_type": CompanyTypeEnum.CT_RUSSIAN,
            "general_manager": {
                "_id": uchreditel_fis_lico_person.id,
                "type": "person"
            },
            "general_manager_caption": u"директор",
            "address": {
                "region": RFRegionsEnum.RFR_IRKUTSKAYA_REGION,
                "index": 123131,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "2",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "778899",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "2",
                "ifns": "1234"
            },
            "phone": "+7(812)1234567",
            "registration_date": datetime(2009, 1, 1)
        })
        sqldb.session.add(uchreditel_rus_jur_lico_company)
        sqldb.session.commit()

        uchreditel_foreign_llc = CompanyDbObject(**{
            "_owner": self.user,
            "full_name": u"Proton",
            "short_name": u"Pro",
            "company_type": CompanyTypeEnum.CT_FOREIGN,
            "general_manager_caption": u"директор",
            "country_code": 100,
            "generic_address": "Generic Address",
            "registration_date": datetime(2009, 1, 1),
            "registration_depart": "depart",
            "registration_number": 123,
            u"general_manager": {
                "_id": general_manager_person.id,
                "type": "person"
            },
        })
        sqldb.session.add(uchreditel_foreign_llc)
        sqldb.session.commit()

        with self.app.app_context():
            data = {
                u"full_name": u"фывафыва",
                u"short_name": u"Бокс",
                u"doc_date": datetime(2019, 9, 24),
                # "address": {
                #     "address_string": u"Санкт-Петербург, наб. Свердловская, д 44, литер. ю, кв. 405",
                #     "building": u"ю",
                #     "street_type": u"наб",
                #     "house": "44",
                #     "house_type": u"д",
                #     "region": u"Санкт-Петербург",
                #     "flat": "405",
                #     "building_type": u"литер",
                #     "street": u"Свердловская",
                #     "long_form_mode": True,
                #     "flat_type": u"кв",
                # },
                u"address_type": "general_manager_registration_address",
                u"starter_capital": {
                    "currency": "rub",
                    "value": "10000"
                },
                u"general_manager_caption": u"повелитель",
                u"share_type": "fraction",
                u"founders": [
                    {
                        "founder": {
                            "_id": uchreditel_rus_jur_lico_company.id,
                            "type": "company"
                        },
                        "nominal_capital": "12312.20",
                        "share": "1.4"
                    },
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person.id,
                            "type": "person"
                        },
                        "nominal_capital": "1500.50",
                        "share": "1.4"
                    },
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person2.id,
                            "type": "person"
                        },
                        "nominal_capital": "1500.50",
                        "share": "1.4"
                    },
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person3.id,
                            "type": "person"
                        },
                        "nominal_capital": "1500.50",
                        "share": "1.4"
                    },
                ],
                u"general_manager": {
                    "_id": general_manager_person.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                # u"job_code_array" : [u"92.31.1", u"74.14", u"10.01.1"],
                u"job_code_array": [],
                u"doc_obtain_founder": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"obtain_way": "founder",
                u'use_foreign_company_name': False,
                u'use_national_language_company_name': False,
                u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
                u'general_manager_term': 20,
                u"preimusch_pravo_priobreteniya_doli_time_span": 60,
                u'necessary_votes_for_general_meeting_decisions': {
                    u"company_strategy": NecessaryVotesEnum.NV_ALL,
                    u"articles_change": NecessaryVotesEnum.NV_3_4,
                    u"executives_formation": NecessaryVotesEnum.NV_2_3,
                    u"auditor_election": NecessaryVotesEnum.NV_2_3,
                    u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                    u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                    u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                    u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                    u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                    u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                    u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                    u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                    u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                    u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                    u"other_issues": NecessaryVotesEnum.NV_2_3
                },
                u"board_of_directors": False,
                u"selected_secretary": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"selected_moderator": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"pravo_otchuzhdeniya_type": 5,
                u"perehod_doli_k_naslednikam_soglasie": True,
                u"taxation_type": "general",
                u"registration_way": "some_founders",
                u"region": u"Санкт-Петербург",
                u"reg_responsible_founder": {
                    u"type": u"person",
                    u"_id": uchreditel_fis_lico_person.id
                },
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                data={},
                paid=True,
                metadata={'_something': "wrong"},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                metadata={'_something': "wrong"},
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            structure = batch.get_api_structure()
            del structure['batch_type']
            batch_json = json.dumps(structure)
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(batch_id),
                'batch': batch_json })
            self.assertEqual(result.status_code, 200)
            # print(result.data)
            #
            #            result = self.test_client.post('/batch/update/', data = {
            #                'batch_id' : unicode(_id),
            #                'batch' : batch_json
            #            })
            #            self.assertEqual(result.status_code, 200)
            #            print(result.data)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(batch_id)})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)

            result = self.test_client.get('/batch/?batch_id=' + batch_id)
            print(result.data)

            result = self.test_client.post('/batch/unfinalise/', data={'batch_id': unicode(batch_id)})
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(batch_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(batch_id)})
            self.assertEqual(result.status_code, 200)

    @authorized()
    def test_ustav(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_ARTICLES]
        uchreditel_fis_lico_person = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": "male",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now(),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "person_type": PersonTypeEnum.PT_RUSSIAN,
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гадюкино",
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
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(uchreditel_fis_lico_person)
        sqldb.session.commit()

        uchreditel_rus_jur_lico_company = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "full_name": u"Протон",
            "short_name": u"Про",
            "kpp": "999999999",
            "company_type": CompanyTypeEnum.CT_RUSSIAN,
            "general_manager": {
                "_id": uchreditel_fis_lico_person.id,
                "type": "person"
            },
            "general_manager_caption": u"директор",
            "address": {
                "region": RFRegionsEnum.RFR_IRKUTSKAYA_REGION,
                "index": 123131,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "2",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "778899",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "2",
                "ifns": 1234
            },
            "phone": "+7(812)1234567"
        })
        sqldb.session.add(uchreditel_rus_jur_lico_company)
        sqldb.session.commit()

        with self.app.app_context():
            data = {
                u"full_name": u"ТестКреатеЛтдАдд1КомпаниНевДиректор",
                u"short_name": u"ТестКреатеЛтдАдд1КомпаниНевДиректор",
                u"address": {
                    "building": u"А",
                    "city_type": u"г",
                    "qc_complete": "0",
                    "street_type": u"ул",
                    "index": 420096,
                    "address_string": u"Респ Татарстан, г Казань, ул Березовая (Малые Дербышки), д 1А, кв 6",
                    "house": "1",
                    "region": u"Татарстан",
                    "okato": "92401385000",
                    "flat": "6",
                    "building_type": u"литер",
                    "street": u"Березовая (Малые Дербышки)",
                    "long_form_mode": False,
                    "flat_type": u"кв",
                    "house_type": u"д",
                    "ifns": "1686",
                    "city": u"Казань",
                    "qc": "0"
                },
                u"address_type": "office_address",
                u"starter_capital": {
                    "currency": "rub",
                    "value": "12312"
                },
                u"general_manager_caption": u"повелитель",
                u"share_type": "percent",
                u"founders": [
                    {
                        "founder": {
                            "_id": uchreditel_rus_jur_lico_company.id,
                            "type": "company"
                        },
                        "nominal_capital": 12312,
                        "share": 85
                    },
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person.id,
                            "type": "person"
                        },
                        "nominal_capital": 1500,
                        "share": 15
                    }
                ],
                u"general_manager": {
                    "_id": uchreditel_fis_lico_person.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                u"doc_obtain_person": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"obtain_way": "founder",
                u'use_foreign_company_name': True,
                u'use_national_language_company_name': False,
                "foreign_language": u"английский",
                u"foreign_full_name": u"\"MEDPRIBOR-21\" Limited Liability Company",
                u"foreign_short_name": u"\"MEDPRIBOR-21\" LLC",
                u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
                u'general_manager_term': 20,
                u"preimusch_pravo_priobreteniya_doli_time_span": 60,
                u'necessary_votes_for_general_meeting_decisions': {
                    u"company_strategy": NecessaryVotesEnum.NV_ALL,
                    u"articles_change": NecessaryVotesEnum.NV_3_4,
                    u"executives_formation": NecessaryVotesEnum.NV_2_3,
                    u"auditor_election": NecessaryVotesEnum.NV_2_3,
                    u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                    u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                    u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                    u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                    u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                    u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                    u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                    u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                    u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                    u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                    u"other_issues": NecessaryVotesEnum.NV_2_3
                },
                u"board_of_directors": False,
                u"selected_secretary": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"selected_moderator": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"pravo_otchuzhdeniya_type": 5,
                u"perehod_doli_k_naslednikam_soglasie": True,
                u"taxation_type": "usn",
                u"registration_way": "some_founders",
                u"region": u"Санкт-Петербург",
                u"general_manager_deals_max_amount": 10000,
                u"large_deals_min_value": 50
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                paid=True,
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            booking = IfnsBookingObject(
                batch_id=batch_id,
                reg_info={
                    'reg_date': datetime.now()
                }
            )
            sqldb.session.add(booking)
            sqldb.session.commit()

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': batch_id})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)

    @authorized()
    def test_decision(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_DECISION]

        bd = datetime.now() - timedelta(days=365 * 30)
        founder_person = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "birthdate": bd,
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": "male",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": bd + timedelta(days=20 * 366),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "qc_complete": "5",
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198259,
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Тамбасова",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "38",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "70"
            },
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(founder_person)
        sqldb.session.commit()

        company_founder = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
            "short_name": u"Бокс",
            "general_manager": {
                "_id": founder_person.id,
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

        input = {
            u'use_foreign_company_name': False,
            u'use_national_language_company_name': False,
            u"full_name": u"ТестКреатеЛтдАдд1КомпаниНевДиректор",
            u"short_name": u"Бокс",
            "address": {
                "flat_type": u"кв",
                "qc_complete": u"0",
                "index": 140008,
                "house": u"85",
                "region": u"Московская",
                "okato": 46231501000,
                "flat": u"2",
                "address_string": u"Московская обл.  в/г Тёплый стан д.85, кв.2",
                "village": u"Тёплый Стан",
                "house_type": u"д",
                "village_type": u"в/гор",
                "ifns": "5027"
            },
            "address_type": "office_address",
            "starter_capital": {
                "currency": "rub",
                "value": "12312.234234"
            },
            "registration_date": datetime.now(),
            "general_manager_caption": u"повелитель",
            "share_type": "percent",
            "founders": [
                {
                    "founder": {
                        "_id": company_founder.id,
                        "type": "company"
                    },
                    "nominal_capital": 1500.5,
                    "share": 100
                }
            ],
            "general_manager": {
                "_id": founder_person.id
            },
            "job_main_code": u"92.31.1",
            "job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
            # "doc_obtain_person" : {
            #                "type" : "person",
            #                "_id" : founder_person._id
            #            },
            "obtain_way": "responsible_person"
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                _documents=[],
                paid=True,
                data={},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                _documents=[],
                data=input,
                _owner=self.user
            )

            batch = DocumentBatch.db_obj_to_field(batch)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })

            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': batch_id})
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)

    @authorized()
    def test_usn(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_USN]

        col = self.db['okvad']
        col.insert({"caption": u"Рыболовство", "okved": "05.01", "nalog": "usn",
                    "parent": ObjectId("5478373ee64bcf4ece4a57d8")})

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
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                'index': 199000,
                "region": RFRegionsEnum.RFR_LENINGRADSKAYA_REGION,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гатчина",
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Радищева",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "26",
                "flat_type": FlatTypeEnum.FLT_FLAT,
                "flat": "80",
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
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                'index': 199000,
                "region": RFRegionsEnum.RFR_LENINGRADSKAYA_REGION,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гатчина",
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Радищева",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "26",
                "flat_type": FlatTypeEnum.FLT_FLAT,
                "flat": "80",
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
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
            "short_name": u"Бокс",
            "general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            "address": {
                'index': '199000',
                "region": RFRegionsEnum.RFR_LENINGRADSKAYA_REGION,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гатчина",
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Радищева",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "26",
                "flat_type": FlatTypeEnum.FLT_FLAT,
                "flat": "80",
            },
            "phone": "+7(812)1234567"
        })
        sqldb.session.add(company_founder)
        sqldb.session.commit()

        input = {
            u"full_name": u"Общество с ограниченной ответственностью образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа",
            "address": {
                'index': 199000,
                "region": RFRegionsEnum.RFR_LENINGRADSKAYA_REGION,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гатчина",
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Радищева",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "26",
                "flat_type": FlatTypeEnum.FLT_FLAT,
                "flat": "80",
                "ifns": 1234
            },
            "address_type": "office_address",
            "starter_capital": {
                "currency": "rub",
                "value": "12312.234234"
            },
            "general_manager_caption": u"повелитель",
            "share_type": "percent",
            "founders": [
                {
                    "founder": {
                        "_id": company_founder.id,
                        "type": "company"
                    },
                    "nominal_capital": 12312.22,
                    "share": 25
                },
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 1500.5,
                    "share": 75
                }
            ],
            "general_manager": {
                "_id": founder_otvetstvennyi.id
            },
            "job_main_code": u"05.01",
            "job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
            "doc_obtain_person": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "obtain_way": "founder",
            u"tax_type": UsnTaxType.UT_INCOME,
            u'general_manager_term': 20,
            u"preimusch_pravo_priobreteniya_doli_time_span": 60,
            u'necessary_votes_for_general_meeting_decisions': {
                u"company_strategy": NecessaryVotesEnum.NV_ALL,
                u"articles_change": NecessaryVotesEnum.NV_3_4,
                u"executives_formation": NecessaryVotesEnum.NV_2_3,
                u"auditor_election": NecessaryVotesEnum.NV_2_3,
                u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                u"other_issues": NecessaryVotesEnum.NV_2_3
            },
            "board_of_directors": False,
            "selected_secretary": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "selected_moderator": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "pravo_otchuzhdeniya_type": 5,
            "short_name": u"АБВ",
            "perehod_doli_k_naslednikam_soglasie": True,
            "taxation_type": "usn",
            "registration_way": "some_founders",
            "region": u"Санкт-Петербург"
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=input,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': batch_id})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertTrue(not not db_batch._documents[0].file)

    @authorized()
    def test_protocol(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_PROTOCOL]

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
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"Том и «Джери»",
            "short_name": u"Т и \"Д\"",
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
            u"full_name": u"ТестКреатеЛтдАдд1КомпаниНевДиректор",
            u"short_name": u"ТестКреатеЛтдАдд1КомпаниНевДиректор",
            u'use_foreign_company_name': False,
            u'use_national_language_company_name': False,
            u'foreign_full_name': u'Microsoft Company',
            u'foreign_short_name': u'Microsoft',
            u'national_language_full_name': u'Эбэртэ Туруун',
            u'national_language_short_name': u'Туруун',
            u"foreign_language": u"английский",
            u"national_language": u"ташкентский",
            u"selected_secretary": {
                u"_id": founder_otvetstvennyi.id,
                u"type": u"person"
            },
            "address": {
                "flat_type": u"кв",
                "qc_complete": u"0",
                "index": 140008,
                "house": u"85",
                "region": u"Московская",
                "okato": 46231501000,
                "flat": u"2",
                "address_string": u"Московская обл.  в/г Тёплый стан д.85, кв.2",
                "village": u"Тёплый Стан",
                "house_type": u"д",
                "village_type": u"в/гор",
                "ifns": 5027
            },
            u"address_type": u"office_address",
            u"starter_capital": {
                u"currency": u"rub",
                u"value": u"38000"
            },
            u"general_manager_caption": u"повелитель",
            u"share_type": u"fraction",
            u"founders": [
                {
                    u"founder": {
                        u"_id": company_founder.id,
                        u"type": u"company"
                    },
                    u"nominal_capital": 12312.22,
                    u"share": "3.4"
                }, {
                    u"founder": {
                        u"_id": founder_otvetstvennyi.id,
                        u"type": u"person"
                    },
                    u"nominal_capital": 1500.5,
                    u"share": "1.4"
                }
            ],
            u"selected_moderator": {
                u"_id": founder_otvetstvennyi.id,
                u"type": u"person"
            },
            u"obtain_way": u"founder",
            u"doc_obtain_founder": {
                u"type": u"person",
                u"_id": founder_otvetstvennyi.id
            },
            u"reg_responsible_founder": {
                u"type": u"person",
                u"_id": founder_otvetstvennyi.id
            },
            u"registration_way": u"some_founders",
            u"general_manager": {
                u"_id": founder_otvetstvennyi.id
            },
            u"job_main_code": u"92.31.1",
            u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
            u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
            u'general_manager_term': 20,
            u"preimusch_pravo_priobreteniya_doli_time_span": 60,
            u'necessary_votes_for_general_meeting_decisions': {
                u"company_strategy": NecessaryVotesEnum.NV_ALL,
                u"articles_change": NecessaryVotesEnum.NV_3_4,
                u"executives_formation": NecessaryVotesEnum.NV_2_3,
                u"auditor_election": NecessaryVotesEnum.NV_2_3,
                u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                u"other_issues": NecessaryVotesEnum.NV_2_3
            },
            u"board_of_directors": False,
            u"pravo_otchuzhdeniya_type": 5,
            u"perehod_doli_k_naslednikam_soglasie": True,
            u"taxation_type": u"usn",
            u"region": u"Санкт-Петербург"
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_EDITED,
                _documents=[],
                data={},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': batch_id})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)

    @authorized()
    def test_eshn(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_ESHN]
        process_okvad()
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
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "index": 190000,
                "region": RFRegionsEnum.RFR_LENINGRADSKAYA_REGION,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гатчина",
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Радищева",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "26",
                "flat_type": FlatTypeEnum.FLT_FLAT,
                "flat": "80",
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
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "address": {
                "index": 190000,
                "region": RFRegionsEnum.RFR_LENINGRADSKAYA_REGION,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гатчина",
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Радищева",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "26",
                "flat_type": FlatTypeEnum.FLT_FLAT,
                "flat": "80",
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
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
            "short_name": u"Бокс",
            "general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            "address": {
                "index": 190000,
                "region": RFRegionsEnum.RFR_LENINGRADSKAYA_REGION,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гатчина",
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Радищева",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "26",
                "flat_type": FlatTypeEnum.FLT_FLAT,
                "flat": "80",
            },
            "phone": "+7(812)1234567"
        })
        sqldb.session.add(company_founder)
        sqldb.session.commit()

        input = {
            u"full_name": u"Общество с ограниченной ответственностью образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа",
            "address": {
                'index': 199000,
                "region": RFRegionsEnum.RFR_LENINGRADSKAYA_REGION,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гатчина",
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Радищева",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "26",
                "flat_type": FlatTypeEnum.FLT_FLAT,
                "flat": "80",
                "ifns": 1234
            },
            "address_type": "office_address",
            "starter_capital": {
                "currency": "rub",
                "value": "12312.234234"
            },
            "general_manager_caption": u"повелитель",
            "share_type": "percent",
            "founders": [
                {
                    "founder": {
                        "_id": founder.id,
                        "type": "person"
                    },
                    "nominal_capital": 12312.22,
                    "share": 85
                },
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 1500.5,
                    "share": 15
                }
            ],
            "general_manager": {
                "_id": founder_otvetstvennyi.id
            },
            "job_main_code": u"01.30",
            "job_code_array": [u"01.30", u"15.32"],
            "doc_obtain_person": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "doc_obtain_founder": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "obtain_way": "founder",
            u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
            u'general_manager_term': 20,
            u"preimusch_pravo_priobreteniya_doli_time_span": 60,
            u'necessary_votes_for_general_meeting_decisions': {
                u"company_strategy": NecessaryVotesEnum.NV_ALL,
                u"articles_change": NecessaryVotesEnum.NV_3_4,
                u"executives_formation": NecessaryVotesEnum.NV_2_3,
                u"auditor_election": NecessaryVotesEnum.NV_2_3,
                u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                u"other_issues": NecessaryVotesEnum.NV_2_3
            },
            "board_of_directors": False,
            "selected_secretary": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "selected_moderator": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "pravo_otchuzhdeniya_type": 5,
            "short_name": u"АБВ",
            "perehod_doli_k_naslednikam_soglasie": True,
            "taxation_type": "eshn",
            "registration_way": "some_founders",
            "region": u"Санкт-Петербург"
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=input,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': batch_id})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch._documents[0].file)

    @authorized()
    def test_contract(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_CONTRACT]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокла",
            "surname": u"Поликарпова",
            "patronymic": u"Поликарповна",
            "inn": "781108730780",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": GenderEnum.G_FEMALE,
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
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
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
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
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
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "incorporation_form": IncorporationFormEnum.IF_LLC,
            "full_name": u"Том и \"Джерри\"",
            "short_name": u"Т и \"Д\"",
            "general_manager": {
                "_id": founder_otvetstvennyi.id,
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

        input = {
            u"full_name": u"ТестКреатеЛтдАдд1КомпаниНевДиректор",
            "address": {
                'index': 199000,
                "region": RFRegionsEnum.RFR_LENINGRADSKAYA_REGION,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гатчина",
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Радищева",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "26",
                "flat_type": FlatTypeEnum.FLT_FLAT,
                "flat": "80",
                "ifns": 1234
            },
            "address_type": "office_address",
            "starter_capital": {
                "currency": "rub",
                "value": "12312.234234"
            },
            "general_manager_caption": u"повелитель",
            "share_type": "percent",
            "founders": [
                {
                    "founder": {
                        "_id": company_founder.id,
                        "type": "company"
                    },
                    "nominal_capital": 12312.22,
                    "share": 85
                },
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 1500.5,
                    "share": 15
                }
            ],
            "general_manager": {
                "_id": founder_otvetstvennyi.id
            },
            "job_main_code": u"92.31.1",
            "job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
            "doc_obtain_person": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "obtain_way": "founder",
            u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
            u'general_manager_term': 20,
            u"preimusch_pravo_priobreteniya_doli_time_span": 60,
            u'necessary_votes_for_general_meeting_decisions': {
                u"company_strategy": NecessaryVotesEnum.NV_ALL,
                u"articles_change": NecessaryVotesEnum.NV_3_4,
                u"executives_formation": NecessaryVotesEnum.NV_2_3,
                u"auditor_election": NecessaryVotesEnum.NV_2_3,
                u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                u"other_issues": NecessaryVotesEnum.NV_2_3
            },
            "board_of_directors": False,
            "selected_secretary": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "selected_moderator": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "pravo_otchuzhdeniya_type": 5,
            "short_name": u"ТестКреатеЛтдАдд1КомпаниНевДиректор",
            "perehod_doli_k_naslednikam_soglasie": True,
            "taxation_type": "eshn",
            "registration_way": "some_founders",
            "region": u"Санкт-Петербург"
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=input,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': batch_id})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)

    @authorized()
    def test_kvitanciya_new(self):
        with self.app.app_context():
            DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_REGISTRATION_FEE_INVOICE]

            founder = PrivatePersonDbObject(**{
                "_owner": self.user,
                "name": u"Прокл",
                "surname": u"Поликарпов",
                "sex": "male",
                "patronymic": u"Поликарпович",
                "inn": "781108730780",
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
                    "street_type": StreetTypeEnum.STT_STREET,
                    "street": u"Тамбасова",
                    "house_type": HouseTypeEnum.HOT_HOUSE,
                    "house": "30",
                    "flat_type": FlatTypeEnum.FLT_OFFICE,
                    "flat": "20",
                    #"okato": "40298562000",
                    "ifns": "7804"
                },
                "caption": u"Сантехник",
                "phone": "+79210001122",
                "email": "somebody@domain.zz",
                "living_country_code": 3,
                "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
            })
            sqldb.session.add(founder)
            sqldb.session.commit()

            company_founder = CompanyDbObject(**{
                "_owner": self.user,
                "ogrn": "1095543023135",
                "inn": "781108730780",
                "kpp": "999999999",
                "general_manager_caption": u"генеральный директор",
                "incorporation_form": IncorporationFormEnum.IF_LLC,
                "full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
                "short_name": u"Бокс",
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
                    "flat_type": FlatTypeEnum.FLT_FLAT,
                    "flat": "2",
                    "okato": "40298562000"
                },
                "phone": "+7(812)1234567"
            })
            sqldb.session.add(company_founder)
            sqldb.session.commit()

            doc_data = {
                u"full_name": u"Общество с ограниченной ответственностью",
                "address": {
                    'index': 199000,
                    "region": RFRegionsEnum.RFR_MOSCOW,
                    "street_type": StreetTypeEnum.STT_HIGHWAY,
                    "street": u"Варшавское",
                    "house_type": HouseTypeEnum.HOT_HOUSE,
                    "house": "21",
                    "flat_type": FlatTypeEnum.FLT_FLAT,
                    "flat": "3"
                },
                "address_type": "founder_registration_address",
                "starter_capital": {
                    "currency": "rub",
                    "value": "12312.234234"
                },
                "general_manager_caption": u"повелитель",
                "share_type": "percent",
                "founders": [
                    {
                        "founder": {
                            "_id": founder.id,
                            "type": "person"
                        },
                        "nominal_capital": 12312.22,
                        "share": 85
                    },
                    {
                        "founder": {
                            "_id": founder.id,
                            "type": "person"
                        },
                        "nominal_capital": 1500.5,
                        "share": 15
                    }
                ],
                "general_manager": {
                    "_id": founder.id
                },
                "address_person": {
                    "_id": founder.id
                },
                "job_main_code": u"92.31.1",
                "job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                "doc_obtain_person": {
                    "type": "person",
                    "_id": founder.id
                },
                "obtain_way": "mail",
                u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
                u'general_manager_term': 20,
                u"preimusch_pravo_priobreteniya_doli_time_span": 60,
                u'necessary_votes_for_general_meeting_decisions': {
                    u"company_strategy": NecessaryVotesEnum.NV_ALL,
                    u"articles_change": NecessaryVotesEnum.NV_3_4,
                    u"executives_formation": NecessaryVotesEnum.NV_2_3,
                    u"auditor_election": NecessaryVotesEnum.NV_2_3,
                    u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                    u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                    u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                    u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                    u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                    u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                    u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                    u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                    u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                    u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                    u"other_issues": NecessaryVotesEnum.NV_2_3
                },
                "board_of_directors": False,
                "selected_secretary": {
                    "type": "person",
                    "_id": founder.id
                },
                "selected_moderator": {
                    "type": "person",
                    "_id": founder.id
                },
                "pravo_otchuzhdeniya_type": 5,
                "short_name": u"АБВ",
                "perehod_doli_k_naslednikam_soglasie": True,
                "taxation_type": "eshn",
                "registration_way": "responsible_person",
                "region": u"Санкт-Петербург"
            }

            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                _documents=[],
                data=doc_data,
                _owner=self.user,
                status=BatchStatusEnum.BS_NEW
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=doc_data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': batch_id})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch._documents[0].file)

        # """addrFl	117105,77,,,,ВАРШАВСКОЕ Ш,17,,25
        #addrFl_ifns	7726
        #addrFl_okatom	45296561000
        #addrUl	117105,77,,,,ВАРШАВСКОЕ Ш,17,,24
        #addrUl_ifns	7726
        #addrUl_okatom	45296561000
        #bank
        #c
        #fam	Долгов
        #gp	11|18210807010011000110|13|ul|4000
        #inn	772900273375
        #nam	Центр
        #otch	Иванович
        #payKind	on
        #region
        #sum	4000
        #        """

    @authorized()
    def test_doverennost(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = \
            [DocumentTypeEnum.DT_DOVERENNOST, DocumentTypeEnum.DT_DOVERENNOST_OBTAIN]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Хомяк",
            "surname": u"Серый",
            "sex": "male",
            "patronymic": u"",
            "inn": "781108730780",
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
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гадюкино",
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "2",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705"
            },
        })
        sqldb.session.add(founder)
        sqldb.session.commit()

        founder2 = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Хомяк",
            "surname": u"Серый",
            "sex": "male",
            "patronymic": u"",
            "inn": "781108730780",
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
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705",
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гадюкино",
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "2",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "705"
            },
        })
        sqldb.session.add(founder2)
        sqldb.session.commit()

        uchreditel_fis_lico_person = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": "male",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "person_type": PersonTypeEnum.PT_RUSSIAN,
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гадюкино",
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
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(uchreditel_fis_lico_person)
        sqldb.session.commit()

        uchreditel_rus_jur_lico_company = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "full_name": u"Протон",
            "short_name": u"Про",
            "kpp": "999999999",
            "company_type": CompanyTypeEnum.CT_RUSSIAN,
            "general_manager": {
                "type": "person",
                "_id": uchreditel_fis_lico_person.id
            },
            "general_manager_caption": u"директор",
            "address": {
                "region": RFRegionsEnum.RFR_IRKUTSKAYA_REGION,
                "index": 123131,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "2",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "778899",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "2",
                "ifns": 1234
            },
            "phone": "+7(812)1234567"
        })
        sqldb.session.add(uchreditel_rus_jur_lico_company)
        sqldb.session.commit()

        with self.app.app_context():
            data = {
                u"full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
                u"short_name": u"Бокс",
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
                u"address_type": "office_address",
                u"starter_capital": {
                    "currency": "rub",
                    "value": "12312.234234"
                },
                u"general_manager_caption": u"повелитель",
                u"share_type": "percent",
                u"founders": [
                    {
                        "founder": {
                            "_id": uchreditel_rus_jur_lico_company.id,
                            "type": "company"
                        },
                        "nominal_capital": 12312.22,
                        "share": 85
                    },
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person.id,
                            "type": "person"
                        },
                        "nominal_capital": 1500.5,
                        "share": 15
                    }
                ],
                u"general_manager": {
                    "_id": uchreditel_fis_lico_person.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                u"doc_obtain_person": {
                    "type": "person",
                    "_id": founder.id
                },
                u"obtain_way": DocumentDeliveryTypeStrEnum.DDT_ISSUE_TO_THE_APPLICANT_OR_AGENT,
                u'use_foreign_company_name': False,
                u'use_national_language_company_name': False,
                u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
                u'general_manager_term': 20,
                u"preimusch_pravo_priobreteniya_doli_time_span": 60,
                u'necessary_votes_for_general_meeting_decisions': {
                    u"company_strategy": NecessaryVotesEnum.NV_ALL,
                    u"articles_change": NecessaryVotesEnum.NV_3_4,
                    u"executives_formation": NecessaryVotesEnum.NV_2_3,
                    u"auditor_election": NecessaryVotesEnum.NV_2_3,
                    u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                    u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                    u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                    u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                    u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                    u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                    u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                    u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                    u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                    u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                    u"other_issues": NecessaryVotesEnum.NV_2_3
                },
                u"board_of_directors": False,
                u"selected_secretary": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"selected_moderator": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"pravo_otchuzhdeniya_type": "5",
                u"perehod_doli_k_naslednikam_soglasie": True,
                u"taxation_type": "usn",
                u"registration_way": RegistrationWay.RW_RESPONSIBLE_PERSON,
                u"region": u"Санкт-Петербург",
                "reg_responsible_person": {
                    "type": "person",
                    "_id": founder2.id
                }
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': batch_id})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 2)
            self.assertTrue(not not db_batch._documents[0].file)
            self.assertTrue(not not db_batch._documents[1].file)

    @authorized()
    def test_render_soglasie_sobstvennikov(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_SOGLASIE_SOBSTVENNIKOV]

        uchreditel_fis_lico_person = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": "male",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "person_type": PersonTypeEnum.PT_RUSSIAN,
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
            "caption": u"Сантехник",
            "phone": "+79210001122",
            "email": "somebody@domain.zz",
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(uchreditel_fis_lico_person)
        sqldb.session.commit()

        uchreditel_rus_jur_lico_company = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "full_name": u"Протон",
            "short_name": u"Про",
            "kpp": "999999999",
            "company_type": CompanyTypeEnum.CT_RUSSIAN,
            "general_manager": {
                "_id": uchreditel_fis_lico_person.id,
                "type": "person"
            },
            "general_manager_caption": u"директор",
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
            "phone": "+7(812)1234567"
        })
        sqldb.session.add(uchreditel_rus_jur_lico_company)
        sqldb.session.commit()

        with self.app.app_context():
            data = {
                u"full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
                u"short_name": u"Бокс",
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
                u"address_type": AddressType.AT_REAL_ESTATE_ADDRESS,
                u"starter_capital": {
                    "currency": "rub",
                    "value": "12312.234234"
                },
                u"general_manager_caption": u"повелитель",
                u"share_type": "percent",
                u"founders": [
                    {
                        "founder": {
                            "_id": uchreditel_rus_jur_lico_company.id,
                            "type": "company"
                        },
                        "nominal_capital": 12312.22,
                        "share": 85
                    },
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person.id,
                            "type": "person"
                        },
                        "nominal_capital": 1500.5,
                        "share": 15
                    }
                ],
                u"general_manager": {
                    "_id": uchreditel_fis_lico_person.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                u"doc_obtain_person": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"obtain_way": DocumentDeliveryTypeStrEnum.DDT_ISSUE_TO_THE_APPLICANT_OR_AGENT,
                u'use_foreign_company_name': False,
                u'use_national_language_company_name': False,
                u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
                u'general_manager_term': 20,
                u"preimusch_pravo_priobreteniya_doli_time_span": 60,
                u'necessary_votes_for_general_meeting_decisions': {
                    u"company_strategy": NecessaryVotesEnum.NV_ALL,
                    u"articles_change": NecessaryVotesEnum.NV_3_4,
                    u"executives_formation": NecessaryVotesEnum.NV_2_3,
                    u"auditor_election": NecessaryVotesEnum.NV_2_3,
                    u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                    u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                    u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                    u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                    u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                    u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                    u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                    u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                    u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                    u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                    u"other_issues": NecessaryVotesEnum.NV_2_3
                },
                u"board_of_directors": False,
                u"selected_secretary": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"selected_moderator": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"pravo_otchuzhdeniya_type": "5",
                u"perehod_doli_k_naslednikam_soglasie": True,
                u"taxation_type": "usn",
                u"registration_way": RegistrationWay.RW_RESPONSIBLE_PERSON,
                u"region": u"Санкт-Петербург",
                u"reg_responsible_person": {
                    "_id": uchreditel_fis_lico_person.id
                },
                u"address_other_owner": True,
                u"address_person": {
                    "_id": uchreditel_fis_lico_person.id
                }
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_EDITED,
                data={},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()

            result = self.test_client.post('/batch/finalise/', data={'batch_id': batch_id})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch._documents[0].file)

    @authorized()
    def test_render_garant_letter_arenda(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_GARANT_LETTER_ARENDA]

        uchreditel_fis_lico_person = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": "male",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "person_type": PersonTypeEnum.PT_RUSSIAN,
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гадюкино",
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
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(uchreditel_fis_lico_person)
        sqldb.session.commit()

        uchreditel_rus_jur_lico_company = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "full_name": u"Протон",
            "short_name": u"Про",
            "kpp": "999999999",
            "company_type": CompanyTypeEnum.CT_RUSSIAN,
            "general_manager": {
                "_id": uchreditel_fis_lico_person.id,
                "type": "person"
            },
            "general_manager_caption": u"директор",
            "address": {
                "region": RFRegionsEnum.RFR_IRKUTSKAYA_REGION,
                "index": 123131,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "2",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "778899",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "2",
                "ifns": 1234
            },
            "phone": "+7(812)1234567"
        })
        sqldb.session.add(uchreditel_rus_jur_lico_company)
        sqldb.session.commit()

        with self.app.app_context():
            data = {
                u"full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
                u"short_name": u"Бокс",
                u"address": {
                    "region": RFRegionsEnum.RFR_IRKUTSKAYA_REGION,
                "index": 123131,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "2",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "778899",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "2",
                "ifns": 1234
                },
                u"address_type": "office_address",
                u"starter_capital": {
                    "currency": "rub",
                    "value": "12312.234234"
                },
                u"general_manager_caption": u"повелитель",
                u"share_type": "percent",
                u"founders": [
                    {
                        "founder": {
                            "_id": uchreditel_rus_jur_lico_company.id,
                            "type": "company"
                        },
                        "nominal_capital": 12312.22,
                        "share": 85
                    },
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person.id,
                            "type": "person"
                        },
                        "nominal_capital": 1500.5,
                        "share": 15
                    }
                ],
                u"general_manager": {
                    "_id": uchreditel_fis_lico_person.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                u"doc_obtain_person": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"obtain_way": "founder",
                u'use_foreign_company_name': False,
                u'use_national_language_company_name': False,
                u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
                u'general_manager_term': 20,
                u"preimusch_pravo_priobreteniya_doli_time_span": 60,
                u'necessary_votes_for_general_meeting_decisions': {
                    u"company_strategy": NecessaryVotesEnum.NV_ALL,
                    u"articles_change": NecessaryVotesEnum.NV_3_4,
                    u"executives_formation": NecessaryVotesEnum.NV_2_3,
                    u"auditor_election": NecessaryVotesEnum.NV_2_3,
                    u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                    u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                    u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                    u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                    u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                    u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                    u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                    u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                    u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                    u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                    u"other_issues": NecessaryVotesEnum.NV_2_3
                },
                u"board_of_directors": False,
                u"selected_secretary": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"selected_moderator": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"pravo_otchuzhdeniya_type": 5,
                u"perehod_doli_k_naslednikam_soglasie": True,
                u"taxation_type": "usn",
                u"registration_way": "some_founders",
                u"region": u"Санкт-Петербург"
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/finalise/', data={'batch_id': batch_id})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch._documents[0].file)

    @authorized()
    def test_render_garant_letter_subarenda(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_GARANT_LETTER_SUBARENDA]

        uchreditel_fis_lico_person = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокл",
            "surname": u"Поликарпов",
            "patronymic": u"Поликарпович",
            "inn": "781108730780",
            "birthdate": datetime.now() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": "male",
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now() - timedelta(days=365 * 2),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "ogrnip": "123456789012345",
            "person_type": PersonTypeEnum.PT_RUSSIAN,
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"НовоПушкинскийСуперДлинноеНазваниеТакогоВообщеНеБывает",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гадюкино",
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
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        sqldb.session.add(uchreditel_fis_lico_person)
        sqldb.session.commit()

        uchreditel_rus_jur_lico_company = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "full_name": u"Протон",
            "short_name": u"Про",
            "kpp": "999999999",
            "company_type": CompanyTypeEnum.CT_RUSSIAN,
            "general_manager": {
                "_id": uchreditel_fis_lico_person.id,
                "type": "person"
            },
            "general_manager_caption": u"директор",
            "address": {
                "region": RFRegionsEnum.RFR_IRKUTSKAYA_REGION,
                "index": 123131,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "2",
                "building_type": BuildingTypeEnum.BIT_HOUSING,
                "building": "778899",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "2",
                "ifns": 1234
            },
            "phone": "+7(812)1234567"
        })
        sqldb.session.add(uchreditel_rus_jur_lico_company)
        sqldb.session.commit()

        with self.app.app_context():
            data = {
                u"full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
                u"short_name": u"Бокс",
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
                u"address_type": "office_address",
                u"starter_capital": {
                    "currency": "rub",
                    "value": "12312.234234"
                },
                u"general_manager_caption": u"повелитель",
                u"share_type": "percent",
                u"founders": [
                    {
                        "founder": {
                            "_id": uchreditel_rus_jur_lico_company.id,
                            "type": "company"
                        },
                        "nominal_capital": 12312.22,
                        "share": 85
                    },
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person.id,
                            "type": "person"
                        },
                        "nominal_capital": 1500.5,
                        "share": 15
                    }
                ],
                u"general_manager": {
                    "_id": uchreditel_fis_lico_person.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                u"doc_obtain_person": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"obtain_way": "founder",
                u'use_foreign_company_name': False,
                u'use_national_language_company_name': False,
                u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
                u'general_manager_term': 20,
                u"preimusch_pravo_priobreteniya_doli_time_span": 60,
                u'necessary_votes_for_general_meeting_decisions': {
                    u"company_strategy": NecessaryVotesEnum.NV_ALL,
                    u"articles_change": NecessaryVotesEnum.NV_3_4,
                    u"executives_formation": NecessaryVotesEnum.NV_2_3,
                    u"auditor_election": NecessaryVotesEnum.NV_2_3,
                    u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                    u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                    u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                    u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                    u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                    u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                    u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                    u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                    u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                    u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                    u"other_issues": NecessaryVotesEnum.NV_2_3
                },
                u"board_of_directors": False,
                u"selected_secretary": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"selected_moderator": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"pravo_otchuzhdeniya_type": 5,
                u"perehod_doli_k_naslednikam_soglasie": True,
                u"taxation_type": "usn",
                u"registration_way": "some_founders",
                u"region": u"Санкт-Петербург"
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)

            result = self.test_client.post('/batch/finalise/', data={'batch_id': batch_id})
            self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)
            self.assertTrue(not not db_batch._documents[0].file)

    @authorized()
    def test_send_please_finalise_email(self):
        # Триггер: в 9 утра местного времени на следующий день после последнего /update/, но не ранее чем через 24 часа.
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_CONTRACT]

        founder = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Прокла",
            "surname": u"Поликарпова",
            "inn": "781108730780",
            "birthdate": datetime.utcnow() - timedelta(days=365 * 30),
            "birthplace": u"Россия, деревня Гадюкино",
            "sex": GenderEnum.G_FEMALE,
            "passport": {
                "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
                "series": u"1123",
                "number": u"192837",
                "issue_date": datetime.now(),
                "issue_depart": u"УМВД Гадюкинского района Гадюкинской области",
                "depart_code": u"111987"
            },
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 198209,
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4"
            },
            "phone": "+79210001122"
        })
        sqldb.session.add(founder)
        sqldb.session.commit()

        founder_otvetstvennyi = PrivatePersonDbObject(**{
            "_owner": self.user,
            "name": u"Семен",
            "surname": u"Семенчук",
            "inn": "781108730780",
            "sex": "male",
            "birthdate": datetime.utcnow() - timedelta(days=365 * 30),
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
                "street_type": StreetTypeEnum.STT_BOULEVARD,
                "street": u"Мотоциклистов",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "4"
            },
            "phone": "+79210001122"
        })
        sqldb.session.add(founder_otvetstvennyi)
        sqldb.session.commit()

        company_founder = CompanyDbObject(**{
            "_owner": self.user,
            "ogrn": "1095543023135",
            "inn": "781108730780",
            "kpp": "999999999",
            "general_manager_caption": u"генеральный директор",
            "incorporation_form": IncorporationFormEnum.IF_LLC,
            "full_name": u"Том и \"Джерри\"",
            "short_name": u"Т и \"Д\"",
            "general_manager": {
                "_id": founder_otvetstvennyi.id,
                "type": "person"
            },
            "address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 123131,
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "2",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "2",
            },
            "phone": "+7(812)1234567"
        })
        sqldb.session.add(company_founder)
        sqldb.session.commit()

        input = {
            u"full_name": u"ТестКреатеЛтдАдд1КомпаниНевДиректор",
            "address": {
                'index': 199000,
                "region": RFRegionsEnum.RFR_LENINGRADSKAYA_REGION,
                "district_type": DistrictTypeEnum.DIT_DISTRICT,
                "district": u"Гатчинский",
                "city_type": CityTypeEnum.CIT_CITY,
                "city": u"Гатчина",
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Радищева",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "26",
                "flat_type": FlatTypeEnum.FLT_FLAT,
                "flat": "80",
                "ifns": 1234
            },
            "address_type": "office_address",
            "starter_capital": {
                "currency": "rub",
                "value": "12312.234234"
            },
            "general_manager_caption": u"повелитель",
            "share_type": "percent",
            "founders": [
                {
                    "founder": {
                        "_id": company_founder.id,
                        "type": "company"
                    },
                    "nominal_capital": 12312.22,
                    "share": 85
                },
                {
                    "founder": {
                        "_id": founder_otvetstvennyi.id,
                        "type": "person"
                    },
                    "nominal_capital": 1500.5,
                    "share": 15
                }
            ],
            "general_manager": {
                "_id": founder_otvetstvennyi.id
            },
            "job_main_code": u"92.31.1",
            "job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
            "doc_obtain_person": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "obtain_way": "founder",
            u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
            u'general_manager_term': 20,
            u"preimusch_pravo_priobreteniya_doli_time_span": 60,
            u'necessary_votes_for_general_meeting_decisions': NECESSARY_VOTES_FOR_GENERAL_MEETING_DECISIONS,
            "board_of_directors": False,
            "selected_secretary": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "selected_moderator": {
                "type": "person",
                "_id": founder_otvetstvennyi.id
            },
            "pravo_otchuzhdeniya_type": 5,
            "short_name": u"ТестКреатеЛтдАдд1КомпаниНевДиректор",
            "perehod_doli_k_naslednikam_soglasie": True,
            "taxation_type": "eshn",
            "registration_way": "some_founders",
            "region": u"Санкт-Петербург"
        }

        with self.app.app_context():
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=input,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': batch_id,
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()

    @authorized()
    def test_profiling(self):
        DocRequisitiesStorage._BATCH_DESCRIPTORS[DocumentBatchTypeEnum.DBT_NEW_LLC]['doc_types'] = [DocumentTypeEnum.DT_P11001]
        # for n in xrange(200):
        #     self.create_company(self.user)
        #     self.create_person(self.user)
        #     self.create_batch('llc', self.user)

        uchreditel_fis_lico_person = self.create_person(self.user, name=u"Прокл", surname=u"Поликарпов", patronymic=u"Поликарпович")
        uchreditel_fis_lico_person2 = self.create_person(self.user, name=u"Прокл", surname=u"Поликарпов", patronymic=u"Поликарпович")
        uchreditel_fis_lico_person3 = self.create_person(self.user, name=u"Прокл", surname=u"Поликарпов", patronymic=u"Поликарпович")
        general_manager_person = self.create_person(self.user, name=u"Прокл", surname=u"Поликарпов", patronymic=u"Поликарпович")
        uchreditel_rus_jur_lico_company = self.create_company(
            self.user,
            general_manager=general_manager_person,
            inn="010101417407",
            kpp="999999999",
            ogrn="1095543023135"
        )

        with self.app.app_context():

            data = {
                u"full_name": u"фывафыва",
                u"short_name": u"Бокс",
                "address": {
                    "building": u"6",
                    "city_type": u"г",
                    "street_type": u"ул",
                    "index": 192212,
                    "house": "5",
                    "region": u"Санкт-Петербург",
                    "flat": "7",
                    "building_type": u"к",
                    "street": u"Уланина",
                    "long_form_mode": False,
                    "flat_type": u"кв",
                    "house_type": u"д",
                    "city": u"Санкт-Петербург",
                    "ifns": "1234"
                },
                u"address_type": "office_address",
                u"starter_capital": {
                    "currency": "rub",
                    "value": "12312.5"
                },
                u"general_manager_caption": u"повелитель",
                u"share_type": "percent",
                u"founders": [
                    {
                        "founder": {
                            "_id": uchreditel_rus_jur_lico_company.id,
                            "type": "company"
                        },
                        "nominal_capital": "12312.20",
                        "share": 25
                    },
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person.id,
                            "type": "person"
                        },
                        "nominal_capital": "1500.50",
                        "share": 25
                    },
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person2.id,
                            "type": "person"
                        },
                        "nominal_capital": "1500.50",
                        "share": 25
                    },
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person3.id,
                            "type": "person"
                        },
                        "nominal_capital": "1500.50",
                        "share": 25
                    },
                ],
                u"general_manager": {
                    "_id": general_manager_person.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                # u"job_code_array" : [u"92.31.1", u"74.14", u"10.01.1"],
                u"job_code_array": [],
                u"doc_obtain_founder": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"obtain_way": "founder",
                u'use_foreign_company_name': False,
                u'use_national_language_company_name': False,
                u"tax_type": UsnTaxType.UT_INCOME_MINUS_EXPENSE,
                u'general_manager_term': 20,
                u"preimusch_pravo_priobreteniya_doli_time_span": 60,
                u'necessary_votes_for_general_meeting_decisions': {
                    u"company_strategy": NecessaryVotesEnum.NV_ALL,
                    u"articles_change": NecessaryVotesEnum.NV_3_4,
                    u"executives_formation": NecessaryVotesEnum.NV_2_3,
                    u"auditor_election": NecessaryVotesEnum.NV_2_3,
                    u"annual_reports_approval": NecessaryVotesEnum.NV_3_4,
                    u"profit_distribution": NecessaryVotesEnum.NV_3_4,
                    u"internal_documents_approval": NecessaryVotesEnum.NV_2_3,
                    u"obligations_emission": NecessaryVotesEnum.NV_ALL,
                    u"audit_assignment": NecessaryVotesEnum.NV_2_3,
                    u"large_deals_approval": NecessaryVotesEnum.NV_3_4,
                    u"concern_deals_approval": NecessaryVotesEnum.NV_2_3,
                    u"reorganization_or_liquidation": NecessaryVotesEnum.NV_ALL,
                    u"liquidation_committee_assignment": NecessaryVotesEnum.NV_2_3,
                    u"branch_establishment": NecessaryVotesEnum.NV_3_4,
                    u"other_issues": NecessaryVotesEnum.NV_2_3
                },
                u"board_of_directors": False,
                u"selected_secretary": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"selected_moderator": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person.id
                },
                u"pravo_otchuzhdeniya_type": 5,
                u"perehod_doli_k_naslednikam_soglasie": True,
                u"taxation_type": "usn",
                u"registration_way": "some_founders",
                u"region": u"Санкт-Петербург"
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                data=data,
                paid=True,
                metadata={'_something': "wrong"},
                _owner=self.user
            )
            sqldb.session.add(batch)
            sqldb.session.commit()
            batch_id = batch.id

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                metadata={'_something': "wrong"},
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.db_obj_to_field(new_batch_db_object)
            structure = batch.get_api_structure()
            del structure['batch_type']
            batch_json = json.dumps(structure)
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(batch_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()

#            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            with TimeCalculator('name', self.app.logger, use_profile=True, min_time=0.001):
                result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(batch_id)})
                self.assertEqual(result.status_code, 200)

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
#            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))
            self.assertEqual(db_batch.status, BatchStatusEnum.BS_FINALISED)
            self.assertEqual(len(db_batch._documents), 1)

            our_md5_string = "%s;%s;%s;%s;%s;%s;%s;%s" % ('checkOrder', '450.0', '450.0',
                                                          '450.0', '1', '2', unicode(self.user.id),
                                                          '1234567890')

            m = hashlib.md5()
            m.update(our_md5_string)
            md5val = m.hexdigest().upper()

            result = self.test_client.post('/payment/checkOrder/', data={
                'md5': md5val,
                'shopId': '1',
                'action': 'checkOrder',
                'orderSumAmount': '450.0',
                'orderSumCurrencyPaycash': '450.0',
                'orderSumBankPaycash': '450.0',
                'invoiceId': '2',
                'customerNumber': unicode(self.user.id),
                'orderNumber': "subscription_1"
            })
            self.assertEqual(result.status_code, 200)

    def test_uninitialized_field(self):
        with self.app.app_context():
            field_description = {
                "type": "db_object",
                "cls": "PrivatePerson"
            }
            with TimeCalculator('name', self.app.logger, use_profile=True, min_time=0.001):
                for i in xrange(10000):
                    x = get_uninitialized_field(field_description)

    @authorized(user_id=245)
    def test_get_batch_status(self):
        batch_id = "54d4b370b8ac2f78815a79ca"

        with self.app.app_context():
            result = self.test_client.get('/batch/status/?batch_id=%s' % batch_id)
            self.assertEqual(result.status_code, 200)

    @authorized()
    def test_get_batch_with_pay_info(self):
        batch = self.create_batch("llc", self.user)

        with self.app.app_context():
            result = self.test_client.get('/batch/?batch_id=%s' % batch.id)
            self.assertEqual(result.status_code, 200)


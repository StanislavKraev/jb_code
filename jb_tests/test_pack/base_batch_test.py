# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from random import randint

from base_test_case import BaseTestCase
from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import RFRegionsEnum, FlatTypeEnum, BuildingTypeEnum, HouseTypeEnum, StreetTypeEnum
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import PrivatePersonDbObject, BatchDocumentDbObject, CompanyDbObject
from fw.documents.enums import PersonDocumentTypeEnum, PersonTypeEnum
from services.car_assurance.db_models import CarAssurance, CarAssuranceBranch
from services.ifns.data_model.models import IfnsCatalogObject


class BaseBatchTestCase(BaseTestCase):
    def setUp(self):
        super(BaseBatchTestCase, self).setUp()
        self.maxDiff = None
        self.events = []
        BatchManager.register_event_consumer('test_logger', self)

    def create_batch(self, batch_type, owner, do_not_save_to_db=False, status=None):
        manager = BatchManager.init(batch_type=batch_type)
        batch = manager.create_batch(owner)
        if status is not None:
            batch.status = status
        if not do_not_save_to_db:
            sqldb.session.add(batch)
            sqldb.session.commit()
        return batch

    def create_document(self, document_type, batch, data=None):
        doc = BatchDocumentDbObject(
            _owner=batch._owner,
            document_type=document_type,
            batch=batch,
            data=data or {},
            status='new',
            caption='caption'
        )
        sqldb.session.add(doc)
        sqldb.session.commit()
        return doc

    def on_event(self, batch_id, event, event_data, logger):
        self.events.append({
            'batch_id': batch_id,
            'event': event,
            'event_data': event_data
        })

    def make_address(self):
        return {
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
            "ifns": 7806
        }

    def create_person(self, owner, batch_id=None,
                      name=u"Трофим",
                      surname=u"Соболенко",
                      patronymic=None,
                      age=40,
                      birthplace=u"неизвестно где",
                      sex='male',
                      inn=781108730780,
                      phone="+79001231313",
                      passport=None,
                      address=None,
                      email=None,
                      person_type=PersonTypeEnum.PT_RUSSIAN,
                      do_not_save_to_db=False
                      ):
        passport = passport or {
            "document_type": PersonDocumentTypeEnum.PD_INTERNAL,
            "series": "4000",
            "number": "111222",
            "issue_date": datetime.now() - timedelta(days=1),
            "issue_depart": u"неизвестно кем",
            "depart_code": "111-222",
            "citizenship": u"РФ"
        }
        person = PrivatePersonDbObject(
            _owner=owner,
            _batch_id=batch_id,
            name=name,
            surname=surname,
            patronymic=patronymic,
            birthdate=datetime.utcnow() - timedelta(days=365 * age),
            birthplace=birthplace,
            sex=sex,
            inn=inn,
            phone=phone,
            passport=passport,
            address=address or self.make_address(),
            email=email,
            person_type=person_type
        )
        if not do_not_save_to_db:
            sqldb.session.add(person)
            sqldb.session.commit()
        return person

    def create_company(self, owner, batch_id=None, general_manager=None, inn=None, kpp=None, ogrn=None):
        company = CompanyDbObject(
            _owner=owner,
            _batch_id=batch_id,
            full_name = u"Компания",
            short_name = u"Ко",
            address = self.make_address(),
        )
        if general_manager:
            company.general_manager = {
                '_id': general_manager.id,
                'type': 'person'
            }
        if inn:
            company.inn = inn
        if kpp:
            company.kpp = kpp
        if ogrn:
            company.ogrn = ogrn

        sqldb.session.add(company)
        sqldb.session.commit()
        return company

    def addCarAssurance(self, assurance_name):
        obj = CarAssurance(
            full_name=assurance_name,
            short_name=assurance_name,
            connection_name=assurance_name,
            address=""
        )
        sqldb.session.add(obj)
        sqldb.session.commit()
        return obj

    def addCarAssuranceBranch(self, assurance=None, region=None):
        region = region or RFRegionsEnum.RFR_LENINGRADSKAYA_REGION
        obj = CarAssuranceBranch(
            title=u'title',
            phone=u'112',
            car_assurance=assurance,
            address=u"дер. Поганкино д. 13",
            region=region
        )
        sqldb.session.add(obj)
        sqldb.session.commit()
        return obj

    def addRegIfns(self, name, code=None, address=None):

        address = address or {
            "city_type": u"г",
            "qc_complete": u"5",
            "street_type": u"ул",
            "index": 450076,
            "house": u"52",
            "region": u"Башкортостан",
            "okato": u"80401380000",
            "address_string": u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
            "qc": u"0",
            "street": u"Красина",
            "coord_lat": u"54.733428",
            "coord_long": u"55.934008",
            "house_type": u"д",
            "source_address": u",450076,,,Уфа г,,Красина ул,52,,",
            "ifns": u"0274",
            "city": u"Уфа"
        }

        new_item = IfnsCatalogObject(**{
            u"code": code or randint(100, 9999),
            u"comment": u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
            u"tel": [
                u"+7(347)2290200",
                u"+7(347)2290210"
            ],
            u"name": name,
            "plat": {
                u"recipient_inn": u"0275067000",
                u"recipient_kpp": u"027501001",
                u"recipient_name": name
            },
            "address": address
        })
        sqldb.session.add(new_item)
        sqldb.session.commit()

        return new_item

    def addIfns(self, name, reg_ifns, address=None, code = None):
        address = address or {
            "city_type": u"г",
            "qc_complete": u"5",
            "street_type": u"ул",
            "index": 450076,
            "house": u"52",
            "region": u"Башкортостан",
            "okato": u"80401380000",
            "address_string": u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
            "qc": u"0",
            "street": u"Красина",
            "coord_lat": u"54.733428",
            "coord_long": u"55.934008",
            "house_type": u"д",
            "source_address": u",450076,,,Уфа г,,Красина ул,52,,",
            "ifns": u"0274",
            "city": u"Уфа"
        }

        code = code or randint(100, 9999)

        new_item = IfnsCatalogObject(**{
            u"code": code,
            u"comment": u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
            u"tel": [
                u"+7(347)2290200",
                u"+7(347)2290210"
            ],
            u"name": name,
            "plat": {
                u"recipient_inn": u"0275067000",
                u"recipient_kpp": u"027501001",
                u"recipient_name": name
            },
            "address": address,
            "rou": {
                u"_id": reg_ifns['_id'],
                u"code": str(code) + "0",
                u"tel": [
                    u"+7(347)2290200",
                    u"+7(347)2290210"
                ],
                "name": reg_ifns['name'],
                "address": {
                    "city_type": u"г",
                    "qc_complete": u"5",
                    "street_type": u"ул",
                    "index": 450076,
                    "house": u"52",
                    "region": u"Башкортостан",
                    "okato": u"80401380000",
                    "address_string": u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    "qc": u"0",
                    "street": u"Красина",
                    "coord_lat": u"54.733428",
                    "coord_long": u"55.934008",
                    "house_type": u"д",
                    "ifns": str(code) + '0',
                    "city": u"Уфа"
                }
            },

        })
        sqldb.session.add(new_item)
        sqldb.session.commit()

        return new_item

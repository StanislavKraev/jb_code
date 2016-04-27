# -*- coding: utf-8 -*-
from copy import copy
from random import randint
from datetime import datetime, timedelta
import os
from fw.api.args_validators import DateTimeValidator, DateTypeValidator
from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import RFRegionsEnum
from fw.documents.address_enums import DistrictTypeEnum
from fw.documents.address_enums import CityTypeEnum
from fw.documents.address_enums import StreetTypeEnum
from fw.documents.address_enums import HouseTypeEnum
from fw.documents.address_enums import BuildingTypeEnum
from fw.documents.address_enums import FlatTypeEnum
from fw.documents.db_fields import DocumentBatchDbObject, PrivatePersonDbObject, CompanyDbObject, BatchDocumentDbObject
from fw.documents.enums import DocumentBatchTypeEnum, PersonTypeEnum, PersonDocumentTypeEnum, CompanyTypeEnum, \
    BatchStatusEnum
from fw.documents.enums import DocumentTypeEnum
from fw.documents.fields.doc_fields import DocumentBatch, UserDocument
from fw.documents.fields.simple_doc_fields import DocDateTimeField
from fw.storage.models import FileObject
from services.ifns.data_model.fields import IfnsBooking
from services.ifns.data_model.models import IfnsBookingObject, IfnsCatalogObject
from services.llc_reg.documents.enums import UsnTaxType, IfnsServiceEnum, FounderTypeEnum, CompanyStarterCapitalTypeEnum
from services.llc_reg.documents.enums import NecessaryVotesEnum
from services.notarius.data_model.models import NotariusObject, NotariusBookingObject
from services.yurist.data_model.enums import YuristBatchCheckStatus
from services.yurist.data_model.fields import YuristBatchCheck
from services.yurist.data_model.models import YuristBatchCheckObject
from test_pack.base_batch_test import BaseBatchTestCase

os.environ['CELERY_CONFIG_MODULE'] = 'local_celery_config'

import html5lib
from lxml.cssselect import CSSSelector
from flask import json, current_app
from bson.objectid import ObjectId
import requests
from manage_commands.batch_commands import CheckBatchIfnsRegStatusCommand

from test_pack.test_api import authorized


class ThirdPartiesApiTestCase(BaseBatchTestCase):
    @authorized()
    def test_get_notarius_list(self):
        batch = DocumentBatchDbObject(
            _owner=self.user,
            batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
        )
        sqldb.session.add(batch)
        sqldb.session.commit()

        doc = BatchDocumentDbObject(
            _owner=self.user,
            batch=batch,
            document_type='test_doc',
            data={
                'address': {
                    'region': u'Санкт-Петербург'
                }
            }
        )
        sqldb.session.add(doc)
        sqldb.session.commit()

        test_notarius = NotariusObject(**{
            "id": "abc",
            "name": u"Петр",
            "surname": u"Мандельштейн",
            "title": u"Нотариус №1",
            "schedule": {
                "type": "cyclic",
                "start_working_day": "2014-08-20",
                "working_days_count": 1,
                "weekends_count": 2,
                "start_time": "10:00",
                "end_time": "13:00"
            },
            "address": {
                "index": 199000,
                "street_type": u"пр-кт",
                "street": u"Народного Ополчения",
                "house_type": u"д",
                "house": "15"
            },
            "region": u"Санкт-Петербург"
        })

        test_notarius2 = NotariusObject(**{
            "id": "def",
            "name": u"Валерия",
            "surname": u"Александрович",
            "title": u"Нотариус №-1",
            "schedule": {
                "type": "normal",
                "weekends": [5, 6, 7],
                "start_time": "11:00",
                "end_time": "18:00",
                "lunch_start": "13:00",
                "lunch_end": "16:30"
            },
            "address": {
                "index": 190000,
                "street_type": u"ул",
                "street": u"Партизана Германа",
                "house_type": u"д",
                "house": "15"
            },
            "region": u"Санкт-Петербург"
        })
        sqldb.session.add(test_notarius)
        sqldb.session.add(test_notarius2)
        sqldb.session.commit()

        result = self.test_client.get(u'/meeting/notarius/?batch_id=%s' % batch.id)
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertIn('result', data)

        self.assertEqual(len(data['result']), 2)
        del data['result'][0]['id']
        del data['result'][1]['id']
        self.maxDiff = None
        self.assertEqual(data['result'][0], {
            u'surname': u'Мандельштейн',
            u'name': u'Петр',
            u'schedule': [{
                              u'slot_end': u'10:30',
                              u'slot_start': u'10:00'
                          }, {u'slot_end': u'11:00', u'slot_start': u'10:30'},
                          {u'slot_end': u'11:30', u'slot_start': u'11:00'},
                          {u'slot_end': u'12:00', u'slot_start': u'11:30'},
                          {u'slot_end': u'12:30', u'slot_start': u'12:00'},
                          {u'slot_end': u'13:00', u'slot_start': u'12:30'}],
            u'region': {
                u'code': u'Санкт-Петербург',
                u'title': u'Санкт-Петербург'
            },
            u'title': u'Нотариус №1',
            u'caption': u'(1 \u0434\u043d\u044f \u0447\u0435\u0440\u0435\u0437 2 \u0434\u043d\u044f) \u2014 \u041d\u043e\u0442\u0430\u0440\u0438\u0443\u0441 \u21161, \u043f\u0440-\u043a\u0442 \u041d\u0430\u0440\u043e\u0434\u043d\u043e\u0433\u043e \u041e\u043f\u043e\u043b\u0447\u0435\u043d\u0438\u044f, \u0434. 15',
            u'address': {
                u'house': u'15',
                u'street': u'\u041d\u0430\u0440\u043e\u0434\u043d\u043e\u0433\u043e \u041e\u043f\u043e\u043b\u0447\u0435\u043d\u0438\u044f',
                u'index': 199000,
                u'street_type': u'\u043f\u0440-\u043a\u0442',
                u'house_type': u'\u0434'
            },
            u'working_hours': u'1 \u0434\u043d\u044f \u0447\u0435\u0440\u0435\u0437 2 \u0434\u043d\u044f'})

        self.maxDiff = None
        self.assertEqual(data['result'][1], {
            u'surname': u'\u0410\u043b\u0435\u043a\u0441\u0430\u043d\u0434\u0440\u043e\u0432\u0438\u0447',
            u'name': u'\u0412\u0430\u043b\u0435\u0440\u0438\u044f',
            u'schedule': [
                {u'slot_end': u'11:30', u'slot_start': u'11:00'},
                {u'slot_end': u'12:00', u'slot_start': u'11:30'},
                {u'slot_end': u'12:30', u'slot_start': u'12:00'},
                {u'slot_end': u'13:00', u'slot_start': u'12:30'},
                {u'slot_end': u'17:00', u'slot_start': u'16:30'},
                {u'slot_end': u'17:30', u'slot_start': u'17:00'},
                {u'slot_end': u'18:00', u'slot_start': u'17:30'}],
            u'region': {
                u'code': u'\u0421\u0430\u043d\u043a\u0442-\u041f\u0435\u0442\u0435\u0440\u0431\u0443\u0440\u0433',
                u'title': u'\u0421\u0430\u043d\u043a\u0442-\u041f\u0435\u0442\u0435\u0440\u0431\u0443\u0440\u0433'},
            u'title': u'\u041d\u043e\u0442\u0430\u0440\u0438\u0443\u0441 \u2116-1',
            u'caption': u'(\u0441 11:00 \u0434\u043e 18:00 \u0441 \u043f\u0435\u0440\u0435\u0440\u044b\u0432\u043e\u043c \u043d\u0430 \u043e\u0431\u0435\u0434 \u0441 13:00 \u0434\u043e 16:30, \u043f\u0442, \u0441\u0431, \u0432\u0441 - \u0432\u044b\u0445\u043e\u0434\u043d\u043e\u0439) \u2014 \u041d\u043e\u0442\u0430\u0440\u0438\u0443\u0441 \u2116-1, \u0443\u043b. \u041f\u0430\u0440\u0442\u0438\u0437\u0430\u043d\u0430 \u0413\u0435\u0440\u043c\u0430\u043d\u0430, \u0434. 15',
            u'address': {u'house': u'15',
                         u'street': u'\u041f\u0430\u0440\u0442\u0438\u0437\u0430\u043d\u0430 \u0413\u0435\u0440\u043c\u0430\u043d\u0430',
                         u'index': 190000, u'street_type': u'\u0443\u043b', u'house_type': u'\u0434'},
            u'working_hours': u'с 11:00 до 18:00 с перерывом на обед с 13:00 до 16:30, пт, сб, вс - выходной'
        })

    @authorized()
    def test_get_notarius_schedule(self):
        test_notarius = NotariusObject(**{
            "id": "abc",
            "name": u"Петр",
            "surname": u"Мандельштейн",
            "title": u"Нотариус №1",
            "schedule": {
                "type": "cyclic",
                "start_working_day": "2014-08-20",
                "working_days_count": 1,
                "weekends_count": 2,
                "start_time": "10:00",
                "end_time": "13:00"
            },
            "address": {
                "index": 199000,
                "street_type": u"пр-кт",
                "street": u"Народного Ополчения",
                "house_type": u"д",
                "house": "33"
            },
            "region": u"Санкт-Петербург"
        })

        test_notarius2 = NotariusObject(**{
            "id": "def",
            "name": u"Валерия",
            "surname": u"Александрович",
            "title": u"Нотариус №-1",
            "schedule": {
                "type": "normal",
                "weekends": [],
                "start_time": "10:00",
                "end_time": "13:00"
            },
            "address": {
                "index": 190000,
                "street_type": u"ул",
                "street": u"Партизана Германа",
                "house_type": u"д",
                "house": "15"
            },
            "region": u"Санкт-Петербург"
        })

        sqldb.session.add(test_notarius)
        sqldb.session.add(test_notarius2)
        sqldb.session.commit()

        _id2 = test_notarius2.id
        dd = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")
        result = self.test_client.get('/meeting/notarius/schedule/?notarius_id=%s&datetime=%s' % (str(_id2), (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")))
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertIn('result', data)

        self.maxDiff = None
        self.assertEqual(data['result'], {
            'nearest_time': dd,
            'slots': [
                {'slot_start': '10:00', 'slot_end': '10:30'},
                {'slot_start': '10:30', 'slot_end': '11:00'},
                {'slot_start': '11:00', 'slot_end': '11:30'},
                {'slot_start': '11:30', 'slot_end': '12:00'},
                {'slot_start': '12:00', 'slot_end': '12:30'},
                {'slot_start': '12:30', 'slot_end': '13:00'},
            ]
        })

    @authorized()
    def test_get_notarius_schedule_w_lunch(self):
        test_notarius = NotariusObject(**{
            "id": "abc",
            "name": u"Петр",
            "surname": u"Мандельштейн",
            "title": u"Нотариус №1",
            "schedule": {
                "type": "cyclic",
                "start_working_day": "2014-08-20",
                "working_days_count": 1,
                "weekends_count": 2,
                "start_time": "10:00",
                "end_time": "13:00"
            },
            "address": {
                "index": 199000,
                "street_type": u"пр-кт",
                "street": u"Народного Ополчения",
                "house_type": u"д",
                "house": "33"
            },
            "region": u"Санкт-Петербург"
        })

        test_notarius2 = NotariusObject(**{
            "id": "def",
            "name": u"Валерия",
            "surname": u"Александрович",
            "title": u"Нотариус №-1",
            "schedule": {
                "type": "normal",
                "weekends": [5, 6, 7],
                "start_time": "11:00",
                "end_time": "18:00",
                "lunch_start": "13:00",
                "lunch_end": "16:30"
            },
            "address": {
                "index": 190000,
                "street_type": u"ул",
                "street": u"Партизана Германа",
                "house_type": u"д",
                "house": "15"
            },
            "region": u"Санкт-Петербург"
        })

        sqldb.session.add(test_notarius)
        sqldb.session.add(test_notarius2)
        sqldb.session.commit()
        _id = test_notarius2.id
        dt = datetime.utcnow() + timedelta(days=1)
        result = self.test_client.get('/meeting/notarius/schedule/?notarius_id=%s&datetime=%s' % (str(_id), dt.strftime("%Y-%m-%d")))
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertIn('result', data)

        self.assertEqual(data['result'], {
            'nearest_time': '%sT00:00:00' % dt.strftime("%Y-%m-%d"),
            'slots': [
                {'slot_start': '11:00', 'slot_end': '11:30'},
                {'slot_start': '11:30', 'slot_end': '12:00'},
                {'slot_start': '12:00', 'slot_end': '12:30'},
                {'slot_start': '12:30', 'slot_end': '13:00'},
                # lunch
                {'slot_start': '16:30', 'slot_end': '17:00'},
                {'slot_start': '17:00', 'slot_end': '17:30'},
                {'slot_start': '17:30', 'slot_end': '18:00'},
            ]
        })

    @authorized()
    def test_get_notarius_schedule_w_lunch_some_reserved(self):
        test_notarius = NotariusObject(**{
            "id": "abc",
            "name": u"Петр",
            "surname": u"Мандельштейн",
            "title": u"Нотариус №1",
            "schedule": {
                "type": "cyclic",
                "start_working_day": "2014-08-20",
                "working_days_count": 1,
                "weekends_count": 2,
                "start_time": "10:00",
                "end_time": "13:00"
            },
            "address": {
                "index": 199000,
                "street_type": u"пр-кт",
                "street": u"Народного Ополчения",
                "house_type": u"д",
                "house": "33"
            },
            "region": u"Санкт-Петербург"
        })

        test_notarius2 = NotariusObject(**{
            "id": "def",
            "name": u"Валерия",
            "surname": u"Александрович",
            "title": u"Нотариус №-1",
            "schedule": {
                "type": "normal",
                "weekends": [],
                "start_time": "11:00",
                "end_time": "18:00",
                "lunch_start": "13:00",
                "lunch_end": "16:30"
            },
            "address": {
                "index": 190000,
                "street_type": u"ул",
                "street": u"Партизана Германа",
                "house_type": u"д",
                "house": "15"
            },
            "region": u"Санкт-Петербург"
        })

        sqldb.session.add(test_notarius)
        sqldb.session.add(test_notarius2)
        sqldb.session.commit()

        _id = test_notarius2.id

        dt = datetime.utcnow() + timedelta(days=1)
        book1 = NotariusBookingObject(notarius_id=_id, address=u"address", owner=self.user,
                                     dt=datetime.strptime("%sT12:30:00" % dt.strftime("%Y-%m-%d"), DocDateTimeField.FORMAT))
        sqldb.session.add(book1)

        book2 = NotariusBookingObject(notarius_id=_id, address=u"address", owner=self.user,
                                     dt=datetime.strptime("%sT17:00:00" % dt.strftime("%Y-%m-%d"), DocDateTimeField.FORMAT))
        sqldb.session.add(book2)
        book3 = NotariusBookingObject(notarius_id=_id, address=u"address", owner=self.user,
                                     dt=datetime.strptime("%sT17:30:00" % dt.strftime("%Y-%m-%d"), DocDateTimeField.FORMAT))
        sqldb.session.add(book3)

        book = NotariusBookingObject(notarius_id=_id, address=u"address", owner=self.user,
                                    dt=datetime.strptime("%sT12:30:00" % dt.strftime("%Y-%m-%d"), DocDateTimeField.FORMAT))
        sqldb.session.add(book)
        book = NotariusBookingObject(notarius_id=_id, address=u"address", owner=self.user,
                                    dt=datetime.strptime("%sT17:00:00" % dt.strftime("%Y-%m-%d"), DocDateTimeField.FORMAT))
        sqldb.session.add(book)
        book = NotariusBookingObject(notarius_id=_id, address=u"address", owner=self.user,
                                    dt=datetime.strptime("%sT17:30:00" % dt.strftime("%Y-%m-%d"), DocDateTimeField.FORMAT))
        sqldb.session.add(book)
        sqldb.session.commit()

        result = self.test_client.get('/meeting/notarius/schedule/?notarius_id=%s&datetime=%s' % (str(_id), dt.strftime("%Y-%m-%d")))
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertIn('result', data)

        self.assertEqual(data['result'], {
            'nearest_time': '%sT00:00:00' % dt.strftime("%Y-%m-%d"),
            'slots': [
                {'slot_start': '11:00', 'slot_end': '11:30'},
                {'slot_start': '11:30', 'slot_end': '12:00'},
                {'slot_start': '12:00', 'slot_end': '12:30'},
                # lunch
                {'slot_start': '16:30', 'slot_end': '17:00'},
            ]
        })

    @authorized()
    def test_reserve_notarius_time_slot(self):
        self.maxDiff = None
        test_notarius = NotariusObject(**{
            "id": "abc",
            "name": u"Петр",
            "surname": u"Мандельштейн",
            "title": u"Нотариус №1",
            "schedule": {
                "type": "cyclic",
                "start_working_day": datetime.now().strftime("%Y-%m-%d"),
                "working_days_count": 1,
                "weekends_count": 2,
                "start_time": "10:00",
                "end_time": "12:00",
            },
            "address": {
                "index": 199000,
                "street_type": u"пр-кт",
                "street": u"Народного Ополчения",
                "house_type": u"д",
                "house": "33"
            },
            "region": u"Санкт-Петербург"
        })
        sqldb.session.add(test_notarius)
        sqldb.session.commit()

        batch = DocumentBatchDbObject(
            _owner=self.user,
            batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
            data={},
        )
        sqldb.session.add(batch)
        sqldb.session.commit()

        _id = test_notarius.id
        dt = datetime.utcnow() + timedelta(days=1)
        self.assertEqual(len(self.mailer.mails), 0)
        result = self.test_client.post('/meeting/notarius/create/',
                                       data={'notarius_id': str(_id), 'datetime': '%sT10:00:00' % dt.strftime("%Y-%m-%d"),
                                             "batch_id": unicode(batch.id)})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(self.mailer.mails), 1)
        self.assertEqual(self.mailer.mails[0]['to'], self.config['NOTARIUS_EMAIL_LIST'][0])

        data = json.loads(result.data)
        self.assertIn('result', data)
        self.assertTrue(data['result'])

        booking = NotariusBookingObject.query.scalar()
        self.assertIsNotNone(booking)
        filter_keys = lambda x, keys: dict([(k, v) for k, v in x.items() if k in keys])
        self.assertEqual(filter_keys(booking.__dict__, ('address', 'dt', 'owner_id', 'notarius_id', '_discarded')), {
            u'address': u'199000, \u043f\u0440\u043e\u0441\u043f\u0435\u043a\u0442 \u041d\u0430\u0440\u043e\u0434\u043d\u043e\u0433\u043e \u041e\u043f\u043e\u043b\u0447\u0435\u043d\u0438\u044f, \u0434\u043e\u043c 33',
            u'dt': datetime(dt.year, dt.month, dt.day, 10, 0),
            u'notarius_id': _id,
            u'owner_id': self.user.id,
            u'_discarded': False
        })

    @authorized()
    def test_reserve_notarius_time_slot_to_specific_batch(self):
        self.maxDiff = None
        test_notarius = NotariusObject(**{
            "id": "abc",
            "name": u"Петр",
            "surname": u"Мандельштейн",
            "title": u"Нотариус №1",
            "schedule": {
                "type": "cyclic",
                "start_working_day": "2014-08-20",
                "working_days_count": 1,
                "weekends_count": 2,
                "start_time": "10:00",
                "end_time": "13:00"
            },
            "address": {
                "index": 199000,
                "street_type": u"пр-кт",
                "street": u"Народного Ополчения",
                "house_type": u"д",
                "house": "33"
            },
            "region": u"Санкт-Петербург"
        })

        test_notarius2 = NotariusObject(**{
            "id": "def",
            "name": u"Валерия",
            "surname": u"Александрович",
            "title": u"Нотариус №-1",
            "schedule": {
                "type": "normal",
                "weekends": [],
                "start_time": "09:00",
                "end_time": "18:00",
                "lunch_start": "13:00",
                "lunch_end": "16:30"
            },
            "address": {
                "index": 190000,
                "street_type": u"ул",
                "street": u"Партизана Германа",
                "house_type": u"д",
                "house": "15"
            },
            "region": u"Санкт-Петербург"
        })

        sqldb.session.add(test_notarius)
        sqldb.session.add(test_notarius2)
        sqldb.session.commit()

        _id = test_notarius2.id

        batch = DocumentBatchDbObject(
            _owner=self.user,
            batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
            data={
                'full_name': u"full name"
            }
        )
        sqldb.session.add(batch)
        sqldb.session.commit()
        dt = datetime.utcnow() + timedelta(days=1)
        result = self.test_client.post('/meeting/notarius/create/',
                                       data={'notarius_id': str(_id), 'datetime': '%sT10:00:00' % dt.strftime("%Y-%m-%d"),
                                             'batch_id': batch.id})
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertIn('result', data)
        self.assertTrue(data['result'])

        booking = NotariusBookingObject.query.scalar()
        self.assertIsNotNone(booking)
        filter_keys = lambda x, keys: dict([(k, v) for k, v in x.items() if k in keys])
        self.assertEqual(filter_keys(booking.__dict__, ('address', 'dt', 'owner_id', 'notarius_id', '_discarded')), {
            u'address': u'190000, \u0443\u043b\u0438\u0446\u0430 \u041f\u0430\u0440\u0442\u0438\u0437\u0430\u043d\u0430 \u0413\u0435\u0440\u043c\u0430\u043d\u0430, \u0434\u043e\u043c 15',
            u'dt': datetime(dt.year, dt.month, dt.day, 10, 0),
            u'notarius_id': _id,
            u'owner_id': self.user.id,
            u'_discarded': False
        })

    @authorized()
    def test_unreserve_notarius_time_slot(self):
        self.maxDiff = None
        test_notarius = NotariusObject(**{
            "id": u"abc",
            "name": u"Петр",
            "surname": u"Мандельштейн",
            "title": u"Нотариус №1",
            "schedule": {
                "type": "cyclic",
                "start_working_day": datetime.now().strftime("%Y-%m-%d"),
                "working_days_count": 1,
                "weekends_count": 2,
                "start_time": "10:00",
                "end_time": "12:00",
            },
            "address": {
                "index": 199000,
                "street_type": u"пр-кт",
                "street": u"Народного Ополчения",
                "house_type": u"д",
                "house": "33"
            },
            "region": u"Санкт-Петербург"
        })

        sqldb.session.add(test_notarius)
        sqldb.session.commit()

        _id = test_notarius.id

        batch = DocumentBatchDbObject(
            _owner=self.user,
            batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
            data={
                'full_name': u"full name"
            }
        )
        sqldb.session.add(batch)
        sqldb.session.commit()
        dt = datetime.utcnow() + timedelta(days=1)

        booking = NotariusBookingObject(
            batch=batch,
            owner=self.user,
            notarius=test_notarius,
            dt=dt,
            address=u"тут")
        sqldb.session.add(booking)
        sqldb.session.commit()

        self.assertEqual(len(self.mailer.mails), 0)
        result = self.test_client.post('/meeting/notarius/discard/', data={
            'booking_id': booking.id,
            'batch_id': batch.id
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(self.mailer.mails), 1)
        self.assertEqual(self.mailer.mails[0]['to'], self.config['NOTARIUS_EMAIL_LIST'][0])

        data = json.loads(result.data)
        self.assertIn('result', data)
        self.assertTrue(data['result'])

        self.assertEqual(NotariusBookingObject.query.count(), 1)
        booking = NotariusBookingObject.query.scalar()
        filter_keys = lambda x, keys: dict([(k, v) for k, v in x.items() if k in keys])
        self.assertEqual(filter_keys(booking.__dict__, ('address', 'dt', 'owner_id', 'notarius_id', '_discarded')), {
            u'address': u'тут',
            u'dt': dt,
            u'notarius_id': _id,
            u'owner_id': self.user.id,
            u'_discarded': True
        })

    @authorized()
    def test_get_notarius_list_for_osago(self):
        batch = self.create_batch('osago', self.user)

        test_notarius = NotariusObject(**{
            "id": "abc",
            "name": u"Петр",
            "surname": u"Мандельштейн",
            "title": u"Нотариус №1",
            "schedule": {
                "type": "cyclic",
                "start_working_day": "2014-08-20",
                "working_days_count": 1,
                "weekends_count": 2,
                "start_time": "10:00",
                "end_time": "13:00"
            },
            "address": {
                "index": 199000,
                "street_type": u"пр-кт",
                "street": u"Народного Ополчения",
                "house_type": u"д",
                "house": "33"
            },
            "region": u"Санкт-Петербург"
        })

        test_notarius2 = NotariusObject(**{
            "id": "def",
            "name": u"Валерия",
            "surname": u"Александрович",
            "title": u"Нотариус №-1",
            "schedule": {
                "type": "normal",
                "weekends": [],
                "start_time": "11:00",
                "end_time": "18:00",
                "lunch_start": "13:00",
                "lunch_end": "16:30"
            },
            "address": {
                "index": 190000,
                "street_type": u"ул",
                "street": u"Партизана Германа",
                "house_type": u"д",
                "house": "15"
            },
            "region": u"Санкт-Петербург"
        })

        sqldb.session.add(test_notarius)
        sqldb.session.add(test_notarius2)
        sqldb.session.commit()

        result = self.test_client.get(u'/meeting/notarius/?batch_id=%s' % batch.id)
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertIn('result', data)

        self.assertEqual(len(data['result']), 2)
        del data['result'][0]['id']
        del data['result'][1]['id']
        self.maxDiff = None
        self.assertEqual(data['result'][0], {
            u'surname': u'Мандельштейн',
            u'name': u'Петр',
            u'schedule': [{
                              u'slot_end': u'10:30',
                              u'slot_start': u'10:00'
                          }, {u'slot_end': u'11:00', u'slot_start': u'10:30'},
                          {u'slot_end': u'11:30', u'slot_start': u'11:00'},
                          {u'slot_end': u'12:00', u'slot_start': u'11:30'},
                          {u'slot_end': u'12:30', u'slot_start': u'12:00'},
                          {u'slot_end': u'13:00', u'slot_start': u'12:30'}],
            u'region': {
                u'code': u'Санкт-Петербург',
                u'title': u'Санкт-Петербург'
            },
            u'title': u'Нотариус №1',
            u'caption': u'(1 \u0434\u043d\u044f \u0447\u0435\u0440\u0435\u0437 2 \u0434\u043d\u044f) \u2014 \u041d\u043e\u0442\u0430\u0440\u0438\u0443\u0441 \u21161, \u043f\u0440-\u043a\u0442 \u041d\u0430\u0440\u043e\u0434\u043d\u043e\u0433\u043e \u041e\u043f\u043e\u043b\u0447\u0435\u043d\u0438\u044f, \u0434. 15',
            u'address': {
                u'house': u'15',
                u'street': u'\u041d\u0430\u0440\u043e\u0434\u043d\u043e\u0433\u043e \u041e\u043f\u043e\u043b\u0447\u0435\u043d\u0438\u044f',
                u'index': 199000,
                u'street_type': u'\u043f\u0440-\u043a\u0442',
                u'house_type': u'\u0434'
            },
            u'working_hours': u'1 \u0434\u043d\u044f \u0447\u0435\u0440\u0435\u0437 2 \u0434\u043d\u044f'})

        self.maxDiff = None
        self.assertEqual(data['result'][1], {
            u'surname': u'\u0410\u043b\u0435\u043a\u0441\u0430\u043d\u0434\u0440\u043e\u0432\u0438\u0447',
            u'name': u'\u0412\u0430\u043b\u0435\u0440\u0438\u044f',
            u'schedule': [
                {u'slot_end': u'11:30', u'slot_start': u'11:00'},
                {u'slot_end': u'12:00', u'slot_start': u'11:30'},
                {u'slot_end': u'12:30', u'slot_start': u'12:00'},
                {u'slot_end': u'13:00', u'slot_start': u'12:30'},
                {u'slot_end': u'17:00', u'slot_start': u'16:30'},
                {u'slot_end': u'17:30', u'slot_start': u'17:00'},
                {u'slot_end': u'18:00', u'slot_start': u'17:30'}],
            u'region': {
                u'code': u'\u0421\u0430\u043d\u043a\u0442-\u041f\u0435\u0442\u0435\u0440\u0431\u0443\u0440\u0433',
                u'title': u'\u0421\u0430\u043d\u043a\u0442-\u041f\u0435\u0442\u0435\u0440\u0431\u0443\u0440\u0433'},
            u'title': u'\u041d\u043e\u0442\u0430\u0440\u0438\u0443\u0441 \u2116-1',
            u'caption': u'(\u0441 11:00 \u0434\u043e 18:00 \u0441 \u043f\u0435\u0440\u0435\u0440\u044b\u0432\u043e\u043c \u043d\u0430 \u043e\u0431\u0435\u0434 \u0441 13:00 \u0434\u043e 16:30, \u043f\u0442, \u0441\u0431, \u0432\u0441 - \u0432\u044b\u0445\u043e\u0434\u043d\u043e\u0439) \u2014 \u041d\u043e\u0442\u0430\u0440\u0438\u0443\u0441 \u2116-1, \u0443\u043b. \u041f\u0430\u0440\u0442\u0438\u0437\u0430\u043d\u0430 \u0413\u0435\u0440\u043c\u0430\u043d\u0430, \u0434. 15',
            u'address': {u'house': u'15',
                         u'street': u'\u041f\u0430\u0440\u0442\u0438\u0437\u0430\u043d\u0430 \u0413\u0435\u0440\u043c\u0430\u043d\u0430',
                         u'index': 190000, u'street_type': u'\u0443\u043b', u'house_type': u'\u0434'},
            u'working_hours': u'с 11:00 до 18:00 с перерывом на обед с 13:00 до 16:30, пт, сб, вс - выходной'
        })

    @authorized()
    def test_reserve_ifns_time_slot(self):
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

        with self.app.app_context():
            data = {
                u"full_name": u"фывафыва",
                u"short_name": u"Бокс",
                u"address_type": "general_manager_registration_address",
                u"starter_capital": {
                    "currency": "rub",
                    "value": "10000"
                },
                u"general_manager_caption": u"повелитель",
                u"share_type": "percent",
                u"founders": [
                    {
                        "founder": {
                            "_id": uchreditel_fis_lico_person.id,
                            "type": "person"
                        },
                        "nominal_capital": "1500.50",
                        "share": "100"
                    }
                ],
                u"general_manager": {
                    "_id": uchreditel_fis_lico_person.id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
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

            db_batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
            print (json.dumps(db_batch.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(batch_id)})
            self.assertEqual(result.status_code, 200)

            new_item = IfnsCatalogObject(**{
                'id': str(ObjectId()),
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

            dt = datetime.now() + timedelta(days=1)
            dt = datetime(dt.year, dt.month, dt.day, 12, 30, 0)
            data = {
                u"service": IfnsServiceEnum.IS_REG_COMPANY,
                u"ifns": "7840",
                u"datetime": dt.strftime(DateTimeValidator.FORMAT),
                u"batch_id": batch_id
            }

            db_model = IfnsBookingObject.query.first()
            self.assertIsNone(db_model)

            result = self.test_client.post('/meeting/ifns/create/', data=data)
            self.assertEqual(result.status_code, 200)

            data = json.loads(result.data)
            self.assertIn('result', data)

            db_model = IfnsBookingObject.query.first()
            self.assertIsNotNone(db_model)

            result = self.test_client.get('/meeting/ifns/?batch_id=%s' % db_model.batch_id)
            self.assertEqual(result.status_code, 200)

            data = json.loads(result.data)
            self.assertIn('result', data)
            meeting_list = data['result']

            self.maxDiff = None
            self.assertIsInstance(meeting_list, list)
            self.assertEqual(len(meeting_list), 1)
            del meeting_list[0]['id']
            del meeting_list[0]['date']
            self.assertEqual(meeting_list[0], {
                u'address': u'\u0441\u0435\u043b\u043e \u0413\u0430\u0434\u044e\u043a\u0438\u043d\u043e, \u0443\u043b. \u0420\u0430\u0437\u044a\u0435\u0437\u0436\u0430\u044f 2',
                u'code': u'111',
                u'how_to_get': u'\u043d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u043e',
                u'ifns': u'\u041c\u0435\u0436\u0440\u0430\u0439\u043e\u043d\u043d\u0430\u044f \u0418\u0424\u041d\u0421 \u211610000000',
                u'phone': u'322223233',
                u'service': u'\u0420\u0435\u0433\u0438\u0441\u0442\u0440\u0430\u0446\u0438\u044f \u041e\u041e\u041e',
                u'service_id': u'1',
                u'window': u'-1'
            })

    def test_check_nalog_ru_api(self):
        s = requests.Session()
        result = s.get(u'http://order.nalog.ru/details/')
        self.assertEqual(result.status_code, 200)
        content = result.content.decode('utf-8')
        self.assertIn(u'Онлайн запись на прием в инспекцию', content)
        self.assertIn(u'"ctl00_face_VI"', content)
        self.assertIn(u'"ctl00$face"', content)
        self.assertIn(u'"ctl00_face_RB0_I"', content)
        self.assertIn(u'"ctl00_face_RB1_I"', content)
        self.assertIn(u'"ctl00$face$RB1"', content)
        self.assertIn(u'"ctl00$btNext"', content)
        self.assertIn(u'"ctl00$email"', content)
        self.assertIn(u'"ctl00$phone"', content)
        self.assertIn(u'"ctl00$inn"', content)
        self.assertIn(u'"ctl00$SecondName"', content)
        self.assertIn(u'"ctl00$FirstName"', content)
        self.assertIn(u'"ctl00$LastName"', content)

        ok = False
        for x in range(4):
            result = s.post(u'http://order.nalog.ru/details/', data={
                "__VIEWSTATE": u"",
                "ctl00$face": u"1",  # 0 - юр. лицо, 1 - физ. лицо, 2 - индивидуальный предприниматель
                "ctl00$LastName": u"Семён",
                "ctl00$FirstName": u"Пётр",
                "ctl00$SecondName": u"Август",
                "ctl00$inn": u"324500141611",
                "ctl00$phone": u"+79000010205",
                "ctl00$email": u"test%d@mail.ru" % randint(1, 1000),
                "ctl00$btNext": ""
            })
            self.assertEqual(result.status_code, 200)
            content = result.content.decode('utf-8')

            if u'Укажите параметры для записи на посещение ИФНС России' in content:
                ok = True
                #print(content)
                break
        self.assertTrue(ok)

        self.assertIn(
            u'dxo.itemsValue=[1,5,26,48,53,74,1755,85,90,94,101,113,120,130,168,1278,170,175,186,190,196,207,224,268,275,297,1727,333,341,367,373,383,395,408,429,1794,440,445,2090,463,473,476,493,506,515,524,553,566,591,595,634,650,673,679,696,713,730,737,771,795,804,825,835,856,901,909,930,958,964,974,984,996,1008,1020,1043,1077,1234,1088,1114,1117,1132,1135,2793,2792]',
            content)
        self.assertIn(u'id="ctl00_ufns_DDD_L_LBT"', content)
        self.assertIn(u'г. Санкт-Петербург', content)
        self.assertIn(u'78', content)

        # check calendar
        result = s.post(u'http://order.nalog.ru/fns_service/', data={
            "__CALLBACKID": u"ctl00$cpday",
            "__CALLBACKPARAM": u'c0:275;0;275;1112',
            "__EVENTTARGET": u"",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": u"",
        })
        self.assertEqual(result.status_code, 200)
        str_data = result.text[26:-3].encode('utf-8').decode('string_escape').replace('!-\\-', '!--').replace('/-\\-',
                                                                                                              '/--').replace(
            '\\/script', '/script')
        content = u"<!DOCTYPE html><html><head><title></title></head><body>%s</body></html>" % str_data.decode('utf-8')

        root = html5lib.parse(content, treebuilder='lxml', namespaceHTMLElements=False)
        self.assertEqual(len(CSSSelector('#ctl00_cpday_day_mc')(root)), 1)
        self.assertEqual(len(CSSSelector('#ctl00_cpday_day_mt')(root)), 1)
        self.assertGreaterEqual(len(CSSSelector('#ctl00_cpday_day_mt tr td')(root)), 30)
        self.assertIn(u'dxeCalendarDay', content)
        self.assertIn(u'dxeCalendarWeekend', content)
        self.assertIn(u'dxeCalendarOtherMonth', content)
        self.assertIn(u'dxeCalendarOutOfRange', content)

        #check ban
        now = datetime.now() + timedelta(seconds=3600 * 24 * 3)
        while now.isoweekday() in (6, 7):
            now += timedelta(days=1)
        result = s.post('http://order.nalog.ru/fns_service/', data={
            "__CALLBACKID": u"ctl00$clBanCheck",
            "__CALLBACKPARAM": u"c0:%d.%d.%d;180;1112;0" % (now.year, now.month, now.day),
            "__EVENTARGUMENT": u"",
            "__EVENTTARGET": u"",
            "__VIEWSTATE": u"",
        })
        self.assertEqual(result.status_code, 200)
        content = result.content.decode('utf-8')
        self.assertIn('s/*DX*/({', content)
        self.assertIn(u"'result':{'data':'1'", content)

        # check time slots
        d = now
        #part = u"%d.%d.%d;%d;%d;%d;%d" % (d.year, d.month, d.day, 182, 1112, 0, 182)
        part = u"%d.%d.%d;%d;%d;%d;%d" % (d.year, d.month, d.day, 182, 1254, 0, 182)
        part2 = u"14|CUSTOMCALLBACK%d|" % len(part) + part
        cb_param = u"c0:KV|2;[];GB|%d;" % len(part2) + part2 + ";"
        data = {
            "__CALLBACKID": u"ctl00$gvTime",
            "__CALLBACKPARAM": cb_param,
            "__EVENTARGUMENT": u"",
            "__EVENTTARGET": u"",
            "__VIEWSTATE": u"",
        }
        with self.app.app_context():
            current_app.logger.debug(json.dumps(data))
        result = s.post('http://order.nalog.ru/fns_service/', data=data)
        self.assertEqual(result.status_code, 200)
        data_str = result.text[19:].encode('utf-8').decode('string_escape').replace('!-\\-', '!--').replace('/-\\-',
                                                                                                            '/--').replace(
            '\\/script', '/script')
        self.assertIn('cpFS_ID\':', data_str)
        sub_service_fs_id = filter(lambda x: x.isdigit(), result.text.split('cpFS_ID\':')[1])
        self.assertGreaterEqual(int(sub_service_fs_id), 1)
        content = u"<!DOCTYPE html><html><head><title></title></head><body>%s</body></html>" % data_str.decode('utf-8')
        root = html5lib.parse(content, treebuilder='lxml', namespaceHTMLElements=False)

        self.assertGreaterEqual(len(CSSSelector('#ctl00_gvTime_DXMainTable tr')(root)), 4)
        self.assertIn(u'Период занят полностью', content)
        self.assertIn(u'type="button"  class="btn-yes"', content)
        self.assertIn(u'id="ctl00_gvTime_tccell0_1"', content)

    @authorized()
    def test_get_nalog_ru_time_slots_view(self):
        founder_person = PrivatePersonDbObject(**{
            "_owner": self.user._id,
            "name": u"Як",
            "surname": u"Самокатов",
            "patronymic": u"Полуэктович",
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
            "phone": u"+79000010205",
            "email": u"test%d@mail.ru" % randint(1, 1000),
            "living_country_code": 3,
            "living_address": u"г. Санкт-Петербург, д. Гадюкино, бульвар Мотоциклистов казарма 4, кв. 705"
        })
        founder_person.insert(self.db)

        result = self.test_client.post('/meeting/ifns/schedule/', data={
            'ifns': 7726,
            'service': 1,
            'datetime': u'2014-09-27',
            'founder_applicant': u'{"founder_type":"1", "person":{"id":"%s"}}' % unicode(founder_person._id)
        })

        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)

    def _test_get_nalog_ru_time_slots_and_register(self):
        s = requests.Session()
        result = s.get(u'http://order.nalog.ru/details/')

        # start session
        #        result = s.post(u'http://order.nalog.ru/details/', data={
        #            "__VIEWSTATE" : u"",
        #            "ctl00$face"	: u"0", # 0 - юр. лицо, 1 - физ. лицо, 2 - индивидуальный предприниматель
        #            "ctl00$LastName"	: u"ООО \"Рога и Копыта2\"",
        #            "ctl00$inn"	: u"3245001416",
        #            "ctl00$phone"	: u"+79000010204",
        #            "ctl00$email"	: u"test%d@mail.ru" % randint(1, 1000),
        #            "ctl00$btNext" : ""
        #        })

        result = s.post(u'http://order.nalog.ru/details/', data={
            "__VIEWSTATE": u"",
            "ctl00$face": u"1",  # 0 - юр. лицо, 1 - физ. лицо, 2 - индивидуальный предприниматель
            "ctl00$LastName": u"Семён",
            "ctl00$FirstName": u"Пётр",
            "ctl00$SecondName": u"Август",
            "ctl00$inn": u"324500141611",
            #            "ctl00$phone"	: u"+79000010205",
            #            "ctl00$email"	: u"test%d@mail.ru" % randint(1, 1000),
            "ctl00$phone": u"",
            "ctl00$email": u"",
            "ctl00$btNext": ""
        })

        # show ifns
        #        result = s.post(u'http://order.nalog.ru/fns_service/', data = {
        #            "__CALLBACKID":u"ctl00$ifns",
        #            "__CALLBACKPARAM":u"c0:LECC|4;1112;LBCRI|4;0:99;", # 1112 = spb
        #            "__EVENTTARGET":u"",
        #        })
        print(result.status_code)
        #print(result.text or result.content)

        # get calendar
        fns_id = '1112'  # спб, 15-я ифнс
        service_id = '275'
        sub_service = '275'  # can be list: '1,2,3'
        is_multi_sub_service = '0'  # can be '1' if sub_service can be list
        cb_param = 'c0:' + sub_service + ";" + is_multi_sub_service + ";" + (
            service_id if is_multi_sub_service == "1" else sub_service) + ";" + fns_id
        print(cb_param)

        result = s.post(u'http://order.nalog.ru/fns_service/', data={
            "__CALLBACKID": u"ctl00$cpday",
            "__CALLBACKPARAM": cb_param,
            "__EVENTTARGET": u"",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": u"",
        })

        #str_data = result.text[26:-3].replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
        str_data = result.text[26:-3].encode('utf-8').decode('string_escape').replace('!-\\-', '!--').replace('/-\\-',
                                                                                                              '/--').replace(
            '\\/script', '/script')
        #print(str_data)
        #print(len(str_data))
        content = u"<!DOCTYPE html><html><head><title></title></head><body>%s</body></html>" % str_data.decode('utf-8')
        root = html5lib.parse(content, treebuilder='lxml', namespaceHTMLElements=False)  # ,

        year = None
        month = None
        for item in CSSSelector('#ctl00_cpday_day_T')(root):
            #print('month: ' + unicode(item.text))
            month = item.text.split(' ')[0].strip()
            year = int(item.text.split(' ')[1].strip())
            break

        MONTHS = {
            u'Январь': 1,
            u'Февраль': 2,
            u'Март': 3,
            u'Апрель': 4,
            u'Май': 5,
            u'Июнь': 6,
            u'Июль': 7,
            u'Август': 8,
            u'Сентябрь': 9,
            u'Октябрь': 10,
            u'Ноябрь': 11,
            u'Декабрь': 12,
        }
        month = MONTHS[month]

        sel = CSSSelector('#ctl00_cpday_day_mt td.dxeCalendarDay')
        day_prev = -1
        days = []
        for item in sel(root):
            classes = filter(lambda x: not not x, [i.strip() for i in item.attrib['class'].split(' ')])
            if 'dxeCalendarOutOfRange' in classes or 'dxeCalendarToday' in classes:
                continue

            day = int(item.text)
            if day_prev > day:
                month += 1
                if month > 12:
                    year += 1
                    month = 1
            day_prev = day
            d = datetime(year, month, day)
            days.append(d)
            print(d.strftime("%d.%m.%Y"))


        # ban check
        result = s.post('http://order.nalog.ru/fns_service/', data={
            "__CALLBACKID": u"ctl00$clBanCheck",
            "__CALLBACKPARAM": u"c0:2014.8.20;180;1112;0",
            "__EVENTARGUMENT": u"",
            "__EVENTTARGET": u"",
            "__VIEWSTATE": u"",
        })
        # not banned: s/*DX*/({'id':0,'result':{'data':'1','parameter':'2014.8.20;180;1112;0'}})
        # banned:     s/*DX*/({'id':0,'result':{'data':'0','parameter':'2014.8.21;180;1112;0'}})

        self.assertNotIn("'data':'0'", result.text, 'banned')
        print('not banned yet')

        # get time slots
        # SelectedDay.getFullYear() + '.' + (SelectedDay.getMonth() + 1) + '.' + SelectedDay.getDate() + ';' + (SelectedService.IsCheck == "1" ? SelectedService.ID : SelectedSubService.ID) + ";" + fns_id + ";" + SelectedService.IsCheck + ";" + SelectedSubServices_IDS;
        d = days[-1]
        cb_param = u"c0:" + u"KV|2;[];GB|44;14|CUSTOMCALLBACK24|" + unicode(d.year) + u"." + unicode(
            d.month) + u"." + unicode(d.day) + u";" + (
                       service_id if is_multi_sub_service == "1" else sub_service) + u";" + fns_id + ";" + is_multi_sub_service + ";" + sub_service + ";"
        print(cb_param)
        data = {
            "__CALLBACKID": u"ctl00$gvTime",
            "__CALLBACKPARAM": cb_param,  #u"c0:KV|2;[];GB|44;14|CUSTOMCALLBACK24|2014.8.20;182;1112;0;182;",
            "__EVENTARGUMENT": u"",
            "__EVENTTARGET": u"",
            "__VIEWSTATE": u"",
        }
        result = s.post('http://order.nalog.ru/fns_service/', data=data)

        print(result.text)
        self.assertIn('cpFS_ID', result.text)

        sub_service_fs_id = filter(lambda x: x.isdigit(), result.text.split('cpFS_ID\':')[1])

        data_str = result.text[19:].encode('utf-8').decode('string_escape').replace('!-\\-', '!--').replace('/-\\-',
                                                                                                            '/--').replace(
            '\\/script', '/script')
        #print(data_str)
        content = u"<!DOCTYPE html><html><head><title></title></head><body>%s</body></html>" % data_str.decode('utf-8')
        root = html5lib.parse(content, treebuilder='lxml', namespaceHTMLElements=False)  # ,

        time_vals = []
        for item in CSSSelector('#ctl00_gvTime_DXMainTable tr')(root):
            tds = CSSSelector('td')(item)
            time_str = tds[0].text
            span_style = CSSSelector('span')(tds[1])[0].attrib['style']
            available = 'block' not in span_style
            print(time_str, available)
            if available:
                hour, minutes = time_str.strip().replace('00', '0').split(':')
                time_vals.append(datetime(2014, 1, 1, int(hour), int(minutes)))

        # register
        # var Register_Parameter = d.getFullYear() + '.' + (d.getMonth() + 1) + '.' + d.getDate() + ' ' + time.Get("Value") + ';' +
        # (SelectedService.IsCheck == "1" ? SelectedService.FS_ID : SelectedSubService.FS_ID) + ";" + fns_id + ";" +
        # time.Get("subs_string") + ";" + time.Get("SelectedService.IsCheck")

        time_val = time_vals[-1]
        cb_param = u"c0:" + unicode(d.year) + u"." + unicode(d.month) + u"." + unicode(
            d.day) + u" " + time_val.strftime("%H:%M:00") + \
                   ";" + sub_service_fs_id + u";" + fns_id + u";" + \
                   sub_service + ";" + is_multi_sub_service

        print(cb_param)
        result = s.post('http://order.nalog.ru/fns_service/', data={
            "__CALLBACKID": u"ctl00$clRegister",
            "__CALLBACKPARAM": cb_param,  # u"c0:2014.8.25 16:30:00;4006544;1112;275;0", юр.лицо
            #   c0:2014.8.21 19:30:00;4006550;1112;281;0   физ. лицо

            "__EVENTARGUMENT": u"",
            "__EVENTTARGET": u"",
            "__VIEWSTATE": u"",
        })

        print(len(result.text), result.text)

        result = result.content.decode('utf-8')
        #result = u"s/*DX*/({'id':0,'result':{'data':'a65d3308115e40889388044322ab21a4','parameter':'2014.8.25 16:30:00;4006544;1112;275;0'}})"
        # registered successfully: (122, u"s/*DX*/({'id':0,'result':{'data':'a65d3308115e40889388044322ab21a4','parameter':'2014.8.25 16:30:00;4006544;1112;275;0'}})")
        # уже записаны на это время в другое окно: (100, u"s/*DX*/({'id':0,'result':{'data':'DoubleTime','parameter':'2014.8.25 17:00:00;4006544;1112;275;0'}})")
        self.assertIn("'data':'", result, u"failed to register")

        code = result.split("'data':'")[1].split("'")[0].strip()
        print(code)

        result = requests.get('http://order.nalog.ru/appointment/R%s/' % code)
        #print(result.text)
        #div id="ctl00_pnlDetails" class="text_block">
        #<table width='100%' class='border_table'><tr><td>Налогоплательщик:</td><td style='width:100%'><table width='100%' class='border_table'><tr><td style='width:150px;'>Категория:</td><td>Юридическое лицо</td></tr><tr><td>Название организации:</td><td>Общество с ограниченной ответственностью  Рога и Копыта </td></tr><tr><td>ИНН:</td><td>7723643863</td></tr><tr><td>Телефон:</td><td>+79000010203</td></tr><tr><td>Email:</td><td>test237@mail.ru</td></tr></table></td></tr><tr><td>Инспекция:</td><td>Межрайонная ИФНС России № 15 по Санкт-Петербургу</td></tr><tr><td style='white-space:nowrap'>Адрес:</td><td>191124,Санкт-Петербург г,Красного Текстильщика ул,10-12 лит.О</td></tr><tr><td style='white-space:nowrap'>Способ проезда:</td><td>ст.метро "пл. Александра Невского", "Чернышевская", "пл. Восстания"
        #автобусы: 15, 22, 22а, 105, 136, 181
        #троллейбусы: 5, 7, 11, 15, 16
        #маршрутные такси: к26, к28, к51, к90, к163, к167, к185, к190, к269</td></tr><tr><td style='white-space:nowrap'>Телефон:</td><td>812-335-14-03</td></tr><tr><td>Услуги:</td><td>Прием документов  при регистрации создания  (1-но ЮЛ)</td></tr><tr><td>Дата приёма:</td><td>25.08.2014</td></tr><tr><td>Время приёма:</td><td>16:30</td></tr><tr><td>Окно приёма:</td><td>03</td></tr><tr><td colspan='2'><button class='blue_button' type='button' onclick='window.print()'>Распечатать</button></td></tr></table><br /><br /><b>Обращаем Ваше внимание!</b><br />В случае занятости сотрудника, осуществляющего прием по выбранной услуге, допускается начало приема  позже выбранного времени, при этом налогоплательщику гарантируется прием в течение получаса. <br /><br />В случае опоздания налогоплательщика более, чем на 10 минут, налогоплательщик утрачивает право на приоритетное обслуживание и обслуживается в порядке общей очереди.<br /><br />Приоритетное обслуживание по предварительной записи осуществляется при условии:<br /><ul><li>соответствия данных предъявленного документа, удостоверяющего личность, данным, указанным при записи в режиме онлайн.</li><li>обращения за получением услуги, выбранной при записи в режиме онлайн.</li></ul>
        #</div>
        root = html5lib.parse(result.text, treebuilder='lxml', namespaceHTMLElements=False)
        cat_tr = CSSSelector("#ctl00_pnlDetails table table tr")(root)[0]
        cat = CSSSelector("td")(cat_tr)[1].text

        name_tr = CSSSelector("#ctl00_pnlDetails table table tr")(root)[1]
        name = CSSSelector("td")(name_tr)[1].text

        inn_tr = CSSSelector("#ctl00_pnlDetails table table tr")(root)[2]
        inn = CSSSelector("td")(inn_tr)[1].text

        phone_tr = CSSSelector("#ctl00_pnlDetails table table tr")(root)[3]
        phone = CSSSelector("td")(phone_tr)[1].text

        email_tr = CSSSelector("#ctl00_pnlDetails table table tr")(root)[4]
        email = CSSSelector("td")(email_tr)[1].text

        print(u"Категория: %s " % cat)
        print(u"Имя/Наименование: %s " % name)
        print(u"ИНН: %s" % inn)
        print(u"Телефон: %s" % phone)
        print(u"Email: %s" % email)

        ifns = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[3].text
        address = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[5].text
        map = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[7].text
        phone = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[9].text
        service = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[11].text
        data_str = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[13].text
        time_str = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[15].text
        window = CSSSelector("#ctl00_pnlDetails>table>tbody>tr>td")(root)[17].text
        print(u"ИФНС: %s" % ifns)
        print(u"Адрес: %s" % address)
        print(u"Способ проезда: %s" % map)
        print(u"Телефон: %s" % phone)
        print(u"Услуги: %s" % service)
        print(u"Дата и время: %s %s" % (data_str, time_str))

        print(u"Окно приёма: %s" % window)

    @authorized()
    def test_get_nalog_ru_time_slots(self):

        founder_person = PrivatePersonDbObject(**{
            "_owner": self.user._id,
            "name": {'nom': u"Прокл"},
            "surname": {'nom': u"Поликарпов"},
            "patronymic": {'nom': u"Поликарпович"},
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
        founder_person.insert(self.db)

        data = {
            u"founder_applicant": json.dumps({
                "founder_type": FounderTypeEnum.FT_PERSON,
                "person": {
                    'id': unicode(ObjectId(founder_person._id))
                },
                "share": {
                    "type": "percent",
                    "value": 100
                },
                "nominal_capital": 7466,
                "properties": [
                    {
                        "name": u"Комплект чистой одноразовой посуды",
                        "price": 13,
                        "count": 1
                    }
                ],
            }),
            u"service": IfnsServiceEnum.IS_REG_COMPANY,
            u"ifns": 7840,
            u"datetime": (datetime.now() + timedelta(seconds=3600 * 1148)).strftime(DateTypeValidator.FORMAT)
        }

        result = self.test_client.post('/meeting/ifns/schedule/', data=data)
        self.assertIsNotNone(result)
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertIn('result', data)
        info = data['result']
        self.assertIsNotNone(info)
        nearest_date = info['nearest_time']
        time_slots = info['slots']

        self.assertGreaterEqual(len(time_slots), 2)
        self.assertGreater(datetime.strptime(nearest_date, "%Y-%m-%d"), datetime.now())
        print(nearest_date)
        print(time_slots)

    @authorized()
    def test_yurist_set_get(self):
        file1 = FileObject(file_path='path', file_name='f.pdf', _owner=self.user)
        sqldb.session.add(file1)
        sqldb.session.commit()

        file2 = FileObject(file_path='path', file_name='f2.pdf', _owner=self.user)
        sqldb.session.add(file2)
        sqldb.session.commit()

        file3 = FileObject(file_path='path', file_name='f3.pdf', _owner=self.user)
        sqldb.session.add(file3)
        sqldb.session.commit()

        self.assertEqual(len(self.mailer.mails), 0)
        batch_db = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
            _owner=self.user
        )
        sqldb.session.add(batch_db)
        sqldb.session.commit()

        result = self.test_client.get('/batch/yurist/?batch_id=%s' % batch_db.id)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {'result': {u'attached_files': [],
              u'batch_id': batch_db.id,
              u'status': u'new',
              u'typos_correction': False}})

        result = self.test_client.post('/batch/yurist/set/', data={
            'batch_id': batch_db.id,
            'check': True,
            'file_list': '[{"id":"%s"}, {"id":"%s"}, {"id":"%s"}]' % (file1.id, file2.id, file3.id)
        })
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {'result': True})
        self.assertEqual(len(self.mailer.mails), 1)
        self.assertEqual(self.mailer.mails[0]['to'], self.config['YURIST_EMAIL_LIST'][0])

        check_obj = YuristBatchCheckObject.query.filter_by(batch_id=batch_db.id).first()
        self.assertIsNotNone(check_obj)
        check_obj_doc = YuristBatchCheck.db_obj_to_field(check_obj)

        result = self.test_client.get('/batch/yurist/?batch_id=%s' % batch_db.id)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        api_val = check_obj_doc.get_api_structure()
        self.assertEqual(result_data, {'result': api_val})

        result = self.test_client.post('/batch/yurist/set/', data={'batch_id': batch_db.id, 'check': False})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {'result': True})

        self.assertEqual(len(self.mailer.mails), 1)

        check_obj = YuristBatchCheckObject.query.filter_by(batch_id=batch_db.id).first()
        self.assertIsNotNone(check_obj)
        self.assertEqual(check_obj.status, YuristBatchCheckStatus.YBS_REFUSED)

        result = self.test_client.get('/batch/yurist/?batch_id=%s' % batch_db.id)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertTrue(result_data['result'])

        self.assertEqual(len(self.mailer.mails), 1)

    @authorized()
    def test_yurist_refuse(self):

        self.assertEqual(len(self.mailer.mails), 0)
        batch_db = self.create_batch(DocumentBatchTypeEnum.DBT_NEW_LLC, self.user)

        result = self.test_client.get('/batch/yurist/?batch_id=%s' % batch_db.id)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {
            u'result': {
                u'attached_files': [],
                u'batch_id': batch_db.id,
                u'status': u'new',
                u'typos_correction': False
            }
        })

        result = self.test_client.post('/batch/yurist/set/', data={'batch_id': batch_db.id, 'check': False})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {'result': True})

        check_obj = YuristBatchCheckObject.query.filter_by(batch_id=batch_db.id).first()
        self.assertIsNone(check_obj)

        result = self.test_client.get('/batch/yurist/?batch_id=%s' % batch_db.id)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertTrue(result_data['result'])

    @authorized(admin=True)
    def test_yurist_set_ok(self):
        batch_db = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
            _owner=self.user
        )
        sqldb.session.add(batch_db)
        sqldb.session.commit()
        _id = batch_db.id

        result = self.test_client.get('/batch/yurist/?batch_id=%s' % unicode(_id))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {'result': {u'attached_files': [],
              u'batch_id': _id,
              u'status': u'new',
              u'typos_correction': False}})

        result = self.test_client.post('/batch/yurist/set/', data={'batch_id': unicode(_id), 'check': True})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {'result': True})

        check_obj = YuristBatchCheckObject.query.filter_by(batch_id=batch_db.id).first()
        self.assertIsNotNone(check_obj)

        result = self.test_client.get('/batch/yurist/commit/?batch_check_id=%s&success=true' % batch_db.id)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {'new_status': 'success'})

        check_obj = YuristBatchCheckObject.query.filter_by(batch_id=batch_db.id).first()
        self.assertIsNotNone(check_obj)
        check_obj_doc = YuristBatchCheck.db_obj_to_field(check_obj)
        self.assertEqual(check_obj_doc.status.value, YuristBatchCheckStatus.YBS_SUCCESS)

        result = self.test_client.get('/batch/yurist/commit/?batch_check_id=%s&success=true' % batch_db.id)
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data['new_status'], 'success')

        check_obj = YuristBatchCheckObject.query.filter_by(batch_id=batch_db.id).first()
        self.assertIsNotNone(check_obj)
        check_obj_doc = YuristBatchCheck.db_obj_to_field(check_obj)
        self.assertTrue(check_obj_doc.status == YuristBatchCheckStatus.YBS_SUCCESS)

    @authorized(admin=True)
    def test_yurist_set_failed(self):
        batch_db = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
            _owner=self.user
        )
        sqldb.session.add(batch_db)
        sqldb.session.commit()
        _id = batch_db.id

        result = self.test_client.get('/batch/yurist/?batch_id=%s' % unicode(_id))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {'result': {u'attached_files': [],
              u'batch_id': _id,
              u'status': u'new',
              u'typos_correction': False}})

        result = self.test_client.post('/batch/yurist/set/', data={'batch_id': unicode(_id), 'check': True})
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {'result': True})

        check_obj = YuristBatchCheckObject.query.filter_by(batch_id=batch_db.id).first()
        self.assertIsNotNone(check_obj)

        result = self.test_client.get('/batch/yurist/commit/?batch_check_id=%s&success=%s' % (
            check_obj.id,
            'False'
        ))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {'new_status': 'failed'})

        check_obj = YuristBatchCheckObject.query.filter_by(batch_id=batch_db.id).first()
        self.assertIsNotNone(check_obj)
        check_obj_doc = YuristBatchCheck.db_obj_to_field(check_obj)
        self.assertTrue(check_obj_doc.status == YuristBatchCheckStatus.YBS_FAILED)

        result = self.test_client.get('/batch/yurist/commit/?batch_check_id=%s&success=%s' % (
            check_obj.id,
            'True'
        ))
        self.assertEqual(result.status_code, 200)
        result_data = json.loads(result.data)
        self.assertEqual(result_data, {'new_status': 'success'})

        check_obj = YuristBatchCheckObject.query.filter_by(batch_id=batch_db.id).first()
        self.assertIsNotNone(check_obj)
        check_obj_doc = YuristBatchCheck.db_obj_to_field(check_obj)
        self.assertTrue(check_obj_doc.status == YuristBatchCheckStatus.YBS_SUCCESS)

    def test_get_ifns_internal_id_by_ifns_name(self):
        s = requests.Session()
        result = s.get(u'http://order.nalog.ru/details/')

        data = {
            "ctl00$LastName": u"наименование",
            "ctl00$inn": u"6514008400",
            "ctl00$phone": u"+79211001010",
            "ctl00$email": u"email@email.com",
            "__VIEWSTATE": u"",
            "ctl00$face": u"0",
            "ctl00$btNext": ""
        }
        # start session
        result = s.post(u'http://order.nalog.ru/details/', data=data)
        if result.status_code != 200 or not result.text:
            print(u"order.nalog.ru вернул неожиданный код: %s" % unicode(result.status_code))
            assert False

        print(result.status_code)

        with self.app.app_context():
            #res = external_tools.get_ifns_internal_id_by_ifns_name(s, u"Санкт-Петербург", u"Межрайонная ИФНС России №15 по Санкт-Петербургу", False, current_app.logger)

            cb_param = u"c0:LECC|%d;%d;LBCRI|4;0:99;" % (len(unicode(1088)), 1088)
            data = {
                "__CALLBACKID": "ctl00$ifns",
                "__CALLBACKPARAM": cb_param,
                "__VIEWSTATE": ""
            }
            result = s.post(u'http://order.nalog.ru/fns_service/', data=data)
            if result.status_code != 200 or u's/*DX*/({' not in result.text:
                print(u"Failed to get internal ifns number. Request was: %s. Response text: %s" % (
                    json.dumps(data), result.text))
            print(result.text)

    @authorized()
    def test_find_ifns_registries(self):
        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(
            document_type=DocumentTypeEnum.DT_ARTICLES,
            data={
                u"doc_date": datetime.now() - timedelta(days=40),
                "full_name": u"юрбюро онлайн",
                "short_name": u"юрбюро онлайн",
                "starter_capital": {
                    u"capital_type": CompanyStarterCapitalTypeEnum.CSC_USTAVNOY_CAPITAL,
                    u"value": {
                        "currency": "rub",
                        "value": "12312.234234"
                    }
                },
                "address": {
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
                    "ifns": 7806
                },
                #                "general_manager" : uchreditel_fis_lico_person._id,
                #                "general_manager_caption" : u"старший помощник младшего черпальщика",
                #                    "manager" : unicode(uchreditel_fis_lico_person._id),
                "job_main_code": u"92.31.1",
                "job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
            }
        ), None, False)
        batch = DocumentBatchDbObject(documents=[new_user_doc.db_value()], batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                      status=BatchStatusEnum.BS_FINALISED, _owner=self.user._id)
        batch.insert(self.db)

        result = self.test_client.post('/ifns/reservations/', data={
            #            'name' : u"Юрбюро онлайн",
            #            'date_from' : (datetime.now() - timedelta(days = 60)).strftime('%Y-%m-%d'),
            #            'date_to' : datetime.now().strftime('%Y-%m-%d'),
            #            'ifns' : '7806'
            "batch_id": unicode(batch._id)
        })
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertNotIn('error', data)
        self.assertIn('result', data)
        self.maxDiff = None
        self.assertEqual(data['result'], {
            u"full_name": u"ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ \"ЮРБЮРО ОНЛАЙН\"",
            u"status": u"registered",
            u"ogrn": u"1147847331367",
            u"reg_date": u"29.09.2014"
        })

    @authorized()
    def test_discard_ifns_booking(self):
        self.maxDiff = None

        batch = DocumentBatchDbObject(
            _owner=self.user._id,
            batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
            documents=[{'data': {'full_name': u"Ромашка"}}]
        )
        batch.insert(current_app.db)

        booking = IfnsBooking.parse_raw_value({
            "batch_id": batch._id,
            "_owner": self.user._id,
            "ifns": u'7805',
            "service": u"регистрация ооо",
            "window": u"1",
            "address": u"на деревню к дедушке",
            "date": datetime(2015, 1, 1, 10, 0),
            "phone": "112",
            "how_to_get": u"пешком",
            "_discarded": False
        }, False)
        booking_db = booking.get_db_object()
        booking_id = booking_db.insert(self.db)

        result = self.test_client.post('/meeting/ifns/discard/', data={
            'booking_id': str(booking_id),
            'batch_id': str(batch._id)
        })
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertIn('result', data)
        self.assertTrue(data['result'])

        self.assertEqual(IfnsBookingObject.query.count(), 1)
        booking = IfnsBookingObject.query.first()
        val = copy(booking.__dict__)
        del val['id']
        del val['batch_id']
        self.assertEqual(val, {
            "ifns": u'7805',
            "service": u"регистрация ооо",
            "window": u"1",
            "address": u"на деревню к дедушке",
            "date": datetime(2015, 1, 1, 10, 0),
            "phone": "112",
            "how_to_get": u"пешком",
            "_discarded": True
        })

    @authorized()
    def test_get_my_ifns_name(self):
        new_user_doc = UserDocument()
        new_user_doc.parse_raw_value(dict(
            document_type=DocumentTypeEnum.DT_ARTICLES,
            data={
                u"doc_date": datetime.now() - timedelta(days=40),
                "full_name": u"юрбюро онлайн",
                "short_name": u"юрбюро онлайн",
                "starter_capital": {
                    u"capital_type": CompanyStarterCapitalTypeEnum.CSC_USTAVNOY_CAPITAL,
                    u"value": {
                        "currency": "rub",
                        "value": "12312.234234"
                    }
                },
                "address": {
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
                    #"ifns" : 7806
                },
                #                "general_manager" : uchreditel_fis_lico_person._id,
                #                "general_manager_caption" : u"старший помощник младшего черпальщика",
                #                    "manager" : unicode(uchreditel_fis_lico_person._id),
                "job_main_code": u"92.31.1",
                "job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
            }
        ), None, False)
        batch = DocumentBatchDbObject(documents=[new_user_doc.db_value()], batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                      status=BatchStatusEnum.BS_FINALISED, _owner=self.user._id)
        batch.insert(self.db)

        new_item = IfnsCatalogObject(**{
            'name': u"Межрайонная ИФНС России №22 по Санкт-Петербургу",
            'address': {
                "address_string": u",198334,Санкт-Петербург г,,,,Партизана Германа ул,37,,",
            },
            'comment': u"Код ОКПО:39449549 Прием: Понедельник, среда с 09.00 до 18.00. Вторник, четверг с 09.00 до 20.00. Пятница с 09.00 до 16.45. Вторая и четвертая субботы месяца с 10.00 до 15.00. Без перерыва на обед.",
            'code': 7807,
            'rou': {
                "name": u"Межрайонная ИФНС России №15 по Санкт-Петербургу",
                "code": u"78086",
                "tel": ["+7(812)3351403"]
            }
        })
        sqldb.session.add(new_item)
        sqldb.session.commit()

        new_item = IfnsCatalogObject(**{
            'name': u"Межрайонная ИФНС России №22 по Санкт-Петербургу",
            'address': {
                "address_string": u",198334,Санкт-Петербург г,,,,Партизана Германа ул,37,,",
            },
            'comment': u"Код ОКПО:39449549 Прием: Понедельник, среда с 09.00 до 18.00. Вторник, четверг с 09.00 до 20.00. Пятница с 09.00 до 16.45. Вторая и четвертая субботы месяца с 10.00 до 15.00. Без перерыва на обед.",
            'code': 5509,
            'rou': {
                "name": u"Межрайонная ИФНС России №15 по Санкт-Петербургу",
                "code": u"78086",
                "tel": ["+7(812)3351403"]
            }
        })
        sqldb.session.add(new_item)
        sqldb.session.commit()

        result = self.test_client.get('/meeting/ifns/name/?ifns=' + str(7807))
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertEqual(data['result'], {
            'title': u'Межрайонная ИФНС России №15 по Санкт-Петербургу',
            'has_booking': True
        })

        result = self.test_client.get('/meeting/ifns/name/?ifns=' + str(5509))
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertEqual(data['result'], {
            'title': u'Межрайонная ИФНС России № 12 по Омской области',
            'has_booking': False
        })

    @authorized()
    def test_get_registered_llc_no_ifns_booking(self):
        with self.app.app_context():
            uchreditel_fis_lico_person = PrivatePersonDbObject(**{
                "_owner": self.user._id,
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
                    "issue_date": datetime.now() - timedelta(days=365 * 14),
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
            uchreditel_fis_lico_person.insert(self.app.db)

            data = {
                u"full_name": u"ЮРБЮРО ОФФЛАЙН",
                u"short_name": u"ЮРБЮРО ПАЙПЛАЙН",
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
                            "_id": uchreditel_fis_lico_person._id,
                            "type": "person"
                        },
                        "nominal_capital": 1500.5,
                        "share": 100
                    }
                ],
                u"general_manager": {
                    "_id": uchreditel_fis_lico_person._id,
                    "type": "person"
                },
                u"job_main_code": u"92.31.1",
                u"job_code_array": [u"92.31.1", u"74.14", u"10.01.1"],
                u"doc_obtain_person": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person._id
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
                    "_id": uchreditel_fis_lico_person._id
                },
                u"selected_moderator": {
                    "type": "person",
                    "_id": uchreditel_fis_lico_person._id
                },
                u"pravo_otchuzhdeniya_type": 5,
                u"perehod_doli_k_naslednikam_soglasie": True,
                u"taxation_type": "usn",
                u"registration_way": "some_founders",
                u"region": u"Санкт-Петербург",
                u"large_deals_min_value": None,
                u"general_manager_deals_max_amount": None
            }
            batch = DocumentBatchDbObject(
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                status=BatchStatusEnum.BS_NEW,
                _documents=[],
                data={},
                _owner=self.user._id
            )
            _id = batch.insert(self.db)

            new_batch_db_object = DocumentBatchDbObject(
                data=data,
                batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC
            )

            batch = DocumentBatch.parse_raw_value(new_batch_db_object.as_dict(), False)
            batch_json = json.dumps(batch.get_api_structure())
            result = self.test_client.post('/batch/update/', data={
                'batch_id': unicode(_id),
                'batch': batch_json
            })
            self.assertEqual(result.status_code, 200)
            db_batch = DocumentBatchDbObject.find_one(self.db, {'_id': _id})

            result = self.test_client.post('/batch/finalise/', data={'batch_id': unicode(_id)})
            self.assertEqual(result.status_code, 200)
            DocumentBatchDbObject.get_collection(self.db).update({'_id': _id}, {
                '$set': {'finalisation_date': datetime.now() - timedelta(days=35)}})

            cmd = CheckBatchIfnsRegStatusCommand(self.db, self.config, current_app.logger)
            cmd.run()

            db_batch = DocumentBatchDbObject.find_one(self.db, {'_id': _id})
            print(json.dumps(db_batch.as_dict(), default=lambda x: unicode(x), indent=1, ensure_ascii=False))

            book = IfnsBookingObject.query.filter_by(batch_id=_id).first()
            print(json.dumps(book.__dict__, default=lambda x: unicode(x), indent=1, ensure_ascii=False))

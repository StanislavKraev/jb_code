# -*- coding: utf-8 -*-
from copy import copy
from datetime import datetime
import json
import os
from bson import ObjectId

from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import RFRegionsEnum
from fw.documents.db_fields import BatchDocumentDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentBatchTypeEnum, DocumentTypeEnum
from services.partners import partners_manage_commands
from services.partners.models import StampPartnersObject, AccountantPartnersObject, BankPartnersObject, \
    BankPartnerRequestObject, BankPartnersServiceObject

os.environ['CELERY_CONFIG_MODULE'] = 'dev_celeryconfig'

from test_pack.base_batch_test import BaseBatchTestCase
from test_pack.test_api import authorized


class PartnersApiTestCase(BaseBatchTestCase):

    @authorized()
    def test_get_stamp_partners(self):
        with self.app.app_context():
            sp = StampPartnersObject(
                id=str(ObjectId()),
                region=RFRegionsEnum.RFR_SPB,
                enabled=True,
                sort_index=10,
                link='http://ya.ru',
                banner='http://yastatic.net/morda-logo/i/logo.svg',
                title='Йандекс'
            )
            sqldb.session.add(sp)

            sp = StampPartnersObject(
                id=str(ObjectId()),
                region=RFRegionsEnum.RFR_SPB,
                enabled=True,
                sort_index=2,
                link='http://ya1.ru',
                banner='http://yastatic1.net/morda-logo/i/logo.svg',
                title='Йандекс2'
            )
            sqldb.session.add(sp)

            sp = StampPartnersObject(
                id=str(ObjectId()),
                region=RFRegionsEnum.RFR_SPB,
                enabled=True,
                sort_index=13,
                link='http://ya2.ru',
                banner='http://yastatic2.net/morda-logo/i/logo.svg',
                title='Йандекс3'
            )
            sqldb.session.add(sp)

            sp = StampPartnersObject(
                id=str(ObjectId()),
                region=RFRegionsEnum.RFR_SPB,
                enabled=False,
                sort_index=11,
                link='http://ya.ru',
                banner='http://yastatic.net/morda-logo/i/logo.svg',
                title='Йандекс'
            )
            sqldb.session.add(sp)

            sp = StampPartnersObject(
                id=str(ObjectId()),
                region=RFRegionsEnum.RFR_MOSCOW,
                enabled=True,
                sort_index=2,
                link='http://ya1.ru',
                banner='http://yastatic1.net/morda-logo/i/logo.svg',
                title='Йандекс2'
            )
            sqldb.session.add(sp)
            sqldb.session.commit()

            batch_id = self.create_batch('llc', self.user).id
            doc1 = BatchDocumentDbObject(
                _owner=self.user,
                document_type='test',
                batch_id=batch_id,
                data={
                    'address': {
                        'region': u'Санкт-Петербург'
                    }
                }
            )
            sqldb.session.add(doc1)
            sqldb.session.commit()

            result = self.test_client.get('/partners/stamps/?batch_id=%s' % batch_id)
            self.assertEqual(result.status_code, 200)

            data = json.loads(result.data)
            self.assertEqual(len(data['result']['stamp_partners']), 3)

    @authorized()
    def test_get_accountant_partners(self):
        with self.app.app_context():
            new_partner = AccountantPartnersObject(
                id=str(ObjectId()),
                region=[RFRegionsEnum.RFR_SPB],
                enabled=True,
                sort_index=10,
                link='http://ya.ru',
                banner='http://yastatic.net/morda-logo/i/logo.svg',
                title='Йандекс',
                type="online"
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()

            new_partner = AccountantPartnersObject(
                id=str(ObjectId()),
                region=[RFRegionsEnum.RFR_SPB],
                enabled=True,
                sort_index=2,
                link='http://ya1.ru',
                banner='http://yastatic1.net/morda-logo/i/logo.svg',
                title="Йандекс2",
                type="offline"
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()

            new_partner = AccountantPartnersObject(
                id=str(ObjectId()),
                region=[RFRegionsEnum.RFR_SPB],
                enabled=True,
                sort_index=13,
                link='http://ya2.ru',
                banner='http://yastatic2.net/morda-logo/i/logo.svg',
                title="Йандекс3",
                type="online"
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()

            new_partner = AccountantPartnersObject(
                id=str(ObjectId()),
                region=[RFRegionsEnum.RFR_SPB],
                enabled=False,
                sort_index=11,
                link='http://ya.ru',
                banner='http://yastatic.net/morda-logo/i/logo.svg',
                title="Йандекс",
                type="online"
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()

            new_partner = AccountantPartnersObject(
                id=str(ObjectId()),
                region=[RFRegionsEnum.RFR_MOSCOW],
                enabled=True,
                sort_index=2,
                link='http://ya1.ru',
                banner='http://yastatic1.net/morda-logo/i/logo.svg',
                title="Йандекс2",
                type="offline"
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()

            batch_id = self.create_batch('llc', self.user).id
            doc1 = BatchDocumentDbObject(
                _owner=self.user,
                document_type='test',
                batch_id=batch_id,
                data={
                    'address': {
                        'region': u'Санкт-Петербург'
                    }
                }
            )
            sqldb.session.add(doc1)
            sqldb.session.commit()

            result = self.test_client.get('/partners/accounts/?batch_id=%s' % str(batch_id))
            self.assertEqual(result.status_code, 200)

            data = json.loads(result.data)
            self.assertEqual(len(data['result']['accounts_partners']), 3)

    @authorized()
    def test_get_bank_partners(self):
            new_partner = BankPartnersObject(
                id=str(ObjectId()),
                region=[RFRegionsEnum.RFR_SPB],
                city=[RFRegionsEnum.RFR_SPB],
                enabled=True,
                sort_index=10,
                link=u'http://ya.ru',
                banner=u'http://yastatic.net/morda-logo/i/logo.svg',
                title=u'Йандекс',
                conditions=[]
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()

            new_partner = BankPartnersObject(
                id=str(ObjectId()),
                region=[RFRegionsEnum.RFR_SPB],
                city=[RFRegionsEnum.RFR_SPB],
                enabled=True,
                sort_index=2,
                link=u'http://ya1.ru',
                banner=u'http://yastatic1.net/morda-logo/i/logo.svg',
                title=u'Йандекс2',
                conditions=[]
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()

            new_partner = BankPartnersObject(
                id=str(ObjectId()),
                region=[RFRegionsEnum.RFR_SPB],
                city=[RFRegionsEnum.RFR_SPB],
                enabled=True,
                sort_index=13,
                link=u'http://ya2.ru',
                banner=u'http://yastatic2.net/morda-logo/i/logo.svg',
                title=u'Йандекс3',
                conditions=[]
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()

            new_partner = BankPartnersObject(
                id=str(ObjectId()),
                region=[RFRegionsEnum.RFR_SPB],
                city=[RFRegionsEnum.RFR_SPB],
                enabled=False,
                sort_index=11,
                link=u'http://ya.ru',
                banner=u'http://yastatic.net/morda-logo/i/logo.svg',
                title=u'Йандекс',
                conditions=[]
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()

            new_partner = BankPartnersObject(
                id=str(ObjectId()),
                region=[RFRegionsEnum.RFR_MOSCOW],
                city=[RFRegionsEnum.RFR_MOSCOW],
                enabled=True,
                sort_index=2,
                link=u'http://ya1.ru',
                banner=u'http://yastatic1.net/morda-logo/i/logo.svg',
                title=u'Йандекс2',
                conditions=[]
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()

            batch_id = self.create_batch('llc', self.user).id
            doc1 = BatchDocumentDbObject(
                _owner=self.user,
                document_type='test',
                batch_id=batch_id,
                data={
                    'address': {
                        'region': u'Санкт-Петербург'
                    }
                }
            )
            sqldb.session.add(doc1)
            sqldb.session.commit()

            result = self.test_client.get('/partners/banks/?batch_id=%s' % str(batch_id))
            self.assertEqual(result.status_code, 200)

            data = json.loads(result.data)
            self.assertEqual(len(data['result']['banks_partners']), 3)

    @authorized()
    def test_request_bank(self):
        with self.app.app_context():
            DocRequisitiesStorage.get_batch_descriptor(DocumentBatchTypeEnum.DBT_NEW_LLC)['doc_types'] = [
                DocumentTypeEnum.DT_P11001]

            general_manager_person = self.create_person(self.user)
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_NEW_LLC, self.user)
            batch.data = {
                u"full_name": u"фывафыва",
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
                    "long_form_mode": True,
                    "ifns": u"7841",
                    "okato": u"92401385000",
                },
                u"address_type": u"general_manager_registration_address",
                u"general_manager_caption": u"повелитель",
                u"general_manager": {
                    "_id": general_manager_person.id,
                    "type": u"person"
                }
            }
            batch.result_fields = {
                'ifns_reg_info': {
                    'status': 'registered',
                    'reg_date': datetime.now(),
                    'full_name': u"Лютик",
                    'ogrn': 1095543023135
                }
            }
            sqldb.session.commit()
            batch_id = batch.id

            new_partner = BankPartnersObject(
                id=str(ObjectId()),
                region=[RFRegionsEnum.RFR_SPB],
                city=[RFRegionsEnum.RFR_SPB],
                enabled=True,
                sort_index=10,
                link=u'http://ya.ru',
                banner=u'http://yastatic.net/morda-logo/i/logo.svg',
                title=u'Йандекс',
                conditions=[]
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()
            bank_id = new_partner.id

            svc = BankPartnersServiceObject(
                id=str(ObjectId()),
                type='email',
                email='test_email@test_domain.zz',
                fields=partners_manage_commands._BANK_PARTNER_SCHEMA,
                template_name='account_creation_consultation_request',
                bank_partner_id=bank_id
            )
            sqldb.session.add(svc)
            sqldb.session.commit()

            result = self.test_client.post('/partners/banks/send/', data={
                'batch_id': batch_id,
                'bank_id': bank_id,
                'bank_contact_phone_general_manager': True,
                'bank_contact_phone': "+79001231213",
                'send_private_data': True
            })
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            batch = data['result']

            # DocumentBatchDbObject.get_collection(self.db).update({'_id': batch_id}, {
            #     '$set': {
            #         'data.ogrn': 1095543023135
            #     }
            # })
            # result = self.test_client.post('/partners/banks/send/', data={
            #     'batch_id': batch_id,
            #     'bank_id': bank_id,
            #     'bank_contact_phone_general_manager': True,
            #     'bank_contact_phone': "+79001231213",
            #     'send_private_data': True
            # })
            # self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            batch = data['result']

            self.assertNotIn('error_info', batch)
            self.assertIn('result_fields', batch)

            result_fields = batch['result_fields']
            self.assertIn('bank_partner_requests', result_fields)
            self.maxDiff = None
            del result_fields['bank_partner_requests'][0]['sent_date']
            self.assertEqual(result_fields['bank_partner_requests'], [{
                'bank_partner_id': str(bank_id),
                'bank_contact_phone': '+79001231213',
                'bank_contact_phone_general_manager': True,
                # идентификатор партнера по банковскому обслуживанию
                'bank_partner_caption': u'Йандекс',
                # название банка-партнера
                'send_private_data': True
                # дата отправки заявки
            }])

            self.assertEqual(BankPartnerRequestObject.query.count(), 1)
            bank_request = BankPartnerRequestObject.query.first()
            bank_request = copy(bank_request.__dict__)
            del bank_request['id']
            del bank_request['sent_date']
            del bank_request['_sa_instance_state']
            self.maxDiff = None
            self.assertEqual(bank_request, {
                'bank_partner_id': bank_id,
                'bank_contact_phone': '+79001231213',
                'bank_contact_phone_general_manager': 'true',
                'batch_id': batch_id,
                'bank_partner_caption': u'Йандекс',
                'send_private_data': True,
                'status': 'success'
            })

    @authorized()
    def test_request_bank_via_web(self):
        with self.app.app_context():
            DocRequisitiesStorage.get_batch_descriptor(DocumentBatchTypeEnum.DBT_NEW_LLC)['doc_types'] = [
                DocumentTypeEnum.DT_P11001]

            general_manager_person = self.create_person(self.user)
            batch = self.create_batch(DocumentBatchTypeEnum.DBT_NEW_LLC, self.user)
            batch.data = {
                u"full_name": u"фывафыва",
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
                    "long_form_mode": True,
                    "ifns": u"7841",
                    "okato": u"92401385000",
                },
                u"address_type": u"general_manager_registration_address",
                u"general_manager_caption": u"повелитель",
                u"general_manager": {
                    "_id": general_manager_person.id,
                    "type": u"person"
                }
            }
            batch.result_fields = {
                'ifns_reg_info': {
                    'status': 'registered',
                    'reg_date': datetime.now(),
                    'full_name': u"Лютик",
                    'ogrn': 1095543023135
                }
            }
            sqldb.session.commit()
            batch_id = batch.id

            new_partner = BankPartnersObject(
                id=str(ObjectId("55c9afab543ed837fea53db2")),
                region=[RFRegionsEnum.RFR_SPB],
                city=[RFRegionsEnum.RFR_SPB],
                enabled=True,
                sort_index=10,
                link=u'',
                banner=u"some link",
                title=u'«Альфа-банк»',
                conditions=[
                    u"бесплатный выезд менеджера в офис",
                    u"открытие расчетного счета за 2‒3 дня",
                    u"3 месяца бесплатно при оплате сразу 9 месяцев",
                    u"до 3000 рублей на поиск профессионалов на HH.ru",
                    u"до 9000 рублей на Яндекс.Директ после открытия счета в подарок"
                ]
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()
            bank_id = new_partner.id

            svc = BankPartnersServiceObject(
                id=str(ObjectId()),
                type='web',
                config={
                    'method': 'post',
                    'url': 'http://ya.ru',
                },
                fields=partners_manage_commands._BANK_PARTNER_SCHEMA2,
                template_name='alpha_bank_web_request',
                bank_partner_id=bank_id
            )
            sqldb.session.add(svc)
            sqldb.session.commit()

            result = self.test_client.post('/partners/banks/send/', data={
                'batch_id': batch_id,
                'bank_id': bank_id,
                'bank_contact_phone': "+79001231213",
                'bank_contact_phone_general_manager': True,
                'send_private_data': True
            })
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            batch = data['result']

            req_col = self.db['bank_partners_request']
            # DocumentBatchDbObject.get_collection(self.db).update({'_id': batch_id}, {
            #     '$set': {
            #         'data.ogrn': 1095543023135
            #     }
            # })
            # result = self.test_client.post('/partners/banks/send/', data={
            #     'batch_id': batch_id,
            #     'bank_id': bank_id,
            #     'bank_contact_phone_general_manager': True,
            #     'bank_contact_phone': "+79001231213",
            #     'send_private_data': True
            # })
            # self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            batch = data['result']

            self.assertNotIn('error_info', batch)
            self.assertIn('result_fields', batch)

            result_fields = batch['result_fields']
            self.assertIn('bank_partner_requests', result_fields)
            self.maxDiff = None
            del result_fields['bank_partner_requests'][0]['sent_date']
            self.assertEqual(result_fields['bank_partner_requests'], [{
                'bank_partner_id': str(bank_id),
                'bank_contact_phone': '+79001231213',
                'bank_contact_phone_general_manager': 'true',
                # идентификатор партнера по банковскому обслуживанию
                'bank_partner_caption': u'«Альфа-банк»',
                # название банка-партнера
                'send_private_data': True,
                # дата отправки заявки
            }])

            self.assertEqual(BankPartnerRequestObject.query.count(), 1)
            bank_request = BankPartnerRequestObject.query.first()
            bank_request = copy(bank_request.__dict__)
            del bank_request['id']
            del bank_request['sent_date']
            del bank_request['_sa_instance_state']
            self.maxDiff = None
            self.assertEqual(bank_request, {
                'bank_partner_id': bank_id,
                'bank_contact_phone': '+79001231213',
                'bank_contact_phone_general_manager': 'true',
                'batch_id': batch_id,
                'bank_partner_caption': u'«Альфа-банк»',
                'send_private_data': True,
                'status': 'failed'
            })

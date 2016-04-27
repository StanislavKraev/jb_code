# -*- coding: utf-8 -*-
import json
import os
from fw.documents.address_enums import RFRegionsEnum

os.environ['CELERY_CONFIG_MODULE'] = 'dev_celeryconfig'

from test_pack.base_batch_test import BaseBatchTestCase
from test_pack.test_api import authorized

class IfnsApiTestCase(BaseBatchTestCase):

    @authorized()
    def test_search_ifns(self):
        r1 = self.addRegIfns(u"ИФНС 1 (рег)", code=100)
        n1 = self.addIfns(u"ИФНС А", r1, code=1001)
        n2 = self.addIfns(u"ИФНС Б", r1, code=1002, address={'region': RFRegionsEnum.RFR_SPB, 'address_string': u'СПБ'})
        n3 = self.addIfns(u"ИФНС В", r1, code=1003, address={'region': RFRegionsEnum.RFR_SPB, 'address_string': u'СПБ'})

        response = self.test_client.get('/structures/ifns/search/')
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.data)
        self.assertEqual(result, {
            u'count': 4,
            u'total': 4,
            u'ifns': [{
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                u'caption': u"ИФНС 1 (рег)",
                u'id': unicode(r1['_id']),
                u'ifns_code': u'0100',
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС 1 (рег)'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }, {
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                u'caption': u"ИФНС А",
                u'id': unicode(n1['_id']),
                u'ifns_code': u'1001',
                u'llc_registration_ifns': {
                    u'caption': u'ИФНС 1 (рег)',
                    u'ifns_reg_code': u'10010',
                    u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    u'phones': [u'+73472290200', u'+73472290210']
                },
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС А'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }, {
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"СПБ",
                u'caption': u"ИФНС Б",
                u'id': unicode(n2['_id']),
                u'ifns_code': u'1002',
                u'llc_registration_ifns': {
                    u'caption': u'ИФНС 1 (рег)',
                    u'ifns_reg_code': u'10020',
                    u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    u'phones': [u'+73472290200', u'+73472290210']
                },
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС Б'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }, {
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"СПБ",
                u'caption': u"ИФНС В",
                u'id': unicode(n3['_id']),
                u'ifns_code': u'1003',
                u'llc_registration_ifns': {
                    u'caption': u'ИФНС 1 (рег)',
                    u'ifns_reg_code': u'10030',
                    u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    u'phones': [u'+73472290200', u'+73472290210']
                },
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС В'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }]
        })

        response = self.test_client.get(u'/structures/ifns/search/?region=%s' % RFRegionsEnum.RFR_SPB)
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.data)
        self.assertEqual(result, {
            u'count': 2,
            u'total': 2,
            u'ifns': [{
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"СПБ",
                u'caption': u"ИФНС Б",
                u'id': unicode(n2['_id']),
                u'ifns_code': u'1002',
                u'llc_registration_ifns': {
                    u'caption': u'ИФНС 1 (рег)',
                    u'ifns_reg_code': u'10020',
                    u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    u'phones': [u'+73472290200', u'+73472290210']
                },
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС Б'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }, {
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"СПБ",
                u'caption': u"ИФНС В",
                u'id': unicode(n3['_id']),
                u'ifns_code': u'1003',
                u'llc_registration_ifns': {
                    u'caption': u'ИФНС 1 (рег)',
                    u'ifns_reg_code': u'10030',
                    u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    u'phones': [u'+73472290200', u'+73472290210']
                },
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС В'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }]
        })

        response = self.test_client.get(u'/structures/ifns/search/?search_string=ИФНС А')
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.data)
        self.assertEqual(result, {
            u'count': 1,
            u'total': 1,
            u'ifns': [{
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                u'caption': u"ИФНС А",
                u'id': unicode(n1['_id']),
                u'ifns_code': u'1001',
                u'llc_registration_ifns': {
                    u'caption': u'ИФНС 1 (рег)',
                    u'ifns_reg_code': u'10010',
                    u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    u'phones': [u'+73472290200', u'+73472290210']
                },
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС А'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }]
        })

        response = self.test_client.get(u'/structures/ifns/search/?search_string=ИФНС')
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.data)
        self.assertEqual(result, {
            u'count': 4,
            u'total': 4,
            u'ifns': [{
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                u'caption': u"ИФНС 1 (рег)",
                u'id': unicode(r1['_id']),
                u'ifns_code': u'0100',
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС 1 (рег)'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }, {
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                u'caption': u"ИФНС А",
                u'id': unicode(n1['_id']),
                u'ifns_code': u'1001',
                u'llc_registration_ifns': {
                    u'caption': u'ИФНС 1 (рег)',
                    u'ifns_reg_code': u'10010',
                    u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    u'phones': [u'+73472290200', u'+73472290210']
                },
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС А'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }, {
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"СПБ",
                u'caption': u"ИФНС Б",
                u'id': unicode(n2['_id']),
                u'ifns_code': u'1002',
                u'llc_registration_ifns': {
                    u'caption': u'ИФНС 1 (рег)',
                    u'ifns_reg_code': u'10020',
                    u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    u'phones': [u'+73472290200', u'+73472290210']
                },
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС Б'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }, {
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"СПБ",
                u'caption': u"ИФНС В",
                u'id': unicode(n3['_id']),
                u'ifns_code': u'1003',
                u'llc_registration_ifns': {
                    u'caption': u'ИФНС 1 (рег)',
                    u'ifns_reg_code': u'10030',
                    u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    u'phones': [u'+73472290200', u'+73472290210']
                },
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС В'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }]
        })

        response = self.test_client.get(u'/structures/ifns/search/?search_string=ИФНС&limit=2&offset=1')
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.data)
        self.assertEqual(result, {
            u'count': 2,
            u'total': 4,
            u'ifns': [{
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                u'caption': u"ИФНС А",
                u'id': unicode(n1['_id']),
                u'ifns_code': u'1001',
                u'llc_registration_ifns': {
                    u'caption': u'ИФНС 1 (рег)',
                    u'ifns_reg_code': u'10010',
                    u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    u'phones': [u'+73472290200', u'+73472290210']
                },
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС А'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }, {
                u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
                u'address': u"СПБ",
                u'caption': u"ИФНС Б",
                u'id': unicode(n2['_id']),
                u'ifns_code': u'1002',
                u'llc_registration_ifns': {
                    u'caption': u'ИФНС 1 (рег)',
                    u'ifns_reg_code': u'10020',
                    u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                    u'phones': [u'+73472290200', u'+73472290210']
                },
                u'payment_details': {
                    u'account': u'',
                    u'bank_caption': u'',
                    u'bik': u'',
                    u'inn': u'0275067000',
                    u'kpp': u'027501001',
                    u'payment_recipient_caption': u'ИФНС Б'
                },
                u'phones': [u'+73472290200', u'+73472290210']
            }]
        })

    @authorized()
    def test_get_ifns(self):
        r = self.addRegIfns(u"ИФНС 1 (рег)", code=100)
        n = self.addIfns(u"ИФНС А", r, code=1003, address={'region': RFRegionsEnum.RFR_SPB, 'address_string': u'СПБ'})

        response = self.test_client.get('/structures/ifns/?id=%s' % str(r['_id']))
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.data)
        self.assertEqual(result, {
            u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
            u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
            u'caption': u'ИФНС 1 (рег)',
            u'id': unicode(r['_id']),
            u'ifns_code': u'0100',
            u'payment_details': {
                u'account': u'',
                u'bank_caption': u'',
                u'bik': u'',
                u'inn': u'0275067000',
                u'kpp': u'027501001',
                u'payment_recipient_caption': u'ИФНС 1 (рег)'
            },
            u'phones': [u'+73472290200', u'+73472290210']
        })

        response = self.test_client.get('/structures/ifns/?id=%s' % str(n['_id']))
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.data)
        self.assertEqual(result, {
            u'additional_info': u"Код ОКПО:88111351 Режим работы Понедельник-четверг: 8.30 - 17.30",
            u'address': u"СПБ",
            u'caption': u'ИФНС А',
            u'id': unicode(n['_id']),
            u'ifns_code': u'1003',
            u'payment_details': {
                u'account': u'',
                u'bank_caption': u'',
                u'bik': u'',
                u'inn': u'0275067000',
                u'kpp': u'027501001',
                u'payment_recipient_caption': u'ИФНС А'
            },
            u'phones': [u'+73472290200', u'+73472290210'],
            u'llc_registration_ifns': {
                u'caption': u'ИФНС 1 (рег)',
                u'ifns_reg_code': u'10030',
                u'address': u"Россия, Респ Башкортостан, г Уфа, ул Красина, д 52",
                u'phones': [u'+73472290200', u'+73472290210']
            }
        })

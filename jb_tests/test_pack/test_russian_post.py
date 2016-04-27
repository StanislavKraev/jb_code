# -*- coding: utf-8 -*-
from datetime import datetime
import json
from lxml import etree, objectify
import os
import requests
from fw.documents.enums import DocumentBatchTypeEnum
from fw.db.sql_base import db as sqldb

os.environ['CELERY_CONFIG_MODULE'] = 'dev_celeryconfig'

from services.russian_post.db_models import RussianPostTrackingItem, PostTrackingStatus
from test_pack.base_batch_test import BaseBatchTestCase
from test_pack.test_api import authorized


class RPTestCase(BaseBatchTestCase):

    @authorized()
    def test_get_status(self):
        url = 'http://tracking.russianpost.ru/rtm34?wsdl'
        headers = {
            "Accept-Encoding": "gzip,deflate",
            "Content-Type": "application/soap+xml;charset=UTF-8",
            "User-Agent": "Apache-HttpClient/4.1.1 (java 1.5)"
        }

        data = u"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:oper="http://russianpost.org/operationhistory" xmlns:data="http://russianpost.org/operationhistory/data" xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
                       <soap:Header/>
                       <soap:Body>
                          <oper:getOperationHistory>
                             <!--Optional:-->
                             <data:OperationHistoryRequest>
                                <data:Barcode>19083586376477</data:Barcode>
                                <data:MessageType>0</data:MessageType>
                                <!--Optional:-->
                                <data:Language>RUS</data:Language>
                             </data:OperationHistoryRequest>
                             <!--Optional:-->
                             <data:AuthorizationHeader soapenv:mustUnderstand="1">
                                <data:login>rocketscienceacademy</data:login>
                                <data:password>dBu46cgOra97s</data:password>
                             </data:AuthorizationHeader>
                          </oper:getOperationHistory>
                       </soap:Body>
                    </soap:Envelope>"""

        response = requests.post(url, data=data, headers=headers)
        self.assertEqual(response.status_code, 200)
        #print(response.text)

        last_status = {}
        root = etree.fromstring(response.content)
        for elem in root.getiterator():
            if not hasattr(elem.tag, 'find'): continue  # (1)
            i = elem.tag.find('}')
            if i >= 0:
                elem.tag = elem.tag[i+1:]
        objectify.deannotate(root, cleanup_namespaces=True)
        tags = root.xpath('//OperationHistoryData/historyRecord')
        for tag in tags:
            oper_type_id = None
            oper_type_descr = None
            date_val = None
            address_descr = None

            oper_tags = tag.xpath('./OperationParameters/OperType/Id')
            for otag in oper_tags:
                oper_type_id = otag.text
                break

            oper_tags = tag.xpath('./OperationParameters/OperType/Name')
            for otag in oper_tags:
                oper_type_descr = otag.text
                break

            operdate_tags = tag.xpath('./OperationParameters/OperDate')
            for otag in operdate_tags:
                date_val = datetime.strptime(otag.text[:19], "%Y-%m-%dT%H:%M:%S")
                break

            address_tags = tag.xpath('./AddressParameters/OperationAddress/Description')
            for atag in address_tags:
                address_descr = atag.text
                break

            if oper_type_id is not None and oper_type_descr is not None and date_val is not None and address_tags is not None:
                last_status = {
                    'operation': oper_type_id,
                    'op_name': oper_type_descr,
                    'dt': date_val,
                    'address': address_descr
                }

        print etree.tostring(root, pretty_print = True, encoding='utf-8')
        print(json.dumps(last_status, ensure_ascii=False, indent=1, default=lambda x: unicode(x)))

    @authorized()
    def test_get_status_from_db(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user)
        tracking1 = RussianPostTrackingItem(
            tracking=u"track1",
            batch=batch,
            owner=self.user
        )
        sqldb.session.add(tracking1)
        sqldb.session.commit()

        tracking2 = RussianPostTrackingItem(
            tracking=u"track2",
            batch=batch,
            owner=self.user
        )
        sqldb.session.add(tracking2)
        sqldb.session.commit()

        tracking3 = RussianPostTrackingItem(
            tracking=u"track3",
            owner=self.user
        )
        sqldb.session.add(tracking3)
        sqldb.session.commit()

        response = self.test_client.get('/external/russianpost/mail/status/?batch_id=%s' % batch.id)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data, {u'result': {u'status': u'progress', u'status_caption': u''}})

        response = self.test_client.get('/external/russianpost/mail/status/?batch_id=%s' % batch.id)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data, {u'result': {u'status': u'progress', u'status_caption': u''}})

    @authorized()
    def test_create_track(self):
        batch = self.create_batch(DocumentBatchTypeEnum.DBT_OSAGO, self.user)

        response = self.test_client.post('/external/russianpost/mail/track/', data={
            'batch_id': batch.id,
            'tracking': "track1"
        })
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data, {u'result': True})

        self.assertEqual(RussianPostTrackingItem.query.count(), 1)
        item = RussianPostTrackingItem.query.first()
        self.assertEqual(item.tracking, 'track1')
        self.assertEqual(item.batch_id, batch.id)
        self.assertEqual(item.status, PostTrackingStatus.PTS_NOT_FOUND)

        response = self.test_client.post('/external/russianpost/mail/track/', data={
            'batch_id': batch.id,
            'tracking': "track2"
        })
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data, {u'result': True})

        self.assertEqual(RussianPostTrackingItem.query.count(), 1)
        item = RussianPostTrackingItem.query.first()
        self.assertEqual(item.tracking, 'track2')
        self.assertEqual(item.batch_id, batch.id)
        self.assertEqual(item.status, PostTrackingStatus.PTS_NOT_FOUND)

        response = self.test_client.post('/external/russianpost/mail/track/', data={
            'batch_id': batch.id,
            'tracking': "track2"
        })
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data, {u'result': True})

        self.assertEqual(RussianPostTrackingItem.query.count(), 1)
        item2 = RussianPostTrackingItem.query.first()
        self.assertEqual(item2.id, item.id)
        self.assertEqual(item2.tracking, 'track2')
        self.assertEqual(item2.batch_id, batch.id)
        self.assertEqual(item2.status, PostTrackingStatus.PTS_NOT_FOUND)

        # todo: duplicate tracking id
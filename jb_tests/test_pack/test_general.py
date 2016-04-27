# -*- coding: utf-8 -*-
from bson import ObjectId

from flask import json

from base_test_case import BaseTestCase
from fw.db.sql_base import db as sqldb
from fw.api.args_validators import EmailAddressValidator
from fw.catalogs.models import OkvadObject
from services.ifns.utils.process_okvad import process_okvad
from test_pack.test_api import authorized


class GeneralTestCase(BaseTestCase):

    @authorized()
    def test_search_for_okvad(self):
        with self.app.app_context():
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.1", caption=u"Образование", nalog=u"usn", parent=None)
            sqldb.session.add(new_ok)
            sqldb.session.commit()
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.2", caption=u"Стройка", nalog=u"eshn", parent=None)
            sqldb.session.add(new_ok)
            sqldb.session.commit()
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.3", caption=u"Программы", nalog=u"usn", parent=new_ok.id)
            sqldb.session.add(new_ok)
            sqldb.session.commit()

            result = self.test_client.get(u'/search_okvad/?title=рой')
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertEqual(len(result_data['result']), 1)
            self.assertEqual(len(result_data['result'][0]), 4)
            self.assertIn('_id', result_data['result'][0])
            self.assertIn('caption', result_data['result'][0])
            self.assertIn('code', result_data['result'][0])
            self.assertIn('parent', result_data['result'][0])

    @authorized()
    def test_search_for_okvad_no_term(self):
        with self.app.app_context():
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.1", caption=u"Образование", nalog=u"usn", parent=None)
            sqldb.session.add(new_ok)
            sqldb.session.commit()
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.2", caption=u"Стройка", nalog=u"eshn", parent=None)
            sqldb.session.add(new_ok)
            sqldb.session.commit()
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.3", caption=u"Программы", nalog=u"usn", parent=new_ok.id)
            sqldb.session.add(new_ok)
            sqldb.session.commit()

            result = self.test_client.get(u'/search_okvad/')
            self.assertEqual(result.status_code, 400)

    @authorized()
    def test_okvad_skeleton(self):
        with self.app.app_context():
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.1", caption=u"Стройка", nalog=u"eshn", parent=None)
            sqldb.session.add(new_ok)
            sqldb.session.commit()
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.2", caption=u"Образование", nalog=u"usn", parent=None)
            sqldb.session.add(new_ok)
            sqldb.session.commit()
            xx = OkvadObject(id=str(ObjectId()), okved=u"100.3", caption=u"Программы", nalog=u"usn", parent=new_ok.id)
            sqldb.session.add(xx)
            sqldb.session.commit()
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.4", caption=u"Программы", nalog=u"usn", parent=new_ok.id)
            sqldb.session.add(new_ok)
            sqldb.session.commit()

            xx = OkvadObject(id=str(ObjectId()), okved=u"200.3", caption=u"Программы", nalog=u"eshn", parent=new_ok.id)
            sqldb.session.add(xx)
            sqldb.session.commit()
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"200.4", caption=u"Программы", nalog=u"eshn", parent=new_ok.id)
            sqldb.session.add(new_ok)
            sqldb.session.commit()

            result = self.test_client.post(u'/get_okvad_skeleton/')
            self.assertEqual(result.status_code, 200)
            print(result.data)

    @authorized()
    def test_search_for_okvad_short_term(self):
        with self.app.app_context():
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.1", caption=u"Образование", nalog=u"usn", parent=None)
            sqldb.session.add(new_ok)
            sqldb.session.commit()
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.2", caption=u"Стройка", nalog=u"eshn", parent=None)
            sqldb.session.add(new_ok)
            sqldb.session.commit()
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.3", caption=u"Программы", nalog=u"usn", parent=new_ok.id)
            sqldb.session.add(new_ok)
            sqldb.session.commit()

            result = self.test_client.get(u'/search_okvad/?title=ab')
            self.assertEqual(result.status_code, 400)

    @authorized()
    def test_search_for_okvad_new(self):
        with self.app.app_context():
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.1", caption=u"Образование", nalog=u"usn", parent=None)
            sqldb.session.add(new_ok)
            sqldb.session.commit()
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.2", caption=u"Стройка", nalog=u"eshn", parent=None)
            sqldb.session.add(new_ok)
            sqldb.session.commit()
            new_ok = OkvadObject(id=str(ObjectId()), okved=u"100.3", caption=u"Программы", nalog=u"usn", parent=new_ok.id)
            sqldb.session.add(new_ok)
            sqldb.session.commit()

            result = self.test_client.post(u'/get_okvad/', data = {})
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertEqual(len(result_data['result']), 3)

            result = self.test_client.post(u'/get_okvad/', data = {"search" : u"образование"})
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertEqual(len(result_data['result']), 1)

            parent_ok = OkvadObject.query.filter_by(okved="100.2").scalar()
            result = self.test_client.post(u'/get_okvad/', data = {"search" : u"програм", "parent" : parent_ok.id})
            self.assertEqual(result.status_code, 200)
            result_data = json.loads(result.data)
            self.assertEqual(len(result_data['result']), 1)


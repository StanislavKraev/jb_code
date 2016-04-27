# -*- coding: utf-8 -*-
import codecs
import glob
import json
import os
from random import randint
import subprocess
from tempfile import NamedTemporaryFile
import tempfile
import requests
import shutil
from fw.api.dadata_proxy import dadata_suggest
from fw.documents.address_enums import RFRegionsEnum
from fw.db.sql_base import db as sqldb
from services.car_assurance.db_models import CarAssuranceBranch, CarAssurance
from services.ifns.utils.process_egrul_captcha import recognize_captcha

os.environ['CELERY_CONFIG_MODULE'] = 'dev_celeryconfig'

from test_pack.base_batch_test import BaseBatchTestCase
from test_pack.test_api import authorized

import html5lib
from lxml.cssselect import CSSSelector

class CarAssuranceApiTestCase(BaseBatchTestCase):

    @authorized()
    def test_get_assurance_list(self):
        response = self.test_client.get('/structures/insurances/')
        self.assertEqual(response.status_code, 400)

        a1 = self.addCarAssurance(u"Assurance 1")
        a2 = self.addCarAssurance(u"Assurance 2")
        a3 = self.addCarAssurance(u"Assurance 3")

        response = self.test_client.get('/structures/insurances/?type=osago')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result, {
            'result': {
                'total': 3,
                'count': 3,
                'ifns': [{
                    'id': a1.id,
                    'short_name': u"Assurance 1",
                    'full_name': u"Assurance 1"
                }, {
                    'id': a2.id,
                    'short_name': u"Assurance 2",
                    'full_name': u"Assurance 2"
                }, {
                    'id': a3.id,
                    'short_name': u"Assurance 3",
                    'full_name': u"Assurance 3"
                }]
            }
        })

        response = self.test_client.get('/structures/insurances/?type=osago&limit=2')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result, {
            'result': {
                'total': 3,
                'count': 2,
                'ifns': [{
                    'id': a1.id,
                    'short_name': u"Assurance 1",
                    'full_name': u"Assurance 1"
                }, {
                    'id': a2.id,
                    'short_name': u"Assurance 2",
                    'full_name': u"Assurance 2"
                }]
            }
        })

        response = self.test_client.get('/structures/insurances/?type=osago&limit=2&offset=1')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result, {
            'result': {
                'total': 3,
                'count': 2,
                'ifns': [{
                    'id': a2.id,
                    'short_name': u"Assurance 2",
                    'full_name': u"Assurance 2"
                }, {
                    'id': a3.id,
                    'short_name': u"Assurance 3",
                    'full_name': u"Assurance 3"
                }]
            }
        })

        response = self.test_client.get('/structures/insurances/?type=osago&search=Assurance%202')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result, {
            'result': {
                'total': 1,
                'count': 1,
                'ifns': [{
                    'id': a2.id,
                    'short_name': u"Assurance 2",
                    'full_name': u"Assurance 2"
                }]
            }
        })

    @authorized()
    def test_get_assurance_branches(self):
        response = self.test_client.get('/structures/insurances/branches/')
        self.assertEqual(response.status_code, 400)

        a1 = self.addCarAssurance(u'А1')
        b1_1 = self.addCarAssuranceBranch(a1)
        b1_2 = self.addCarAssuranceBranch(a1, region=RFRegionsEnum.RFR_ADYGEYA)
        b1_3 = self.addCarAssuranceBranch(a1)

        a2 = self.addCarAssurance(u'А2')
        b2_1 = self.addCarAssuranceBranch(a2)
        b2_2 = self.addCarAssuranceBranch(a2, region=RFRegionsEnum.RFR_ADYGEYA)
        b2_3 = self.addCarAssuranceBranch(a2, region=RFRegionsEnum.RFR_ADYGEYA)

        response = self.test_client.get('/structures/insurances/branches/?id=%s' % a1.id)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result, {
            u'result': {
                u'total': 3,
                u'count': 3,
                u'ifns': [{
                    u'id': b1_2.id,
                    u'title': u"title",
                    u'phone': u"112",
                    u'address': u"дер. Поганкино д. 13",
                    u'region': RFRegionsEnum.RFR_ADYGEYA
                }, {
                    u'id': b1_1.id,
                    u'title': u"title",
                    u'phone': u"112",
                    u'address': u"дер. Поганкино д. 13",
                    u'region': RFRegionsEnum.RFR_LENINGRADSKAYA_REGION
                }, {
                    u'id': b1_3.id,
                    u'title': u"title",
                    u'phone': u"112",
                    u'address': u"дер. Поганкино д. 13",
                    u'region': RFRegionsEnum.RFR_LENINGRADSKAYA_REGION
                }]
            }
        })

        response = self.test_client.get('/structures/insurances/branches/?id=%s&limit=1&offset=1' % a2.id)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result, {
            u'result': {
                u'total': 3,
                u'count': 1,
                u'ifns': [{
                    u'id': b2_3.id,
                    u'title': u"title",
                    u'phone': u"112",
                    u'address': u"дер. Поганкино д. 13",
                    u'region': RFRegionsEnum.RFR_ADYGEYA
                }]
            }
        })

        response = self.test_client.get('/structures/insurances/branches/?id=%s&region=%s' % (a2.id, RFRegionsEnum.RFR_ADYGEYA))
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result, {
            u'result': {
                u'total': 2,
                u'count': 2,
                u'ifns': [{
                    u'id': b2_2.id,
                    u'title': u"title",
                    u'phone': u"112",
                    u'address': u"дер. Поганкино д. 13",
                    u'region': RFRegionsEnum.RFR_ADYGEYA
                }, {
                    u'id': b2_3.id,
                    u'title': u"title",
                    u'phone': u"112",
                    u'address': u"дер. Поганкино д. 13",
                    u'region': RFRegionsEnum.RFR_ADYGEYA
                }]
            }
        })

    def _test_collect_strah_info(self):
        response = requests.get('http://autoins.ru/ru/about_rsa/members/actual_members.wbp')

        str_data = response.text.encode('utf-8').decode('string_escape')
        content = u"<!DOCTYPE html><html><head><title></title></head><body>%s</body></html>" % str_data.decode('utf-8')
        root = html5lib.parse(content, treebuilder='lxml', namespaceHTMLElements=False)

        names = ('N', 'full_name', 'short_name', 'old_name', 'lic N', 'lic Dt', 'svid N', 'svid Dt', 'phone', 'email', 'address', 'inn')

        objects = []
        for tr_item in CSSSelector('table.usual tr:not(.header)')(root):
            i = 0
            obj = {}
            for td in CSSSelector('td')(tr_item):
                text = td.text.strip() if td.text else u""
                obj[names[i]] = text
                i += 1
            objects.append(obj)
            assert(obj['inn'])

        print(json.dumps(objects, indent=1, ensure_ascii=False, default=lambda x: unicode(x)))

        failed_inns = []
        for obj in objects:
            inn = obj['inn']
            print(obj['inn'])
            files = [f for f in glob.glob('/tmp/%s_*.pdf' % inn)]
            if files:
                print('already has')
                continue

            s = requests.Session()
            s.get('http://egrul.nalog.ru/')
            response = s.get('http://egrul.nalog.ru/static/captcha.html?%s' % str(randint(100000, 100000000)))

            token = response.text
            captcha = recognize_captcha(token)
            if not captcha:
                print(u'failed to get captcha')
                failed_inns.append(obj['inn'])
                continue

            response = s.post('http://egrul.nalog.ru/', data={
                'captcha': captcha,
                'captchaToken': token,
                'fam': u'',
                'kind': u'ul',
                'nam': u'',
                'namul':'',
                'ogrninnfl':'',
                'ogrninnul': obj['inn'],
                'otch': '',
                'region': '',
                'regionul': '',
                'srchFl': 'ogrn',
                'srchUl': 'ogrn'})

            if response.status_code != 200:
                print("invalid response: %s" % str(response.status_code))
                failed_inns.append(obj['inn'])
                continue

            data = json.loads(response.text)
            for r in data["rows"]:
                file_url = "http://egrul.nalog.ru/download/%s" % r["T"]
                print(file_url)

                response = s.get(file_url, stream=True)
                tmp_file = NamedTemporaryFile(delete=False, prefix=obj['inn'] + '_', suffix='.pdf')
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, tmp_file)
                tmp_file.close()
                print(tmp_file.name)

        print(failed_inns)

    def _test_collect_strah_info_stage2(self):
        def is_quoted_text_end(t):
            if '"' not in t:
                return False
            if not t:
                return False
            if t[0] == '"':
                return False
            for c in t[1:]:
                if c.isalpha():
                    continue
                if c == '"':
                    return True
                if c == ' ':
                    return False
            return False

        file_path = "/home/skraev/strah_info/*_*.pdf"

        address_starts = (
            (u"Почтовый индекс", ""),
            (u"Субъект Российской Федерации", ""),
            (u"Улица (проспект, переулок и т.д.)", ""),
            (u"Дом (владение и т.п.)", u"д."),
            (u"Корпус (строение и т.п.)", u"корпус"),
            (u"Город (волость и т.п.)", ""),
            (u"Офис (квартира и т.п.)", u"кв."),
            (u"Район (улус и т.п.)", ""),
        )

        CarAssuranceBranch.query.filter().delete()
        sqldb.session.commit()
        CarAssurance.query.filter().delete()
        sqldb.session.commit()

        for path in glob.glob(file_path):
            temp_file_out = tempfile.NamedTemporaryFile(mode="w+", suffix=".txt")
            output_file_name = temp_file_out.name
            temp_file_out.close()
            p = subprocess.Popen(['pdftotext', '-layout', path, output_file_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
            out, err = p.communicate()
            rc = p.returncode
            if rc is not 0:
                print(u"Failed to executed pdftotext (%s, %s)" % (out, err))
                return
            if not os.path.exists(output_file_name):
                print(u"No file were generated")
                return

            with codecs.open(output_file_name, 'r', 'utf-8') as f:
                content = f.read()

            inn = os.path.split(path)[-1].split('_')[0]
            status = 'initial'

            full_name = u""
            short_name = u""
            address = u""
            branch_name = u""
            branch_address = u""

            branches = []

            for line in content.split('\n'):
                text = line.strip()
                if not text or text.startswith(u"Сведения с сайта ФНС России"):
                    continue
                if status == 'initial':
                    if text == u'Наименование':
                        status = 'full_name'
                        continue
                elif status == 'full_name':
                    if u'Полное наименование' in text:
                        status = u'full_name_continue'
                        full_name = text[text.find(u'Полное наименование') + len(u'Полное наименование'):].strip()
                elif status == u'full_name_continue':
                    if u'ГРН и дата внесения в ЕГРЮЛ записи' in text:
                        status = "waiting_short_name"
                        continue
                    if u"Сокращенное наименование" in text:
                        status = u'short_name'
                        short_name = text[text.find(u'Сокращенное наименование') + len(u'Сокращенное наименование'):].strip()
                        continue
                    if full_name.endswith('-') or (full_name.endswith('"') and is_quoted_text_end(text)):
                        full_name += text
                    else:
                        full_name += u" " + text
                    while u"  " in full_name:
                        full_name = full_name.replace(u"  ", " ")
                elif status == 'waiting_short_name':
                    if u"Сокращенное наименование" in text:
                        status = u'short_name'
                        short_name = text[text.find(u'Сокращенное наименование') + len(u'Сокращенное наименование'):].strip()
                        continue
                elif status == 'short_name':
                    if u"ГРН и дата внесения в ЕГРЮЛ записи" in text:
                        status = 'waiting_for_address'
                        continue
                    if short_name.endswith('-') or (short_name.endswith('"') and is_quoted_text_end(text)):
                        short_name += text
                    else:
                        short_name += u" " + text
                    while u"  " in short_name:
                        short_name = short_name.replace(u"  ", " ")
                elif status == 'waiting_for_address':
                    if text == u"Адрес (место нахождения)":
                        status = "address"
                elif status == 'address':
                    if u"ГРН и дата внесения в ЕГРЮЛ записи" in text:
                        status = 'branches_and_agencies'
                        continue

                    for ads, rep in address_starts:
                        if ads in text:
                            text = rep + " " + text[text.find(ads) + len(ads):].strip()
                            break
                    address += text + " "
                elif status == 'branches_and_agencies':
                    if text == u"Филиалы":
                        status = 'branches'
                        branch_name = u""
                        continue
                elif status == 'branches':
                    if u"Наименование" in text:
                        branch_name = text[text.find(u"Наименование") + len(u"Наименование"):].strip()
                        status = "branch_name_continue"
                        continue
                    if u"Почтовый индекс" in text:
                        branch_address = text[text.find(u"Почтовый индекс") + len(u"Почтовый индекс"):].strip()
                        status = "branch_address"
                elif status == 'branch_name_continue':
                    if u"Почтовый индекс" in text:
                        branch_address = text[text.find(u"Почтовый индекс") + len(u"Почтовый индекс"):].strip()
                        status = "branch_address"
                        continue
                    if u"ГРН и дата внесения в ЕГРЮЛ записи" in text:
                        status = "waiting_branch_address"
                        continue
                    branch_name += u" " + text
                elif status == "waiting_branch_address":
                    if u"Почтовый индекс" in text:
                        branch_address = text[text.find(u"Почтовый индекс") + len(u"Почтовый индекс"):].strip()
                        status = "branch_address"
                        continue
                elif status == "branch_address":
                    if u"ГРН и дата внесения в ЕГРЮЛ записи" in text:
                        status = 'branches'
                        branches.append({
                            'name': branch_name,
                            'address': branch_address
                        })
                        continue

                    for ads, rep in address_starts:
                        if ads in text:
                            text = rep + " " + text[text.find(ads) + len(ads):].strip()
                            break
                    branch_address += text + " "

            if not short_name or not address:
                continue

            resp = dadata_suggest('address', {"query": address})
            new_ca = CarAssurance(
                full_name=full_name,
                short_name=short_name,
                address=resp['suggestions'][0]['value']
            )
            sqldb.session.add(new_ca)
            sqldb.session.commit()

            print(u"inn: %s\n full_name: %s\n short_name: %s\n address: %s\n" % (inn, full_name, short_name, address))
            for branch in branches:
#                print(json.dumps(branch, indent=1, ensure_ascii=False))
                address = branch['address']
                resp = dadata_suggest('address', {"query": address})
                region = resp['suggestions'][0]['data']['region']
                new_ca_branch = CarAssuranceBranch(
                    address=resp['suggestions'][0]['value'],
                    car_assurance=new_ca,
                    region=region
                )
                if branch['name']:
                    new_ca_branch.title = branch['name']

                sqldb.session.add(new_ca_branch)
                sqldb.session.commit()

        a = 1
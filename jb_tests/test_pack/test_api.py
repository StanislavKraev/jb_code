# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import pickle
import random
import string

from flask import json, current_app
from bson.objectid import ObjectId

from base_test_case import BaseTestCase, authorized, registered_user
from fw.api import errors
from fw.api.errors import UserNotFound, ActivationCodeExpiredOrInvalid
from fw.api.sql_session_storage import Session
from fw.auth.encrypt import encrypt_password
from fw.auth.models import AuthUser, UserActivationLink, ConfirmationLinkTypeEnum, AuthorizationUrl
from fw.auth.user_manager import UserManager
from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import RFRegionsEnum, HouseTypeEnum, FlatTypeEnum
from fw.documents.address_enums import StreetTypeEnum
from fw.documents.db_fields import PrivatePersonDbObject, CompanyDbObject, DocumentBatchDbObject, BatchDocumentDbObject
from fw.documents.enums import CompanyTypeEnum, DocumentTypeEnum, BatchStatusEnum, DocumentBatchTypeEnum
from services.ifns.data_model.fields import IfnsBooking
from services.llc_reg.documents.enums import IfnsServiceEnum
from services.notarius.data_model.models import NotariusBookingObject, NotariusObject
from services.yurist.data_model.enums import YuristBatchCheckStatus
from services.yurist.data_model.fields import YuristBatchCheck


class ApiTestCase(BaseTestCase):
    def setUp(self):
        super(ApiTestCase, self).setUp()

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def _make_ua_link(self, use_chars, link_type, user_id=None, new_mobile=None, new_email=None):
        max_activation_link_length = self.config['max_activation_link_length']
        digital_activation_link_length = self.config['digital_activation_link_length']

        if use_chars:
            link_code = u''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(max_activation_link_length))
        else:
            link_code = u''.join(random.choice(string.digits) for _ in range(digital_activation_link_length))
        recovery_link = UserActivationLink(
            link_code=link_code,
            auth_user_id=user_id,
            link_type=link_type
        )
        if new_mobile is not None:
            recovery_link.new_mobile = new_mobile
        if new_email is not None:
            recovery_link.new_email = new_email

        return recovery_link

    @authorized(is_temporal=True)
    def test_logout_temp_user(self):
        result = self.test_client.post('/account/logout/')
        self.assertEqual(result.status_code, 403)

    def test_authorize_temporary_user(self):
        result = self.test_client.post('/account/login/temporal/')
        self.assertEqual(result.status_code, 200)

        user = AuthUser.query.first()
        self.assertTrue(user.temporal)

        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)

        del result_data['result']['id']
        del result_data['result']['registration_date']
        self.assertEqual(result_data['result'], {
            u'email': u'',
            u'email_confirmed': False,
            u'mobile': u'',
            u'mobile_confirmed': False,
            u'person': {
                u'name': u'',
                u'patronymic': u'',
                u'surname': u''
            },
            u'facebook': None,
            u'vk': None,
            u'subscription': None,
            u'temporal': True,
            u'password_set': False,
            u'role': [u'user']
        })

        result = self.test_client.get('/account/profile/')
        self.assertEqual(result.status_code, 200)

        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)

        del result_data['result']['id']
        del result_data['result']['registration_date']
        self.assertEqual(result_data['result'], {
            u'email': u'',
            u'email_confirmed': False,
            u'mobile': u'',
            u'mobile_confirmed': False,
            u'person': {
                u'name': u'',
                u'patronymic': u'',
                u'surname': u''
            },
            u'facebook': None,
            u'vk': None,
            u'subscription': None,
            u'temporal': True,
            u'password_set': False,
            u'role': [u'user']
        })

    def test_authorize_temporary_user_while_authorized_temporary_user(self):
        result = self.test_client.post('/account/login/temporal/')
        self.assertEqual(result.status_code, 200)

        user = AuthUser.query.first()
        self.assertTrue(user.temporal)

        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)

        id1 = result_data['result']['id']
        del result_data['result']['id']
        del result_data['result']['registration_date']
        self.assertEqual(result_data['result'], {
            u'email': u'',
            u'email_confirmed': False,
            u'mobile': u'',
            u'mobile_confirmed': False,
            u'person': {
                u'name': u'',
                u'patronymic': u'',
                u'surname': u''
            },
            u'facebook': None,
            u'vk': None,
            u'subscription': None,
            u'temporal': True,
            u'password_set': False,
            u'role': [u'user']
        })

        result = self.test_client.post('/account/login/temporal/')
        self.assertEqual(result.status_code, 200)

        user = AuthUser.query.first()
        self.assertTrue(user.temporal)

        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)

        self.assertEqual(id1, result_data['result']['id'])
        del result_data['result']['id']
        del result_data['result']['registration_date']
        self.assertEqual(result_data['result'], {
            u'email': u'',
            u'email_confirmed': False,
            u'mobile': u'',
            u'mobile_confirmed': False,
            u'person': {
                u'name': u'',
                u'patronymic': u'',
                u'surname': u''
            },
            u'facebook': None,
            u'vk': None,
            u'subscription': None,
            u'temporal': True,
            u'password_set': False,
            u'role': [u'user']
        })

    @authorized()
    def test_authorize_temporary_user_while_authorized_persistent_user(self):
        result = self.test_client.post('/account/login/temporal/')
        self.assertEqual(result.status_code, 200)

        user = AuthUser.query.first()
        self.assertFalse(user.temporal)

        result_data = json.loads(result.data)
        self.assertIn('result', result_data)
        self.assertNotIn('error', result_data)

        del result_data['result']['id']
        del result_data['result']['registration_date']
        self.assertEqual(result_data['result'], {
            u'email': u'test@somedomain.zz',
            u'email_confirmed': True,
            u'mobile': u'+79001112233',
            u'mobile_confirmed': True,
            u'person': {
                u'name': u'Name',
                u'surname': u'Surname',
                u'patronymic': u'Patronymic'
            },
            u'facebook': None,
            u'vk': None,
            u'subscription': None,
            u'temporal': False,
            u'password_set': True,
            u'role': [u'user']
        })

    def test_sign_up_email(self):
        with self.app.app_context():
            args = {
                'name': u'Станислав'.encode('utf8'),
                'email': 'test@somedomain.zz',
                'password': 'TestPassword123'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            uid = data['result']['id']
            self.assertEqual(data['result']['email'], 'test@somedomain.zz')
            user = AuthUser.query.filter_by(uuid=uid).first()
            self.assertIsNotNone(user)
            self.assertFalse(user.email_confirmed)
            self.assertLess((datetime.utcnow() - user.signup_date).total_seconds(), 10)
            self.assertIsNotNone(user.last_login_date)
            self.assertTrue(user.enabled)

            # user_profile_obj = UserProfile.find_one(current_app.db, {'auth_user_id': user.id})
            # self.assertIsNotNone(user_profile_obj)

            self.assertEqual(len(self.mailer.mails), 1)

            user_activation_link = UserActivationLink.query.first()
            self.assertIsNotNone(user_activation_link)
            self.assertEqual(user_activation_link.auth_user_id, user.id)
            self.assertEqual(len(user_activation_link.link_code), self.config['max_activation_link_length'])
            self.assertTrue(user_activation_link.link_code.isalnum())
            self.assertLess((datetime.utcnow() - user_activation_link.creation_date).total_seconds(), 10)
            self.assertIsNone(user_activation_link.used_date)
            self.assertEqual(user_activation_link.new_email, 'test@somedomain.zz')

            result = self.test_client.get('/account/profile/')

            self.assertEqual(result.status_code, 200)

    def test_get_profile_unauthorized(self):
        with self.app.app_context():
            result = self.test_client.get('/account/profile/')

            self.assertEqual(result.status_code, 403)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            error = data['error']
            self.assertIn('code', error)
            self.assertEqual(error['code'], 100)

    @authorized()
    def test_get_profile_authorized(self):
        with self.app.app_context():
            result = self.test_client.get('/account/profile/')

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)

    def test_sign_up_short_password(self):
        with self.app.app_context():
            args = {
                'name': 'ТестовоеИмя',
                'surname': 'ТестоваяФамилия',
                'patronymic': 'ТестовоеОтчество',
                'email': 'test@somedomain.zz',
                'password': 'shrtp'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            error = data['error']
            self.assertIn('code', error)
            self.assertEqual(error['code'], 109)

    def test_sign_up_simple_password(self):
        with self.app.app_context():
            args = {
                'name': 'ТестовоеИмя',
                'surname': 'ТестоваяФамилия',
                'patronymic': 'ТестовоеОтчество',
                'email': 'test@somedomain.zz',
                'password': 'longbutverysimple'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertNotIn('error', data)

    def test_sign_up_no_uppercase_in_password(self):
        with self.app.app_context():
            args = {
                'name': 'ТестовоеИмя',
                'surname': 'ТестоваяФамилия',
                'patronymic': 'ТестовоеОтчество',
                'email': 'test@somedomain.zz',
                'password': 'longbutverysimple123_'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertNotIn('error', data)

    def test_sign_up_no_email_no_phone(self):
        with self.app.app_context():
            args = {
                'name': 'ТестовоеИмя',
                'surname': 'ТестоваяФамилия',
                'patronymic': 'ТестовоеОтчество',
                'password': 'shrtpw'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 400)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            error = data['error']
            self.assertIn('code', error)
            self.assertEqual(error['code'], 4)

    def test_sign_up_invalid_email(self):
        with self.app.app_context():
            args = {
                'name': 'ТестовоеИмя',
                'surname': 'ТестоваяФамилия',
                'patronymic': 'ТестовоеОтчество',
                'password': 'shrtpw',
                'email': 'invalid'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 400)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            error = data['error']
            self.assertIn('code', error)
            self.assertEqual(error['code'], 5)

    def test_sign_up_duplicate_email(self):
        with self.app.app_context():
            args = {
                'name': 'ТестовоеИмя',
                'surname': 'ТестоваяФамилия',
                'patronymic': 'ТестовоеОтчество',
                'email': 'test@somedomain.zz',
                'password': 'TestPassword123'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 200)
            self.test_client.post('/account/logout/', data={})
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)

    def test_sign_up_duplicate_activated_email(self):
        with self.app.app_context():
            args = {
                'name': 'ТестовоеИмя',
                'surname': 'ТестоваяФамилия',
                'patronymic': 'ТестовоеОтчество',
                'email': 'test@somedomain.zz',
                'password': 'TestPassword123'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 200)

            user_activation_link = UserActivationLink.query.first()
            user = AuthUser.query.first()

            args = {
                'user_id': user.id,
                'type': 'email',
                'code': user_activation_link.link_code
            }
            result = self.test_client.post('/account/confirm/', data=args)
            self.assertEqual(result.status_code, 200)

            self.test_client.post('/account/logout/', data={})
            args = {
                'name': 'ТестовоеИмя',
                'surname': 'ТестоваяФамилия',
                'patronymic': 'ТестовоеОтчество',
                'email': 'test@somedomain.zz',
                'password': 'TestPassword123'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)

    @registered_user()
    def test_login_email(self):
        args = {'email': 'test@somedomain.zz',
                'password': 'TestPassword123'}

        result = self.test_client.post('/account/login/', data=args)

        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertIsNotNone(data)
        self.assertIn('result', data)

    def test_logout(self):
        with self.app.app_context():
            args = {
                'email': 'test@somedomain.zz',
                'password': 'TestPassword123'
            }
            self.test_client.post('/account/create/', data=args)
            user = AuthUser.query.first()

            user_activation_link = UserActivationLink.query.first()
            args = {
                'user_id': user.id,
                'type': 'email',
                'code': user_activation_link.link_code
            }

            result = self.test_client.post('/account/confirm/', data=args)

            self.assertEqual(result.status_code, 200)

            args = {'email': 'test@somedomain.zz',
                    'password': 'TestPassword123'}

            result = self.test_client.post('/account/login/', data=args)

            self.assertEqual(result.status_code, 200)

            #cookie = result.headers['Set-Cookie'].split('=')[1].split(';')[0]
            #self.test_client.set_cookie('localhost', u'_jbuid_', cookie)
            result = self.test_client.post('/account/logout/')
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            self.assertEqual(data['result'], 'OK')

    def test_logout_unauthorized(self):
        result = self.test_client.post('/account/logout/')
        self.assertEqual(result.status_code, 403)

    def test_activate_by_email_link(self):
        with self.app.app_context():
            args = {
                'email': 'test@somedomain.zz',
                'password': 'TestPassword123'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 200)
            user_activation_link = UserActivationLink.query.first()
            self.assertIsNotNone(user_activation_link)

            user = AuthUser.query.first()
            self.assertIsNotNone(user)
            self.assertTrue(user.enabled)

#            user_profile_obj = UserProfile.find_one(current_app.db, {'auth_user_id': user.id})

            self.assertFalse(user.mobile_confirmed)
            self.assertFalse(user.email_confirmed)

            args = {
                'user_id': user.uuid,
                'type': 'email',
                'code': user_activation_link.link_code
            }
            result = self.test_client.post('/account/confirm/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            self.assertTrue(data['result'])
            user = AuthUser.query.first()
            self.assertTrue(user.enabled)
            user_activation_link = UserActivationLink.query.first()
            self.assertIsNotNone(user_activation_link.used_date)
            self.assertLess((user_activation_link.used_date - datetime.utcnow()).total_seconds(), 10)

            self.assertFalse(user.mobile_confirmed)
            self.assertTrue(user.email_confirmed)

        #    def test_activate_by_email_link_get_method(self):
        #        with self.app.app_context():
        #            args = {
        #                'email' : 'test@somedomain.zz',
        #                'password' : 'TestPassword123'
        #            }
        #            result = self.test_client.post('/account/create/', data = args)
        #
        #            self.assertEqual(result.status_code, 200)
        #            user_activation_link = UserActivationLink.query.first()
        #            self.assertIsNotNone(user_activation_link)
        #
        #            user = AuthUser.query.first()
        #            self.assertIsNotNone(user)
        #            self.assertFalse(user.enabled)
        #
        #            user_profile_obj = UserProfile.find_one(current_app.db, {'auth_user_id' : user.id})
        #            self.assertIsNotNone(user_profile_obj)
        #
        #            self.assertFalse(user.mobile_confirmed)
        #            self.assertFalse(user.email_confirmed)
        #
        #            result = self.test_client.get('/account/confirm/?user_id=%s&type=%s&code=%s' % (user.id, 'email', user_activation_link.link_code))
        #
        #            self.assertEqual(result.status_code, 200)
        #            data = json.loads(result.data)
        #            self.assertIsNotNone(data)
        #            self.assertIn('result', data)
        #            self.assertTrue(data['result'])
        #            user = AuthUser.query.first()
        #            self.assertTrue(user.enabled)
        #            user_activation_link = UserActivationLink.query.first()
        #            self.assertIsNotNone(user_activation_link.used_date)
        #            self.assertLess((user_activation_link.used_date - datetime.utcnow()).total_seconds(), 10)
        #
        #            self.assertFalse(user.mobile_confirmed)
        #            self.assertTrue(user.email_confirmed)

        #    def test_activation_code_not_found(self):
        #        with self.app.app_context():
        #            args = {
        #                'email' : 'test@somedomain.zz',
        #                'password' : 'TestPassword123'
        #            }
        #            result = self.test_client.post('/account/create/', data = args)
        #
        #            self.assertEqual(result.status_code, 200)
        #            user_activation_link = UserActivationLink.query.first()
        #            self.assertIsNotNone(user_activation_link)
        #
        #            user = AuthUser.query.first()
        #            self.assertIsNotNone(user)
        #            self.assertFalse(user.enabled)
        #
        #            args = {
        #                'user_id' : user.id,
        #                'type' : 'email',
        #                'code' : 'A' * self.config['max_activation_link_length']
        #            }
        #            result = self.test_client.post('/account/confirm/', data = args)
        #
        #            self.assertEqual(result.status_code, 200)
        #            data = json.loads(result.data)
        #            self.assertIsNotNone(data)
        #            self.assertIn('error', data)
        #            error = data['error']
        #            self.assertIn('code', error)
        #            self.assertEqual(error['code'], ActivationCodeExpiredOrInvalid.ERROR_CODE)
        #
        #            user = AuthUser.query.first()
        #            self.assertFalse(user.enabled)
        #            user_activation_link = UserActivationLink.query.first()
        #            self.assertIsNone(user_activation_link.used_date)

        #    def test_activation_code_malformed(self):
        #        with self.app.app_context():
        #            args = {
        #                'email' : 'test@somedomain.zz',
        #                'password' : 'TestPassword123'
        #            }
        #            result = self.test_client.post('/account/create/', data = args)
        #
        #            self.assertEqual(result.status_code, 200)
        #            user_activation_link = UserActivationLink.query.first()
        #            self.assertIsNotNone(user_activation_link)
        #
        #            user = AuthUser.query.first()
        #            self.assertIsNotNone(user)
        #            self.assertFalse(user.enabled)
        #
        #            args = {
        #                'user_id' : user.id,
        #                'type' : 'email',
        #                'code' : 'xyz'
        #            }
        #            result = self.test_client.post('/account/confirm/', data = args)
        #
        #            self.assertEqual(result.status_code, 400)
        #
        #            user = AuthUser.query.first()
        #            self.assertFalse(user.enabled)
        #            user_activation_link = UserActivationLink.query.first()
        #            self.assertIsNone(user_activation_link.used_date)

        #    def test_email_not_activated(self):
        #        with self.app.app_context():
        #            args = {
        #                'email' : 'test@somedomain.zz',
        #                'password' : 'TestPassword123'
        #            }
        #            self.test_client.post('/account/create/', data = args)
        #
        #            args = {'email' : 'test@somedomain.zz',
        #                    'password' : 'TestPassword123'}
        #
        #            result = self.test_client.post('/account/login/', data = args)
        #
        #            data = json.loads(result.data)
        #            self.assertIn('error', data)
        #            error = data['error']
        #            self.assertIn('code', error)
        #            self.assertEqual(error['code'], errors.EmailIsNotConfirmed.ERROR_CODE)

        #    def test_activate_already_activated(self):
        #        with self.app.app_context():
        #            args = {
        #                'email' : 'test@somedomain.zz',
        #                'password' : 'TestPassword123'
        #            }
        #            result = self.test_client.post('/account/create/', data = args)
        #
        #
        #            self.assertEqual(result.status_code, 200)
        #            user_activation_link = UserActivationLink.query.first()
        #            self.assertIsNotNone(user_activation_link)
        #
        #            user = AuthUser.query.first()
        #            self.assertIsNotNone(user)
        #            self.assertFalse(user.enabled)
        #
        #            args = {
        #                'user_id' : user.id,
        #                'type' : 'email',
        #                'code' : user_activation_link.link_code
        #            }
        #            result = self.test_client.post('/account/confirm/', data = args)
        #
        #            self.assertEqual(result.status_code, 200)
        #            user = AuthUser.query.first()
        #            self.assertTrue(user.enabled)
        #            user_activation_link = UserActivationLink.query.first()
        #            self.assertIsNotNone(user_activation_link.used_date)
        #            self.assertLess((user_activation_link.used_date - datetime.utcnow()).total_seconds(), 10)
        #            result = self.test_client.post('/account/confirm/', data = args)
        #            self.assertEqual(result.status_code, 200)
        #            user = AuthUser.query.first()
        #            self.assertTrue(user.enabled)
        #            data = json.loads(result.data)
        #            self.assertIsNotNone(data)
        #            self.assertIn('error', data)
        #            self.assertEqual(data['error']['code'], 108)
        #
        #    def test_activate_by_alien_code(self):
        #        with self.app.app_context():
        #            args = {
        #                'email' : 'test@somedomain.zz',
        #                'password' : 'TestPassword123'
        #            }
        #            result = self.test_client.post('/account/create/', data = args)
        #
        #            alien_user = AuthUser()
        #            alien_user.email = u'asdfasdfasdf'
        #            alien_user.password = u'asdfasdfasdfasdf'
        #            alien_user.signup_date = datetime.utcnow()
        #            alien_user.insert(current_app.db)
        #
        #            self.assertEqual(result.status_code, 200)
        #            user_activation_link = UserActivationLink.query.first()
        #            self.assertIsNotNone(user_activation_link)
        #            user_activation_link.auth_user_id = alien_user.id
        #            user_activation_link.save(current_app.db)
        #
        #            user = AuthUser.query.first()
        #            self.assertIsNotNone(user)
        #            self.assertFalse(user.enabled)
        #
        #            args = {
        #                'user_id' : user.id,
        #                'type' : 'email',
        #                'code' : user_activation_link.link_code
        #            }
        #            result = self.test_client.post('/account/confirm/', data = args)
        #
        #            self.assertEqual(result.status_code, 200)
        #            data = json.loads(result.data)
        #            self.assertIsNotNone(data)
        #            self.assertIn('error', data)
        #            error = data['error']
        #            self.assertIn('code', error)
        #            self.assertEqual(error['code'], ActivationCodeExpiredOrInvalid.ERROR_CODE)
        #
        #    def test_activation_retries_count_exceeded(self):
        #        with self.app.app_context():
        #            args = {
        #                'email' : 'test@somedomain.zz',
        #                'password' : 'TestPassword123'
        #            }
        #            result = self.test_client.post('/account/create/', data = args)
        #
        #            self.assertEqual(result.status_code, 200)
        #            user_activation_link = UserActivationLink.query.first()
        #            correct_code = user_activation_link.link_code
        #            self.assertIsNotNone(user_activation_link)
        #
        #            user = AuthUser.query.first()
        #            self.assertIsNotNone(user)
        #            self.assertFalse(user.enabled)
        #
        #            args = {
        #                'user_id' : user.id,
        #                'type' : 'email',
        #                'code' : 'A' * self.config['max_activation_link_length']
        #            }
        #            for _ in xrange(self.config['max_activation_attempts_count']):
        #                result = self.test_client.post('/account/confirm/', data = args)
        #
        #                self.assertEqual(result.status_code, 200)
        #                data = json.loads(result.data)
        #                self.assertIsNotNone(data)
        #                self.assertIn('error', data)
        #                error = data['error']
        #                self.assertIn('code', error)
        #                self.assertEqual(error['code'], ActivationCodeExpiredOrInvalid.ERROR_CODE)
        #
        #            result = self.test_client.post('/account/confirm/', data = args)
        #            self.assertEqual(result.status_code, 200)
        #            data = json.loads(result.data)
        #            self.assertIsNotNone(data)
        #            self.assertIn('error', data)
        #            error = data['error']
        #            self.assertIn('code', error)
        #            self.assertEqual(error['code'], ActivationAttemptsCountExceeded.ERROR_CODE)
        #
        #            args = {
        #                'user_id' : user.id,
        #                'type' : 'email',
        #                'code' : correct_code
        #            }
        #            result = self.test_client.post('/account/confirm/', data = args)
        #
        #            self.assertEqual(result.status_code, 200)
        #            data = json.loads(result.data)
        #            self.assertIsNotNone(data)
        #            self.assertIn('error', data)
        #            error = data['error']
        #            self.assertIn('code', error)
        #            self.assertEqual(error['code'], ActivationAttemptsCountExceeded.ERROR_CODE)

    def test_request_new_activation_code(self):
        with self.app.app_context():
            args = {
                'email': 'test@somedomain.zz',
                'password': 'TestPassword123'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 200)
            user_activation_link = UserActivationLink.query.first()
            self.assertIsNotNone(user_activation_link)
            old_code = user_activation_link.link_code
            old_code_id = user_activation_link.id

            user = AuthUser.query.first()
            self.assertIsNotNone(user)
            self.assertTrue(user.enabled)

            args = {
                'email': 'test@somedomain.zz'
            }
            result = self.test_client.post('/account/send_activation_code/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            self.assertTrue(data['result'])

            user_activation_link = UserActivationLink.query.first()
            self.assertIsNotNone(user_activation_link)
            self.assertNotEqual(old_code, user_activation_link.link_code)
            self.assertNotEqual(old_code_id, user_activation_link.id)

            self.assertEqual(user_activation_link.auth_user_id, user.id)
            self.assertEqual(len(user_activation_link.link_code), self.config['max_activation_link_length'])
            self.assertTrue(user_activation_link.link_code.isalnum())
            self.assertLess((datetime.utcnow() - user_activation_link.creation_date).total_seconds(), 10)
            self.assertIsNone(user_activation_link.used_date)

            old_code = user_activation_link.link_code
            old_code_id = user_activation_link.id

            user = AuthUser.query.first()
            self.assertIsNotNone(user)
            self.assertTrue(user.enabled)

            result = self.test_client.post('/account/send_activation_code/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            self.assertTrue(data['result'])

            self.assertEqual(UserActivationLink.query.count(), 1)
            user_activation_link = UserActivationLink.query.first()
            self.assertIsNotNone(user_activation_link)
            self.assertNotEqual(old_code, user_activation_link.link_code)
            self.assertNotEqual(old_code_id, user_activation_link.id)

            self.assertEqual(user_activation_link.auth_user_id, user.id)
            self.assertEqual(len(user_activation_link.link_code), self.config['max_activation_link_length'])
            self.assertTrue(user_activation_link.link_code.isalnum())
            self.assertLess((datetime.utcnow() - user_activation_link.creation_date).total_seconds(), 10)
            self.assertIsNone(user_activation_link.used_date)

    def test_request_new_activation_code_mobile(self):
        with self.app.app_context():
            args = {
                'email': 'test@somedomain.zz',
                'password': 'TestPassword123'
            }
            result = self.test_client.post('/account/create/', data=args)

            self.assertEqual(result.status_code, 200)
            user_activation_link = UserActivationLink.query.first()
            self.assertIsNotNone(user_activation_link)
            old_code = user_activation_link.link_code
            old_code_id = user_activation_link.id
            UserActivationLink.query.filter_by(id=user_activation_link.id).delete()

            user = AuthUser.query.first()
            new_link = self._make_ua_link(use_chars=False, new_mobile="+78881112233", user_id=user.id,
                                          link_type=ConfirmationLinkTypeEnum.CLT_MOBILE)
            sqldb.session.add(new_link)
            sqldb.session.commit()

            user = AuthUser.query.first()
            self.assertIsNotNone(user)
            self.assertTrue(user.enabled)

            args = {
                'mobile': '+78881112233'
            }
            result = self.test_client.post('/account/send_activation_code/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            self.assertTrue(data['result'])

            user_activation_link = UserActivationLink.query.first()
            self.assertIsNotNone(user_activation_link)
            self.assertNotEqual(old_code, user_activation_link.link_code)
            self.assertNotEqual(old_code_id, user_activation_link.id)

            self.assertEqual(user_activation_link.auth_user_id, user.id)
            self.assertEqual(len(user_activation_link.link_code), self.config['digital_activation_link_length'])
            self.assertTrue(user_activation_link.link_code.isalnum())
            self.assertLess((datetime.utcnow() - user_activation_link.creation_date).total_seconds(), 10)
            self.assertIsNone(user_activation_link.used_date)

            old_code = user_activation_link.link_code
            old_code_id = user_activation_link.id

            self.assertIsNotNone(user)
            self.assertTrue(user.enabled)

            result = self.test_client.post('/account/send_activation_code/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            self.assertTrue(data['result'])

            self.assertEqual(UserActivationLink.query.count(), 1)
            user_activation_link = UserActivationLink.query.first()
            self.assertIsNotNone(user_activation_link)
            self.assertNotEqual(old_code, user_activation_link.link_code)
            self.assertNotEqual(old_code_id, user_activation_link.id)

            self.assertEqual(user_activation_link.auth_user_id, user.id)
            self.assertEqual(len(user_activation_link.link_code), self.config['digital_activation_link_length'])
            self.assertTrue(user_activation_link.link_code.isalnum())
            self.assertLess((datetime.utcnow() - user_activation_link.creation_date).total_seconds(), 10)
            self.assertIsNone(user_activation_link.used_date)

    @authorized(is_temporal=True)
    def test_update_profile_for_temporary_user(self):
        with self.app.app_context():
            self.assertEqual(len(self.mailer.mails), 0)
            user = AuthUser.query.filter_by(id=self.user.id).first()
            self.assertEqual(user.email, None)
            new_email = 'newemail@somedomain.zz'
            params = {
                'email': new_email
            }
            result = self.test_client.post('/account/profile/update/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            user_obj = data['result']

            user = AuthUser.query.filter_by(id=self.user.id).first()
            self.assertEqual(user_obj['email'], user.email)
            self.assertEqual(user_obj['email'], new_email)
            self.assertEqual(user.email_confirmed, False)
            self.assertIsNotNone(user.password)
            self.assertNotEqual(user.password, None)

            self.assertEqual(len(self.mailer.mails), 2)

            mail1 = self.mailer.mails[0]
            self.assertEqual(mail1['message']['subject'], u'Регистрация на ЮРБЮРО')

            mail2 = self.mailer.mails[1]
            self.assertEqual(mail2['message']['subject'], u'Подтвердите почтовый адрес в «ЮРБЮРО»')

            self.assertEqual(user.temporal, False)
            self.assertEqual(user.id, self.user.id)

    @authorized()
    def test_update_email(self):
        with self.app.app_context():
            self.assertEqual(len(self.mailer.mails), 0)
            user = AuthUser.query.filter_by(id=self.user.id).first()
            self.assertEqual(user.email, 'test@somedomain.zz')
            new_email = 'newemail@somedomain.zz'
            params = {
                'email': new_email
            }
            result = self.test_client.post('/account/profile/update/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            user_obj = data['result']

            user = AuthUser.query.filter_by(id=self.user.id).first()
            self.assertEqual(user_obj['email'], user.email)
            self.assertEqual(user_obj['email'], new_email)
            self.assertEqual(user.email_confirmed, False)

            self.assertEqual(len(self.mailer.mails), 1)

    @authorized()
    def test_update_mobile(self):
        with self.app.app_context():
            self.assertEqual(len(self.sms_sender.sms), 0)
            user = AuthUser.query.filter_by(id=self.user.id).first()
            self.assertEqual(user.mobile, '+79001112233')
            new_mobile = '+79003332211'
            params = {
                'mobile': new_mobile
            }
            result = self.test_client.post('/account/profile/update/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            user_obj = data['result']

            user = AuthUser.query.filter_by(id=self.user.id).first()
            self.assertEqual(user_obj['mobile'], user.mobile)
            self.assertEqual(user_obj['mobile'], new_mobile)
            self.assertEqual(user.mobile_confirmed, False)

            self.assertEqual(len(self.sms_sender.sms), 1)

    @authorized()
    def test_update_email_several_times(self):
        with self.app.app_context():
            self.assertEqual(len(self.mailer.mails), 0)
            user = AuthUser.query.filter_by(id=self.user.id).first()
            self.assertEqual(user.email, 'test@somedomain.zz')
            new_email = 'newemail@somedomain.zz'
            params = {
                'email': new_email
            }
            result = self.test_client.post('/account/profile/update/', data=params)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            user_obj = data['result']

            user = AuthUser.query.filter_by(id=self.user.id).first()
            self.assertEqual(user_obj['email'], user.email)
            self.assertEqual(user_obj['email'], new_email)
            self.assertEqual(user.email_confirmed, False)

            self.assertEqual(len(self.mailer.mails), 1)
            self.assertEqual(
                UserActivationLink.query.filter_by(link_type=ConfirmationLinkTypeEnum.CLT_EMAIL).count(), 1)

            params = {
                'email': 'newemail2@somedomain.zz'
            }
            result = self.test_client.post('/account/profile/update/', data=params)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)

            self.assertEqual(
                UserActivationLink.query.filter_by(link_type=ConfirmationLinkTypeEnum.CLT_EMAIL).count(), 1)
            email_confirmation_link = UserActivationLink.query.filter_by(link_type=ConfirmationLinkTypeEnum.CLT_EMAIL).first()

            self.assertIsNotNone(email_confirmation_link)

            self.assertEqual(email_confirmation_link.new_mobile, None)
            self.assertEqual(email_confirmation_link.new_email, 'newemail2@somedomain.zz')
            self.assertEqual(email_confirmation_link.use_attempts, 0)
            self.assertEqual(email_confirmation_link.used_date, None)

            self.assertEqual(len(self.mailer.mails), 2)

    @authorized()
    def test_get_profile(self):
        with self.app.app_context():
            result = self.test_client.get('/account/profile/')

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)
            user_obj = data['result']

            user = AuthUser.query.filter_by(id=self.user.id).first()

            self.assertIn('id', user_obj)
            self.assertIn('email', user_obj)
            self.assertIn('registration_date', user_obj)

            self.assertEqual(user_obj['email'], u'' if not user.email else user.email)

    @registered_user()
    def test_request_password_recovery_email(self):
        with self.app.app_context():
            self.assertEqual(len(self.mailer.mails), 0)
            params = {
                'email': 'test@somedomain.zz'
            }
            result = self.test_client.post('/account/password_recovery/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)

            password_change_link = UserActivationLink.query.filter_by(
                auth_user_id=self.user.id,
                link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD,
                used_date=None)
            self.assertIsNotNone(password_change_link)
            self.assertEqual(len(self.mailer.mails), 1)

    @registered_user()
    def test_request_password_recovery_mobile(self):
        with self.app.app_context():
            self.assertEqual(len(self.sms_sender.sms), 0)
            params = {
                'mobile': '+79001112233'
            }
            result = self.test_client.post('/account/password_recovery/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)

            password_change_link = UserActivationLink.query.filter_by(
                auth_user_id=self.user.id,
                link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD,
                used_date=None).first()
            self.assertIsNotNone(password_change_link)
            self.assertEqual(len(self.sms_sender.sms), 1)

    @registered_user()
    def test_request_password_recovery_max_attempts(self):
        with self.app.app_context():
            self.assertEqual(len(self.mailer.mails), 0)
            params = {
                'email': 'test@somedomain.zz'
            }
            # first two attempts will pass
            for i in xrange(2):
                result = self.test_client.post('/account/password_recovery/', data=params)
                self.assertEqual(result.status_code, 200)
                data = json.loads(result.data)
                self.assertIsNotNone(data)
                self.assertIn('result', data)
                # the fird one will fail
            result = self.test_client.post('/account/password_recovery/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)

            password_change_link = UserActivationLink.query.filter_by(
                auth_user_id=self.user.id,
                link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD,
                used_date=None).first()
            # FF 2 days
            self.user.last_password_drop_attempts_date = datetime.utcnow() - timedelta(2)

            # now it should be ok
            result = self.test_client.post('/account/password_recovery/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)

    def test_request_password_recovery_invalid_email(self):
        with self.app.app_context():
            self.assertEqual(len(self.mailer.mails), 0)
            params = {
                'email': 'test@somedomain.zz'
            }
            result = self.test_client.post('/account/password_recovery/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            self.assertEqual(data['error']['code'], 105)

            password_change_link = UserActivationLink.query.filter_by(
                link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD,
                used_date=None).first()
            self.assertIsNone(password_change_link)
            self.assertEqual(len(self.mailer.mails), 0)

    @registered_user()
    def test_recover_password(self):
        with self.app.app_context():
            recovery_link = self._make_ua_link(use_chars=True, user_id=self.user.id, link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD)
            sqldb.session.add(recovery_link)

            params = {
                'user_id': self.user.uuid,
                'code': recovery_link.link_code,
                'new_password': 'New_password2'
            }
            result = self.test_client.post('/account/password_change/', data=params)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)

            recovery_link = UserActivationLink.query.filter_by(id=recovery_link.id).first()
            self.assertIsNotNone(recovery_link)
            self.assertIsNotNone(recovery_link.used_date)

            args = {'email': 'test@somedomain.zz',
                    'password': 'New_password2'}

            result = self.test_client.post('/account/login/', data=args)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)

    @authorized()
    def test_recover_password_logged_in(self):
        with self.app.app_context():
            recovery_link = self._make_ua_link(use_chars=True, user_id=self.user.id, link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD)
            sqldb.session.add(recovery_link)

            params = {
                'user_id': self.user.uuid,
                'code': recovery_link.link_code,
                'new_password': 'New_password2'
            }
            result = self.test_client.post('/account/password_change/', data=params)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertNotIn('error', data)

    @registered_user()
    def test_set_new_password(self):
        params = {
            'user_id': self.user.uuid,
            'old_password': 'TestPassword123',
            'new_password': 'New_password2'
        }
        result = self.test_client.post('/account/password_change/', data=params)
        self.assertEqual(result.status_code, 200, str(result.data))
        data = json.loads(result.data)
        self.assertIsNotNone(data)
        self.assertIn('result', data)

        args = {'email': 'test@somedomain.zz',
                'password': 'New_password2',
                'client': 'android'}

        result = self.test_client.post('/account/login/', data=args)

        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertIsNotNone(data)
        self.assertIn('result', data)

    @registered_user()
    def test_set_new_password_with_email(self):
        with self.app.app_context():
            params = {
                'email': self.user.email,
                'old_password': 'TestPassword123',
                'new_password': 'New_password2'
            }
            result = self.test_client.post('/account/password_change/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)

            args = {'email': self.user.email,
                    'password': 'New_password2',
                    'client': 'android'}

            result = self.test_client.post('/account/login/', data=args)

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('result', data)

    @registered_user()
    def test_set_new_password_invalid_old(self):
        with self.app.app_context():
            params = {
                'user_id': self.user.uuid,
                'old_password': 'TestPassword1234',
                'new_password': 'New_password2'
            }
            result = self.test_client.post('/account/password_change/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            self.assertEqual(data['error']['code'], errors.InvalidCurrentPassword.ERROR_CODE)

    @registered_user()
    def test_set_new_password_invalid_user_id(self):
        with self.app.app_context():
            params = {
                'user_id': str(ObjectId()),
                'old_password': 'TestPassword123',
                'new_password': 'New_password2'
            }
            result = self.test_client.post('/account/password_change/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            self.assertEqual(data['error']['code'], UserNotFound.ERROR_CODE)

    @registered_user()
    def test_set_new_password_unauthorized(self):
        with self.app.app_context():
            params = {
                'user_id': str(ObjectId()),
                'old_password': 'TestPassword123',
                'new_password': 'New_password2'
            }
            result = self.test_client.post('/account/password_change/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            self.assertEqual(data['error']['code'], UserNotFound.ERROR_CODE)

    @registered_user()
    def test_set_new_password_invalid_code(self):
        with self.app.app_context():
            recovery_link = self._make_ua_link(use_chars=True, user_id=self.user.id, link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD)
            sqldb.session.add(recovery_link)

            params = {
                'user_id': self.user.uuid,
                'code': u'u' * self.config['max_activation_link_length'],
                'new_password': 'New_password2'
            }
            result = self.test_client.post('/account/password_change/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            self.assertEqual(data['error']['code'], ActivationCodeExpiredOrInvalid.ERROR_CODE)

    @registered_user()
    def test_set_new_password_invalid_code_max_retries(self):
        with self.app.app_context():
            recovery_link = self._make_ua_link(use_chars=True, user_id=self.user.id, link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD)
            sqldb.session.add(recovery_link)

            valid_code = recovery_link.link_code

            params = {
                'user_id': self.user.uuid,
                'code': u'u' * self.config['max_activation_link_length'],
                'new_password': 'New_password2'
            }
            for i in xrange(5):
                result = self.test_client.post('/account/password_change/', data=params)
                self.assertEqual(result.status_code, 200)
                data = json.loads(result.data)
                self.assertIsNotNone(data)
                self.assertIn('error', data)
                self.assertEqual(data['error']['code'], ActivationCodeExpiredOrInvalid.ERROR_CODE)
                # now try valid code
            params = {
                'user_id': self.user.uuid,
                'code': valid_code,
                'new_password': 'New_password2'
            }
            result = self.test_client.post('/account/password_change/', data=params)
            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            self.assertEqual(data['error']['code'], ActivationCodeExpiredOrInvalid.ERROR_CODE)

    @registered_user()
    def _test_get_user_data_for_password_recovery_request_handler(self):
        recovery_link = self._make_ua_link(use_chars=True, user_id=self.user.id, link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD)
        sqldb.session.add(recovery_link)

        result = self.test_client.get('/account/by/code/?user_id=%s&code=%s' % (self.user.id, recovery_link.link_code))
        self.assertEqual(result.status_code, 200)

        data = json.loads(result.data)
        self.assertIsNotNone(data)
        self.assertIn('result', data)
        user_json = data['result']
        self.assertEqual(ObjectId(user_json['id']), self.user.uuid)

    @registered_user()
    def test_get_user_data_for_password_recovery_request_handler_invalid_code(self):
        with self.app.app_context():
            recovery_link = self._make_ua_link(use_chars=True, user_id=self.user.id, link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD)
            sqldb.session.add(recovery_link)

            result = self.test_client.get('/account/by/code/?user_id=%s&code=invalid' % self.user.id)

            self.assertEqual(result.status_code, 400)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            error_json = data['error']
            self.assertEqual(error_json['code'], 5)

    @registered_user()
    def test_get_user_data_for_password_recovery_request_handler_invalid_user_and_code(self):
        with self.app.app_context():
            recovery_link = self._make_ua_link(use_chars=True, user_id=self.user.id, link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD)
            sqldb.session.add(recovery_link)

            result = self.test_client.get('/account/by/code/?user_id=%s&code=1234' % ObjectId())

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            error_json = data['error']
            self.assertEqual(error_json['code'], 108)

    @registered_user()
    def test_get_user_data_for_password_recovery_request_handler_invalid_user(self):
        with self.app.app_context():
            recovery_link = self._make_ua_link(use_chars=True, user_id=self.user.id, link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD)
            sqldb.session.add(recovery_link)

            result = self.test_client.get(
                '/account/by/code/?user_id=%s&code=%s' % (ObjectId(), recovery_link.link_code))

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            error_json = data['error']
            self.assertEqual(error_json['code'], 108)

    @registered_user()
    def test_get_user_data_for_password_recovery_request_handler_used_code(self):
        with self.app.app_context():
            recovery_link = self._make_ua_link(use_chars=True, user_id=self.user.id, link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD)
            recovery_link.used_date = datetime.now()
            sqldb.session.add(recovery_link)

            result = self.test_client.get(
                '/account/by/code/?user_id=%s&code=%s' % (self.user.id, recovery_link.link_code))

            self.assertEqual(result.status_code, 200)
            data = json.loads(result.data)
            self.assertIsNotNone(data)
            self.assertIn('error', data)
            error_json = data['error']
            self.assertEqual(error_json['code'], 108)

    @authorized(is_temporal=True)
    def test_keep_account_data_after_login_temporary_user(self):

        data = {
            'name': u"Нейм",
            'surname': u"Сёрнейм",
            'inn': "781108730780",
            'phone': "+79110010203",
            'email': "test@test.email",
            '_owner': self.user
        }
        person = PrivatePersonDbObject(**data)
        sqldb.session.add(person)
        sqldb.session.commit()

        new_company = CompanyDbObject(**dict({
            "_owner": self.user,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "full_name": u"Протон",
            "short_name": u"Про",
            "kpp": "999999999",
            "company_type": CompanyTypeEnum.CT_RUSSIAN,
            "general_manager": {
                '_id': person.id,
                'type': 'person'
            }
        }))

        sqldb.session.add(new_company)
        sqldb.session.commit()
        new_company_id = new_company.id

        data = {
            u"full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
            u"doc_date": datetime.now(),
            u"address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 123131,
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Седова",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "2",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "2",
                "ifns": 1234
            },
            u"selected_secretary": {
                "type": "company",
                "_id": new_company.id
            },
        }
        new_batch_db_object = DocumentBatchDbObject(batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user)
        sqldb.session.add(new_batch_db_object)

        new_doc = BatchDocumentDbObject(
            _owner = self.user,
            document_type = DocumentTypeEnum.DT_GARANT_LETTER_SUBARENDA,
            batch = new_batch_db_object,
            data = data,
            caption = "Caption"
        )
        sqldb.session.add(new_doc)
        sqldb.session.commit()

        new_booking = IfnsBooking.db_model(batch_id=new_batch_db_object.id,
                                           service_id=IfnsServiceEnum.IS_REG_COMPANY,
                                           id=ObjectId())
        new_booking_id = new_booking.insert(self.db)

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
        sqldb.session.add(test_notarius)
        sqldb.session.commit()

        notarius_booking = NotariusBookingObject(batch=new_batch_db_object,
                                                 owner=self.user,
                                                 notarius=test_notarius,
                                                 dt=datetime.now(),
                                                 address="here")
        sqldb.session.add(notarius_booking)
        sqldb.session.commit()
        notarius_booking_id = notarius_booking.id

        ybc = YuristBatchCheck.db_model(batch_id=new_batch_db_object.id,
                                        create_date=datetime.now(),
                                        typos_correction=False,
                                        status=YuristBatchCheckStatus.YBS_NEW)

        ybc_id = ybc.insert(self.db)

        args = {
            'name': u'Станислав',
            'email': 'test@somedomain.zz',
            'password': 'TestPassword123'
        }
        result = self.test_client.post('/account/create/', data=args)

        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertIsNotNone(data)
        self.assertIn('result', data)
        uid = data['result']['id']
        self.assertEqual(data['result']['email'], 'test@somedomain.zz')
        user = AuthUser.query.filter_by(uuid=uid).first()
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user.id)

        # profile = UserProfile.find_one(current_app.db, {'auth_user_id': ObjectId(uid)})
        # self.assertEqual(profile._id, self.user_profile._id)

        self.assertEqual(AuthUser.query.count(), 1)

        ifns_booking = IfnsBooking.db_model.find_one(self.db, {'_id': new_booking_id})
        self.assertEqual(ifns_booking.batch_id, new_batch_db_object.id)

        notarius_booking = NotariusBookingObject.query.filter_by(
            id=notarius_booking_id
        ).scalar()
        self.assertEqual(notarius_booking.owner_id, self.user.id)

        ybc = YuristBatchCheck.db_model.find_one(self.db, {'_id': ybc_id})
        self.assertEqual(ybc.batch_id, new_batch_db_object.id)

        batch = DocumentBatchDbObject.query.filter_by(id=new_batch_db_object.id).first()
        self.assertEqual(batch._owner_id, self.user.id)

        company = CompanyDbObject.query.filter_by(id=new_company_id).first()
        self.assertEqual(company._owner_id, self.user.id)
        self.assertEqual(company.general_manager['_id'], person.id)

        person = PrivatePersonDbObject.query.filter_by(id=person.id).first()
        self.assertEqual(person._owner_id, self.user.id)

    @authorized(is_temporal=True)
    def test_merge_account_data_after_login_temporary_user(self):
        new_user = AuthUser(password=encrypt_password('TestPassword123'),
                            email='test@somedomain.zz',
                            enabled=True,
                            email_confirmed=True,
                            mobile="+79001112233",
                            mobile_confirmed=True)
        sqldb.session.add(new_user)

        data = {
            'name': u"Нейм",
            'surname': u"Сёрнейм",
            'inn': "781108730780",
            'phone': "+79110010203",
            'email': "test@test.email",
            '_owner': self.user
        }
        person = PrivatePersonDbObject(**data)
        sqldb.session.add(person)
        sqldb.session.commit()
        person_id = person.id

        new_company = CompanyDbObject(**dict({
            "_owner": self.user,
            "ogrn": "1234567890123",
            "inn": "781108730780",
            "full_name": u"Протон",
            "short_name": u"Про",
            "kpp": "999999999",
            "company_type": CompanyTypeEnum.CT_RUSSIAN,
            "general_manager": {
                '_id': person.id,
                'type': 'person'
            }
        }))

        sqldb.session.add(new_company)
        sqldb.session.commit()
        new_company_id = new_company.id

        data = {
            u"full_name": u"образовательное учреждение дополнительного образования детей специализированная детско-юношеская спортивная школа олимпийского резерва по боксу",
            u"doc_date": datetime.now(),
            u"address": {
                "region": RFRegionsEnum.RFR_SPB,
                "index": 123131,
                "street_type": StreetTypeEnum.STT_STREET,
                "street": u"Седова",
                "house_type": HouseTypeEnum.HOT_HOUSE,
                "house": "2",
                "flat_type": FlatTypeEnum.FLT_OFFICE,
                "flat": "2",
                "ifns": 1234
            },
            u"selected_secretary": {
                "type": "company",
                "_id": new_company_id
            },
        }
        new_batch_db_object = DocumentBatchDbObject(batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
                                                    status=BatchStatusEnum.BS_NEW, _owner=self.user)
        sqldb.session.add(new_batch_db_object)

        new_doc = BatchDocumentDbObject(
            _owner = self.user,
            document_type = DocumentTypeEnum.DT_GARANT_LETTER_SUBARENDA,
            batch = new_batch_db_object,
            data = data,
            caption = "Caption"
        )
        sqldb.session.add(new_doc)

        sqldb.session.commit()

        new_booking = IfnsBooking.db_model(batch_id=new_batch_db_object.id,
                                           service_id=IfnsServiceEnum.IS_REG_COMPANY,
                                           id=ObjectId())
        new_booking_id = new_booking.insert(self.db)

        notarius_booking = NotariusBooking.db_model(batch_id=new_batch_db_object.id,
                                                    _owner=self.user.id,
                                                    notarius_id=ObjectId(),
                                                    dt=datetime.now(),
                                                    address="here")
        notarius_booking_id = notarius_booking.insert(self.db)

        ybc = YuristBatchCheck.db_model(batch_id=new_batch_db_object.id,
                                        create_date=datetime.now(),
                                        typos_correction=False,
                                        status=YuristBatchCheckStatus.YBS_NEW)

        ybc_id = ybc.insert(self.db)

        rsa_sid = self.test_client.cookie_jar._cookies['localhost.local']['/']['rsa_sid']
        print(rsa_sid.value)
        val = Session.query.get(rsa_sid.value)
        print(pickle.loads(val.data))

        args = {
            'email': 'test@somedomain.zz',
            'password': 'TestPassword123'
        }
        #rsa_sid.value = "ybf19fa423c0ed51cbc4c74c0b6564f92d"
        result = self.test_client.post('/account/login/', data=args)

        rsa_sid = self.test_client.cookie_jar._cookies['localhost.local']['/']['rsa_sid']
        print(rsa_sid)
        val = Session.query.get(rsa_sid.value)
        print(pickle.loads(val.data))

        result = self.test_client.post('/account/login/temporal/')
        self.assertEqual(result.status_code, 200)

        print(rsa_sid)
        val = Session.query.get(rsa_sid.value)
        print(pickle.loads(val.data))

        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertIsNotNone(data)

        self.assertEqual(AuthUser.query.count(), 1)

        ifns_booking = IfnsBooking.db_model.find_one(self.db, {'_id': new_booking_id})
        self.assertEqual(ifns_booking.batch_id, new_batch_db_object.id)

        notarius_booking = NotariusBooking.db_model.find_one(self.db, {'_id': notarius_booking_id})
        self.assertEqual(notarius_booking._owner, new_user.id)

        ybc = YuristBatchCheck.db_model.find_one(self.db, {'_id': ybc_id})
        self.assertEqual(ybc.batch_id, new_batch_db_object.id)

        batch = DocumentBatchDbObject.query.filter_by(id=new_batch_db_object.id).first()
        self.assertEqual(batch._owner_id, new_user.id)

        company = CompanyDbObject.query.filter_by(id=new_company_id).first()
        self.assertEqual(company._owner_id, new_user.id)
        self.assertEqual(company.general_manager['_id'], person.id)

        person = PrivatePersonDbObject.query.filter_by(id=person_id).first()
        self.assertEqual(person._owner_id, new_user.id)

    @registered_user()
    def test_create_authorization_url(self):
        auth_url_object = UserManager.make_auth_url(
            url="http://test/url",
            owner=self.user,
            expiration_td=timedelta(seconds=3600 * 24 * 7),
        )
        self.assertEqual(AuthorizationUrl.query.count(), 1)
        self.assertEqual(auth_url_object.url, 'http://test/url')
        self.assertLessEqual((datetime.now() - auth_url_object.created).total_seconds(), 1)
        exp = auth_url_object.created + timedelta(seconds=3600 * 24 * 7)
        self.assertLessEqual((exp - auth_url_object.expire_at).total_seconds(), 1)
        self.assertEqual(auth_url_object.used_times, 0)
        self.assertEqual(auth_url_object.owner_id, self.user.id)

    @registered_user()
    def test_authorize_through_url(self):
        auth_url_object = UserManager.make_auth_url(
            url="http://test/url",
            owner=self.user,
            expiration_td=timedelta(seconds=3600 * 24 * 7)
        )

        response = self.test_client.get(auth_url_object.get_url(self.config))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], "http://test/url")
        self.assertIn('rsa_sid', response.headers['Set-Cookie'])

        self.assertEqual(auth_url_object.used_times, 1)

    @registered_user()
    def test_authorize_through_expired_url(self):
        auth_url_object = UserManager.make_auth_url(
            url="http://test/url",
            owner=self.user,
            expiration_td=timedelta(seconds=1)
        )

        auth_url_object.expire_at = datetime.utcnow() - timedelta(days=1)
        sqldb.session.commit()

        response = self.test_client.get(auth_url_object.get_url(self.config))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('Set-Cookie', response.headers)

        self.assertEqual(auth_url_object.used_times, 1)

    @registered_user()
    def test_authorize_through_url_several_times(self):
        auth_url_object = UserManager.make_auth_url(
            url="http://test/url",
            owner=self.user,
            expiration_td=timedelta(seconds=3600 * 24 * 7)
        )

        response = self.test_client.get(auth_url_object.get_url(self.config))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], "http://test/url")
        self.assertIn('rsa_sid', response.headers['Set-Cookie'])

        self.assertEqual(auth_url_object.used_times, 1)

        response = self.test_client.get(auth_url_object.get_url(self.config))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], "http://test/url")
        self.assertIn('rsa_sid', response.headers['Set-Cookie'])

        self.assertEqual(auth_url_object.used_times, 2)

        response = self.test_client.get(auth_url_object.get_url(self.config))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], "http://test/url")
        self.assertIn('rsa_sid', response.headers['Set-Cookie'])

        self.assertEqual(auth_url_object.used_times, 3)

    @registered_user()
    def test_authorize_through_missing_url(self):
        auth_url_object = UserManager.make_auth_url(
            url="http://test/url",
            owner=self.user,
            expiration_td=timedelta(seconds=1)
        )

        auth_url_object.expire_at = datetime.utcnow() - timedelta(days=1)
        sqldb.session.commit()

        url = auth_url_object.get_url(self.config)
        AuthorizationUrl.query.filter_by(id=auth_url_object.id).delete()
        sqldb.session.commit()
        response = self.test_client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertNotIn('Set-Cookie', response.headers)

    @authorized()
    def test_authorize_through_url_while_authorized(self):
        auth_url_object = UserManager.make_auth_url(
            url="http://test/url",
            owner=self.user,
            expiration_td=timedelta(seconds=3600 * 24 * 7)
        )

        response = self.test_client.get(auth_url_object.get_url(self.config))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers['Location'], "http://test/url")
        self.assertIn('rsa_sid', response.headers['Set-Cookie'])

        self.assertEqual(auth_url_object.used_times, 1)

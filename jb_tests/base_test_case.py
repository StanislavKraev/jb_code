# -*- coding: utf-8 -*-
import logging
import os

from flask import json, _request_ctx_stack
from fw.api import errors
from fw.auth.encrypt import encrypt_password
from fw.auth.models import AuthUser
from fw.auth.user_manager import UserManager
from fw.db.sql_base import db as sql_db

os.environ['CELERY_CONFIG_MODULE'] = 'local_celery_config'


CURRENT_DIR = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))

TEST_CONFIG = {
    'DEBUG': True,
    'TEST': True,
    "PDF_BUILDER_PATH": os.path.normpath(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), '../app/pdf-builder.jar')),
    "PDFTK_PATH": os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../app/pdftk')),
    "SECRET_KEY": "secret_test",
    "SESSION_COOKIE_NAME": "rsa_sid",
    "PERMANENT_SESSION_LIFETIME": 86400,
    "DOMAIN": "jur-bureau.org",
    'max_activation_link_length': 20,
    'digital_activation_link_length': 4,
    'digital_activation_code_timeout': 900,
    'email_activation_code_timeout': 86400,
    'max_activation_attempts_count': 3,
    'site_domain': 'legalcloud.ru',
    'resources_path': os.path.join(CURRENT_DIR, 'test_data'),
    'db_host': '127.0.0.1',
    'db_name': 'test_db',
    'WEB_SCHEMA': '',
    'DOCUMENT_STORAGE': '/tmp/jb_docs/',
    'STORAGE_URL': 'http://service.zz/storage/',
    'PRIVATE_STORAGE': '/tmp/jb_docs/',
    'bind_addr': '/tmp/tmp.tmp',
    'UPLOAD_FOLDER': '/tmp',
    'YURIST_EMAIL_LIST': ['rocsatest@gmail.com'],
    'NOTARIUS_EMAIL_LIST': ['rocsatest@gmail.com'],
    'mailer_reply_to': u'Юрбюро Онлайн <rocsatest@gmail.com>',
    'log_file_path': '/tmp/tmp.log',
    'LOG_LEVEL': 'DEBUG',
    'api_url': 'legalcloud.ru/api',
    'pdf_preview_watermark': os.path.normpath(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_data/preview_watermark.png')),
    'PDF_STAMPER_PATH': os.path.normpath(
        os.path.join(os.path.abspath(os.path.dirname(__file__)), '../app/pdf-stamper.jar')),
    'celery_tasks_dir': '/tmp/',
    'service_name': u"ЮРБЮРО",
    'sms_gate_address': 'address',
    'sms_gate_user': 'user',
    'sms_gate_password': 'password',
    'sms_gate_sender': 'YURBURO',
    'mailer_smtp_user': 'user',
    'vk_api_version': '5.2',
    'vk_app_id': 4629685,
    'vk_app_permissions': 2 + 4194304,  # 73730,
    'vk_auth_redirect_url': '/account/login/external/vk/',
    'vk_test_token': '868218ba11994a0a334257b0e07acc45f0333fe77700d5e395d723feefd1b4188a5d77700d48b63a5c9c7',
    'facebook_app_secret': '73535b9a524f23dc3e3efe4a576a3807',
    'facebook_app_permissions': 'publish_stream,email,publish_actions',
    'facebook_app_id': 673204526111410,
    'facebook_auth_redirect_url': '/account/login/external/facebook/',
    'SERVICE_NALOG_RU_URL': 'https://service.nalog.ru/',
    'be_quiet': True,
    'STAGING': False,
    'ADMIN_EMAIL_LIST': ['test@test.test'],
    'YAD_ESHOP_PASSWORD': '1234567890',
    'YAD_IP_LIST': [],
    'MAX_CONTENT_LENGTH': 1024000,
    'OFFICE_IP': ['1.0.0.0'],
    'NOT_PAID_BATCH_NOTIFY_TIMEOUT_SECONDS': 86400,
    'NOT_PAID_BATCH_NOTIFY_DESIRED_TIME': '08:30',
    'SEND_DOCS_TO_YURIST_DELAY_SECONDS': 0,
    'user_by_code_tries_count': 5,
    'SQLALCHEMY_DATABASE_URI': 'postgres://postgres:postgres@localhost/test_db',
    'RUSSIAN_POST_API_LOGIN': 'test',
    'RUSSIAN_POST_API_PASSWORD': 'test',
    'CELERY_LOG_LEVEL': 'DEBUG',
    'MEMCACHED_HOST': '127.0.0.1',
    'RAISE_RIGHT_OFF': True,
#    'SQLALCHEMY_ECHO': True
}

from unittest import TestCase

from flask.app import Flask
from flask_login import LoginManager
from celery import current_app as celery

from common_utils import LazyClassLoader
from fw.auth import load_user
from fw.api.sql_session_storage import SQLAlchemySessionInterface
from fw.documents.contexts import ValidatorContext, RenderingContext, ModelCacheContext
from template_filters import load_filters, set_template_loader
import test_external_tools

from flask import Response


def init_db(app):
    app.external_tools = test_external_tools
    app.cache = test_external_tools.cache


def init_configuration(app, config):
    app.config.update(config)
    app.production = os.environ.get('JB_PRODUCTION', None) is not None
    celery.conf['config'] = config
    for handler in app.logger.handlers:
        celery.log.get_default_logger().addHandler(handler)


def init_login_system(app):
    app.session_interface = SQLAlchemySessionInterface(app.config)
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        raise errors.NotAuthorized()

    login_manager.user_callback = load_user


def init_blueprints(_app):
    from fw.api.views.auth import auth_bp
    from fw.api.views.documents import documents_bp
    from fw.api.views.general import general_bp
    from fw.api.views.object_management import domain_objects_bp
    from fw.api.views.system_views import system_bp
    from fw.api.views.files import files_bp

    _app.register_blueprint(general_bp)
    _app.register_blueprint(auth_bp)
    _app.register_blueprint(documents_bp)
    _app.register_blueprint(domain_objects_bp)
    _app.register_blueprint(files_bp)
    _app.register_blueprint(system_bp)


def init_services(_app):
    from services import ifns, notarius, yurist, partners, pay, llc_reg, ip_reg, osago, test_svc, car_assurance, russian_post
    class_loader = LazyClassLoader
    _app.class_loader = class_loader

    services = (ifns, notarius, yurist, partners, pay, llc_reg, ip_reg, osago, test_svc, car_assurance, russian_post)
    for service in services:
        service.register(_app, _app.jinja_env, class_loader)

def init_plugins():
    class_loader = LazyClassLoader
    from fw.plugins import emailer_plugin, register, doc_builder_plugin, batch_manager_plugin, car_assurance_plugin, task_scheduler
    plugins = (emailer_plugin, doc_builder_plugin, batch_manager_plugin, car_assurance_plugin, task_scheduler)
    for p in plugins:
        register(p.PLUGIN_NAME, p, class_loader=class_loader)


class BaseTestCase(TestCase):
    def setUp(self):
        self.app = Flask(__name__)

        self.test_client = self.app.test_client()
        self.init_logging()
        self.init_validator_context()
        self.config = TEST_CONFIG

        self.auth_cookie = None
        load_filters(self.app.jinja_env, self.config)
        self.app_context = self.app.app_context()
        self.app_context.__enter__()
        set_template_loader(self.app.jinja_env)
        init_configuration(self.app, self.config)
        init_blueprints(self.app)
        init_services(self.app)
        init_login_system(self.app)
        init_db(self.app)
        init_plugins()
        self.mailer = celery.conf['MAILER']
        self.mailer.mails = []
        self.sms_sender = celery.conf['SMS_SENDER']
        self.sms_sender.sms = []
        self.user = None
        self.user_profile = None
        UserManager.init(self.config, self.app.logger)
        sql_db.init_app(self.app)
        sql_db.create_all()
        for table in reversed(sql_db.metadata.sorted_tables):
            sql_db.engine.execute(table.delete())

        @self.app.errorhandler(413)
        def catcher(error):
            data_json = json.dumps({"error": {"code": errors.FileToLarge.ERROR_CODE, "message": errors.FileToLarge.ERROR_MESSAGE}})
            result = Response(data_json, mimetype='application/json', status=400)
            result.headers.add('Access-Control-Allow-Credentials', "true")
            result.headers.add('Access-Control-Allow-Origin', "http://%s" % self.config['site_domain'])
            return result

    def tearDown(self):
        sql_db.session.close()
        #sql_db.drop_all()
        for table in reversed(sql_db.metadata.sorted_tables):
            sql_db.engine.execute(table.delete())

        # noinspection PyUnresolvedReferences
        self.app.model_cache_context.clear()
        self.app_context.__exit__(None, None, None)

    def get_test_resource_name(self, name):
        return os.path.join(CURRENT_DIR, 'test_data', name)

    def init_logging(self):
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        consoleHandler.setLevel(logging.DEBUG)
        self.app.logger.addHandler(consoleHandler)
        self.app.logger.setLevel(logging.DEBUG)

    def init_validator_context(self):
        self.app.validator_context = ValidatorContext()
        self.app.rendering_context = RenderingContext()
        self.app.model_cache_context = ModelCacheContext()


def authorized(admin=False, is_temporal=False, user_id=None):
    def _wrapper(func):
        def _authorize(self, *args, **kwargs):
            if user_id is not None:
                user = AuthUser.query.filter_by(id=user_id).first()
                with self.test_client.session_transaction() as sess:
                    sess['user_id'] = user_id
                self.user = user
                with self.app.test_request_context():
                    _request_ctx_stack.top.user = self.user
                    return func(self, *args, **kwargs)

            enabled = kwargs.get('user_enabled', True)
            data = {
                "password": encrypt_password('TestPassword123'),
                "email": 'test@somedomain.zz',
                'enabled': enabled,
                'email_confirmed': True,
                'mobile': "+79001112233",
                'mobile_confirmed': True,

                'name': 'Name',
                'surname': 'Surname',
                'patronymic': 'Patronymic',
                'is_tester': True,
                'temporal': is_temporal
            } if not is_temporal else {
                'enabled': enabled,
                'is_tester': True,
                'temporal': is_temporal
            }
            if admin:
                data['admin'] = True
            new_user = AuthUser(**data)
            sql_db.session.add(new_user)
            sql_db.session.commit()
            with self.test_client.session_transaction() as sess:
                sess['user_id'] = new_user.get_id()
            self.user = new_user
            with self.app.test_request_context():
                _request_ctx_stack.top.user = self.user
                return func(self, *args, **kwargs)

        return _authorize

    return _wrapper


def registered_user(is_temporal=False):
    def _wrapper(func):
        def _register(self, *args, **kwargs):
            new_user = AuthUser(**{
                "password": encrypt_password('TestPassword123'),
                "email": 'test@somedomain.zz',
                'enabled': True,
                'email_confirmed': True,
                'mobile': "+79001112233",
                'mobile_confirmed': True,

                'name': 'Name',
                'surname': 'Surname',
                'patronymic': 'Patronymic',
                'is_tester': True,
                'temporal': is_temporal
            })
            sql_db.session.add(new_user)
            sql_db.session.flush()
            self.user = new_user
            return func(self, *args, **kwargs)

        return _register

    return _wrapper

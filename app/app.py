# -*- coding: utf-8 -*-
from datetime import timedelta
import json
import logging
from logging.handlers import DEFAULT_TCP_LOGGING_PORT, SocketHandler
import os

from flask import Flask, Response
from flask_compress import Compress
from flask_login import LoginManager
from werkzeug.contrib.fixers import ProxyFix

from fw.api import errors
from fw.api.errors import NotAuthorized
from fw.api.sql_session_storage import SQLAlchemySessionInterface
from fw.documents.contexts import ValidatorContext, RenderingContext, ModelCacheContext
from jb_config import JBConfiguration
from template_filters import load_filters, set_template_loader
from common_utils import LazyClassLoader


SERVICE_DESCRIPTION = 'JurBureau'
DEFAULT_CONFIG_PATH = '/etc/jurbureau/config.cfg'

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)

Compress(app)


def init_logging(app):
    log_file_path = app.config['log_file_path']
    if not os.path.exists(os.path.dirname(log_file_path)):
        raise Exception('Failed to open log file: no such directory %s' % os.path.dirname(log_file_path))

    del app.logger.handlers[:]
    # consoleHandler = logging.StreamHandler()
    #    consoleHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    #    app.logger.addHandler(consoleHandler)

    socketHandler = SocketHandler('localhost', DEFAULT_TCP_LOGGING_PORT)
    socketHandler.setLevel(app.config['LOG_LEVEL'])
    socketHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.addHandler(socketHandler)
    app.logger.setLevel(app.config['LOG_LEVEL'])


def init_login_system(app, config):
    app.session_interface = SQLAlchemySessionInterface(config)
    login_manager = LoginManager()
    login_manager.init_app(app)

    def load_user(user_id):
        from fw.auth.models import AuthUser
        return AuthUser.query.filter_by(id=user_id).first()

    @login_manager.unauthorized_handler
    def unauthorized():
        raise NotAuthorized()

    login_manager.user_callback = load_user


def init_configuration():
    config = JBConfiguration(SERVICE_DESCRIPTION, DEFAULT_CONFIG_PATH)
    app.config.update(config.settings)
    app.config.update({
        'PERMANENT_SESSION_LIFETIME': timedelta(days=60)
    })
    app.production = os.environ.get('JB_PRODUCTION', None) is not None


def init_db():
    import external_tools
    app.external_tools = external_tools


def init_contexts(target_app=None):
    app1 = target_app or app
    app1.validator_context = ValidatorContext()
    app1.rendering_context = RenderingContext()
    app1.model_cache_context = ModelCacheContext()


init_configuration()
init_logging(app)
init_db()
init_contexts()


def init_blueprints(_app):
    from fw.api.views.auth import auth_bp
    from fw.api.views.documents import documents_bp
    from fw.api.views.general import general_bp
    from fw.api.views.object_management import domain_objects_bp
    from fw.api.views.system_views import system_bp
    from fw.api.views.files import files_bp

    url_prefix = None if app.config['DEBUG'] else '/api'

    _app.register_blueprint(general_bp, url_prefix=url_prefix)
    _app.register_blueprint(auth_bp, url_prefix=url_prefix)
    _app.register_blueprint(documents_bp, url_prefix=url_prefix)
    _app.register_blueprint(domain_objects_bp, url_prefix=url_prefix)
    _app.register_blueprint(files_bp, url_prefix=url_prefix)
    _app.register_blueprint(system_bp, url_prefix=url_prefix)


def init_services(_app):
    from services import ifns, notarius, yurist, partners, pay, llc_reg, ip_reg, osago, test_svc, car_assurance, russian_post
    class_loader = LazyClassLoader
    _app.class_loader = class_loader

    url_prefix = None if app.config['DEBUG'] else '/api'
    services = (ifns, notarius, yurist, partners, pay, llc_reg, ip_reg, osago, test_svc, car_assurance, russian_post)
    for service in services:
        service.register(_app, _app.jinja_env, class_loader, url_prefix=url_prefix)


def init_plugins():
    class_loader = LazyClassLoader
    from fw.plugins import emailer_plugin, register, doc_builder_plugin, batch_manager_plugin, car_assurance_plugin, task_scheduler
    plugins = (emailer_plugin, doc_builder_plugin, batch_manager_plugin, car_assurance_plugin, task_scheduler)
    for p in plugins:
        register(p.PLUGIN_NAME, p, class_loader=class_loader)

def init_sql_db(_app):
    from fw.db.sql_base import db
    db.init_app(_app)


def init_flask_signals():
    from fw.db.sql_base import db as sqldb

    def finish_db_transaction(sender, **extra):
        sqldb.session.commit()
        app.model_cache_context.clear()

    def rollback(sender, **extra):
        sqldb.session.rollback()

    from flask import request_finished, got_request_exception
    request_finished.connect(finish_db_transaction, app)
    got_request_exception.connect(rollback, app)


load_filters(app.jinja_env, app.config)
set_template_loader(app.jinja_env)

init_blueprints(app)
init_services(app)
init_sql_db(app)
init_plugins()
init_flask_signals()

#noinspection PyUnresolvedReferences
init_login_system(app, app.config)
app.secret_key = app.config['secret_key']
from fw.auth.user_manager import UserManager
UserManager.init(app.config, app.logger)


@app.errorhandler(413)
def catcher(error):
    data_json = json.dumps(
        {"error": {"code": errors.FileToLarge.ERROR_CODE, "message": errors.FileToLarge.ERROR_MESSAGE}})
    result = Response(data_json, mimetype='application/json', status=400)
    result.headers.add('Access-Control-Allow-Credentials', "true")
    result.headers.add('Access-Control-Allow-Origin', "http://%s" % app.config['site_domain'])
    return result


@app.context_processor
def inject_user():
    return dict(js_scripts_suffix=u".min" if not app.production else u"")


if __name__ == '__main__':
    try:
        app.run()
    except KeyboardInterrupt:
        pass

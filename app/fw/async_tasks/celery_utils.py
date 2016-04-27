# -*- coding: utf-8 -*-
import os

from flask import Flask, current_app
from celery import current_app as celery_app
from fw.documents.contexts import ValidatorContext, RenderingContext, ModelCacheContext
from template_filters import load_filters, set_template_loader


def init_flask_signals(_app):
    from fw.db.sql_base import db as sqldb

    def finish_db_transaction(sender, **extra):
        sqldb.session.commit()

    def rollback(sender, **extra):
        sqldb.session.rollback()

    from flask import request_finished, got_request_exception
    request_finished.connect(finish_db_transaction, _app)
    got_request_exception.connect(rollback, _app)


def init_sql_db(app):
    from fw.db.sql_base import db
    db.init_app(app)

    init_flask_signals(app)

CELERY_FLASK_APP = None

def make_app(config, external_tools):
    def _make_app():
        global CELERY_FLASK_APP

        if CELERY_FLASK_APP:
            return CELERY_FLASK_APP

        from app import init_blueprints, init_services
        app = Flask(__name__)
        if not isinstance(config, dict):
            app.config.update(config.settings)
        else:
            app.config.update(config)

        app.validator_context = ValidatorContext()
        app.rendering_context = RenderingContext()
        app.model_cache_context = ModelCacheContext()
        app.external_tools = external_tools
        load_filters(app.jinja_env, app.config)
        set_template_loader(app.jinja_env)
        init_blueprints(app)
        init_services(app)
        if not app.config['TEST']:
            init_sql_db(app)
        app.cache = external_tools.cache
        app.logger_name = "celery"
        # log_file_path = os.path.join(os.path.split(app.config['log_file_path'])[0], "celeryd.log")
        # file_handler = TimedRotatingFileHandler(log_file_path, backupCount=7, encoding='utf-8', when="midnight")
        # file_handler.setLevel()
        # file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        app.logger.setLevel(app.config['CELERY_LOG_LEVEL'])

        CELERY_FLASK_APP = app
        return app
    return _make_app

class TaskFileIdHolder(object):
    def __init__(self, task_id, config):
        self.task_id = task_id
        self.config = config
        self.file_name = os.path.join(os.path.dirname(self.config['celery_tasks_dir']), unicode(self.task_id))

    def __enter__(self):
        if not os.path.exists(self.file_name):
            try:
                with open(self.file_name, 'w') as f:
                    f.write(str(self.task_id))
            except Exception:
                pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.file_name):
            try:
                os.unlink(self.file_name)
            except Exception:
                pass

    def exists(self):
        return os.path.exists(self.file_name)

def found_same_task(task_name, request = None, task_id = None, args = None, kwargs = None, inspect_tasks = None):
    if inspect_tasks is not None and not inspect_tasks:
        return False

    kwargs = kwargs or {}
    args = request.args if request else args
    kwargs = request.kwargs if request else kwargs
    _id = request.id if request else task_id

    current_app.logger.info(u"Searching for celery task %s" % task_name)
    inspector = celery_app.control.inspect()
    tasks = []

    if inspect_tasks:
        tasks = inspect_tasks
    else:
        actives = inspector.active()
        for item in (actives.values() if actives else []):
            tasks.extend(item)
        schedules = inspector.scheduled()
        for item in (schedules.values() if schedules else []):
            tasks.extend(item)

    for task_info in tasks:
        task_id = task_info.get('id', None)
        if not task_id:
            continue
        if task_id == _id:
            continue

        this_task_name = task_info.get('name', None)
        if this_task_name != task_name:
            current_app.logger.info(u"task names differ - skip")
            continue

        if args is not None:
            this_task_args = task_info.get('args', None) # todo: test empty args
            current_app.logger.info(u"Comparing args. Our args: <%s> Their args: <%s> " % (unicode(args), this_task_args))
            if unicode(args) != this_task_args:
                continue

        if kwargs is not None:
            this_task_kwargs = task_info.get('kwargs', {})
            #current_app.logger.info(u"Comparing kwargs. Our args: <%s> Their args: <%s> " % (unicode(kwargs), this_task_kwargs))
            if unicode(kwargs) != this_task_kwargs:
                continue
        return True

    return False


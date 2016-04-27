# -*- coding: utf-8 -*-

from celery import current_app as celery
from flask.globals import current_app

celery.config_from_envvar('CELERY_CONFIG_MODULE')

@celery.task()
def test_task(a = 1, b = 2):
    config = celery.conf.get('config')
    db = celery.conf.get('db')

    with celery.conf['flask_app']().app_context():
        logger = current_app.logger
        logger.warn(u"Test task started: %s" % str((a, b)))
        return True

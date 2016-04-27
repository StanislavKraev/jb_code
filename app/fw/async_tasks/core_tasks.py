# -*- coding: utf-8 -*-

#noinspection PyUnresolvedReferences
from datetime import datetime
from celery import current_app as celery
from fw.async_tasks.models import CeleryScheduledTask
from fw.async_tasks.scheduler import CeleryScheduler

celery.config_from_envvar('CELERY_CONFIG_MODULE')

@celery.task()
def send(batch_id, event, event_data=None):
    event_data = event_data or {}
    from fw.documents.batch_manager import BatchManager
    app = celery.conf['flask_app']()
    logger = app.logger
    logger.info(u"PROCESSING event %s for batch %s" % (event, batch_id))
    with app.app_context():
        result = BatchManager.handle_event(batch_id, event, event_data, logger=logger, config=app.config)
        logger.info(u"FINISH PROCESSING event %s for batch %s" % (event, batch_id))
        return result

@celery.task()
def check_scheduled_tasks():
    app = celery.conf['flask_app']()
    with app.app_context():
        for task in CeleryScheduledTask.query.filter(
            CeleryScheduledTask.sent==False,
            CeleryScheduledTask.eta.__le__(datetime.utcnow())
        ):
            CeleryScheduler.run_task(task)

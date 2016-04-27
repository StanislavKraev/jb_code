# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from celery import current_app as celery
from flask.globals import current_app
from fw.async_tasks import celery_utils
from fw.db.sql_base import db as sqldb
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import DocumentBatchDbObject
from fw.documents.enums import BatchStatusEnum

celery.config_from_envvar('CELERY_CONFIG_MODULE')

from manage_commands.batch_commands import GetFssNumberCommand

BATCH_FINALISATION_MAX_DURATION = 120  # seconds


@celery.task()
def check_frozen_batch_finalisation():
    config = celery.conf.get('config')

    with celery.conf['flask_app']().app_context():
        logger = current_app.logger
        logger.debug(u"Starting dead batches being finalised")

        cur = DocumentBatchDbObject.query.filter(
            DocumentBatchDbObject.current_task_id != None,
            DocumentBatchDbObject.batch_rendering_start < datetime.utcnow() - timedelta(seconds=BATCH_FINALISATION_MAX_DURATION),
            DocumentBatchDbObject.status == BatchStatusEnum.BS_BEING_FINALISED
        )

        inspect_tasks = []
        inspector = celery.control.inspect()
        actives = inspector.active()
        for item in (actives.values() if actives else []):
            inspect_tasks.extend(item)
        schedules = inspector.scheduled()
        for item in (schedules.values() if schedules else []):
            inspect_tasks.extend(item)

        for batch in cur:
            logger.debug(u"checking %s" % batch.id)
            task_id = batch.current_task_id
            if not celery_utils.found_same_task('fw.async_tasks.rendering.render_batch',
                                                task_id=task_id, args=(batch.id, ),
                                                inspect_tasks=inspect_tasks):
                logger.warn(
                    u"Batch %s is being finalised but corresponding celery task was not found. "
                    u"Cancelling batch finalisation!" % batch.id)

                try:
                    BatchManager.cancel_batch_finalization(batch, config, logger)
                except Exception:
                    current_app.logger.exception(u"Failed to cancel batch finalization.")
                    continue

        cur = DocumentBatchDbObject.query.filter(
            DocumentBatchDbObject.current_task_id == None,
            DocumentBatchDbObject.status == BatchStatusEnum.BS_BEING_FINALISED
        )
        for batch in cur:
            logger.warn(
                u"Batch %s is being finalised but corresponding celery task was not found [2]. "
                u"Cancelling batch finalisation!" % batch.id)

            try:
                BatchManager.cancel_batch_finalization(batch, config, logger)
            except Exception:
                current_app.logger.exception(u"Failed to cancel batch finalization.")
                continue

        return True

@celery.task()
def get_fss_task():
    config = celery.conf.get('config')
    db = celery.conf.get('db')

    with celery.conf['flask_app']().app_context():
        logger = current_app.logger
        GetFssNumberCommand.get_fss_number(logger)


@celery.task()
def clean_kombu_messages():
    with celery.conf['flask_app']().app_context():
        sqldb.engine.execute(u"DELETE FROM kombu_message WHERE timestamp < '%s';" %
                             (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S"))

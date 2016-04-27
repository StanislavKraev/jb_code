# -*- coding: utf-8 -*-
from celery import current_app as celery
from datetime import datetime, timedelta
from fw.api import errors

from fw.async_tasks.models import CeleryScheduledTask
from fw.db.sql_base import db as sqldb

from celery import current_app as celery_current_app
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import DocumentBatchDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage


class CeleryScheduler(object):

    @staticmethod
    def post(task_name, countdown_seconds=None, eta=None, args=None, kwargs=None, task_id=None, force_replace_task=False):
        assert countdown_seconds or eta

        # all_task_names = celery_current_app.tasks.keys()
        # if task_name not in all_task_names:
        #     raise ValueError()

        eta_calc = eta or datetime.utcnow() + timedelta(seconds=countdown_seconds)
        # if eta_calc < datetime.utcnow():
        #     raise ValueError()

        new_task = CeleryScheduledTask(
            task_name=task_name,
            args=args,
            kwargs=kwargs,
            eta=eta_calc
        )
        if task_id is not None:
            if CeleryScheduledTask.query.filter_by(id=task_id).count():
                if not force_replace_task:
                    raise errors.DuplicateIdError()
                CeleryScheduledTask.query.filter_by(id=task_id).delete()
                sqldb.session.commit()
            new_task.id = task_id

        sqldb.session.add(new_task)
        sqldb.session.commit()
        return new_task

    @staticmethod
    def remove(task_id):
        assert task_id

        CeleryScheduledTask.query.filter_by(id=task_id).delete()
        sqldb.session.commit()

    @staticmethod
    def run_task(task):
        assert isinstance(task, CeleryScheduledTask)
        task_obj = celery_current_app.tasks[task.task_name]
        task.sent = True
        sqldb.session.commit()
        task_obj.apply_async(args=task.args, kwargs=task.kwargs)

@celery.task()
def run_scheduled_task(descriptor_name, action_name, batch_id):
    app = celery.conf['flask_app']()
    with app.app_context():
        batch_db = DocumentBatchDbObject.query.filter_by(id=batch_id).scalar()
        descriptor = DocRequisitiesStorage.get_batch_descriptor(descriptor_name)
        action = descriptor['actions'][action_name]
        BatchManager.perform_action(action, batch_db, {}, app.logger, app.config)

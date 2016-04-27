# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
import os
from fw.api import errors
from fw.async_tasks.models import CeleryScheduledTask
from fw.async_tasks.scheduler import CeleryScheduler
from fw.db.sql_base import db as sqldb

os.environ['CELERY_CONFIG_MODULE'] = 'dev_celeryconfig'

from fw.async_tasks.core_tasks import check_scheduled_tasks
from test_pack.base_batch_test import BaseBatchTestCase
from test_pack.test_api import authorized

class CelerySchedulerTestCase(BaseBatchTestCase):

    @authorized()
    def test_post_simple_task(self):
        new_task = CeleryScheduler.post("fw.async_tasks.test_task.test_task", countdown_seconds=1)
        task_obj = CeleryScheduledTask.query.filter_by(id=new_task.id).scalar()
        self.assertIsNotNone(task_obj)

    @authorized()
    def test_post_task_with_args_and_kwargs(self):
        new_task = CeleryScheduler.post("fw.async_tasks.test_task.test_task", args=(1, 2), kwargs={'a': 1, 'b': 2}, countdown_seconds=1)
        task_obj = CeleryScheduledTask.query.filter_by(id=new_task.id).scalar()
        self.assertIsNotNone(task_obj)
        self.assertEqual(task_obj.args, [1, 2])
        self.assertEqual(task_obj.kwargs, {'a': 1, 'b': 2})

    @authorized()
    def test_post_task_with_eta_in_past(self):
        with self.assertRaises(ValueError):
            CeleryScheduler.post("fw.async_tasks.test_task.test_task", eta=datetime.utcnow() - timedelta(days=1))

    @authorized()
    def test_replace_task(self):
        new_task = CeleryScheduler.post("fw.async_tasks.test_task.test_task", countdown_seconds=1, task_id="abc")
        task_obj = CeleryScheduledTask.query.filter_by(id=new_task.id).scalar()
        self.assertIsNotNone(task_obj)
        self.assertEqual(CeleryScheduledTask.query.count(), 1)

        with self.assertRaises(errors.DuplicateIdError):
            CeleryScheduler.post("fw.async_tasks.test_task.test_task", countdown_seconds=1, task_id="abc")

        new_task = CeleryScheduler.post("fw.async_tasks.test_task.test_task", countdown_seconds=1, task_id="abc", force_replace_task=True)
        task_obj = CeleryScheduledTask.query.filter_by(id=new_task.id).scalar()
        self.assertIsNotNone(task_obj)
        self.assertEqual(CeleryScheduledTask.query.count(), 1)

    @authorized()
    def test_post_invalid_task(self):
        with self.assertRaises(ValueError):
            CeleryScheduler.post("test_task1", countdown_seconds=1)

    @authorized()
    def test_run_simple_task(self):
        new_task = CeleryScheduledTask(
            task_name="fw.async_tasks.test_task.test_task",
            eta=datetime.utcnow() + timedelta(seconds=1),
            kwargs={'a': 5, 'b': 4}
        )
        sqldb.session.add(new_task)
        sqldb.session.commit()

        self.app.logger.info('1')
        check_scheduled_tasks.delay()
        time.sleep(1)
        self.app.logger.info('2')
        check_scheduled_tasks.delay()


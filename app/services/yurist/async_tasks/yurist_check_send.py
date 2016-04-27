# -*- coding: utf-8 -*-
from celery import current_app as celery
from fw.async_tasks import send_email
from fw.db.sql_base import db as sqldb
from services.yurist.data_model.enums import YuristBatchCheckStatus
from services.yurist.data_model.models import YuristBatchCheckObject

celery.config_from_envvar('CELERY_CONFIG_MODULE')


@celery.task()
def check_and_send(*args, **kwargs):
    if 'batch_check_id' and kwargs['batch_check_id']:
        with celery.conf['flask_app']().app_context():
            check_obj = YuristBatchCheckObject.query.filter_by(id=kwargs['batch_check_id']).first()
            if not check_obj or check_obj.status != YuristBatchCheckStatus.YBS_WAIT:
                return False
            check_obj.status = YuristBatchCheckStatus.YBS_IN_PROGRESS
            sqldb.session.commit()
            for rec in kwargs['rec_list']:
                send_email.send_email.delay(rec, kwargs['mail_type'], **kwargs)

# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from celery.exceptions import SoftTimeLimitExceeded
from celery import current_app as celery

from fw.db.sql_base import db as sqldb
from services.russian_post.db_models import RussianPostTrackingItem, PostTrackingStatus
from services.russian_post.integration import get_current_mail_status

celery.config_from_envvar('CELERY_CONFIG_MODULE')


def _post_oper_type_2_tracking_status(oper_type):
    if oper_type in ('2',):
        return PostTrackingStatus.PTS_DELIVERED

    if oper_type in ('5', '22', '3', '16'):
        return PostTrackingStatus.PTS_FAILED

    return PostTrackingStatus.PTS_PROGRESS

@celery.task()
def get_tracking_info_async(batch_id=None):
    config = celery.conf.get('config')
    db = celery.conf.get('db')
    app = celery.conf['flask_app']()
    logger = celery.log.get_default_logger()
    login, password = config['RUSSIAN_POST_API_LOGIN'], config['RUSSIAN_POST_API_PASSWORD']
    with app.app_context():
        dt = datetime.utcnow() - timedelta(days=31)
        cur = RussianPostTrackingItem.query.filter(
            RussianPostTrackingItem.batch_id == batch_id,
            RussianPostTrackingItem.status.in_([PostTrackingStatus.PTS_UNKNOWN,
                                                PostTrackingStatus.PTS_NOT_FOUND,
                                                PostTrackingStatus.PTS_PROGRESS]),
            RussianPostTrackingItem.creation_date.__ge__(dt)
        ) if batch_id else RussianPostTrackingItem.query.filter(
            RussianPostTrackingItem.status.in_([PostTrackingStatus.PTS_UNKNOWN,
                                                PostTrackingStatus.PTS_NOT_FOUND,
                                                PostTrackingStatus.PTS_PROGRESS]),
            RussianPostTrackingItem.creation_date.__ge__(dt)
        )

        for tracking_item in cur.order_by(RussianPostTrackingItem.last_check_dt.asc()):
            tracking_number = tracking_item.tracking
            if not tracking_number:
                continue
            try:
                logger.info(u"Checking tracking item %s" % tracking_number)

                new_data = get_current_mail_status(tracking_item.tracking, login, password)
                if not new_data:
                    tracking_item.status = PostTrackingStatus.PTS_NOT_FOUND
                    tracking_item.status_caption = u"Почтовое отправление не найдено"
                    tracking_item.last_check_dt = datetime.utcnow()
                    sqldb.session.commit()
                    return True
                new_status = _post_oper_type_2_tracking_status(new_data['operation'])
                if new_data['dt'] != tracking_item.status_change_dt or new_status != tracking_item.status:
                    tracking_item.status = new_status
                    tracking_item.status_change_dt = new_data['dt']
                    tracking_item.last_location = new_data['address']
                    tracking_item.status_caption = new_data['op_name']
                    tracking_item.last_check_dt = datetime.utcnow()
                    sqldb.session.commit()
                    return True
            except SoftTimeLimitExceeded:
                logger.warn(u"Had not enough time to check all tracking items")
            except Exception:
                logger.exception(u"Failed to check tracking item %s" % tracking_number)
                continue

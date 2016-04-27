# -*- coding: utf-8 -*-
from datetime import datetime
import os
from celery import current_app as celery
from flask.globals import current_app
from fw.async_tasks import send_email
from fw.auth.user_manager import UserManager
from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject
from fw.documents.enums import BatchStatusEnum, UserDocumentStatus
from fw.storage.file_storage import FileStorage
from template_filters import utm_args

celery.config_from_envvar('CELERY_CONFIG_MODULE')


@celery.task()
def not_paid_check_and_send(*args, **kwargs):
    config = celery.conf.get('config')

    batch_id = kwargs['batch_id']
    last_change_dt_str = kwargs['last_change_dt_str']

    with celery.conf['flask_app']().app_context():
        logger = current_app.logger
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).scalar()
        if not batch or not batch.data or batch.status != BatchStatusEnum.BS_FINALISED:
            logger.info("Exit 1")
            return False

        last_change_dt = batch.last_change_dt
        if last_change_dt and isinstance(last_change_dt, datetime):
            if last_change_dt_str != last_change_dt.strftime("%Y-%m-%dT%H:%M:%S"):
                logger.info("Exit 2")
                return True

        if batch.paid:
            return True

        user = batch._owner
        if not user or not user.email:
            logger.info("Exit 3")
            return False

        send_mails = batch.sent_mails or []
        if send_mails and "please_pay_finalised" in send_mails or "please_pay_finalised_double" in send_mails:
            logger.info("Exit 4")
            return False

        mail_type = "please_pay_finalised" if "please_finalise" not in send_mails else "please_pay_finalised_double"

        batch_url = u"%s://%s/ooo/?id=%s" % (config['WEB_SCHEMA'], config['DOMAIN'], batch_id)
        batch_url = utm_args(batch_url, mail_type, user.id)

        tmpl_data = {
            "short_name": batch.data.get('short_name', ""),
            "domain": config['DOMAIN'],
            "schema": config['WEB_SCHEMA'],
            "user_id": str(user.id),
            "batch_url": UserManager.make_auth_url(batch_url, user).get_url(config)
        }

        send_email.send_email(user.email, mail_type, **tmpl_data)

        mails_sent = set(send_mails)
        mails_sent.add(mail_type)
        DocumentBatchDbObject.query.filter_by(id=batch_id).update({
            'sent_mails': list(mails_sent)
        })
        sqldb.session.commit()
        logger.info("Exit 5")
        return True


@celery.task()
def make_all_user_fin_batch_paid_and_replace_watermarked_docs_with_normal(*args, **kwargs):
    db = celery.conf.get('db')
    config = celery.conf.get('config')

    user_id = kwargs['user_id']

    with celery.conf['flask_app']().app_context():
        logger = current_app.logger
        batches = DocumentBatchDbObject.query.filter_by(_owner_id=user_id, paid=False, status=BatchStatusEnum.BS_FINALISED)

        for batch in batches:
            batch.paid = True
            for doc in batch._documents:
                if doc.status == UserDocumentStatus.DS_RENDERED and doc.file:
                    try:
                        batch_id = batch.id
                        file_obj = doc.file
                        if not file_obj:
                            logger.error(u"Can't replace watermarked file: "
                                         u"Failed to find file of batch %s" % unicode(batch_id))
                            continue
                        file_path = FileStorage.get_path(file_obj, current_app.config)
                        if not file_path or not os.path.exists(file_path) or not os.path.exists(file_path + '.src'):
                            logger.error(u"Can't replace watermarked file: "
                                         u"Failed to find original or source file %s of batch %s" % (
                                             unicode(file_path + '.src'), unicode(batch_id)))
                            continue
                        os.rename(file_path + '.src', file_path)
                    except Exception:
                        logger.exception(u"Can't replace watermarked file")
        sqldb.session.commit()
        return True


@celery.task()
def not_finalised_check_and_send(batch_id=None, last_change_dt_str=None):
    if not batch_id or not last_change_dt_str:
        return False

    config = celery.conf.get('config')

    with celery.conf['flask_app']().app_context():
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id, deleted=False, finalisation_count=0).scalar()
        if not batch or batch.status not in (BatchStatusEnum.BS_NEW, BatchStatusEnum.BS_EDITED):
            return False

        last_change_dt = batch.last_change_dt
        if last_change_dt and isinstance(last_change_dt, datetime):
            if last_change_dt_str != last_change_dt.strftime("%Y-%m-%dT%H:%M:%S"):
                return True

        mail_type = 'please_finalise'
        if mail_type in (batch.sent_mails or []):
            return False
        mails_sent = set(batch.sent_mails or [])

        user = batch._owner
        if not user or not user.email:
            return False
        batch_data = batch.data

        batch_url = u"%s://%s/ooo/?id=%s" % (config['WEB_SCHEMA'], config['DOMAIN'], batch_id)

        tmpl_data = {
            "short_name": batch_data.get('short_name', ""),
            "domain": config['DOMAIN'],
            "schema": config['WEB_SCHEMA'],
            "user_id": str(user.id),
            "batch_url": UserManager.make_auth_url(batch_url, user).get_url(config)
        }

        send_email.send_email(user.email, mail_type, **tmpl_data)

        mails_sent.add(mail_type)
        DocumentBatchDbObject.query.filter_by(id=batch_id).update({
            'sent_mails': list(mails_sent)
        })
        sqldb.session.commit()
        return True

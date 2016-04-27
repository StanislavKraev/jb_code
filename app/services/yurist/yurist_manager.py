# -*- coding: utf-8 -*-

from datetime import datetime
from flask_login import current_user
import os
from fw.auth.social_services import SocialServiceBackends
from fw.db.sql_base import db as sqldb
from fw.storage.file_storage import FileStorage
from services.yurist.data_model.enums import YuristBatchCheckStatus
from services.yurist.data_model.models import YuristBatchCheckObject


def yurist_check(config, batch_db, file_obj_list, logger):
    # get batch id and check if it is still in active state
    batch_check = YuristBatchCheckObject.query.filter(
        YuristBatchCheckObject.batch_id == batch_db.id,
        YuristBatchCheckObject.status.notin_(YuristBatchCheckStatus.FINAL_STATUSES)
    ).order_by(YuristBatchCheckObject.create_date.desc()).first()
    # this check should be performed later
    if not batch_check:
        return False
    user = batch_db._owner
    if not user:
        raise Exception("Failed to find batch owner")

    from fw.documents.batch_manager import BatchManager
    attaches = BatchManager.get_shared_links_to_rendered_docs(batch_db, config, logger)

    schema = config['WEB_SCHEMA']
    domain = config['DOMAIN']
    for file_obj in file_obj_list:
        path = FileStorage.get_path(file_obj, config)
        if os.path.exists(path):
            if file_obj._owner:
                url = u"%s://%s%s" % (schema, domain, FileStorage.get_shared_link(file_obj.id, config))
            else:
                url = u"%s://%s%s" % (schema, domain, FileStorage.get_url(file_obj, config))

            attaches.append({
                'url': url,
                'title': file_obj.file_name or url
            })

    rec_list = config['YURIST_EMAIL_LIST']
    from services.yurist.async_tasks import yurist_check_send
    batch_check_id = batch_check.id if batch_check else "not-found"
    # countdown 2 hours before execution
    yurist_check_send.check_and_send.apply_async(
        args=[],
        kwargs=dict(
            email=user.email,
            batch_check_id=batch_check_id,
            server_url_schema=config['WEB_SCHEMA'],
            api_url=config['api_url'],
            attaches=attaches,
            mail_type='yurist_batch_check',
            rec_list=rec_list
        ),
        countdown=config['SEND_DOCS_TO_YURIST_DELAY_SECONDS']
    )


def cancel_check(batch, config, logger):
    """
        @type batch: db.db_fields.DocumentBatchDbObject
    """
    try:
        batch_id = batch.id
        yurist_check = YuristBatchCheckObject.query.filter(
            YuristBatchCheckObject.batch_id == batch_id,
            YuristBatchCheckObject.status.in_([YuristBatchCheckStatus.YBS_IN_PROGRESS, YuristBatchCheckStatus.YBS_WAIT])
        ).first()

        if not yurist_check:
            check_new = YuristBatchCheckObject.query.filter_by(batch_id=batch_id,
                                                               status=YuristBatchCheckStatus.YBS_NEW).first()
            if not check_new:
                yurist_batch_check = YuristBatchCheckObject(**{
                    'batch_id': batch_id,
                    'create_date': datetime.now(),
                    'status': YuristBatchCheckStatus.YBS_NEW,
                    'typos_correction': False
                })
                sqldb.session.add(yurist_batch_check)
                sqldb.session.commit()
            return

        status = yurist_check.status

        yurist_check.status = YuristBatchCheckStatus.YBS_NEW
        sqldb.session.commit()

        if status == YuristBatchCheckStatus.YBS_IN_PROGRESS:
            llc_full_name = batch.data.get('full_name', "")
            social_link = SocialServiceBackends.get_user_social_network_profile_url(current_user.id, db)
            rec_list = config['YURIST_EMAIL_LIST']
            from fw.async_tasks import send_email
            for recipient in rec_list:
                send_email.send_email.delay(
                    recipient,
                    'yurist_batch_check_discard',
                    email=current_user.email,
                    mobile=current_user.mobile,
                    social_link=social_link,
                    full_name=llc_full_name
                )
    except Exception, ex:
        logger.exception(u"Failed to cancel yurist batch check")

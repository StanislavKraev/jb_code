# -*- coding: utf-8 -*-
from flask_login import current_user
import pytils
from fw.auth.social_services import SocialServiceBackends
from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject
from services.notarius.data_model.models import NotariusBookingObject


def discard_booking(batch, config, logger):
    from fw.async_tasks import send_email

    try:
        batch_id = batch.id
        booking = NotariusBookingObject.query.filter_by(
            batch=batch,
            owner=current_user,
            _discarded=False).scalar()
        if not booking:
            return

        booking._discarded = True
        batch_data = batch.data or {}
        batch_data['lawyer_check'] = False
        DocumentBatchDbObject.query.filter_by(id=batch_id).update({
            'data': batch_data
        })
        sqldb.session.commit()

        llc_full_name = batch.data.get('full_name', "")
        social_link = SocialServiceBackends.get_user_social_network_profile_url(current_user.id)
        rec_list = config['YURIST_EMAIL_LIST']

        notarius_id = booking.notarius_id
        dt = booking.dt
        address = booking.address

        for recipient in rec_list:
            logger.info(u"Sending %s email to %s" % ('notarius_discard_on_batch_change', recipient))
            send_email.send_email.delay(
                recipient,
                'notarius_discard_on_batch_change',
                notarius_id=unicode(notarius_id),
                booking_time=pytils.dt.ru_strftime(u"%d %B %Y в %H:%M", inflected=True,
                                                   date=dt) if dt else u"<неизвестно>",
                address=address,
                email=current_user.email,
                mobile=current_user.mobile,
                social_link=social_link,
                full_name=llc_full_name
            )

        if current_user.email:
            logger.info(u"Sending %s email to %s" % ('notarius_discard_user_notify', current_user.email))
            send_email.send_email.delay(
                current_user.email,
                'notarius_discard_user_notify',
                notarius_id=unicode(notarius_id),
                booking_time=pytils.dt.ru_strftime(u"%d %B %Y в %H:%M", inflected=True,
                                                   date=dt) if dt else u"<неизвестно>",
                address=address,
                email=current_user.email,
                mobile=current_user.mobile,
                domain=config['DOMAIN'],
                schema=config['WEB_SCHEMA'],
                batch_id=batch_id,
                user_id=str(current_user.id)
            )
    except Exception, ex:
        logger.exception(u"Failed to discard notarius booking")


def change_objects_owner(old_user_id, new_user_id):
    NotariusBookingObject.query.filter_by(owner_id=old_user_id).update({
        'owner_id': new_user_id
    })
    sqldb.session.commit()

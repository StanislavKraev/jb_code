# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject
from services.notarius.data_model.models import NotariusObject, NotariusBookingObject


def forward(config, logger):
    logger.debug(u"Migrate notarius models")

    notarius_col = db['notarius']
    NotariusBookingObject.query.delete()
    NotariusObject.query.delete()
    sqldb.session.commit()
    for old_notarius in notarius_col.find():
        new_notarius = NotariusObject(
            id=str(old_notarius['_id']),
            surname=old_notarius.get('surname', u""),
            name=old_notarius.get('name', u""),
            patronymic=old_notarius.get('patronymic', None),

            schedule=old_notarius['schedule'],
            schedule_caption=old_notarius.get('schedule_caption', ''),
            title=old_notarius.get('title', ''),
            address=old_notarius.get('address'),
            region=old_notarius['region']['code'],
            metro_station=old_notarius.get('metro_station', '')
        )
        sqldb.session.add(new_notarius)
        sqldb.session.commit()

    booking_col = db['notarius_booking']
    for old_booking in booking_col.find():
        notarius_id = str(old_booking['notarius_id'])
        notarius = NotariusObject.query.filter_by(id=notarius_id).first()
        if not notarius:
            continue

        batch_id = str(old_booking['batch_id'])
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
        if not batch:
            continue

        new_booking = NotariusBookingObject(
            id=str(old_booking['_id']),
            batch_id=str(old_booking['batch_id']),
            owner_id=str(old_booking['_owner']),
            notarius_id=notarius_id,
            dt=old_booking['dt'],
            address=old_booking['address'],
            _discarded=old_booking['_discarded']
        )
        sqldb.session.add(new_booking)
        sqldb.session.commit()

def rollback(config, logger):
    pass

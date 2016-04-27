# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject
from fw.documents.enums import DocumentBatchTypeEnum
from services.notarius.data_model.models import NotariusBookingObject
from services.pay.models import PayInfoObject, PurchaseServiceType


def forward(config, logger):
    logger.debug(u"Add new argument to data")

    batches = set()
    for booking in NotariusBookingObject.query.filter(NotariusBookingObject.batch_id != None):
        if booking.batch_id in batches:
            continue
        for batch in DocumentBatchDbObject.query.filter_by(id=booking.batch_id, deleted=False, _broken=False):
            batches.add(batch.id)
            data = batch.data or {}
            data['lawyer_check'] = not booking._discarded
            DocumentBatchDbObject.query.filter_by(id=batch.id).update({
                'data': data
            })
            sqldb.session.commit()


def rollback(config, logger):
    pass

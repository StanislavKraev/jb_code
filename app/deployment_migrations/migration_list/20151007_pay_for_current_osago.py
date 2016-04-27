# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject
from fw.documents.enums import DocumentBatchTypeEnum
from services.pay.models import PayInfoObject, PurchaseServiceType


def forward(config, logger):
    logger.debug(u"Add payments for currently existing osago batches")

    for batch in DocumentBatchDbObject.query.filter_by(_broken=False, deleted=False,
                                                       batch_type=DocumentBatchTypeEnum.DBT_OSAGO, status="claim"):
        new_pay_info = PayInfoObject(
            user=batch._owner,
            batch=batch,
            pay_record_id=0,
            payment_provider=0,
            service_type=PurchaseServiceType.OSAGO_PART1
        )
        sqldb.session.add(new_pay_info)

    for batch in DocumentBatchDbObject.query.filter_by(_broken=False, deleted=False,
                                                       batch_type=DocumentBatchTypeEnum.DBT_OSAGO, status="court"):
        new_pay_info = PayInfoObject(
            user=batch._owner,
            batch=batch,
            pay_record_id=0,
            payment_provider=0,
            service_type=PurchaseServiceType.OSAGO_PART1
        )
        sqldb.session.add(new_pay_info)

        new_pay_info = PayInfoObject(
            user=batch._owner,
            batch=batch,
            pay_record_id=0,
            payment_provider=0,
            service_type=PurchaseServiceType.OSAGO_PART2
        )
        sqldb.session.add(new_pay_info)
    sqldb.session.commit()

def rollback(config, logger):
    pass

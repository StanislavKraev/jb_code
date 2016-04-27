# -*- coding: utf-8 -*-
from copy import copy

from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject
from fw.documents.enums import DocumentBatchTypeEnum


def forward(config, logger):
    logger.debug(u"Migrate lawsuit fields")

    m = {
        'yes': 'success',
        'no': 'refuse',
        'notAll': 'partial_success',
        'tooEarly': 'unknown'
    }
    for batch in DocumentBatchDbObject.query.filter_by(deleted=False, batch_type=DocumentBatchTypeEnum.DBT_OSAGO):
        metadata = batch._metadata or {}
        if not metadata or '_isClaimSubmissionToInsurance' not in metadata or '_insuranceReturnDebtByClaimType' not in metadata:
            continue
        _isClaimSubmissionToInsurance = metadata['_isClaimSubmissionToInsurance']
        _insuranceReturnDebtByClaimType = metadata['_insuranceReturnDebtByClaimType']

        make_lawsuit = _isClaimSubmissionToInsurance
        pretension_result = m.get(_insuranceReturnDebtByClaimType, 'unknown')

        for doc in BatchDocumentDbObject.query.filter_by(batch=batch):
            dd = copy(doc.data)
            dd.update({
                'make_lawsuit': make_lawsuit,
                'pretension_result': pretension_result
            })
            BatchDocumentDbObject.query.filter_by(id=doc.id).update({
                'data': dd
            })
    sqldb.session.commit()

def rollback(config, logger):
    pass

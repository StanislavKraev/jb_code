# -*- coding: utf-8 -*-
from fw.documents.db_fields import DocumentBatchDbObject
from fw.documents.enums import DocumentTypeEnum
from services.pay.models import PayInfoObject


def is_paid_document(batch_id=None, document_type=None):
    if not document_type or not batch_id:
        return False

    batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
    if not batch:
        return False

    if document_type not in (DocumentTypeEnum.DT_OSAGO_PRETENSION, DocumentTypeEnum.DT_OSAGO_LAWSUIT):
        return True

    payments_count = PayInfoObject.query.filter_by(batch=batch).count()
    if document_type == DocumentTypeEnum.DT_OSAGO_PRETENSION:
        return payments_count > 0
    if document_type == DocumentTypeEnum.DT_OSAGO_LAWSUIT:
        return payments_count > 1

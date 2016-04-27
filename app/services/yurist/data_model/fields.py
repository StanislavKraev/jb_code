# -*- coding: utf-8 -*-
from fw.documents.fields.complex_doc_fields import DocArrayField
from fw.documents.fields.doc_fields import document_model, BaseDocField
from fw.documents.fields.simple_doc_fields import DocMongoIdField, DocDateTimeField, DocBoolField, DocEnumField, \
    DocTextField
from services.yurist.data_model.enums import YuristBatchCheckStatus


@document_model
class YuristBatchCheck(BaseDocField):

    id = DocMongoIdField(is_parse_from_api=False)
    batch_id = DocTextField(is_parse_from_api=False)

    create_date = DocDateTimeField()
    attached_files = DocArrayField(cls=u"DocFileAttachField")
    typos_correction = DocBoolField(required=False, default=False)

    status = DocEnumField(enum_cls="YuristBatchCheckStatus", required=True, is_parse_from_api=False,
                          default=YuristBatchCheckStatus.YBS_NEW)

    __api_to_db_mapping__ = {'id': '_id'}

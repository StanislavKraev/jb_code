# -*- coding: utf-8 -*-
from fw.documents.fields.doc_fields import BaseDocField
from fw.documents.fields.general_doc_fields import general_doc_field
from fw.documents.fields.simple_doc_fields import DocMongoIdField, DocBoolField, DocEnumField, DocTextField, \
    DocDateTimeField, DocPhoneNumberField, DocJsonField


@general_doc_field
class IfnsBooking(BaseDocField):

    batch_id = DocTextField(is_service=True, required=False)
    _discarded = DocBoolField(is_service=True, required=False)
    service_id = DocEnumField(enum_cls="IfnsServiceEnum", required=True)

    id = DocMongoIdField(is_parse_from_api=False)

    ifns = DocTextField()
    service = DocTextField()
    date = DocDateTimeField()
    window = DocTextField()
    address = DocTextField()
    phone = DocPhoneNumberField()
    how_to_get = DocTextField()
    code = DocTextField(required=False)  # from appointment url

    reg_info = DocJsonField(is_parse_from_api=False, required=False)

    __api_to_db_mapping__ = {'id': '_id'}


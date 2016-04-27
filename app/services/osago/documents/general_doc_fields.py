# -*- coding: utf-8 -*-

from fw.documents.fields.complex_doc_fields import ObjectRefField
from fw.documents.fields.general_doc_fields import general_doc_field, GeneralField
from fw.documents.fields.simple_doc_fields import DocTextField, DocEnumField, DocIntField


@general_doc_field
class DriveObject(GeneralField):
    name = DocTextField(max_length=70, required=False)
    surname = DocTextField(max_length=70, required=False)
    patronymic = DocTextField(max_length=70, required=False)
    sex = DocEnumField(enum_cls='GenderEnum')


@general_doc_field
class CarWithDriver(GeneralField):
    driver = DriveObject()
    car_brand = DocTextField(max_length=100, required=False)
    car_number = DocTextField(max_length=10, required=False)

@general_doc_field
class DocLawSuitDocPageCount(GeneralField):
    page = DocEnumField(enum_cls='OsagoDocTypeEnum')
    pagecount = DocIntField(min_val=0, max_val=1000, required=True)

@general_doc_field
class CourtLawsuitDocInfo(GeneralField):
    doc_name = DocEnumField(enum_cls='CourtLawsuitDocEnum')
    originals = DocIntField(min_val=0, max_val=1000)
    copies = DocIntField(min_val=0, max_val=1000)
    title = DocTextField()
    pagecount = DocIntField(min_val=0, max_val=1000)

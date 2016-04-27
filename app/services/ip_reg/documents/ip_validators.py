# -*- coding: utf-8 -*-
from flask.globals import current_app
from custom_exceptions import InvalidFieldValueException
from fw.catalogs.models import OkvadObject


def _push_error(field_name, code):
    next_exc = InvalidFieldValueException("")
    next_data = {
        "field": field_name,
        "error_code": code
    }
    next_exc.ext_data.append(next_data)
    raise next_exc


def ip_eshn_tax_type(eshn_doc):
    eshn_doc = eshn_doc.value
    job_main_code = eshn_doc['job_main_code'].db_value()

    okvad = OkvadObject.query.filter_by(okved=job_main_code).scalar()
    if not okvad or okvad.nalog != 'eshn':
        _push_error("taxation_type", 5)

    return True


def ip_usn_tax_type(usn_doc):
    usn_doc = usn_doc.value
    job_main_code = usn_doc['job_main_code'].db_value()

    okvad = OkvadObject.query.filter_by(okved=job_main_code).scalar()
    if not okvad or okvad.nalog not in ('usn', 'eshn'):
        _push_error("taxation_type", 5)

    return True

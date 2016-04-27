# -*- coding: utf-8 -*-
from custom_exceptions import InvalidFieldValueException


def _push_error(field_name, code):
    next_exc = InvalidFieldValueException("")
    next_data = {
        "field": field_name,
        "error_code": code
    }
    next_exc.ext_data.append(next_data)
    raise next_exc



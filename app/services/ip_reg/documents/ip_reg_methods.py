# -*- coding: utf-8 -*-
from datetime import datetime
from flask import current_app
from common_utils import num_word
from fw.catalogs.models import BikCatalog
from services.ifns.data_model.enums import IfnsRegStatusEnum
from services.ifns.data_model.models import IfnsBookingObject


def get_company_registration_info(batch_id=None):
    null_value = {
        "status": IfnsRegStatusEnum.IRS_UNKNOWN
    }
    if not batch_id:
        return null_value
    booking = IfnsBookingObject.query.filter(
        IfnsBookingObject.batch_id==batch_id,
        # todo: add ifns service id, reg_date date range
        IfnsBookingObject.reg_info.__ne__(None)
    ).first()
    if booking:
        result = {
            "status": booking.reg_info.get('status', 'unknown')
        }
        try:
            reg_date = booking.reg_info.get('reg_date', None)
            if isinstance(reg_date, basestring):
                reg_date = datetime.strptime(reg_date, "%d.%m.%Y")
            if reg_date:
                result['reg_date'] = reg_date
        except Exception:
            current_app.logger.exception(u"Failed to get date")

        try:
            ogrn = booking.reg_info.get('ogrnip', None)
            if isinstance(ogrn, basestring):
                ogrn = int(ogrn)
            if ogrn is not None:
                result['ogrnip'] = ogrn
        except Exception:
            current_app.logger.exception(u"Failed to get ogrnip")

        return result

    return null_value


def get_bank_info(bank_bik=None):
    if not bank_bik:
        return {}

    bank_bik = unicode(bank_bik)
    if not bank_bik.isdigit():
        return {}

    info = BikCatalog.query.filter_by(bik=bank_bik).scalar()
    return {
        '_id': info.id,
        'name': info.name,
        'okpo': info.okpo,
        'bik': info.bik,
        'phone': info.phone,
        'address': info.address,
        'kor_account': info.kor_account
    } or {}


def num_to_text(value):
    if not isinstance(value, int):
        return

    return num_word(value)
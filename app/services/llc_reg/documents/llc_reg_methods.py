# -*- coding: utf-8 -*-
from datetime import datetime
from decimal import Decimal
from flask import current_app
from common_utils import num_word
from fw.catalogs.models import BikCatalog
from services.ifns.data_model.enums import IfnsRegStatusEnum
from services.ifns.data_model.models import IfnsBookingObject
from services.llc_reg.documents.enums import FounderStrTypeEnum


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
            ogrn = booking.reg_info.get('ogrn', None)
            if ogrn is not None:
                result['ogrn'] = ogrn
        except Exception:
            current_app.logger.exception(u"Failed to get ogrn")

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
    } if info else {}


def num_to_text(value):
    if not isinstance(value, int):
        return

    return num_word(value)

def _get_person_full_name(person_id):
    from fw.documents.db_fields import PrivatePersonDbObject
    person = PrivatePersonDbObject.query.filter_by(id=person_id).first()
    if person:
        full_name = u"%s %s" % (person.surname, person.name)
        if person.patronymic:
            full_name += u" " + person.patronymic
        return full_name

def check_founder_has_same_fio(founders=None, founder=None):
    if not founder or not founders:
        return False

    if len(founders) < 2:
        return False

    if founder.get('type', None) != FounderStrTypeEnum.FST_PERSON:
        return False

    for founder_item in founders:
        item = founder_item.get('founder', {})
        if item.get('type', None) != FounderStrTypeEnum.FST_PERSON:
            continue

        if founder['_id'] == item['_id']:
            continue
        founder_name = _get_person_full_name(founder['_id'])
        item_name = _get_person_full_name(item['_id'])
        if founder_name == item_name:
            return True

    return False


def is_starter_capital_dividable(founder_share=None, starter_capital=None, share_type=None):
    if not founder_share or not starter_capital or share_type != "fraction":
        return False
    starter_capital_value = starter_capital
    # noinspection PyTypeChecker
    if '.' not in founder_share:
        founder_share = founder_share + '.0'
    flor = int(founder_share.split('.')[1])
    if flor == 0:
        return False
    div_result = starter_capital_value / flor
    div_str = str(div_result)
    if '.' not in div_str:
        return True
    min, maj = div_str.split('.')
    return len(maj) < 3

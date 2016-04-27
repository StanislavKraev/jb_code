# -*- coding: utf-8 -*-
from flask import current_app
from common_utils import get_russian_month_skl, num_word
from fw.documents.address_enums import RFRegionsEnum
from services.ip_reg.documents.enums import IPDocumentDeliveryTypeStrEnum
from services.llc_reg.documents.enums import GovernmentFounderTypeEnum, FounderTypeEnum, JSCMemberTypeEnum


class ShortDistrictTypeAdapter(object):
    @staticmethod
    def adapt(value):
        if not hasattr(value, 'api_value'):
            return u""
        return value.api_value()


class RFRegionNumberAdapter(object):
    @staticmethod
    def adapt(value):
        if value is None:
            return None
        if isinstance(value, basestring):
            return RFRegionsEnum._NUMBERS.get(value, u"")
        return RFRegionsEnum._NUMBERS.get(value.api_value(), u"")


class ShortCityTypeAdapter(object):
    @staticmethod
    def adapt(value):
        if not hasattr(value, 'api_value'):
            return u""
        return value.api_value()


class ShortVillageTypeAdapter(object):
    @staticmethod
    def adapt(value):
        if not hasattr(value, 'api_value'):
            return u""
        return value.api_value()


class ShortStreetTypeAdapter(object):
    @staticmethod
    def adapt(value):
        if not hasattr(value, 'api_value'):
            return u""
        return value.api_value()


class InternalPassportAdapter(object):
    @staticmethod
    def adapt(value):
        value = value.replace(u' ', u'')
        return u"%s %s %s" % (value[:2], value[2:4], value[4:])


class CitizenshipToNumberAdapter(object):
    @staticmethod
    def adapt(value):
        if value.lower() in {u'россиия', u'рф', u'российская федерация'}:
            return 1
        elif value:
            return 2
        return 3


class CountryCodeRusAdapter(object):
    @staticmethod
    def adapt(value):
        if value == 643:
            return 1
        elif value:
            return 2
        return 3


class GenderToNumberAdapter(object):
    @staticmethod
    def adapt(value):
        if value == 'male':
            return 1
        elif value == 'female':
            return 2
        return 0


class GovernmentFounderTypeNumberAdapter(object):
    @staticmethod
    def adapt(value):
        if value == GovernmentFounderTypeEnum.GF_RUSSIA:
            return 1
        if value == GovernmentFounderTypeEnum.GF_REGION:
            return 2
        if value == GovernmentFounderTypeEnum.GF_MUNICIPALITY:
            return 3
        return u""


class DocumentDeliveryNumberAdapter(object):
    @staticmethod
    def adapt(value):
        if value is None:
            return None
        if isinstance(value, basestring):
            return value
        return value.api_value()


class DocumentObtainNumberAdapter(object):
    @staticmethod
    def adapt(value):
        if value == IPDocumentDeliveryTypeStrEnum.IP_DDT_IN_PERSON:
            return 1
        elif value == IPDocumentDeliveryTypeStrEnum.IP_DDT_RESPONSIBLE_PERSON:
            return 2
        elif value == IPDocumentDeliveryTypeStrEnum.IP_DDT_MAIL:
            return 3


class FounderTypeNumberAdapter(object):
    @staticmethod
    def adapt(value):
        if value == FounderTypeEnum.FT_PERSON:
            return 1
        elif value == FounderTypeEnum.FT_COMPANY:
            return 2
        current_app.logger.warn(u"FounderTypeNumberAdapter failed to adapt value %s" % unicode(value))
        return u""


class JSCMemberTypeNumberAdapter(object):
    @staticmethod
    def adapt(value):
        if value == JSCMemberTypeEnum.JSCMT_NEW_JSC:
            return 1
        elif value == JSCMemberTypeEnum.JSCMT_REGISTRATOR:
            return 2
        return u""


class UsnTaxTypeAdapter(object):
    @staticmethod
    def adapt(value):
        if not hasattr(value, 'api_value'):
            return u""
        return value.api_value()


class MonthRusNameDeclAdapter(object):
    @staticmethod
    def adapt(value):
        if not isinstance(value, int):
            return ""
        if value < 1 or value > 12:
            return ""
        return get_russian_month_skl(value)


class NumToTextAdapter(object):
    @staticmethod
    def adapt(value):
        if not isinstance(value, int):
            return

        return num_word(value)
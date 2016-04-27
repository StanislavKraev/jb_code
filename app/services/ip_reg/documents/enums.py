# -*- coding: utf-8 -*-


class IPRegistrationWayEnum(object):
    IP_RW_IN_PERSON = "in_person"
    IP_RW_RESPONSIBLE_PERSON = "responsible_person"
    IP_RW_NOTARY = "notary"
    IP_RW_MAIL = "mail"

    _NAMES = {
        IP_RW_IN_PERSON: u"лично",
        IP_RW_RESPONSIBLE_PERSON: u"ответсвенное лицо",
        IP_RW_MAIL: u"по почте",
        IP_RW_NOTARY: u"нотариус"
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return IPRegistrationWayEnum._NAMES.get(value, u"")


class IPDocumentDeliveryTypeStrEnum(object):
    IP_DDT_IN_PERSON = "in_person"
    IP_DDT_RESPONSIBLE_PERSON = "responsible_person"
    IP_DDT_MAIL = "mail"

    _NAMES = {
        IP_DDT_IN_PERSON: u"лично",
        IP_DDT_RESPONSIBLE_PERSON: u"ответсвенное лицо",
        IP_DDT_MAIL: u"по почте",
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return IPDocumentDeliveryTypeStrEnum._NAMES.get(value, u"неизвестно")


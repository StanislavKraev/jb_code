# -*- coding: utf-8 -*-


class IfnsRegStatusEnum(object):
    IRS_REGISTERED = "registered"
    IRS_REGISTRATION_DECLINED = "registration_declined"
    IRS_PROGRESS = "progress"
    IRS_UNKNOWN = "unknown"

    _NAMES = {
        IRS_REGISTERED: IRS_REGISTERED,
        IRS_REGISTRATION_DECLINED: IRS_REGISTRATION_DECLINED,
        IRS_PROGRESS: IRS_PROGRESS,
        IRS_UNKNOWN: IRS_UNKNOWN
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return IfnsRegStatusEnum._NAMES.get(value, u"unknown")

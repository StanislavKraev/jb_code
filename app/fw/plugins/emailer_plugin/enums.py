# -*- coding: utf-8 -*-


class MailTypeEnum(object):
    MT_SOME_EMAIL = 'simple_mail'

    _ALL = {
        MT_SOME_EMAIL
    }

    @classmethod
    def validate(cls, value):
        return value in cls._ALL

    @staticmethod
    def get_name(value):
        return value


class MailTargetEnum(object):

    MTA_SPECIFIED = 'specified_users'
    MTA_BATCH_OWNER = 'batch_owner'
    MTA_EVENT_DATA_FIELD = 'event_data_field'

    _ALL = {
        MTA_SPECIFIED,
        MTA_BATCH_OWNER,
        MTA_EVENT_DATA_FIELD
    }

    @classmethod
    def validate(cls, value):
        return value in cls._ALL

    @staticmethod
    def get_name(value):
        return value

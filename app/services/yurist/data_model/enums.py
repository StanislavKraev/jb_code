# -*- coding: utf-8 -*-


class YuristBatchCheckStatus(object):
    YBS_NEW = "new"
    YBS_IN_PROGRESS = "progress"
    YBS_WAIT = "wait"
    YBS_SUCCESS = "success"
    YBS_FAILED = "failed"
    YBS_REFUSED = "refused"

    _NAMES = {
        YBS_NEW: u"проверки не было",
        YBS_IN_PROGRESS: u"в процессе",
        YBS_SUCCESS: u"проверка закончена успешно",
        YBS_FAILED: u"проверка закончена с ошибками",
        YBS_REFUSED: u"отказ от проверки",
        YBS_WAIT: u"ожидает перехода в статус 'в процессе'"
    }

    FINAL_STATUSES = [YBS_REFUSED, YBS_SUCCESS, YBS_FAILED]

    @classmethod
    def validate(cls, value):
        return value in YuristBatchCheckStatus._NAMES

    @staticmethod
    def get_name(value):
        return YuristBatchCheckStatus._NAMES.get(value, u"")

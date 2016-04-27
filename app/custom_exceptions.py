# -*- coding: utf-8 -*-
from fw.api.errors import ApiBaseError


class MissingRequiredFieldException(ApiBaseError):
    ERROR_CODE = 4
    HTTP_ERROR_CODE = 400
    ERROR_MESSAGE = u"Пропущено обязательное поле %s"

    def __init__(self, field_name, *args, **kwargs):
        super(MissingRequiredFieldException, self).__init__(field_name, *args, **kwargs)
        self.field_name = field_name
        self.ext_data = kwargs.get('ext_data', [])

    def get_error_message(self):
        return self.ERROR_MESSAGE % self.field_name


class InvalidFieldValueException(ApiBaseError):
    ERROR_CODE = 5
    HTTP_ERROR_CODE = 400
    ERROR_MESSAGE = u"Недопустимое значение поля %s"

    def __init__(self, field_name=u"", *args, **kwargs):
        super(InvalidFieldValueException, self).__init__(field_name, *args, **kwargs)
        self.field_name = field_name
        self.ext_data = []

    def get_error_message(self):
        if not self.field_name and self.ext_data:
            return self.ERROR_MESSAGE % unicode(self.ext_data)
        return self.ERROR_MESSAGE % self.field_name


class InvalidRawFieldValueException(ApiBaseError):
    ERROR_CODE = 5
    HTTP_ERROR_CODE = 400
    ERROR_MESSAGE = u"Недопустимое значение поля %s"

    def __init__(self, field_name, *args, **kwargs):
        super(InvalidRawFieldValueException, self).__init__(field_name, *args, **kwargs)
        self.field_name = field_name
        self.ext_data = []

    def get_error_message(self):
        return self.ERROR_MESSAGE % self.field_name


class ArrayFieldTooShortException(Exception):
    def __init__(self, field_name, *args, **kwargs):
        super(ArrayFieldTooShortException, self).__init__(field_name, *args, **kwargs)
        self.field_name = field_name
        self.ext_data = []


class ArrayFieldTooLongException(Exception):
    def __init__(self, field_name, *args, **kwargs):
        super(ArrayFieldTooLongException, self).__init__(field_name, *args, **kwargs)
        self.field_name = field_name
        self.ext_data = []


class NotInitialized(Exception):
    ERROR_CODE = 4


class NotMineException(Exception):
    pass


class FileNotFound(Exception):
    pass


class CacheMiss(Exception):
    pass
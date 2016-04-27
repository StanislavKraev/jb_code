# -*- coding: utf-8 -*-


class ApiBaseError(Exception):

    def __init__(self, *args, **kwargs):
        super(ApiBaseError, self).__init__()
        self.ext_data = []

    @classmethod
    def get_error_code(cls):
        return cls.ERROR_CODE

    def get_error_message(self):
        return self.ERROR_MESSAGE

    @classmethod
    def get_http_error_code(cls):
        return cls.HTTP_ERROR_CODE


class BadRequestError(ApiBaseError):

    ERROR_CODE = 1
    HTTP_ERROR_CODE = 400
    ERROR_MESSAGE = u"Неверный запрос"


class HttpNotSupportedError(ApiBaseError):

    ERROR_CODE = 2
    HTTP_ERROR_CODE = 400
    ERROR_MESSAGE = u"Метод доступен только через защищенное соединение"


class BadRequestFormatError(ApiBaseError):

    ERROR_CODE = 3
    HTTP_ERROR_CODE = 400
    ERROR_MESSAGE = u"Неправильный формат входных данных %s"

    def __init__(self, parameter_name):
        super(BadRequestFormatError, self).__init__()
        self.parameter_name = parameter_name

    def get_error_message(self):
        return self.ERROR_MESSAGE % self.parameter_name


class MissingRequiredParameter(ApiBaseError):

    ERROR_CODE = 4
    HTTP_ERROR_CODE = 400
    ERROR_MESSAGE = u"Пропущен обязательный параметр %s"

    def __init__(self, parameter_name):
        super(MissingRequiredParameter, self).__init__()
        self.parameter_name = parameter_name
        self.ext_data = []

    def get_error_message(self):
        return self.ERROR_MESSAGE % self.parameter_name


class InvalidParameterValue(ApiBaseError):

    ERROR_CODE = 5
    HTTP_ERROR_CODE = 400
    ERROR_MESSAGE = u"Недопустимое значение параметра %s"

    def __init__(self, parameter_name):
        super(InvalidParameterValue, self).__init__()
        self.parameter_name = parameter_name
        self.ext_data = []

    def get_error_message(self):
        return self.ERROR_MESSAGE % self.parameter_name


class ParameterLengthTooLong(ApiBaseError):

    ERROR_CODE = 6
    HTTP_ERROR_CODE = 400
    ERROR_MESSAGE = u"Длина %s превышает допустимое значение"

    def __init__(self, parameter_name):
        super(ParameterLengthTooLong, self).__init__()
        self.parameter_name = parameter_name

    def get_error_message(self):
        return self.ERROR_MESSAGE % self.parameter_name

class FileToLarge(ApiBaseError):

    ERROR_CODE = 10
    HTTP_ERROR_CODE = 400
    ERROR_MESSAGE = u"Превышен допустимый размер файла"

class NotAuthorized(ApiBaseError):

    ERROR_CODE = 100
    HTTP_ERROR_CODE = 403
    ERROR_MESSAGE = u"Пользователь не авторизован"


class InvalidLoginOrPassword(ApiBaseError):

    ERROR_CODE = 102
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Неверная пара логин/пароль"


class SocialAuthError(ApiBaseError):

    ERROR_CODE = 104
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Ошибка авторизации через соцсеть"


class UserNotFound(ApiBaseError):

    ERROR_CODE = 105
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Пользователь не найден"


class ActivationAttemptsCountExceeded(ApiBaseError):

    ERROR_CODE = 106
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Превышено количество попыток использования кода подтверждения"


class RecoveryAttemptsCountExceeded(ApiBaseError):

    ERROR_CODE = 107
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Превышено количество попыток восстановления пароля"


class ActivationCodeExpiredOrInvalid(ApiBaseError):

    ERROR_CODE = 108
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Истек период действия кода подтверждения или код неверен"


class InvalidPassword(ApiBaseError):

    ERROR_CODE = 109
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Пароль должен быть от 6 до 32 символов"


class DuplicateEmail(ApiBaseError):

    ERROR_CODE = 110
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Указанный email уже занят"


class DuplicateMobile(ApiBaseError):

    ERROR_CODE = 111
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Указанный телефон уже занят"


class EmailIsNotConfirmed(ApiBaseError):

    ERROR_CODE = 112
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Адрес электронной почты не подтвержден"


class MobileIsNotConfirmed(ApiBaseError):

    ERROR_CODE = 113
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Телефонный номер не подтвержден"


class InvalidCurrentPassword(ApiBaseError):

    ERROR_CODE = 114
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Текущий пароль указан неверно"
    

class RenewAuthTokenError(ApiBaseError):

    ERROR_CODE = 120
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Access token устарел. Необходимо получить новый."

class NoPushTokenError(ApiBaseError):

    ERROR_CODE = 121
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Не указан push-токен для push уведомлений"


class SocialServiceRedirect(Exception):
    def __init__(self, url, *args, **kwargs):
        super(SocialServiceRedirect, self).__init__(*args, **kwargs)
        self.url = url


class BatchNotFound(ApiBaseError):

    ERROR_CODE = 200
    HTTP_ERROR_CODE = 404
    ERROR_MESSAGE = u"Пакет документов не найден"


class DocumentNotFound(ApiBaseError):

    ERROR_CODE = 201
    HTTP_ERROR_CODE = 404
    ERROR_MESSAGE = u"Документ не найден"


class DocumentBatchFinalizedError(ApiBaseError):

    ERROR_CODE = 202
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Невозможно изменить документ в финализированном пакете"


class DocumentBatchFinalizationError(ApiBaseError):

    ERROR_CODE = 203
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Пакет документов не может быть финализирован"

class DocumentBatchDefinalizationError(ApiBaseError):

    ERROR_CODE = 204
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Пакет документов не может быть дефинализирован"


class DocumentBatchUpdateError(ApiBaseError):

    ERROR_CODE = 205
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Пакет документов не может быть обновлен"


class DuplicatedStoredObjectsChangesFoundException(ApiBaseError):

    ERROR_CODE = 206
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Хранимые сущности изменились. Требуется передать флаг force для дефинализации"


class EntityNotFound(ApiBaseError):

    ERROR_CODE = 207
    HTTP_ERROR_CODE = 404
    ERROR_MESSAGE = u"Хранимая сущность не найдена"

class NotariusBookingNotFound(ApiBaseError):

    ERROR_CODE = 208
    HTTP_ERROR_CODE = 404
    ERROR_MESSAGE = u"Запись к нотариусу не найдена"

class IfnsBookingNotFound(ApiBaseError):

    ERROR_CODE = 209
    HTTP_ERROR_CODE = 404
    ERROR_MESSAGE = u"Запись в налоговую не найдена"

class PaidBatchUpdateError(ApiBaseError):

    ERROR_CODE = 211
    HTTP_ERROR_CODE = 403
    ERROR_MESSAGE = u"Данное изменение не доступно для оплаченного пакета документов"

class NotariusNotFound(ApiBaseError):
    ERROR_CODE = 300
    HTTP_ERROR_CODE = 404
    ERROR_MESSAGE = u"Данный нотариус не найден"


class IfnsNotFound(ApiBaseError):
    ERROR_CODE = 301
    HTTP_ERROR_CODE = 404
    ERROR_MESSAGE = u"Данная налоговая не найдена"


class InvalidCodeProvided(ApiBaseError):
    ERROR_CODE = 302
    HTTP_ERROR_CODE = 403
    ERROR_MESSAGE = u"Указан неверный код"


class MobileNotSet(ApiBaseError):
    ERROR_CODE = 303
    HTTP_ERROR_CODE = 403
    ERROR_MESSAGE = u"Мобильный телефон не задан"


class MobileNotConfirmed(ApiBaseError):
    ERROR_CODE = 304
    HTTP_ERROR_CODE = 403
    ERROR_MESSAGE = u"Мобильный телефон не подтвержден"


class MaximumRegistrationsExceeded(ApiBaseError):
    ERROR_CODE = 305
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Превышено количество регистраций в данный промежуток времени. Попробуйте позже"


class DuplicateBookingAtTheSameTime(ApiBaseError):
    ERROR_CODE = 306
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Вы уже записались на данную услугу на то же время"


class DayBusyOrHolliday(ApiBaseError):

    ERROR_CODE = 307
    HTTP_ERROR_CODE = 200

    def __init__(self, dt, *args, **kwargs):
        self.dt = dt
        self.ERROR_MESSAGE = u"День полностью занят или выходной (%s)" % self.dt.strftime("%Y-%m-%d")
        super(DayBusyOrHolliday, self).__init__(*args, **kwargs)

class IfnsSessionExpired(ApiBaseError):
    ERROR_CODE = 308
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Сессия с сервером ИФНС устарела"


class IfnsServiceUnavailable(ApiBaseError):
    ERROR_CODE = 309
    HTTP_ERROR_CODE = 200
    ERROR_MESSAGE = u"Сервер ИФНС недоступен"


class ServerUnavailable(ApiBaseError):

    HTTP_ERROR_CODE = 503
    ERROR_MESSAGE = u"Server temporarily unavailable. Please try again later."


class ServerError(ApiBaseError):

    HTTP_ERROR_CODE = 500
    ERROR_MESSAGE = u"Server error."
    ERROR_CODE = 500


class SkipException(Exception):
    pass


class PostTrackingItemNotFound(ApiBaseError):
    ERROR_CODE = 501
    HTTP_ERROR_CODE = 404
    ERROR_MESSAGE = u"Почтовое отправление не найдено"


class DuplicateIdError(Exception):
    pass

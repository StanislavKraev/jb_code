# -*- coding: utf-8 -*-
from datetime import datetime
from functools import wraps
from bson.objectid import ObjectId
import flask
from flask import current_app, request
import re
from unidecode import unidecode
from fw.api import errors
from fw.auth.models import ConfirmationLinkTypeEnum
from fw.auth.social_services.social_models import SocialServiceEnum


class ArgumentValidator(object):
    def __init__(self, required=True, default_value=None, min_length=None, max_length=None, raise_exception=None):
        self.required = required
        self.default_value = default_value
        self.min_length = min_length
        self.max_length = max_length
        self.application = None
        self.raise_exception = raise_exception
        if self.default_value and not self._validate(self.default_value):
            raise ValueError(default_value)

    def validation_result(self, result):
        if not result and self.raise_exception:
            raise self.raise_exception()
        return result

    def validate(self, argument):
        return self._validate(argument)

    def _validate(self, argument):
        if self.required and argument is None:
            return self.validation_result(False)

        if argument is None:
            return self.validation_result(False)

        if self.min_length and len(argument) < self.min_length:
            return self.validation_result(False)

        if self.max_length and len(argument) > self.max_length:
            return self.validation_result(False)

        return self.validation_result(True)

    def get_value(self, argument):
        if argument is None:
            return self.default_value
        return argument

    def __or__(self, other):
        if not isinstance(other, ArgumentValidator):
            raise ValueError("Invalid argument")

        return OneOfTypeArgumentValidator(self, other)


class OneOfTypeArgumentValidator(ArgumentValidator):
    # noinspection PyMissingConstructor
    def __init__(self, validator1, validator2):
        super(OneOfTypeArgumentValidator, self).__init__()

        self.val1 = validator1
        self.val2 = validator2

        self.val1.required = False
        self.val2.required = False

    def validate(self, argument):
        self.val1.application = self.application
        self.val2.application = self.application
        return self.validation_result(self.val1.validate(argument) or self.val2.validate(argument))

    def get_value(self, argument):
        if argument is None:
            return False
        if self.val1.validate(argument):
            return self.val1.get_value(argument)
        return self.val2.get_value(argument)


def _validate(arg_name, validator, required_args):
    if isinstance(validator, ArgumentValidator):
        validator.application = current_app
        try:
            if not len(request.form) and not len(request.args) and request.data:
                from werkzeug.urls import url_decode

                args = url_decode(request.data)
                if arg_name not in args:
                    raise KeyError(arg_name)
                value = args[arg_name]
            else:
                value = request.form[arg_name] if arg_name in request.form else request.args[arg_name]
            if not validator.validate(value):
                raise errors.InvalidParameterValue(arg_name)
        except KeyError:
            if validator.required:
                raise errors.MissingRequiredParameter(arg_name)
            value = validator.default_value
        required_args[arg_name] = validator.get_value(value) if value is not None else None
    else:
        raise ValueError("Invalid parameter in argument validator description: %s" % str(validator))


def validate_arguments(*arguments_list, **arguments_dict):
    def _decorator(function):
        wrapped = function

        @wraps(function)
        def wrapper():
            required_args = {}
            for arg_name, validator in arguments_dict.items():
                _validate(arg_name, validator, required_args)

            for validator in arguments_list:
                if isinstance(validator, AtLeastOneOfValidator):
                    if not validator.arguments_dict:
                        raise ValueError(
                            "Invalid parameter in argument validator description: AtLeastOneOfValidator has no items.")

                    required_args_part = {}
                    first_arg_name = u""
                    for arg_name, single_validator in validator.arguments_dict.items():
                        single_validator.required = False
                        single_validator.default = None
                        if not first_arg_name:
                            first_arg_name = arg_name
                        _validate(arg_name, single_validator, required_args_part)
                    if not required_args_part:
                        raise errors.MissingRequiredParameter(first_arg_name)
                    required_args.update(required_args_part)

            return wrapped(**required_args)

        return wrapper

    return _decorator



class AtLeastOneOfValidator(object):
    def __init__(self, **kwargs):
        self.arguments_dict = kwargs


class IntValidator(ArgumentValidator):
    def __init__(self, min_val=None, max_val=None, **kwargs):
        super(IntValidator, self).__init__(**kwargs)
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, argument):
        if not super(IntValidator, self).validate(argument):
            return False

        try:
            int_val = int(argument)
        except ValueError:
            return False

        if self.min_val is not None:
            if int_val < self.min_val:
                return False

        if self.max_val is not None:
            if int_val > self.max_val:
                return False

        return True

    def get_value(self, argument):
        return int(argument)


class ClientTypeValidator(ArgumentValidator):
    CLIENT_TYPES = ('android', 'ios')

    def validate(self, argument):
        if not super(ClientTypeValidator, self).validate(argument):
            return False
        return self.validation_result(argument in ClientTypeValidator.CLIENT_TYPES)


class EmailAddressValidator(ArgumentValidator):
    def __init__(self, max_length=100, **kwargs):
        self.max_length = max_length
        super(EmailAddressValidator, self).__init__(**kwargs)

    def validate(self, argument):
        if not super(EmailAddressValidator, self).validate(argument):
            return False

        rus_chars = u"абвгдеёжзийклмнопрстуфхцчшщьыъэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ"
        email_re = ur"^[a-zA-Z" + rus_chars + ur"0-9._%\-+]+\@[a-zA-Z" + rus_chars + ur"0-9._%-]+\.[a-zA-Z" + rus_chars + ur"]{2,}$"
        if re.match(email_re, argument, re.IGNORECASE) is not None:
            return True

        email_re = r"^.*\<[a-zA-Z" + rus_chars + ur"0-9._%\-+]+\@[a-zA-Z" + rus_chars + ur"0-9._%-]+\.[a-zA-Z" + rus_chars + ur"]{2,}>$"
        return self.validation_result(re.match(email_re, argument, re.IGNORECASE) is not None)


class MobileNumberValidator(ArgumentValidator):
    def __init__(self, max_length=20, **kwargs):
        self.max_length = max_length
        super(MobileNumberValidator, self).__init__(**kwargs)

    def validate(self, argument):
        if not super(MobileNumberValidator, self).validate(argument):
            return False

        return self.validation_result(
            (argument[0] == '+' and argument[1:].isdigit()) or (argument.isdigit() and argument[0] == "8"))

    def get_value(self, argument):
        if not argument or len(argument) < 2:
            return argument
        return ("+7" + argument[1:]) if argument[0] == '8' else argument


class HumanNameValidator(ArgumentValidator):
    ALLOWED_CHARS = u'.,-\'" абвгдеёжзийклмнопрстуфхцчшщьыъэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ0123456789'
    ALLOWED_CHARS_ENG = u'.,-\'" абвгдеёжзийклмнопрстуфхцчшщьыъэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def __init__(self, max_length=100, allow_english_chars=False, **kwargs):
        self.max_length = max_length
        self.allow_english_chars = allow_english_chars
        super(HumanNameValidator, self).__init__(**kwargs)

    def validate(self, argument):
        if not super(HumanNameValidator, self).validate(argument):
            return False

        name = argument.strip()
        if not name:
            return self.validation_result(False)

        if self.max_length is not None and len(name) > self.max_length:
            return self.validation_result(False)

        test_set = HumanNameValidator.ALLOWED_CHARS if not self.allow_english_chars else HumanNameValidator.ALLOWED_CHARS_ENG
        for c in name:
            if c not in test_set:
                return self.validation_result(False)
        return True

    def get_value(self, argument):
        return argument.strip()


class LoginValidator(ArgumentValidator):
    def __init__(self, max_length=20, min_length=5, **kwargs):
        self.max_length = max_length
        self.min_length = min_length
        super(LoginValidator, self).__init__(**kwargs)

    def validate(self, argument):
        if not super(LoginValidator, self).validate(argument):
            return False

        name = argument.strip()
        if not name:
            return self.validation_result(False)

        if self.max_length is not None and len(name) > self.max_length:
            return self.validation_result(False)

        for c in name:
            if c.lower() not in 'abcdefghijklmnopqrstuvwxyz0123456789':
                return self.validation_result(False)
        return True

    def get_value(self, argument):
        return argument.strip()


class PasswordValidator(ArgumentValidator):
    def __init__(self, min_length=6, max_length=32, **kwargs):
        super(PasswordValidator, self).__init__(min_length=min_length, max_length=max_length, **kwargs)


class AccessTokenValidator(ArgumentValidator):
    def __init__(self, min_length=40, max_length=300, **kwargs):
        self.min_length = min_length
        self.max_length = max_length
        super(AccessTokenValidator, self).__init__(**kwargs)

    def validate(self, argument):
        if not super(AccessTokenValidator, self).validate(argument):
            return False

        if '@' in argument or '+' in argument:
            return self.validation_result(False)

        return True


class FloatTypeValidator(ArgumentValidator):
    def validate(self, argument):
        if not super(FloatTypeValidator, self).validate(argument):
            return False

        try:
            float(argument)
        except ValueError:
            return self.validation_result(False)

        return True

    def get_value(self, argument):
        return float(argument)


class BoolTypeValidator(ArgumentValidator):
    def validate(self, argument):
        if not super(BoolTypeValidator, self).validate(argument):
            return False

        if argument.lower() in ("true", "t", "false", "f"):
            return True

        return self.validation_result(False)

    def get_value(self, argument):
        argument = argument.lower()
        if not argument:
            return None
        elif argument in ("true", "t"):
            return True
        elif argument in ("false", "f"):
            return False

        return None


class CarNumberValidator(ArgumentValidator):
    # basic number
    CAR_NUMBER_RE1 = r"^\w{1}\d{3}\w{2} \d{2,3}$"
    # commercial transport
    CAR_NUMBER_RE2 = r"^\w{2}\d{4} \d{2,3}$"

    def validate(self, argument):
        if not super(CarNumberValidator, self).validate(argument):
            return False

        argument = unidecode(argument).upper()
        number_matched = re.match(CarNumberValidator.CAR_NUMBER_RE1, argument, re.IGNORECASE) or \
                         re.match(CarNumberValidator.CAR_NUMBER_RE2, argument, re.IGNORECASE) or None
        if number_matched is None:
            return self.validation_result(False)
        return True

    def get_value(self, argument):
        argument = unidecode(argument).upper()
        return unicode(argument)


class DateTimeValidator(ArgumentValidator):
    FORMAT = '%Y-%m-%dT%H:%M:%S'

    def validate(self, argument):
        if not super(DateTimeValidator, self).validate(argument):
            return False

        if "." in argument:
            tmpl = '%Y-%m-%dT%H:%M:%S.%f'
        else:
            tmpl = '%Y-%m-%dT%H:%M:%S'
        try:
            datetime.strptime(argument, tmpl)
        except ValueError:
            return self.validation_result(False)
        return True

    def get_value(self, argument):
        if "." in argument:
            tmpl = '%Y-%m-%dT%H:%M:%S.%f'
        else:
            tmpl = '%Y-%m-%dT%H:%M:%S'
        return datetime.strptime(argument, tmpl)


class DateTypeValidator(ArgumentValidator):
    FORMAT = '%Y-%m-%d'

    def validate(self, argument):
        if not super(DateTypeValidator, self).validate(argument):
            return False

        try:
            datetime.strptime(argument, DateTypeValidator.FORMAT)
        except ValueError:
            return self.validation_result(False)
        return True

    def get_value(self, argument):
        return datetime.strptime(argument, DateTypeValidator.FORMAT)


class PhotoDocListValidator(ArgumentValidator):
    def validate(self, argument):
        if not super(PhotoDocListValidator, self).validate(argument):
            return False

        try:
            data = flask.json.loads(argument)
        except ValueError:
            # raise ValueError(str(argument) + "  " + str(type(argument)))
            return self.validation_result(False)

        if not isinstance(data, list):
            return self.validation_result(False)

        for photo in data:
            # print str(photo)
            if "id" in photo and "shoot_time" in photo and "coord" in photo:
                try:
                    unicode(photo['id'])
                except ValueError:
                    return self.validation_result(False)
                    # check shoot time
                if not DateTimeValidator().validate(photo['shoot_time']):
                    return self.validation_result(False)
                    # check coords
                coord = photo['coord']
                if not isinstance(coord, dict):
                    return self.validation_result(False)
                if not "lat" in coord or not "lon" in coord:
                    return self.validation_result(False)
                if not FloatTypeValidator().validate(coord['lat']) or not FloatTypeValidator().validate(coord['lon']):
                    return self.validation_result(False)
            else:
                return self.validation_result(False)
        return True

    def get_value(self, argument):
        data_list = flask.json.loads(argument)
        for data in data_list:
            data['id'] = unicode(data['id'])
            data['shoot_time'] = DateTimeValidator().get_value(data['shoot_time'])
            data['coord']['lat'] = FloatTypeValidator().get_value(data['coord']['lat'])
            data['coord']['lon'] = FloatTypeValidator().get_value(data['coord']['lon'])
        return data_list


class ConfirmationCodeValidator(ArgumentValidator):
    def validate(self, argument):
        if not super(ConfirmationCodeValidator, self).validate(argument):
            return False

        code_len = len(argument)
        if code_len == self.application.config['max_activation_link_length']:
            return self.validation_result(argument.isalnum())

        if code_len == self.application.config['digital_activation_link_length']:
            return self.validation_result(argument.isdigit())

        return self.validation_result(False)


class JsonValidator(ArgumentValidator):
    def validate(self, argument):
        if not super(JsonValidator, self).validate(argument):
            return False

        try:
            flask.json.loads(argument)
        except Exception:
            return False

        return True

    def get_value(self, argument):
        try:
            return flask.json.loads(argument)
        except Exception:
            return None


class SocialNetworkTypeValidator(ArgumentValidator):
    def validate(self, argument):
        if not super(SocialNetworkTypeValidator, self).validate(argument):
            return False

        return self.validation_result(argument in SocialServiceEnum.TAG_ALL)


class ObjectIdValidator(ArgumentValidator):
    def validate(self, argument):
        if not super(ObjectIdValidator, self).validate(argument):
            return False

        try:
            ObjectId(argument)
        except Exception:
            return self.validation_result(False)

        return True

    def get_value(self, argument):
        return ObjectId(argument)


class ObjectRefValidator(ArgumentValidator):
    def validate(self, argument):
        if not super(ObjectRefValidator, self).validate(argument):
            return False

        if "_" in argument:
            try:
                _id, _type = argument.split('_')
                obj_id = ObjectId(_id)
            except Exception:
                return self.validation_result(False)
        else:
            try:
                obj_id = ObjectId(argument)
            except Exception:
                return self.validation_result(False)

        return True

    def get_value(self, argument):
        _id, _type = argument.split('_')
        return ObjectId(_id)


class ConfirmationCodeTypeValidator(ArgumentValidator):
    CODE_TYPES = ('email', 'mobile', 'password')

    def validate(self, argument):
        if not super(ConfirmationCodeTypeValidator, self).validate(argument):
            return False
        return self.validation_result(argument in ConfirmationCodeTypeValidator.CODE_TYPES)

    def get_value(self, argument):
        return ConfirmationLinkTypeEnum.from_string(argument) or None


class EnumValidator(ArgumentValidator):
    def __init__(self, enum_cls, **kwargs):
        super(EnumValidator, self).__init__(**kwargs)
        self.enum_cls = enum_cls

    def validate(self, argument):
        cls = getattr(self.enum_cls, 'TYPE_CLS', unicode)
        return self.validation_result(self.enum_cls.validate(cls(argument)))


class MyObjectValidator(object):
    def __init__(self, user_id):
        self.user_id = user_id

    def validate(self, base_obj_field):
        if not base_obj_field.id.initialized:
            return True
        owner = base_obj_field.get_object_owner()
        if not owner or owner != self.user_id:
            current_app.logger.warn(u"Not my object")
            return False
        return True
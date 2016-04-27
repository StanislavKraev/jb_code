# -*- coding: utf-8 -*-

import getpass
import sys

class BaseManageCommand(object):
    def __init__(self, config = None, logger = None):
        assert config
        assert logger

        self.config = config
        self.logger = logger

    def run(self):
        raise NotImplementedError()


def get_single(prompt, hide_echo = False, validator = None, error_hint = "", retry_count = 3):
    for _ in xrange(retry_count):
        if not hide_echo:
            value = raw_input(prompt).decode(sys.stdin.encoding)
            if validator:
                if not validator.validate(value):
                    if not error_hint:
                        error_hint = "Некорректное значение"
                    print(error_hint)
                else:
                    return validator.get_value(unicode(value))
            else:
                return value
        else:
            value = getpass.getpass(prompt).decode(sys.stdin.encoding)
            if validator:
                if not validator.validate(unicode(value)):
                    if not error_hint:
                        error_hint = "Некорректное значение"
                    print(error_hint)
                else:
                    return validator.get_value(unicode(value))
            else:
                return value
    exit(-1)


# -*- coding: utf-8 -*-

import ConfigParser
import argparse
import logging
import os


class Configuration(object):
    LEVEL_NAME_VALUE_DICT = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARN': logging.WARN,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    def __init__(self, service_description, default_config_path):
        kwargs = Configuration.parse_command_line_options(service_description, default_config_path)
        self.settings = {}
        self.settings.update(vars(kwargs))
        config_file_path = self.settings.get('config', '')
        if config_file_path:
            if not os.path.exists(config_file_path):
                raise Exception("Can not find config file: %s" % config_file_path)
            self.config_file = ConfigParser.RawConfigParser()
            self.config_file.read(config_file_path)

    def get_from_config(self, full_key_name, default=None):
        section, key = full_key_name.split(':')
        try:
            value = self.config_file.get(section, key)
        except ConfigParser.NoOptionError:
            if default is not None:
                return default
            raise
        return value

    def get_int_from_config(self, full_key_name, default=None):
        return int(self.get_from_config(full_key_name, default))

    def __getitem__(self, key):
        return self.settings[key]

    def __setitem__(self, key, value):
        self.settings[key] = value

    @staticmethod
    def parse_command_line_options(service_description, default_config_path):
        parser = argparse.ArgumentParser(description=service_description)
        parser.add_argument('--config', dest='config', action='store', help='path to config file',
                            default=default_config_path)

        return parser.parse_known_args()[0]

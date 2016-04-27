# -*- coding: utf-8 -*-

import argparse
import inspect
import logging
import os
from flask import Flask
import external_tools
from fw.cache.cache_wrapper import CacheWrapper
from jb_config import JBConfiguration
from manage_commands import BaseManageCommand
from template_filters import load_filters
from services import ifns, ip_reg, llc_reg, notarius, osago, partners, pay, yurist, car_assurance


SERVICE_DESCRIPTION = 'JurBureau'
DEFAULT_CONFIG_PATH = '/etc/jurbureau/config.cfg'

app = Flask(__name__)

SERVICES = (ifns, ip_reg, llc_reg, notarius, osago, partners, pay, yurist, car_assurance)


def init_configuration():
    parser = argparse.ArgumentParser(description=SERVICE_DESCRIPTION)
    parser.add_argument('command', action='store')
    parser.add_argument("--config", help="config file")
    parser.add_argument("--quiet", help="skip user interaction if possible", action="store_true")

    res = parser.parse_known_args()

    config = JBConfiguration(SERVICE_DESCRIPTION, res[0].config if res[0].config else DEFAULT_CONFIG_PATH)
    config.settings['be_quiet'] = not not res[0].quiet
    app.config.update(config.settings)
    return res[0].command


def load_commands(command_locations=None):
    command_locations = command_locations or []

    def load_command_from_module(module):
        commands = {}
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BaseManageCommand) and obj.__name__ != 'BaseManageCommand':
                # noinspection PyUnresolvedReferences
                commands[obj.NAME] = obj(config=app.config, logger=app.logger)
        return commands

    commands = {}
    command_locations.append(os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "manage_commands")))
    base_dir = os.path.normpath(os.path.abspath(os.path.dirname(__file__)))
    for command_dir in command_locations:
        for root, dirs, files in os.walk(command_dir):
            mod_rel_dir = command_dir[len(base_dir) + 1:].replace('/', '.')
            for file_name in files:
                if os.path.splitext(file_name)[1] != '.py':
                    continue
                mod_path = os.path.splitext(file_name)[0]
                try:
                    mod = __import__(mod_rel_dir + '.' + mod_path, fromlist=mod_rel_dir)
                except ImportError, ex:
                    continue
                mod_commands = load_command_from_module(mod)
                commands.update(mod_commands)

    return commands


def init_db():
    app.cache = CacheWrapper()
    app.external_tools = external_tools

    from fw.db.sql_base import db
    db.init_app(app)


if __name__ == '__main__':
    del app.logger.handlers[:]
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    consoleHandler.setLevel(logging.DEBUG)
    app.logger.addHandler(consoleHandler)
    app.logger.setLevel(logging.DEBUG)
    command = init_configuration()
    init_db()
    load_filters(app.jinja_env, app.config)
    os.environ['CELERY_CONFIG_MODULE'] = app.config['CELERY_CONFIG_MODULE']
    from app import init_contexts

    init_contexts(app)

    command_locations = []
    for service in SERVICES:
        if hasattr(service, 'get_manager_command_locations'):
            command_locations.extend(service.get_manager_command_locations())
    COMMAND_HANDLERS = load_commands(command_locations)
    handler = COMMAND_HANDLERS.get(command, None)
    if not handler:
        print('Do not know how to handle "%s" command\r\n' % command)
        print('Available commands:\r\n * %s' % '\r\n * '.join(sorted(COMMAND_HANDLERS.keys())))
        exit(-1)

    with app.app_context():
        handler.run()
# -*- coding: utf-8 -*-
import os

import jinja2

from services.notarius.api import notarius_bp


def register(app, jinja_env, class_loader, url_prefix=None):
    app.register_blueprint(notarius_bp, url_prefix=url_prefix)

    search_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), u"templates"))
    jinja_env.loader.loaders.append(jinja2.FileSystemLoader(search_path))

    class_loader.POSSIBLE_LOCATIONS.append('services.notarius.data_model.db_models')
    class_loader.POSSIBLE_LOCATIONS.append('services.notarius.data_model.fields')


def get_manager_command_locations():
    return [os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), 'manage_commands')))]
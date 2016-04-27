# -*- coding: utf-8 -*-
import os
import jinja2
from services.ifns.api import ifns_bp


def register(app, jinja_env, class_loader, url_prefix=None):
    app.register_blueprint(ifns_bp, url_prefix=url_prefix)

    search_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), u"templates"))
    jinja_env.loader.loaders.append(jinja2.FileSystemLoader(search_path))

    class_loader.POSSIBLE_LOCATIONS.append('services.ifns.data_model.db_models')
    class_loader.POSSIBLE_LOCATIONS.append('services.ifns.data_model.enums')
    class_loader.POSSIBLE_LOCATIONS.append('services.ifns.data_model.fields')
    class_loader.POSSIBLE_LOCATIONS.append('services.ifns.data_model.okved')


def get_manager_command_locations():
    return [os.path.normpath(os.path.abspath(os.path.dirname(__file__)))]
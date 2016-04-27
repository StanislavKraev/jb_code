# -*- coding: utf-8 -*-
import os

import jinja2
from services.partners.api import partners_bp


def register(app, jinja_env, class_loader, url_prefix=None):
    app.register_blueprint(partners_bp, url_prefix=url_prefix)

    search_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), u"templates"))
    jinja_env.loader.loaders.append(jinja2.FileSystemLoader(search_path))


def get_manager_command_locations():
    return [os.path.normpath(os.path.abspath(os.path.dirname(__file__)))]
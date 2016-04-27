# -*- coding: utf-8 -*-
import os
from services.russian_post.api import russian_post_bp


def register(app, jinja_env, class_loader, url_prefix=None):
    app.register_blueprint(russian_post_bp, url_prefix=url_prefix)

    #search_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), u"templates"))
    #jinja_env.loader.loaders.append(jinja2.FileSystemLoader(search_path))

    class_loader.POSSIBLE_LOCATIONS.append('services.russian_post.db_models')


def get_manager_command_locations():
    return [os.path.normpath(os.path.abspath(os.path.dirname(__file__)))]

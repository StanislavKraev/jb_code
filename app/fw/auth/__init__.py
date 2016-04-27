# -*- coding: utf-8 -*-
from flask.globals import current_app
from fw.auth.encrypt import check_password


def load_user(user_id):
    from fw.auth.models import AuthUser
    return AuthUser.query.filter_by(id=user_id).first()

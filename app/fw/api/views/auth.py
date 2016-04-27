# -*- coding: utf-8 -*-
from datetime import datetime
import json

import flask
from flask import current_app, Response, request, session, Blueprint, abort, redirect
from flask_login import (login_user, logout_user, login_required, current_user)
from fw import metrics

from fw.api import errors
from fw.api.api_data import get_user_api_structure
from fw.api.args_validators import (validate_arguments, EmailAddressValidator, PasswordValidator, AtLeastOneOfValidator,
                                    AccessTokenValidator, SocialNetworkTypeValidator, ConfirmationCodeValidator,
                                    ArgumentValidator)
from fw.api.base_handlers import api_view
from fw.auth.models import ConfirmationLinkTypeEnum, AuthUser, AuthorizationUrl, UserActivationLink
from fw.auth.social_services import SocialServiceBackends
from fw.auth.social_services.social_models import SocialServiceEnum
from fw.auth.user_manager import UserManager
from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject, CompanyDbObject, PrivatePersonDbObject, BatchDocumentDbObject
from fw.storage.models import FileObject
from services.russian_post.db_models import RussianPostTrackingItem

auth_bp = Blueprint('auth', __name__)


class MyResp(Response):
    def set_cookie(self, key, value='', max_age=None, expires=None,
                   path='/', domain=None, secure=None, httponly=False):
        self.__name = key
        self.__val = value
        super(MyResp, self).set_cookie(key, value, max_age, expires, path, domain, secure, httponly)


def change_account_data_owner(old_user_id, new_user_id):
    from services.notarius import notarius_manager

    DocumentBatchDbObject.query.filter_by(_owner_id=old_user_id).update({'_owner_id': new_user_id})
    BatchDocumentDbObject.query.filter_by(_owner_id=old_user_id).update({'_owner_id': new_user_id})
    CompanyDbObject.query.filter_by(_owner_id=old_user_id).update({'_owner_id': new_user_id})
    PrivatePersonDbObject.query.filter_by(_owner_id=old_user_id).update({'_owner_id': new_user_id})
    RussianPostTrackingItem.query.filter_by(owner_id=old_user_id).update({'owner_id': new_user_id})

    notarius_manager.change_objects_owner(old_user_id, new_user_id)
    FileObject.query.filter_by(_owner_id=old_user_id).update({'_owner_id': new_user_id})
    AuthorizationUrl.query.filter_by(owner_id=old_user_id).update({'owner_id': new_user_id})
    UserActivationLink.query.filter_by(auth_user_id=old_user_id).update({'auth_user_id': new_user_id})
    sqldb.session.commit()

    AuthUser.query.filter_by(id=old_user_id, temporal=True).delete()
    sqldb.session.commit()


@auth_bp.route('/account/login/', methods=['POST'])
@api_view
@validate_arguments(email=EmailAddressValidator(), password=PasswordValidator())
def login(email=None, password=None):
    user = UserManager.login_user(email, password)
    if not user:
        raise errors.InvalidLoginOrPassword()

    google_client_id = request.cookies.get('_ga_cid')
    old_user_id = None
    if current_user and not current_user.is_anonymous:
        if not current_user.temporal:
            my_resp = MyResp()
            current_app.session_interface.save_session(current_app, flask.session, my_resp)
            if google_client_id:
                metrics.update_user_info(current_user, google_client_id=google_client_id)
            # noinspection PyUnresolvedReferences
            my_resp = MyResp(json.dumps({"result": my_resp._MyResp__val}), status=200, content_type="application/json")
            return my_resp

        old_user_id = current_user.id

    login_user(user)
    if google_client_id:
        metrics.update_user_info(user, google_client_id=google_client_id)

    if old_user_id:
        new_user_id = user.id
        change_account_data_owner(old_user_id, new_user_id)

    my_resp = MyResp()
    current_app.session_interface.save_session(current_app, flask.session, my_resp)
    # noinspection PyUnresolvedReferences
    my_resp = MyResp(json.dumps({"result": my_resp._MyResp__val}), status=200, content_type="application/json")
    user.last_login_date = datetime.utcnow()
    return my_resp


@auth_bp.route('/account/logout/', methods=['POST'])
@api_view
@login_required
def logout():
    if current_user.temporal:
        raise errors.NotAuthorized()
    logout_user()
    session['logout'] = True
    return {"result": "OK"}


@auth_bp.route('/account/create/', methods=['POST'])
@api_view
@validate_arguments(AtLeastOneOfValidator(
    email=EmailAddressValidator(),
    access_token=AccessTokenValidator()),
    password=PasswordValidator(required=False, raise_exception=errors.InvalidPassword),
    social_network=SocialNetworkTypeValidator(required=False))
def signup(email=None, access_token=None, password=None, social_network=None):
    if "X-Forwarded-For" in request.headers and request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    elif "X-Real-Ip" in request.headers and request.headers.getlist("X-Real-Ip"):
        ip = request.headers.getlist("X-Real-Ip")[0]
    else:
        ip = request.remote_addr

    if ip in current_app.config['OFFICE_IP']:
        is_test_user = True
    else:
        is_test_user = False

    if not email and not access_token:
        raise errors.MissingRequiredParameter('email')

    if not EmailAddressValidator().validate(email) and not access_token:
        raise errors.InvalidParameterValue('email')

    if access_token:
        password = ''

    if social_network and social_network not in SocialServiceEnum.TAG_ALL:
        raise errors.InvalidParameterValue('social_network')

    if not PasswordValidator().validate(password) and not access_token:
        raise errors.MissingRequiredParameter('password')

    if current_user and not current_user.is_anonymous:
        if not current_user.temporal:
            raise errors.InvalidParameterValue('email')

        new_user = UserManager.promote_temp_user(current_user, access_token, None, email, u"", u"", u"", password, social_network)
        new_user.is_tester = is_test_user
    else:
        new_user = UserManager.register_user(access_token, None, email, u"", u"", u"", password, social_network)
        new_user.is_tester = is_test_user

    google_client_id = request.cookies.get('_ga_cid')
    if google_client_id and not new_user.temporal:
        metrics.update_user_info(new_user, google_client_id=google_client_id)

    new_user.email = new_user.email.lower() if new_user.email else u""

    data = get_user_api_structure(new_user)
    result = {"result": data}

    if not email and access_token:
        login_user(new_user)
        my_resp = MyResp()
        current_app.session_interface.save_session(current_app, flask.session, my_resp)
        return result

    user = UserManager.login_user(email, password)
    if user:
        login_user(user)
        my_resp = MyResp()
        current_app.session_interface.save_session(current_app, flask.session, my_resp)
        user.last_login_date = datetime.utcnow()

    return result


@auth_bp.route('/account/profile/', methods=['GET'])
@api_view
@login_required
def get_profile():
    data = get_user_api_structure(current_user)
    return {"result": data}


@auth_bp.route('/account/confirm/', methods=['POST', 'GET'])
@api_view
@validate_arguments(code=ConfirmationCodeValidator(),
                    user_id=ArgumentValidator(required=False))
def confirm_account(code=None, user_id=None):
    if len(code) != current_app.config['max_activation_link_length'] and \
                    len(code) != current_app.config['digital_activation_link_length']:
        raise errors.InvalidParameterValue('code')

    if len(code) == current_app.config['digital_activation_link_length'] and not user_id:
        raise errors.MissingRequiredParameter('code')

    link_type = ConfirmationLinkTypeEnum.CLT_MOBILE if (
        len(code) == current_app.config['digital_activation_link_length']) else ConfirmationLinkTypeEnum.CLT_EMAIL
    user = UserManager.confirm_email_or_mobile(code, user_id if user_id else None, link_type)
    if not user:
        raise errors.UserNotFound()

    data = get_user_api_structure(user)
    return {"result": data}


@auth_bp.route('/account/send_activation_code/', methods=['POST'])
@api_view
@validate_arguments(AtLeastOneOfValidator(
    email=EmailAddressValidator(),
    mobile=ArgumentValidator()
))
def resend_activation_code(email=None, mobile=None):
    UserManager.resend_activation_code(email, mobile)
    return {'result': True}


@auth_bp.route('/account/login/temporal/', methods=['POST'])
@api_view
@validate_arguments(guid=ArgumentValidator(required=False))
def login_temporal(guid=None):
    if "X-Forwarded-For" in request.headers and request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    elif "X-Real-Ip" in request.headers and request.headers.getlist("X-Real-Ip"):
        ip = request.headers.getlist("X-Real-Ip")[0]
    else:
        ip = request.remote_addr

    if ip in current_app.config['OFFICE_IP']:
        test_user = True
    else:
        test_user = False

    user = None
    if current_user and current_user.is_anonymous:
        user = UserManager.create_temp_user()
        if user:
            login_user(user)
            user.last_login_date = datetime.utcnow()
        user.is_tester = test_user

    elif current_user:
        user = current_user

    if not user:
        raise errors.UserNotFound()

    data = get_user_api_structure(user)
    return {"result": data}


@auth_bp.route('/account/profile/update/', methods=['POST'])
@api_view
@login_required
@validate_arguments(email=ArgumentValidator(required=False),
                    mobile=ArgumentValidator(required=False),
                    notifications=ArgumentValidator(required=False)
                    )
def update_profile(email=None, notifications=None, mobile=None):
    UserManager.update_profile(current_user, email, new_mobile=mobile)

    data = get_user_api_structure(current_user)
    return {"result": data}


@auth_bp.route('/account/password_recovery/', methods=['POST'])
@api_view
@validate_arguments(AtLeastOneOfValidator(email=EmailAddressValidator(), mobile=ArgumentValidator()))
def password_recovery(email=None, mobile=None):
    UserManager.send_password_recovery_code(email, mobile)
    return {"result": True}


@auth_bp.route('/account/password_change/', methods=['POST'])
@api_view
@validate_arguments(
    AtLeastOneOfValidator(
        user_id=ArgumentValidator(),
        email=EmailAddressValidator()),
    AtLeastOneOfValidator(
        code=ArgumentValidator(),
        old_password=PasswordValidator(raise_exception=errors.InvalidPassword)
    ),
    new_password=PasswordValidator()
)
def password_change(user_id=None, email=None, code=None, old_password=None, new_password=None):
    email = email.lower() if email else u""

    if not user_id and email:
        # find user based on email
        user = AuthUser.query.filter_by(email=email).first()
        if not user:
            raise errors.UserNotFound()
        user_id = user.uuid
    elif not user_id:
        raise errors.InvalidParameterValue('user_id')

    user = UserManager.change_password(user_id, code, old_password, new_password)
    if user and not current_user.is_authenticated:
        login_user(user)
    return {"result": True}


@auth_bp.route('/account/by/code/', methods=['GET'])
@api_view
@validate_arguments(user_id=ArgumentValidator(),
                    code=ConfirmationCodeValidator())
def account_by_code(user_id=None, code=None):
    user = UserManager.get_user_by_code(user_id, code)

    data = get_user_api_structure(user)
    return {"result": data}


@auth_bp.route('/account/login/external/<string:social_network>/<path:next_page>', methods=['GET'], strict_slashes=True)
@auth_bp.route('/account/login/external/<string:social_network>/', methods=['GET'])
@api_view
def login_external(social_network=None, next_page=""):
    class MyResp(Response):
        def set_cookie(self, key, value='', max_age=None, expires=None,
                       path='/', domain=None, secure=None, httponly=False):
            self.__name = key
            self.__val = value
            super(MyResp, self).set_cookie(key, value, max_age, expires, path, domain, secure, httponly)

    try:
        code = request.args['code']
    except Exception:
        if 'error' in request.args:
            html = u"""<html><head></head><body><script>window.location.href = "/";</script></body></html>"""
            my_resp = MyResp(html, status=200, content_type="text/html; charset=utf-8")
            return my_resp
        raise errors.InvalidParameterValue('code')

    if social_network not in ('facebook', 'vk', 'google'):
        raise errors.InvalidParameterValue('social_network')

    backend = SocialServiceBackends.backends.get(social_network)
    if not backend:
        raise errors.InvalidParameterValue('social_network')

    config = current_app.config

    if backend:
        if '?' in next_page:
            next_page = next_page.split('?')[0]
        current_app.logger.debug(u"2 redirect url: %s" % next_page)
        access_token, ext_data = backend.get_token(code, config, next_page=next_page)
        if not access_token:
            raise errors.SocialAuthError()

        user_data = backend.get_user_data(config, access_token)
        social_uid = user_data.get('id')
        if not social_uid:
            raise errors.SocialAuthError()
        social_service_user_link = backend.get_user_link(unicode(social_uid))
        if social_service_user_link:
            user = social_service_user_link.user
        else:
            ext_data = ext_data or {}
            if 'email' not in ext_data:
                ext_data = backend.get_user_data(config, access_token)
            user, user_profile = UserManager.create_user(access_token, "", ext_data.get('email', ""), "", "", "", "",
                                                            social_network, email_is_social=True)

        old_user_id = current_user.id if (
            current_user and not current_user.is_anonymous and current_user.temporal) else None
        if old_user_id:
            new_user_id = user.id
            change_account_data_owner(old_user_id, new_user_id)

        google_client_id = request.cookies.get('_ga_cid')
        if google_client_id and not user.temporal:
            metrics.update_user_info(user, google_client_id=google_client_id)
        login_user(user)
        user.last_login_date = datetime.utcnow()

        my_resp = MyResp()
        current_app.session_interface.save_session(current_app, flask.session, my_resp)
        # noinspection PyUnresolvedReferences
        html = u"""
        <html>
        <head></head>
        <body>
        <script>
        window.location.href = "/%s";
        </script>
        </body>
        </html>
    """ % next_page
        my_resp = MyResp(html, status=200, content_type="text/html; charset=utf-8")
        return my_resp

    return {"result": None}


@auth_bp.route('/account/login/external-url/', methods=['GET'])
@api_view
@validate_arguments(social_network=ArgumentValidator())
def get_external_login_url(social_network=None):
    if social_network not in ('facebook', 'vk', 'google'):
        raise errors.InvalidParameterValue('social_network')

    backend = SocialServiceBackends.backends.get(social_network)
    if not backend:
        raise errors.InvalidParameterValue('social_network')

    config = current_app.config
    next_page = request.args['next_page']

    if '?' in next_page:
        next_page = next_page.split('?')[0]
    current_app.logger.debug(u"2 redirect url: %s" % next_page)

    token_url = backend.get_token_url(config, next_page=next_page)
    return {"result": token_url}


@auth_bp.route('/go/<go_id>/', methods=['GET'])
def go_auth_url(go_id):
    if not go_id or not go_id.isalnum():
        abort(404)

    try:
        return redirect(UserManager.authorize_by_url(go_id))
    except Exception:
        pass
    abort(404)

# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import random
import string
from bson import ObjectId

from flask_login import login_user

from fw.api import errors
from fw.auth.encrypt import encrypt_password, check_password
from fw.auth.models import AuthUser, UserActivationLink, ConfirmationLinkTypeEnum, AuthorizationUrl
from fw.auth.social_services import SocialServiceBackends
from fw.db.sql_base import db
from template_filters import utm_args


class UserManager(object):
    __config = None
    __logger = None

    @classmethod
    def _generate_link_code(cls, use_chars):
        max_activation_link_length = cls.__config['max_activation_link_length']
        digital_activation_link_length = cls.__config['digital_activation_link_length']
        if use_chars:
            return u''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(max_activation_link_length))
        return u''.join(random.choice(string.digits) for _ in range(digital_activation_link_length))

    @classmethod
    def init(cls, config, logger):
        cls.__config = config
        cls.__logger = logger

        assert cls.__config
        assert cls.__logger

    @staticmethod
    def create_temp_user(is_tester=False):
        result = UserManager.create_user("", "", "", "", "", "", "", "", is_tester=is_tester)
        if result:
            return result[0]

    @classmethod
    def register_user(cls, social_service_access_token, mobile, email, name, surname, patronymic, password,
                      social_network, temp_user=None):
        """
            @type social_service_access_token: string
            @type email: string
            @type name: string
            @type surname: string
            @type patronymic: string
            @type password: string
            @type social_network: string
        """

        user, is_new_account = UserManager.create_user(social_service_access_token, mobile, email,
                                                       name, surname, patronymic, password, social_network,
                                                       temp_user=temp_user
                                                       )

        if (mobile and not user.mobile_confirmed) or (email and not user.email_confirmed):
            activate_by_mobile = not not mobile

            try:
                if activate_by_mobile:
                    # UserManager.confirm_new_mobile(store, user, mobile, config)
                    pass
                else:
                    UserManager.confirm_new_email(user, email)
            except Exception, exc:
                cls.__logger.exception(u'Failed to create user: %s' % str(exc))
                raise errors.ServerUnavailable(exc.message)
        return user

    @classmethod
    def promote_temp_user(cls, current_user, social_service_access_token, mobile, email, name,
                          surname, patronymic, password, social_network):

        new_user = UserManager.register_user(social_service_access_token, mobile, email, name,
                                             surname, patronymic, password, social_network, temp_user=current_user)

        return new_user

    @classmethod
    def resend_activation_code(cls, email, mobile):
        if email:
            user = AuthUser.query.filter_by(email=email).first()

            if not user:
                user_activation_link = UserActivationLink.query.filter_by(
                    new_email=email,
                    used_date=None,
                    link_type=ConfirmationLinkTypeEnum.CLT_EMAIL).first()

                if not user_activation_link:
                    raise errors.UserNotFound()
                user = AuthUser.query.filter_by(id=user_activation_link.auth_user_id).first()
                if not user:
                    raise errors.UserNotFound()

                db.session.delete(user_activation_link)
                db.session.commit()

            UserManager.confirm_new_email(user, email, email_type='activate_account')
            return

        user = AuthUser.query.filter_by(mobile=mobile).first()

        if not user:
            user_activation_link = UserActivationLink.query.filter_by(
                new_mobile=mobile,
                used_date=None,
                link_type=ConfirmationLinkTypeEnum.CLT_MOBILE).first()

            if not user_activation_link:
                raise errors.UserNotFound()
            user = AuthUser.query.filter_by(id=user_activation_link.auth_user_id).first()
            if not user:
                raise errors.UserNotFound()

            db.session.delete(user_activation_link)
            db.session.commit()

        UserManager.confirm_new_mobile(user, mobile)


    @classmethod
    def create_user(cls, social_service_access_token, mobile, email,
                    name, surname, patronymic, password, social_network, email_is_social=False, temp_user=None,
                    is_tester=False):

        is_temp_user = not mobile and not email
        email_confirmed = False
        social_uid = None
        social_email = ''
        social_backend = None
        token = None
        if social_service_access_token and social_network:
            token = social_service_access_token
            social_backend = SocialServiceBackends.backends.get(social_network)
            if social_backend:
                social_data = social_backend.get_user_data(cls.__config, token)
                social_uid = social_data.get('id', None)
                if not social_data or not social_uid:
                    raise errors.SocialAuthError()
                social_email = social_data.get('email', None)
                if social_email:
                    social_email = social_email.lower()
                social_service_user_link = social_backend.get_user_link(social_uid)
                if social_service_user_link:
                    user_id = social_service_user_link.auth_user
                    user = AuthUser.query.filter_by(id=user_id)
                    return user, False

        email = email.lower() if email else u''
        if email:
            if email_is_social or (social_email and email == social_email):
                email_confirmed = True
        elif not email and not mobile and social_backend:
            email = social_email
            if email:
                email_confirmed = True

        current_user = (AuthUser.query.filter_by(email=unicode(email)).first() if email else AuthUser.query.filter_by(mobile=unicode(mobile)).first() if mobile else None)

        if current_user:
            if email:
                if social_email and social_uid:
                    if current_user.email_confirmed:
                        social_backend.make_link(token, social_uid, current_user, cls.__config)
                        return current_user, False
                    else:
                        email = u''
                        email_confirmed = False
                else:
                    raise errors.DuplicateEmail()
            else:
                raise errors.DuplicateMobile()

        # Creating new auth user record
        user = temp_user or AuthUser(uuid=unicode(ObjectId()))
        user.email_confirmed = email_confirmed
        user.mobile_confirmed = False
        user.is_tester = is_tester
        if email_confirmed:
            user.email = email
        user.password = unicode(encrypt_password(password)) if password else None
        user.signup_date = datetime.utcnow()
        user.enabled = True
        user.email = unicode(email) if email else None
        user.mobile = unicode(mobile) if mobile else None
        user.name = unicode(name)
        user.surname = unicode(surname)
        user.patronymic = unicode(patronymic)
        user.temporal = is_temp_user

        try:
            db.session.add(user)
        except Exception, exc:
            cls.__logger.error('Failed to add user to DB: %s' % str(exc))
            db.session.rollback()
            raise

        # add link to user profile
        if social_uid:
            social_backend.make_link(token, social_uid, user, cls.__config)
            user.enabled = True

        db.session.commit()
        return user, True

    @classmethod
    def login_user(cls, email, password):
        email = email.lower()
        if not email:
            return
        user = AuthUser.query.filter_by(email=email).first()
        staging = cls.__config['STAGING']
        if staging and password == "111111":
            if not user:
                try:
                    user = AuthUser.query.filter_by(uuid=email.split('@')[0]).first()
                except Exception:
                    db.session.rollback()
                    return
            db.session.commit()
            return user

        db.session.commit()
        if not user or not user.password or not check_password(password, user.password):
            return

        return user

    @classmethod
    def confirm_email_or_mobile(cls, code, user_id, link_type):
        user = None
        cls.__logger.debug(
            u"confirm_email_or_mobile: %s, %s, %s" % (unicode(code), unicode(user_id), unicode(link_type)))
        if user_id:
            user = AuthUser.query.filter_by(uuid=user_id).first()
            if not user:
                raise errors.ActivationCodeExpiredOrInvalid()
            activation_link = UserActivationLink.query.filter_by(
                link_code=code,
                auth_user_id=user.id,
                link_type=link_type,
                used_date=None
            ).first()
        else:
            activation_link = UserActivationLink.query.filter_by(
                link_code=code,
                link_type=link_type,
                used_date=None
            ).first()

        if activation_link:
            user = AuthUser.query.filter_by(id=activation_link.auth_user_id).first()
            if not user:
                raise errors.ActivationCodeExpiredOrInvalid()
            if activation_link.used_date:
                raise errors.ActivationCodeExpiredOrInvalid()
            if activation_link.use_attempts >= cls.__config['max_activation_attempts_count']:
                raise errors.ActivationAttemptsCountExceeded()
        else:
            if user:
                real_link = UserActivationLink.query.filter_by(
                    auth_user_id=user.id,
                    link_type=link_type,
                    used_date=None
                ).first()
                if real_link:
                    real_link.use_attempts += 1
                    db.session.commit()
                    if real_link.use_attempts > cls.__config['max_activation_attempts_count']:
                        raise errors.ActivationAttemptsCountExceeded()
            raise errors.ActivationCodeExpiredOrInvalid()

        if activation_link.link_type == ConfirmationLinkTypeEnum.CLT_MOBILE:
            # if user.mobile != activation_link.new_mobile:
            user.mobile = activation_link.new_mobile
            user.mobile_confirmed = True
            user.enabled = True
        elif activation_link.link_type == ConfirmationLinkTypeEnum.CLT_EMAIL:
            # if user.email != activation_link.new_email:
            user.email = activation_link.new_email
            user.email_confirmed = True
            user.enabled = True
        activation_link.used_date = datetime.utcnow()
        db.session.commit()
        return user

    @staticmethod
    def generate_password():
        return ''.join(random.choice(string.digits) for _ in range(8))

    @classmethod
    def update_profile(cls, auth_user, new_email, new_mobile=None):

        temp_user = auth_user.temporal
        if new_email:
            new_email = new_email.lower()

        if new_email and auth_user.email != new_email:
            if AuthUser.query.filter_by(email=new_email).count():
                raise errors.DuplicateEmail()

            auth_user.email = new_email
            auth_user.email_confirmed = False

            if temp_user:
                new_password = UserManager.generate_password()
                password = unicode(encrypt_password(new_password))

                link_code = cls._generate_link_code(True)

                activation_link = UserActivationLink(
                    link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD,
                    link_code=link_code,
                    auth_user=auth_user
                )
                db.session.add(activation_link)

                from fw.async_tasks import send_email

                schema = cls.__config['WEB_SCHEMA']
                domain = cls.__config['DOMAIN']
                selfcare_url = u"%s://%s/account/?" % (schema, domain)
                selfcare_url = utm_args(selfcare_url, 'new_account_user_notify', auth_user.id)
                selfcare_url = cls.make_auth_url(selfcare_url, auth_user).get_url(cls.__config)
                tmpl_data = {
                    'password': new_password,
                    "link_code": activation_link.link_code,
                    'email': new_email,
                    "domain": domain,
                    "schema": schema,
                    "user_id": auth_user.uuid,
                    "selfcare_url": selfcare_url # {{'?'|utm_args('', user_id)}}
                }
                send_email.send_email.delay(new_email, "new_account_user_notify", **tmpl_data)
                auth_user.password = password
                auth_user.temporal = False

            UserManager.confirm_new_email(auth_user, new_email, email_type="confirm_email")
            db.session.commit()

        elif new_email == u'':
            # empty string: delete current email
            raise errors.InvalidParameterValue('email')

        if new_mobile and auth_user.mobile != new_mobile:
            if AuthUser.query.filter_by(mobile=new_mobile).count():
                raise errors.DuplicateMobile()

            auth_user.mobile = new_mobile
            auth_user.mobile_confirmed = False
            UserManager.confirm_new_mobile(auth_user, new_mobile)
            db.session.commit()
        elif new_mobile == u"":
            auth_user.mobile = None
            auth_user.mobile_confirmed = False
            db.session.commit()

        return auth_user

    @classmethod
    def confirm_new_mobile(cls, auth_user, new_mobile):
        UserActivationLink.query.filter(
            UserActivationLink.auth_user == auth_user,
            UserActivationLink.link_type == ConfirmationLinkTypeEnum.CLT_MOBILE,
            UserActivationLink.used_date == None).delete()

        link_code = cls._generate_link_code(False)

        activation_link = UserActivationLink(
            new_mobile=new_mobile,
            link_type=ConfirmationLinkTypeEnum.CLT_MOBILE,
            link_code=link_code,
            auth_user=auth_user
        )
        db.session.add(activation_link)
        db.session.commit()

        cls.__logger.info("Sending sms to %s" % str(new_mobile))
        from fw.async_tasks import send_sms_task

        result = send_sms_task.send_sms.delay(
            new_mobile,
            "activate_account",
            link_code=activation_link.link_code,
            service_name=cls.__config['service_name']
        )
        cls.__logger.info("Sending sms to %s result: %s" % (str(new_mobile), str(result)))

    @classmethod
    def confirm_new_email(cls, auth_user, new_email, email_type="activate_account"):
        link = UserActivationLink.query.filter_by(auth_user=auth_user).first()
        if link:
            db.session.delete(link)
        new_email = new_email.lower()
        link_code = UserManager._generate_link_code(True)
        activation_link = UserActivationLink(
            auth_user=auth_user,
            link_code=link_code,
            new_email=new_email,
            link_type=ConfirmationLinkTypeEnum.CLT_EMAIL
        )
        db.session.add(activation_link)

        tmpl_data = {
            "uid": auth_user.uuid,
            "link_code": activation_link.link_code,
            "name": auth_user.name,
            "patronymic": auth_user.patronymic,
            "domain": cls.__config['DOMAIN'],
            "schema": cls.__config['WEB_SCHEMA'],
            "email_confirm_link": "%s://%s/confirm/?code=%s" % (
                cls.__config['WEB_SCHEMA'], cls.__config['DOMAIN'], activation_link.link_code)
        }
        from fw.async_tasks import send_email

        db.session.commit()
        send_email.send_email.delay(new_email, email_type, **tmpl_data)

    @classmethod
    def send_password_recovery_code(cls, email, mobile):
        auth_user = None

        if email:
            auth_user = AuthUser.query.filter_by(email=email).first()
        elif mobile:
            auth_user = AuthUser.query.filter_by(mobile=mobile).first()

        if not auth_user:
            raise errors.UserNotFound()

        # check last password drop attempts: time and count
        last_drop_date = auth_user.last_password_drop_attempts_date

        if last_drop_date and last_drop_date >= datetime.utcnow() - timedelta(days=1):
            # the attempt was less then 1 day ago
            if auth_user.last_password_drop_attempts_count >= 2:
                raise errors.RecoveryAttemptsCountExceeded()
            else:
                auth_user.last_password_drop_attempts_count += 1
        else:
            auth_user.last_password_drop_attempts_count = 1
            auth_user.last_password_drop_attempts_date = datetime.utcnow()

        UserActivationLink.query.filter_by(auth_user_id=auth_user.id,
                                                             link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD).delete()

        link_code = cls._generate_link_code(bool(email))

        activation_link = UserActivationLink(
            auth_user=auth_user,
            link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD,
            link_code=link_code
        )
        db.session.add(activation_link)
        db.session.commit()

        if email:
            from fw.async_tasks import send_email

            tmpl_data = {
                "user_id": auth_user.uuid,
                "link_code": activation_link.link_code,
                "domain": cls.__config['DOMAIN'],
                "web_schema": cls.__config['WEB_SCHEMA'],
            }
            send_email.send_email.delay(auth_user.email, 'change_password', **tmpl_data)
            return

        from fw.async_tasks import send_sms_task

        send_sms_task.send_sms(
            mobile,
            'activate_account',
            link_code=activation_link.link_code,
            service_name=cls.__config['service_name']
        )


    @classmethod
    def change_password(cls, user_id, code, old_password, new_password):
        user = AuthUser.query.filter_by(uuid=user_id).first()
        if not user:
            raise errors.UserNotFound()

        if code:
            return UserManager._change_password_by_code(code, user, new_password)

        if user.password is not None:
            if not check_password(old_password, user.password):
                raise errors.InvalidCurrentPassword()

        user.password = unicode(encrypt_password(new_password))
        db.session.commit()
        return user

    @classmethod
    def _change_password_by_code(cls, code, user, new_password):
        code_links = UserActivationLink.query.filter_by(auth_user=user, used_date=None, link_type=ConfirmationLinkTypeEnum.CLT_PASSWORD)

        if not code_links.count():
            raise errors.ActivationCodeExpiredOrInvalid()

        max_use_count = 0
        found_link = None
        for code_link in code_links:
            code_link.use_attempts += 1

            if code_link.use_attempts > max_use_count:
                max_use_count = code_link.use_attempts
            if code_link.link_code != code:
                continue

            found_link = code_link

        if not found_link or max_use_count > 5:
            raise errors.ActivationCodeExpiredOrInvalid()

        found_link.used_date = datetime.utcnow()
        user = found_link.auth_user
        user.password = unicode(encrypt_password(new_password))
        db.session.commit()
        return user

    @classmethod
    def get_user_by_code(cls, user_id, code):
        user = AuthUser.query.filter_by(uuid=user_id).first()
        if not user:
            raise errors.ActivationCodeExpiredOrInvalid()

        code_links = UserActivationLink.query.filter_by(auth_user=user, used_date=None, link_code=code)
        if not code_links.count():
            raise errors.ActivationCodeExpiredOrInvalid()

        code_link = code_links[0]
        if code_link.use_attempts > cls.__config['user_by_code_tries_count']:
            raise errors.ActivationCodeExpiredOrInvalid()

        user = AuthUser.query.filter_by(id=code_link.auth_user_id).first()
        if not user or user_id != user.uuid:
            raise errors.UserNotFound()

        return user

    @classmethod
    def get_user_email(cls, user_id):
        user = AuthUser.query.filter_by(id=user_id).first()
        if not user:
            return

        return user.email or ""

    @staticmethod
    def generate_password():
        return ''.join(random.choice(string.digits) for _ in range(8))

    @staticmethod
    def make_auth_url(url, owner, expiration_td=timedelta(days=7)):
        assert url
        assert expiration_td
        assert owner

        AuthorizationUrl.query.filter_by(url=url, owner=owner).delete()
        auth_url = AuthorizationUrl(
            url=url,
            expire_at=datetime.now() + expiration_td,
            owner=owner
        )
        db.session.add(auth_url)
        db.session.commit()
        return auth_url

    @staticmethod
    def authorize_by_url(go_id):
        auth_url = AuthorizationUrl.query.filter_by(id=go_id).scalar()
        if not auth_url:
            raise Exception()

        auth_url.used_times += 1
        db.session.commit()

        if auth_url.expire_at >= datetime.utcnow():
            user = auth_url.owner
            if user:
                login_user(user)

        return auth_url.url

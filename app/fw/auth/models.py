# -*- coding: utf-8 -*-
from bson.objectid import ObjectId
from flask import current_app
from sqlalchemy.sql.functions import func
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from fw.db.sql_base import db


class AnonymousUser(object):

    @property
    def is_anonymous(self):
        return True


class AuthUser(db.Model):

    __tablename__ = 'authuser'

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, default=lambda: unicode(ObjectId()))
    name = Column(String)
    surname = Column(String)
    patronymic = Column(String)
    password = Column(String)
    enabled = Column(Boolean, default=True)
    signup_date = Column(DateTime, default=func.now(), nullable=False)
    last_login_date = Column(DateTime)

    email_confirmed = Column(Boolean, nullable=False, default=False)
    mobile_confirmed = Column(Boolean, nullable=False, default=False)
    email = Column(String)
    mobile = Column(String)

    is_tester = Column(Boolean, nullable=False, default=False)
    temporal = Column(Boolean, nullable=False, default=False)
    last_password_drop_attempts_date = Column(DateTime)
    last_password_drop_attempts_count = Column(Integer)

    admin = Column(Boolean, default=False)

    @property
    def is_anonymous(self):
        return False

    @property
    def is_active(self):
        #return self.enabled
        return True

    @property
    def is_authenticated(self):
        return True

    def get_id(self):
        return self.id

    @property
    def user_id(self):
        return self.get_id()


class UserActivationLink(db.Model):

    __tablename__ = "useractivationlink"

    id = Column(Integer, primary_key=True)

    auth_user_id = Column(Integer, ForeignKey('authuser.id'))
    auth_user = relationship("AuthUser")

    use_attempts = Column(Integer, default=0, nullable=False)
    new_email = Column(String)
    new_mobile = Column(String)

    link_code = Column(String, nullable=False)
    creation_date = Column(DateTime, default=func.now(), nullable=False)
    used_date = Column(DateTime)
    link_type = Column(Integer, nullable=False)


class ConfirmationLinkTypeEnum(object):

    CLT_INVALID = 0
    CLT_EMAIL = 1
    CLT_MOBILE = 2
    CLT_PASSWORD = 3
    CLT_ALL = [CLT_EMAIL, CLT_MOBILE, CLT_PASSWORD]

    @classmethod
    def from_string(cls, val):
        if val == 'email':
            return cls.CLT_EMAIL
        if val == 'mobile':
            return cls.CLT_MOBILE
        if val == 'password':
            return cls.CLT_PASSWORD
        return cls.CLT_INVALID


class AuthorizationUrl(db.Model):

    __tablename__ = "authorization_url"

    id = Column(String, primary_key=True, default=lambda: unicode(ObjectId()))
    url = Column(String)
    created = Column(DateTime, default=func.now(), nullable=False)
    expire_at = Column(DateTime, nullable=False)
    used_times = Column(Integer, default=0, nullable=False)

    owner_id = Column(Integer, ForeignKey('authuser.id'))
    owner = relationship("AuthUser")

    def get_url(self, config):
        return u"%s://%s/go/%s/" % (config['WEB_SCHEMA'], config['api_url'], self.id) if config['WEB_SCHEMA'] else u"/go/%s/" % self.id

    def __unicode__(self):
        return self.get_url(current_app.config)
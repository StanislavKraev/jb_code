# -*- coding: utf-8 -*-

from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship

from fw.db.sql_base import db as sqldb


class SocialServiceEnum(object):
    SS_UNKNOWN = 0
    SS_VK = 1
    SS_FACEBOOK = 2
    SS_GOOGLE = 3
    SS_TWITTER = 4
    SS_OK = 5
    SS_MYMAILRU = 6
    SS_OPENID = 7

    TAG_VK = 'vk'
    TAG_FACEBOOK = 'facebook'
    TAG_GOOGLE = 'ggogle'
    TAG_TWITTER = 'twitter'
    TAG_OK = 'ok'
    TAG_MYMAILRU = 'mymailru'
    TAG_OPENID = 'openid'
    TAG_ALL = [TAG_VK, TAG_FACEBOOK, TAG_GOOGLE]

    _SS_TAGS = {
        SS_FACEBOOK: TAG_FACEBOOK,
        SS_VK: TAG_VK,
        SS_GOOGLE: TAG_GOOGLE,
        SS_TWITTER: TAG_TWITTER,
        SS_OK: TAG_OK,
        SS_MYMAILRU: TAG_MYMAILRU,
        SS_OPENID: TAG_OPENID,
    }

    _TAG_SS = dict((tag, ss) for ss, tag in _SS_TAGS.items())

    @staticmethod
    def from_tag(tag):
        return SocialServiceEnum._TAG_SS.get(tag, SocialServiceEnum.SS_UNKNOWN)

    @staticmethod
    def tag(value):
        return SocialServiceEnum._SS_TAGS.get(value, None)


class SocialUserLink(sqldb.Model):
    __tablename__ = 'socialserviceuserlink'

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, nullable=False)
    uid = Column(String, nullable=False)
    access_token = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey('authuser.id'))
    user = relationship("AuthUser")

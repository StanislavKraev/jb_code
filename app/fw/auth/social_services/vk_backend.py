# -*- coding: utf-8 -*-
import requests
from fw.api import errors
from fw.auth.social_services.social_backend import SocialBackend
from fw.auth.social_services.social_models import SocialUserLink, SocialServiceEnum
from fw.db.sql_base import db as sqldb

VK_API_URL = 'https://api.vk.com/method/'


class VkBackend(SocialBackend):
    @staticmethod
    def is_token_expired(data):
        return 'error' in data and 'error_code' in data['error'] and data['error']['error_code'] in (2, 4, 5, 7)

    @staticmethod
    def call_vk_method(method, **kwargs):
        response = requests.get(VK_API_URL + method + u'?' + u'&'.join([u"%s=%s" % (k, v) for k, v in kwargs.items()]))
        if response.status_code != 200:
            raise errors.SocialAuthError()

        data = response.json()
        if not data:
            if VkBackend.is_token_expired(data):
                raise errors.RenewAuthTokenError()
            else:
                raise errors.SocialAuthError('Failed to decode server answer')

        return data

    @staticmethod
    def get_user_data(config, access_token):
        vk_api_version = "3"
        data = VkBackend.call_vk_method('users.get', v=vk_api_version, access_token=access_token)

        if 'response' not in data:
            raise errors.SocialAuthError('Failed to decode server answer. data=%s; api version=%s; access_token=%s' % (
                data, vk_api_version, access_token))

        user_data = data['response'][0]
        try:
            user_id = int(user_data['uid'])
        except ValueError:
            raise errors.SocialAuthError('Failed to decode server answer. data=%s; api version=%s; access_token=%s' % (
                data, vk_api_version, access_token))

        return dict(id=user_id)

    @staticmethod
    def get_user_link(social_uid):
        return SocialUserLink.query.filter_by(uid=str(social_uid), service_id=SocialServiceEnum.SS_VK).first()

    @staticmethod
    def make_link(access_token, social_uid, auth_user, config):
        link = SocialUserLink(
            uid=social_uid,
            user=auth_user,
            service_id=SocialServiceEnum.SS_VK,
            access_token=access_token
        )
        sqldb.session.add(link)
        sqldb.session.commit()
        return link

    @staticmethod
    def get_token_url(config, next_page="/"):
        if next_page.startswith("/"):
            next_page = next_page[1:]
        vk_api_version = config['vk_api_version']
        permissions = config['vk_app_permissions']
        vk_app_id = config['vk_app_id']
        redirect_url = "%s://%s%s" % (
            config['WEB_SCHEMA'], config['api_url'], config['vk_auth_redirect_url'] + next_page)
        return "https://oauth.vk.com/authorize?client_id=%d&scope=%d&redirect_uri=%s&display=page&v=%s&response_type=code" % (
            vk_app_id, permissions, redirect_url, vk_api_version)

    @staticmethod
    def new_post(post_content, auth_user, config, link_to_attach=None):
        link = SocialUserLink.query.filter_by(user=auth_user, service_id=SocialServiceEnum.SS_VK).first()
        if not link or not link.access_token:
            raise errors.SocialAuthError()

        try:
            params = dict(v=config['vk_api_version'], access_token=link.access_token, message=post_content)
            if link_to_attach:
                params['attachments'] = link_to_attach

            response_data = VkBackend.call_vk_method('wall.post', **params)
        except errors.RenewAuthTokenError, exc:
            link.access_token = ""
            sqldb.session.commit()
            raise

        if 'response' not in response_data:
            raise errors.SocialAuthError('Failed to decode server answer')
        else:
            post_data = dict(id=response_data['response']['post_id'])

        return post_data

    @staticmethod
    def get_token(code, config, next_page):
        redirect_url = VkBackend.get_token_url(config, next_page=next_page)
        vk_app_id = config['vk_app_id']
        vk_app_secret = config['vk_app_secret']
        url = "https://oauth.vk.com/access_token?client_id=%s&client_secret=%s&code=%s&redirect_uri=%s" % (
            unicode(vk_app_id), vk_app_secret, unicode(code), redirect_url)
        result = requests.get(url)

        if result.status_code != 200:
            return None, None
        data = result.json()
        return data['access_token'], data

    @staticmethod
    def get_profile_url(social_link_object):
        if not social_link_object:
            return
        if not isinstance(social_link_object, dict):
            social_link_object = social_link_object.as_dict()
            if 'uid' in social_link_object:
                return u"http://vk.com/id%s" % unicode(social_link_object['uid'])

# -*- coding: utf-8 -*-
import re
import requests
from flask import current_app
from fw.api import errors
from fw.auth.social_services.social_backend import SocialBackend
from fw.auth.social_services.social_models import SocialUserLink, SocialServiceEnum
from fw.db.sql_base import db as sqldb

GRAPH_URL = 'https://graph.facebook.com/v2.2'


class FacebookBackend(SocialBackend):
    @staticmethod
    def get_user_data(config, access_token):
        try:
            response = requests.get(GRAPH_URL + '/me?access_token=%s' % access_token)
            if response.status_code != 200:
                raise errors.SocialAuthError("response.code == %s" % str(response.code))
            data = response.json()
            if not data or 'id' not in data:
                raise Exception('Failed to decode server answer: %s' % response.body)
            result = {
                'id': int(data['id']),
                'email': data.get('email', None)
            }
        except KeyError, exc:
            # noinspection PyUnboundLocalVariable
            raise errors.SocialAuthError("Invalid response: %s. No such field %s" % (response.body, str(exc)))
        except errors.SocialAuthError:
            raise
        except Exception, exc:
            raise errors.SocialAuthError(str(exc))
        return result

    @staticmethod
    def get_user_link(social_uid):
        return SocialUserLink.query.filter_by(uid=str(social_uid), service_id=SocialServiceEnum.SS_FACEBOOK).first()

    @staticmethod
    def make_link(access_token, social_uid, auth_user, config):
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': config['facebook_app_id'],
            'client_secret': config['facebook_app_secret'],
            'fb_exchange_token': access_token
        }
        url = GRAPH_URL + '/oauth/access_token?grant_type=%(grant_type)s&client_id=%(client_id)s&client_secret=%(client_secret)s&fb_exchange_token=%(fb_exchange_token)s' % params

        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise errors.SocialAuthError()
            data = response.text
            if not data or 'access_token=' not in data or '&expires=' not in data:
                raise Exception('Failed to decode server answer')

            # access_token=CAAT75UAyEFYBACPLRT6WOgehcXxVa6FiaRxwm1lcloroS7SehVtF2tS1zNm6wpNOae5atg4LcMq3PmNHqUoPXJcyDzGN69ZBCD61eTUPaWUFK9mEd4qZAO6Q9Bg0lSPZAIvJswI5WHSOLTjMNceL116V6us8uy98ZCFcwHJJzKVZABZATbn7ajMo7okd7cbCgZD&expires=5183836
            new_access_token = data[data.find('access_token=') + 13:data.find('&expires')]
        except Exception, exc:
            raise errors.SocialAuthError()

        link = SocialUserLink(
            uid=social_uid,
            user=auth_user,
            service_id=SocialServiceEnum.SS_FACEBOOK,
            access_token=new_access_token
        )
        sqldb.session.add(link)
        sqldb.session.commit()
        return link

    @staticmethod
    def get_token_url(config, next_page="/"):
        permissions = config['facebook_app_permissions']
        facebook_app_id = config['facebook_app_id']
        if next_page.startswith("/"):
            next_page = next_page[1:]
        redirect_url = "%s://%s%s" % (
            config['WEB_SCHEMA'], config['api_url'], config['facebook_auth_redirect_url'] + next_page)
        current_app.logger.info(redirect_url)
        return "https://www.facebook.com/dialog/oauth?client_id=%d&scope=%s&response_type=code&redirect_uri=%s" % (
            facebook_app_id, permissions, redirect_url)

    @staticmethod
    def new_post(post_content, auth_user, config, link_to_attach=None):
        link = SocialUserLink.query.filter_by(user=auth_user, service_id=SocialServiceEnum.SS_FACEBOOK).first()
        if not link or not link.access_token:
            raise errors.SocialAuthError()

        url = "https://graph.facebook.com/%s/feed" % link.uid
        params = {
            'message': post_content,
            'access_token': link.access_token,
            'name': ' ',  # image title
        }
        if link_to_attach:
            params['link'] = link_to_attach
            # params['caption'] = u'Научим людей парковаться правильно. Spot.'
            params['description'] = ' '
            del params['message']

        try:
            response = requests.post(url, data=params)
        except Exception, exc:
            raise errors.SocialAuthError()

        if response.status_code != 200:  # todo: handle expired/invalidated token response to tell client to retrieve new token
            raise errors.SocialAuthError()

        try:
            response_data = response.json()
            if not response_data or 'id' not in response_data:
                raise Exception('Failed to decode server answer')
            post_data = {
                'id': response_data['id']
            }
        except Exception:
            raise errors.SocialAuthError()
        return post_data

    @staticmethod
    def get_token(code, config, next_page):
        if next_page.startswith("/"):
            next_page = next_page[1:]
        redirect_url = "%s://%s%s" % (
            config['WEB_SCHEMA'], config['api_url'], config['facebook_auth_redirect_url'] + next_page)

        current_app.logger.info(redirect_url)
        facebook_app_id = config['facebook_app_id']
        facebook_app_secret = config['facebook_app_secret']
        url = "https://graph.facebook.com/oauth/access_token?client_id=%s&client_secret=%s&code=%s&redirect_uri=%s" % (
            unicode(facebook_app_id), facebook_app_secret, unicode(code), redirect_url)
        result = requests.get(url)
        current_app.logger.debug(u"code: %s, data:%s" % (unicode(result.status_code), result.text))
        if result.status_code != 200:
            current_app.logger.error(u"result.status_code != 200")
            current_app.logger.error(result.text)
            return None, None
        match = re.match(ur'access_token=(.+)&expires=(.+)', result.text.strip())
        if not match:
            current_app.logger.warn(u"failed to get token")
            return None, None
        access_token = match.groups()[0].strip()
        current_app.logger.debug(u"token %s" % access_token)
        return access_token, {}

    @staticmethod
    def get_profile_url(social_link_object):
        if not social_link_object:
            return
        if not isinstance(social_link_object, dict):
            social_link_object = social_link_object.as_dict()
            if 'uid' in social_link_object:
                return u"https://www.facebook.com/%s" % unicode(social_link_object['uid'])
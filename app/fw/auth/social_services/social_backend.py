# -*- coding: utf-8 -*-


class SocialBackend(object):
    @staticmethod
    def get_user_data(config, access_token):
        """
            Verify access token and return social service user data (dict)
        """
        raise NotImplementedError("Must be implemented in derived classes")

    @staticmethod
    def get_user_link(social_uid):
        """
            Return instance of BaseSocialUserLink subclass corresponding to given user id.
        """
        raise NotImplementedError("Must be implemented in derived classes")

    @staticmethod
    def make_link(access_token, social_uid, auth_user, config):
        """
            Make social service user link.
        """
        raise NotImplementedError("Must be implemented in derived classes")

    @staticmethod
    def get_token_url(config, next_page="/"):
        raise NotImplementedError("Must be implemented in derived classes")

    @staticmethod
    def new_post(post_content, auth_user, config, link_to_attach=None):
        return

    @staticmethod
    def get_profile_url(social_link_object):
        raise NotImplementedError("Must be implemented in derived classes")
# -*- coding: utf-8 -*-
from fw.auth.social_services.facebook_backend import FacebookBackend
from fw.auth.social_services.social_models import SocialUserLink
from fw.auth.social_services.vk_backend import VkBackend


class SocialServiceBackends(object):
    backends = {
        'vk': VkBackend,
        'facebook': FacebookBackend
    }

    @staticmethod
    def get_user_social_network_profile_url(user_id):
        link = SocialUserLink.query.filter_by(user_id=user_id).first()
        if link:
            backend_type = link.service_id
            backend = SocialServiceBackends.backends.get(backend_type)
            if backend:
                return backend.get_profile_url(link)
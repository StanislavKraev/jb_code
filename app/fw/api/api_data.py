# -*- coding: utf-8 -*-


def get_user_api_structure(auth_user):
    result = {
        'temporal': auth_user.temporal or False,

        'id': unicode(auth_user.uuid),
        'email': auth_user.email or u"",
        'email_confirmed': auth_user.email_confirmed,
        'mobile': auth_user.mobile or u"",
        'mobile_confirmed': auth_user.mobile_confirmed,

        'password_set': bool(auth_user.password and auth_user.password != u'!notset!'),    # bool

        'registration_date': auth_user.signup_date.strftime("%Y-%m-%dT%H:%M:%S"),    # — дата регистрации
        'facebook': None,                   # — идентификатор пользователя в facebook (если есть)
        'vk': None,                         # — идентификатор пользователя в VK (если есть)

        'person': {                         # — физическое лицо
            'name': auth_user.name,
            'surname': auth_user.surname,
            'patronymic': auth_user.patronymic
        },
        'role': ['user']                    # — список ролей пользователя, в виде массива,
                                            # пример: ["user", "support", "moderator", "admin"]
    }

    from fw.documents.batch_manager import BatchManager
    batch = BatchManager.get_last_modified_batch(auth_user.id)

    if batch:
        batch_manager = BatchManager.init(batch)

        batch_caption = batch_manager.get_last_modified_batch_caption(batch)
        batch_type = batch.batch_type
        batch_stage = batch_manager.get_stage(batch)

        last_service_data = {
            'id': batch.id,
            'caption': batch_caption,
            'type': batch_type,
            'stage': batch_stage
        }

        result['last_service'] = last_service_data

    from services.pay.subs_manager import SubscriptionManager

    user_subs = SubscriptionManager.get_user_active_subscription(auth_user.id)

    result['subscription'] = {
        'type': user_subs.type,
        'last_day': user_subs.end_dt.strftime("%Y-%m-%dT%H:%M:%S")
    } if user_subs else None

    return result

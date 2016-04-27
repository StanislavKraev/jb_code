# -*- coding: utf-8 -*-
from datetime import datetime
from services.pay.models import PaymentSubscriptionObject


class SubscriptionManager(object):

    @staticmethod
    def if_user_subscribed(auth_user_id):
        user_subs = PaymentSubscriptionObject.query.filter(
            PaymentSubscriptionObject.user_id == auth_user_id,
            PaymentSubscriptionObject.end_dt.__ge__(datetime.utcnow())
        )
        if user_subs.count():
            return True
        return False

    @staticmethod
    def get_user_active_subscription(user_id):
        user_sub = PaymentSubscriptionObject.query.filter(
            PaymentSubscriptionObject.user_id == user_id,
            PaymentSubscriptionObject.end_dt.__ge__(datetime.utcnow())
        ).order_by(PaymentSubscriptionObject.end_dt.desc()).limit(1).first()

        return user_sub

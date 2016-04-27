# -*- coding: utf-8 -*-
from datetime import datetime

import dateutil.parser
from decimal import Decimal
import pytz

from fw.db.sql_base import db as sqldb
from services.pay.models import YadRequestsObject, PaymentSubscriptionObject


def _parse_iso_dt(str_val):
    val = dateutil.parser.parse(str_val)
    return val.astimezone(pytz.timezone('utc')).replace(tzinfo=None)


def forward(config, logger):
    logger.debug(u"Migrate pay models")

    yad_requests = db['yad_requests']
    YadRequestsObject.query.delete()
    sqldb.session.commit()
    for old_req in yad_requests.find():
        new_req = YadRequestsObject(
            ip=old_req['ip'],
            created=old_req['created'],
            request_datetime=_parse_iso_dt(old_req['request_datetime']),
            md5=old_req['md5'],
            shop_id=int(old_req['shop_id']),
            shop_article_id=int(old_req['shop_article_id']) if 'shop_article_id' in old_req and old_req['shop_article_id'] else 0,
            invoice_id=int(old_req['invoice_id']),
            order_number=old_req['order_number'],
            customer_number=old_req['customer_number'],
            order_created_datetime=_parse_iso_dt(old_req['order_created_datetime']),
            order_sum_amount=Decimal(old_req['order_sum_amount']),
            order_sum_currency_paycash=old_req['order_sum_currency_paycash'],
            order_sum_bank_paycash=old_req['order_sum_bank_paycash'],
            shop_sum_amount=Decimal(old_req['shop_sum_amount']),
            shop_sum_currency_paycash=old_req['shop_sum_currency_paycash'],
            shop_sum_bank_paycash=old_req['shop_sum_bank_paycash'],
            payment_payer_code=old_req['payment_payer_code'],
            payment_type=old_req['payment_type'],
            action=old_req['action'],
            payment_datetime=_parse_iso_dt(old_req['payment_datetime']) if (
                'payment_datetime' in old_req and old_req['payment_datetime']) else None,
            cps_user_country_code=old_req.get('cps_user_country_code', None)
        )
        sqldb.session.add(new_req)
    try:
        sqldb.session.commit()
    except:
        raise

    PaymentSubscriptionObject.query.delete()
    sqldb.session.commit()

    subs_col = db['payment_subscription']
    for old_sub in subs_col.find():
        if 'user' not in old_sub or not isinstance(old_sub['user'], int):
            continue
        new_sub = PaymentSubscriptionObject(
            pay_info=old_sub['pay_info'],
            created=old_sub.get('created', datetime.utcnow()),
            end_dt=old_sub.get('end_dt', datetime.utcnow()),
            type=old_sub.get('type', 'subscription_3'),
            user_id=old_sub['user']
        )
        sqldb.session.add(new_sub)
    sqldb.session.commit()


def rollback(config, logger):
    pass

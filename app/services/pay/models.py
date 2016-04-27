# -*- coding: utf-8 -*-
from sqlalchemy.orm import relationship

from sqlalchemy.sql.functions import func
from sqlalchemy import Column, Unicode, DateTime, Integer, ForeignKey, DECIMAL, BigInteger, String
from sqlalchemy.dialects.postgresql import JSONB

from fw.db.sql_base import db as sqldb


class PaymentProvider(object):
    YAD = 1


class PurchaseServiceType(object):
    LLC_PURCHASE = "llc_purchase"
    LLC_AUTO_PURCHASE = "llc_auto_purchase"

    IP_PURCHASE = "ip_purchase"
    IP_AUTO_PURCHASE = "ip_auto_purchase"

    OSAGO_PART1 = "osago_part1"
    OSAGO_PART2 = "osago_part2"


class PaymentSubscriptionObject(sqldb.Model):
    __tablename__ = "payment_subscription"

    id = Column(Integer, primary_key=True)
    pay_info = Column(JSONB, nullable=False)
    created = Column(DateTime, nullable=False, default=func.now())
    end_dt = Column(DateTime, nullable=False)
    type = Column(Unicode, nullable=False)
    user_id = Column(Integer, ForeignKey('authuser.id'), index=True)
    user = relationship("AuthUser", uselist=False)

    pay_record_id = Column(Integer, nullable=False)
    payment_provider = Column(Integer, nullable=False)


class YadRequestsObject(sqldb.Model):
    __tablename__ = "yad_requests"

    id = Column(Integer, primary_key=True)

    ip = Column(Unicode, nullable=False)
    created = Column(DateTime, nullable=False, default=func.now())
    request_datetime = Column(DateTime, nullable=False)
    md5 = Column(Unicode, nullable=False)
    shop_id = Column(BigInteger, nullable=False)
    shop_article_id = Column(BigInteger, nullable=False)
    invoice_id = Column(BigInteger, nullable=False, index=True)
    order_number = Column(Unicode, nullable=False, index=True)
    customer_number = Column(Unicode, nullable=False, index=True)
    order_created_datetime = Column(DateTime, nullable=False)
    order_sum_amount = Column(DECIMAL, nullable=False)
    order_sum_currency_paycash = Column(Unicode, nullable=False)
    order_sum_bank_paycash = Column(Unicode, nullable=False)
    shop_sum_amount = Column(DECIMAL, nullable=False)
    shop_sum_currency_paycash = Column(Unicode, nullable=False)
    shop_sum_bank_paycash = Column(Unicode, nullable=False)
    payment_payer_code = Column(Unicode, nullable=False)
    payment_type = Column(Unicode, nullable=False)
    action = Column(Unicode, nullable=False)
    payment_datetime = Column(DateTime, nullable=True)
    cps_user_country_code = Column(Unicode, nullable=True)

# "_id" : ObjectId("5502f094e64bcf076f79bc87"),
# "ip" : "77.75.157.170",
# "cps_user_country_code" : "RU",
# "request_datetime" : "2015-03-13T17:14:08.976+03:00",
# "shop_id" : "29372",
# "shop_sum_currency_paycash" : "10643",
# "order_sum_currency_paycash" : "10643",
# "order_created_datetime" : "2015-03-13T17:14:07.860+03:00",
# "shop_sum_amount" : "434.25",
# "order_sum_bank_paycash" : "1003",
# "shop_article_id" : "139366",
# "payment_datetime" : "2015-03-13T17:14:08.795+03:00",
# "md5" : "5411413BADFD93ECF8BD3F7D4DF24CD6",
# "shop_sum_bank_paycash" : "1003",
# "order_sum_amount" : "450.00",
# "payment_payer_code" : "4100322062290",
# "created" : ISODate("2015-03-13T14:13:40.197Z"),
# "invoice_id" : "2000000424994",
# "customer_number" : "5502efbde64bcf076f79bbcf",
# "payment_type" : "AC",
# "action" : "paymentAviso",
# "order_number" : "5502efc0e64bcf076f79bbd1"


class PayInfoObject(sqldb.Model):
    __tablename__ = "pay_info"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('authuser.id'), index=True)
    user = relationship("AuthUser", uselist=False)

    batch_id = Column(String, ForeignKey('doc_batch.id'), nullable=False)
    batch = relationship("DocumentBatchDbObject", uselist=False)

    pay_record_id = Column(Integer, index=True, nullable=False)
    payment_provider = Column(Integer, nullable=False)

    dt = Column(DateTime, nullable=True, default=func.now())
    service_type = Column(String, nullable=False)


# -*- coding: utf-8 -*-
from datetime import datetime

import hashlib
from dateutil.relativedelta import relativedelta
import dateutil.parser
import os
from decimal import Decimal
from flask import request, current_app, make_response, redirect, abort, Blueprint
import pytz
from fw.auth.models import AuthUser
from fw.db.sql_base import db as sqldb
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject
from fw.documents.enums import UserDocumentStatus, DocumentBatchTypeEnum
from fw.metrics import appcraft, mixpanel_metrics
from fw.storage.file_storage import FileStorage
from services.pay.models import PaymentSubscriptionObject, YadRequestsObject, PayInfoObject, PaymentProvider, \
    PurchaseServiceType

pay_bp = Blueprint('pay', __name__)


def _xml_resp(str_val):
    response = make_response(str_val)
    response.headers["Content-Type"] = "application/xml"
    return response


def _notify_admin(action, message, recipient_list):
    from fw.async_tasks import send_email
    for rec in recipient_list:
        send_email.send_email.delay(
            rec,
            'yad_request_error',
            action=action,
            message=message
        )


def parse_iso_dt(str_val):
    val = dateutil.parser.parse(str_val)
    return val.astimezone(pytz.timezone('utc')).replace(tzinfo=None)


@pay_bp.route('/payment/paymentAviso/', methods=['POST'])
def yad_payment_aviso():
    dt_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")  # u"2011-05-04T20:38:01.000+04:00"

    logger = current_app.logger

    request_datetime = request.form.get('requestDatetime', "")
    md5 = request.form.get('md5', "")
    shop_id = request.form.get('shopId', "")
    shop_article_id = request.form.get('shopArticleId', "")
    invoice_id = request.form.get('invoiceId', "")
    orderId = request.form.get('orderId', "")
    customer_number = request.form.get('customerNumber', "")
    order_created_datetime = request.form.get('orderCreatedDatetime', "")
    order_sum_amount = request.form.get('orderSumAmount', "")
    order_sum_currency_paycash = request.form.get('orderSumCurrencyPaycash', "")
    order_sum_bank_paycash = request.form.get('orderSumBankPaycash', "")
    shop_sum_amount = request.form.get('shopSumAmount', "")
    shop_sum_currency_paycash = request.form.get('shopSumCurrencyPaycash', "")
    shop_sum_bank_paycash = request.form.get('shopSumBankPaycash', "")
    payment_payer_code = request.form.get('paymentPayerCode', "")
    payment_type = request.form.get('paymentType', "")
    action = request.form.get('action', "")
    payment_datetime = request.form.get('paymentDatetime', "")
    cps_user_country_code = request.form.get('cps_user_country_code', "")

    invalid_request_error = u"""<?xml version="1.0" encoding="UTF-8"?>
<paymentAvisoResponse  performedDatetime="%s" code="200" invoiceId="%s" shopId="%s" message="msg"/>""" % (
        dt_str, invoice_id, shop_id)

    authorization_error = u"""<?xml version="1.0" encoding="UTF-8"?>
<paymentAvisoResponse  performedDatetime="%s" code="1" invoiceId="%s" shopId="%s" message="Invalid request: md5 sum does not match provided value"/>""" % (
        dt_str, invoice_id, shop_id)

    admins_emails = current_app.config['ADMIN_EMAIL_LIST']
    if not md5 or not shop_id or not action or not order_sum_amount or not order_sum_currency_paycash \
            or not order_sum_bank_paycash or not invoice_id or not customer_number or not orderId:
        current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
        _notify_admin(action, u"missing one of required arguments", admins_emails)
        return _xml_resp(invalid_request_error.replace(u'msg', u"missing one of required arguments"))

    shop_password = current_app.config['YAD_ESHOP_PASSWORD']
    yad_ip_list = current_app.config['YAD_IP_LIST']

    # MD5 calc
    # action;orderSumAmount;orderSumCurrencyPaycash;orderSumBankPaycash;shopId;invoiceId;customerNumber;shopPassword
    our_md5_string = "%s;%s;%s;%s;%s;%s;%s;%s" % (action, order_sum_amount, order_sum_currency_paycash,
                                                  order_sum_bank_paycash, shop_id, invoice_id, customer_number,
                                                  shop_password)

    m = hashlib.md5()
    m.update(our_md5_string)

    ip = None
    if 'X-Forwarded-For' in request.headers:
        ip = request.headers['X-Forwarded-For']
    if not ip and 'X-Real-Ip' in request.headers:
        ip = request.headers['X-Real-Ip']
    if not ip:
        ip = request.remote_addr

    new_item = YadRequestsObject(
        ip=ip,
        created=datetime.utcnow(),
        request_datetime=parse_iso_dt(request_datetime),
        md5=md5,
        shop_id=int(shop_id),
        shop_article_id=int(shop_article_id) if shop_article_id else 0,
        invoice_id=int(invoice_id),
        order_number=orderId,
        customer_number=customer_number,
        order_created_datetime=parse_iso_dt(order_created_datetime),
        order_sum_amount=Decimal(order_sum_amount),
        order_sum_currency_paycash=order_sum_currency_paycash,
        order_sum_bank_paycash=order_sum_bank_paycash,
        shop_sum_amount=Decimal(shop_sum_amount),
        shop_sum_currency_paycash=shop_sum_currency_paycash,
        shop_sum_bank_paycash=shop_sum_bank_paycash,
        payment_payer_code=payment_payer_code,
        payment_type=payment_type,
        action=action,
        payment_datetime=parse_iso_dt(payment_datetime),
        cps_user_country_code=cps_user_country_code
    )
    sqldb.session.add(new_item)
    sqldb.session.commit()

    if action != u'paymentAviso':
        current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
        _notify_admin(action, u"invalid action id: %s" % unicode(action), admins_emails)
        return _xml_resp(invalid_request_error.replace(u'msg', u"invalid action id: %s" % unicode(action)))

    if yad_ip_list:
        if ip not in yad_ip_list:
            current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
            _notify_admin(action, u"sender ip (%s) not in whitelist" % ip, admins_emails)
            return _xml_resp(invalid_request_error.replace(u'msg', u"sender ip not in whitelist"))
    else:
        current_app.logger.warn(u"Can't check IP address: YAD_IP_LIST config option is empty")

    if m.hexdigest().upper() != md5:
        current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
        _notify_admin(action, u"arguments md5 digests do not match", admins_emails)
        return _xml_resp(authorization_error)

    try:
        auth_user_id = customer_number
        batch_id = orderId if orderId not in ('subscription_3', 'subscription_1') else None
        subs_type = orderId if orderId in ('subscription_3', 'subscription_1') else None
        if not batch_id and not subs_type:
            raise Exception("Invalid order number:%s" % orderId)
    except Exception:
        current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
        _notify_admin(action, u"Invalid user id or batch id", admins_emails)
        return _xml_resp(invalid_request_error.replace(u'msg', u"Invalid user id or batch id"))

    user = AuthUser.query.filter_by(uuid=auth_user_id).scalar()
    if not user:
        current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
        _notify_admin(action, u"User with id %s not found" % unicode(auth_user_id), admins_emails)
        return _xml_resp(invalid_request_error.replace(u'msg', u"User not found"))

    success_result = u"""<?xml version="1.0" encoding="UTF-8"?>
    <paymentAvisoResponse performedDatetime ="%s" code="0" invoiceId="%s" shopId="%s"/>""" % (
        dt_str, invoice_id, shop_id)

    pay_info = {
        'dt': datetime.now(),
        'shop_id': shop_id,
        'invoice_id': invoice_id,
        'order_sum_amount': order_sum_amount,
        'order_sum_currency_paycash': order_sum_currency_paycash,
        'order_sum_bank_paycash': order_sum_bank_paycash
    }

    if shop_article_id is not None:
        pay_info['shop_article_id'] = shop_article_id
    if order_created_datetime:
        pay_info['order_created_datetime'] = order_created_datetime
    if shop_sum_amount:
        pay_info['shop_sum_amount'] = shop_sum_amount
    if shop_sum_currency_paycash:
        pay_info['shop_sum_currency_paycash'] = shop_sum_currency_paycash
    if shop_sum_bank_paycash:
        pay_info['shop_sum_bank_paycash'] = shop_sum_bank_paycash
    if payment_payer_code:
        pay_info['payment_payer_code'] = payment_payer_code
    if payment_type:
        pay_info['payment_type'] = payment_type
    if payment_datetime:
        pay_info['payment_datetime'] = payment_datetime
    if cps_user_country_code:
        pay_info['cps_user_country_code'] = cps_user_country_code
    if request_datetime:
        pay_info['request_datetime'] = request_datetime

    if batch_id:
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).scalar()

        if not batch:
            current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
            _notify_admin(action, u"Batch with id %s not found" % batch_id, admins_emails)
            return _xml_resp(invalid_request_error.replace(u'msg', u"Batch not found"))

        modify_result = DocumentBatchDbObject.query.filter_by(id=batch_id).update({
            "pay_info": pay_info,
            "paid": True
        })
        if batch.batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC:
            pay_info = PayInfoObject(
                user=batch._owner,
                batch=batch,
                pay_record_id=new_item.id,
                payment_provider=PaymentProvider.YAD,
                service_type=PurchaseServiceType.LLC_PURCHASE
            )
            sqldb.session.add(pay_info)
            sqldb.session.commit()
        elif batch.batch_type == DocumentBatchTypeEnum.DBT_OSAGO:
            count = PayInfoObject.query.filter_by(batch=batch).count()
            osago_service_code = PurchaseServiceType.OSAGO_PART1 if count < 1 else PurchaseServiceType.OSAGO_PART2
            pay_info = PayInfoObject(
                user=batch._owner,
                batch=batch,
                pay_record_id=new_item.id,
                payment_provider=PaymentProvider.YAD,
                service_type=osago_service_code
            )
            sqldb.session.add(pay_info)
            batch.paid = True
            sqldb.session.commit()
            event = {
                PurchaseServiceType.OSAGO_PART1: 'rerender_pretension',
                PurchaseServiceType.OSAGO_PART2: 'rerender_claim'
            }.get(osago_service_code, None)
            if event:
                BatchManager.handle_event(batch_id, event, {'batch_id': batch_id}, current_app.logger, current_app.config)

        if modify_result is None:
            logger.error(u"Failed to set payment info to batch")
            _notify_admin(action, u"Failed to set payment info to batch", admins_emails)
            return _xml_resp(invalid_request_error.replace(u'msg', u"Failed to process"))

        try:
            for doc in BatchDocumentDbObject.query.filter_by(batch=batch, status=UserDocumentStatus.DS_RENDERED):
                if not doc.file:
                    continue

                file_obj = doc.file
                if not file_obj:
                    logger.error(u"Can't replace watermarked file: Failed to find file of batch %s" % batch_id)
                    continue

                file_path = FileStorage.get_path(file_obj, current_app.config)
                if not file_path or not os.path.exists(file_path) or not os.path.exists(file_path + '.src'):
                    logger.error(
                        u"Can't replace watermarked file: Failed to find original or source file %s of batch %s" % (
                            unicode(file_path + '.src'), batch_id))
                    continue
                os.rename(file_path + '.src', file_path)
        except Exception:
            current_app.logger.exception(u"FAILED TO REPLACE WATERMARKED DOCS")

        if current_app.config.get('PROD', False):
            appcraft.send_stat(batch.batch_type + '_payment_received', batch._owner, batch.id, batch.batch_type, int(invoice_id))
            mixpanel_metrics.send_stat(batch.batch_type + '_payment_received', batch._owner, batch.id, batch.batch_type)

        try:
            if batch.batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC:
                BatchManager.send_batch_docs_to_user(batch_id, current_app.config)
        except Exception:
            logger.exception(u"Failed to send documents to user.")
    elif subs_type:
        user_subs = PaymentSubscriptionObject.query.filter(
            PaymentSubscriptionObject.user == user,
            PaymentSubscriptionObject.end_dt.__ge__(datetime.utcnow())
        )

        if not user_subs.count():
            end_date = datetime.utcnow()
            if subs_type == 'subscription_3':
                end_date += relativedelta(months=3)
            elif subs_type == 'subscription_1':
                end_date += relativedelta(months=1)

            new_subs = PaymentSubscriptionObject(
                pay_info=pay_info,
                created=datetime.utcnow(),
                end_dt=end_date,
                user=user,
                type=subs_type
            )
            sqldb.session.add(new_subs)
            sqldb.session.commit()

            from fw.async_tasks import not_paid_check_send

            not_paid_check_send.make_all_user_fin_batch_paid_and_replace_watermarked_docs_with_normal.delay(
                user_id=user.id)

    current_app.logger.info(u"yad - success")
    return _xml_resp(success_result)


    # request


# Параметр	                    Тип	                        Описание
#   requestDatetime	                xs:dateTime	                Момент формирования запроса в ИС Оператора.
#   md5	                            xs:normalizedString, ровно 32 шестнадцатеричных символа, в верхнем регистре	    MD5-хэш параметров платежной формы, правила формирования описаны в разделе 4.4 «Правила обработки HTTP-уведомлений Контрагентом».
#   shopId	                        xs:long	                    Идентификатор Контрагента, присваиваемый Оператором.
#   shopArticleId	                xs:long	                    Идентификатор товара, присваиваемый Оператором.
#   invoiceId	                    xs:long	                    Уникальный номер транзакции в ИС Оператора.
#   orderNumber	                    xs:normalizedString, до 64 символов	        Номер заказа в ИС Контрагента. Передается, только если был указан в платежной форме.
#   customerNumber	                xs:normalizedString, до 64 символов	        Идентификатор плательщика (присланный в платежной форме) на стороне Контрагента: номер договора, мобильного телефона и т.п.
#   orderCreatedDatetime	        xs:dateTime	                Момент регистрации заказа в ИС Оператора.
#   orderSumAmount	                CurrencyAmount	            Стоимость заказа. Может отличаться от суммы платежа, если пользователь платил в валюте, которая отличается от указанной в платежной форме. В этом случае Оператор берет на себя все конвертации.
#   orderSumCurrencyPaycash	        CurrencyCode	            Код валюты для суммы заказа.
#   orderSumBankPaycash	            CurrencyBank	            Код процессингового центра Оператора для суммы заказа.
#   shopSumAmount	                CurrencyAmount	            Сумма к выплате Контрагенту на р/с (стоимость заказа минус комиссия Оператора).
#   shopSumCurrencyPaycash	        CurrencyCode	            Код валюты для shopSumAmount.
#   shopSumBankPaycash	            CurrencyBank	            Код процессингового центра Оператора для shopSumAmount.
#   paymentPayerCode	            YMAccount	                Номер счета в ИС Оператора, с которого производится оплата.
#   paymentType	xs:normalizedString	Способ оплаты заказа.       Список значений приведен в таблице 6.6.1.

#   action	                        xs:normalizedString, до 16 символов	    Тип запроса, значение: paymentAviso.
#   paymentDatetime	                xs:dateTime	                            Момент регистрации оплаты заказа в ИС Оператора.
#   cps_user_country_code	        xs:string, 2 символа	                Двухбуквенный код страны плательщика в соответствии с ISO 3166-1 alpha-2.

#   Любые названия, отличные от перечисленных выше	xs:string	Параметры, добавленные Контрагентом в платежную форму.

# RESPONSE

#Параметр	            Тип	                        Описание
#performedDatetime	    xs:dateTime	                Момент обработки запроса по часам ИС Контрагента.
#code	                xs:int	                    Код результата обработки. Список допустимых значений приведен в таблице ниже.
#shopId	                xs:long	                    Идентификатор Контрагента. Должен дублировать поле shopId запроса.
#invoiceId	            xs:long	                    Идентификатор транзакции в ИС Оператора. Должен дублировать поле invoiceId запроса.
#orderSumAmount	        CurrencyAmount	            Стоимость заказа в валюте, определенной параметром запроса orderSumCurrencyPaycash.
#message	                xs:string, до 255 символов	Текстовое пояснение в случае отказа принять платеж.
#techMessage	            xs:string, до 64 символов	Дополнительное текстовое пояснение ответа Контрагента. Как правило, используется как дополнительная информация об ошибках. Необязательное поле.


# result codes

#   0	    Успешно	Успешно — даже если Оператор прислал данный запрос повторно.
#   1	    Ошибка авторизации	Значение параметра md5 не совпадает с результатом расчета хэш-функции. Оператор не будет повторять запрос и пометит заказ как «Уведомление Контрагенту не доставлено».
#   200	    Ошибка разбора запроса	ИС Контрагента не в состоянии разобрать запрос. Оператор не будет повторять запрос и пометит заказ как «Уведомление Контрагенту не доставлено».

@pay_bp.route('/payment/checkOrder/', methods=['POST'])
def yad_check_order():
    dt_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000+00:00")  # u"2011-05-04T20:38:01.000+04:00"

    request_datetime = request.form.get('requestDatetime', "")
    action = request.form.get('action', "")
    md5 = request.form.get('md5', "")
    shop_id = request.form.get('shopId', "")
    shop_article_id = request.form.get('shopArticleId', "")
    invoice_id = request.form.get('invoiceId', "")
    order_number = request.form.get('orderId', "")
    customer_number = request.form.get('customerNumber', "")
    order_created_datetime = request.form.get('orderCreatedDatetime', "")
    order_sum_amount = request.form.get('orderSumAmount', "")
    order_sum_currency_paycash = request.form.get('orderSumCurrencyPaycash', "")
    order_sum_bank_paycash = request.form.get('orderSumBankPaycash', "")
    shop_sum_amount = request.form.get('shopSumAmount', "")
    shop_sum_currency_paycash = request.form.get('shopSumCurrencyPaycash', "")
    shop_sum_bank_paycash = request.form.get('shopSumBankPaycash', "")
    payment_payer_code = request.form.get('paymentPayerCode', "")
    payment_type = request.form.get('paymentType', "")

    invalid_request_error = u"""<?xml version="1.0" encoding="UTF-8"?>
    <checkOrderResponse  performedDatetime="%s" code="200" invoiceId="%s" shopId="%s" message="msg"/>""" % (
        dt_str, invoice_id, shop_id)

    authorization_error = u"""<?xml version="1.0" encoding="UTF-8"?>
<checkOrderResponse  performedDatetime="%s" code="1" invoiceId="%s" shopId="%s" message="Invalid request: md5 sum does not match provided value"/>""" % (
        dt_str, invoice_id, shop_id)

    admins_emails = current_app.config['ADMIN_EMAIL_LIST']
    if not md5 or not shop_id or not action or not order_sum_amount or not order_sum_currency_paycash \
            or not order_sum_bank_paycash or not invoice_id or not customer_number or not order_number:
        current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
        _notify_admin(action, u"missing one of required arguments", admins_emails)
        return _xml_resp(invalid_request_error.replace(u'msg', u"missing one of required arguments"))

    shop_password = current_app.config['YAD_ESHOP_PASSWORD']
    yad_ip_list = current_app.config['YAD_IP_LIST']

    # MD5 calc
    # action;orderSumAmount;orderSumCurrencyPaycash;orderSumBankPaycash;shopId;invoiceId;customerNumber;shopPassword
    our_md5_string = "%s;%s;%s;%s;%s;%s;%s;%s" % (action, order_sum_amount, order_sum_currency_paycash,
                                                  order_sum_bank_paycash, shop_id, invoice_id, customer_number,
                                                  shop_password)

    m = hashlib.md5()
    m.update(our_md5_string)

    ip = None
    if 'X-Forwarded-For' in request.headers:
        ip = request.headers['X-Forwarded-For']
    if not ip and 'X-Real-Ip' in request.headers:
        ip = request.headers['X-Real-Ip']
    if not ip:
        ip = request.remote_addr

    new_item = YadRequestsObject(
        ip=ip,
        created=datetime.utcnow(),
        request_datetime=parse_iso_dt(request_datetime),
        md5=md5,
        shop_id=int(shop_id),
        shop_article_id=int(shop_article_id) if shop_article_id else 0,
        invoice_id=int(invoice_id),
        order_number=order_number,
        customer_number=customer_number,
        order_created_datetime=parse_iso_dt(order_created_datetime),
        order_sum_amount=Decimal(order_sum_amount),
        order_sum_currency_paycash=order_sum_currency_paycash,
        order_sum_bank_paycash=order_sum_bank_paycash,
        shop_sum_amount=Decimal(shop_sum_amount),
        shop_sum_currency_paycash=shop_sum_currency_paycash,
        shop_sum_bank_paycash=shop_sum_bank_paycash,
        payment_payer_code=payment_payer_code,
        payment_type=payment_type,
        action=action
    )
    sqldb.session.add(new_item)
    sqldb.session.commit()

    if action != u'checkOrder':
        current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
        _notify_admin(action, u"invalid action id: %s" % unicode(action), admins_emails)
        return _xml_resp(invalid_request_error.replace(u'msg', u"invalid action id: %s" % unicode(action)))

    if yad_ip_list:
        if ip not in yad_ip_list:
            current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
            _notify_admin(action, u"sender ip (%s) not in whitelist" % ip, admins_emails)
            return _xml_resp(invalid_request_error.replace(u'msg', u"sender ip not in whitelist"))
    else:
        current_app.logger.warn(u"Can't check IP address: YAD_IP_LIST config option is empty")

    if m.hexdigest().upper() != md5:
        current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
        _notify_admin(action, u"arguments md5 digests do not match", admins_emails)
        return _xml_resp(authorization_error)

    try:
        auth_user_id = customer_number
        batch_id = order_number if order_number not in ('subscription_3', 'subscription_1') else None
        subs_type = order_number if order_number in ('subscription_3', 'subscription_1') else None
        if not batch_id and not subs_type:
            raise Exception("Invalid order number:%s" % order_number)
    except Exception:
        current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
        _notify_admin(action, u"Invalid user id or batch id", admins_emails)
        return _xml_resp(invalid_request_error.replace(u'msg', u"Invalid user id or batch id"))

    reject_error = u"""<?xml version="1.0" encoding="UTF-8"?>
<checkOrderResponse  performedDatetime="%s" code="100" invoiceId="%s" shopId="%s" message="msg"/>""" % (
        dt_str, invoice_id, shop_id)

    user = AuthUser.query.filter_by(uuid=auth_user_id).scalar()
    if not user:
        current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
        _notify_admin(action, u"User with id %s not found" % unicode(auth_user_id), admins_emails)
        return _xml_resp(reject_error.replace(u'msg', u"User not found"))

    if batch_id:
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).scalar()

        if not batch:
            current_app.logger.warn(u"Invalid request from yad: %s" % unicode(request.form))
            _notify_admin(action, u"Batch with id %s not found" % batch_id, admins_emails)
            return _xml_resp(reject_error.replace(u'msg', u"Batch not found"))

        if batch.batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC:
            pay_info = PayInfoObject.query.filter_by(batch_id=batch_id).first()
            if pay_info or batch.paid:
                current_app.logger.warn(u"Batch already paid!")
                _notify_admin(action, u"Batch with id %s is already paid" % batch_id, admins_emails)
                return _xml_resp(reject_error.replace(u'msg', u"Услуга уже оплачена"))
        elif batch.batch_type == DocumentBatchTypeEnum.DBT_OSAGO:
            payments = PayInfoObject.query.filter_by(batch_id=batch_id).count()
            if payments > 1:
                current_app.logger.warn(u"Batch already paid!")
                _notify_admin(action, u"Batch with id %s is already paid" % batch_id, admins_emails)
                return _xml_resp(reject_error.replace(u'msg', u"Услуга уже оплачена"))
        else:
            current_app.logger.warn(u"Invalid batch type: %s" % batch.batch_type)
            return _xml_resp(reject_error.replace(u'msg', u"Данная услуга не продается"))

    elif subs_type:
        user_subs = PaymentSubscriptionObject.query.filter(
            PaymentSubscriptionObject.user == user,
            PaymentSubscriptionObject.end_dt.__ge__(datetime.utcnow())
        )

        if user_subs.count() > 0:
            current_app.logger.warn(u"User has subscription already!")
            _notify_admin(action, u"User with id %s already has subscription" % unicode(auth_user_id), admins_emails)
            return _xml_resp(reject_error.replace(u'msg', u"Услуга уже оплачена"))

    success_result = u"""<?xml version="1.0" encoding="UTF-8"?>
<checkOrderResponse performedDatetime ="%s" code="0" invoiceId="%s"  shopId="%s"/>""" % (dt_str, invoice_id, shop_id)

    current_app.logger.info(u"yad - success. returning %s" % success_result)
    return _xml_resp(success_result)

    # request


#   Параметр	                    Тип	                        Описание
#   requestDatetime	                xs:dateTime	                Момент формирования запроса в ИС Оператора.
#   action	                        xs:normalizedString, до 16 символов	        Тип запроса. Значение: «checkOrder» (без кавычек).
#   md5	                            xs:normalizedString, ровно 32 шестнадцатеричных символа, в верхнем регистре	    MD5-хэш параметров платежной формы, правила формирования описаны в разделе 4.4 «Правила обработки HTTP-уведомлений Контрагентом».
#   shopId	                        xs:long	                    Идентификатор Контрагента, присваиваемый Оператором.
#   shopArticleId	                xs:long	                    Идентификатор товара, присваиваемый Оператором.
#   invoiceId	                    xs:long	                    Уникальный номер транзакции в ИС Оператора.
#   orderNumber	                    xs:normalizedString, до 64 символов	        Номер заказа в ИС Контрагента. Передается, только если был указан в платежной форме.
#   customerNumber	                xs:normalizedString, до 64 символов	        Идентификатор плательщика (присланный в платежной форме) на стороне Контрагента: номер договора, мобильного телефона и т.п.
#   orderCreatedDatetime	        xs:dateTime	                Момент регистрации заказа в ИС Оператора.
#   orderSumAmount	                CurrencyAmount	            Стоимость заказа. Может отличаться от суммы платежа, если пользователь платил в валюте, которая отличается от указанной в платежной форме. В этом случае Оператор берет на себя все конвертации.
#   orderSumCurrencyPaycash	        CurrencyCode	            Код валюты для суммы заказа.
#   orderSumBankPaycash	            CurrencyBank	            Код процессингового центра Оператора для суммы заказа.
#   shopSumAmount	                CurrencyAmount	            Сумма к выплате Контрагенту на р/с (стоимость заказа минус комиссия Оператора).
#   shopSumCurrencyPaycash	        CurrencyCode	            Код валюты для shopSumAmount.
#   shopSumBankPaycash	            CurrencyBank	            Код процессингового центра Оператора для shopSumAmount.
#   paymentPayerCode	            YMAccount	                Номер счета в ИС Оператора, с которого производится оплата.
#   paymentType	xs:normalizedString	Способ оплаты заказа.       Список значений приведен в таблице 6.6.1.
#   Любые названия, отличные от перечисленных выше	xs:string	Параметры, добавленные Контрагентом в платежную форму.

# response:
#Параметр	            Тип	                        Описание
#performedDatetime	    xs:dateTime	                Момент обработки запроса по часам ИС Контрагента.
#code	                xs:int	                    Код результата обработки. Список допустимых значений приведен в таблице ниже.
#shopId	                xs:long	                    Идентификатор Контрагента. Должен дублировать поле shopId запроса.
#invoiceId	            xs:long	                    Идентификатор транзакции в ИС Оператора. Должен дублировать поле invoiceId запроса.
#orderSumAmount	        CurrencyAmount	            Стоимость заказа в валюте, определенной параметром запроса orderSumCurrencyPaycash.
#message	                xs:string, до 255 символов	Текстовое пояснение в случае отказа принять платеж.
#techMessage	            xs:string, до 64 символов	Дополнительное текстовое пояснение ответа Контрагента. Как правило, используется как дополнительная информация об ошибках. Необязательное поле.

# result codes
#   Код	    Значение	                Описание ситуации
#   0	    Успешно	                    Контрагент дал согласие и готов принять перевод.
#   1	    Ошибка авторизации	        Несовпадение значения параметра md5 с результатом расчета хэш-функции. Оператор считает ошибку окончательной и не будет осуществлять перевод.
#   100	    Отказ в приеме перевода	    Отказ в приеме перевода с заданными параметрами. Оператор считает ошибку окончательной и не будет осуществлять перевод.
#   200	    Ошибка разбора запроса	    ИС Контрагента не в состоянии разобрать запрос. Оператор считает ошибку окончательной и не будет осуществлять перевод.


@pay_bp.route('/payment/redirect/', methods=['GET'])
def yad_redirect():
    has_error = request.args.get('payerr', "false") == "true"
    success_url = request.args.get('shopSuccessURL', "")
    fail_url = request.args.get('shopFailURL', "")

    if has_error and fail_url:
        return redirect(fail_url)
    if not has_error and success_url:
        return redirect(success_url)
    abort(400)

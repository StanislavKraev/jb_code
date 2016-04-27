# -*- coding: utf-8 -*-
from celery import current_app as celery
from flask.templating import render_template


@celery.task(default_retry_delay=15,max_retries=10)
def send_sms(number_to, sms_type, **kwargs):
    sms_sender = celery.conf.get('SMS_SENDER')

    with celery.conf['flask_app']().app_context():
        text = render_template("sms/%s.sms" % sms_type, **kwargs)

        values = {
            'phones':number_to,
            'mes':unicode(text),
            'charset':'utf-8',
            'fmt' : 3   # json response
        }
        # check sms cost first. do not send if more than 3 rubles
        values_cost = values.copy()
        values_cost['cost'] = 1
        try:
            cost = sms_sender.get_sms_cost(values)
        except Exception, ex:
            raise RuntimeError("Bad answer from sms gate: %s" % unicode(ex))

        if cost > 3.0:
            raise RuntimeError("SMS cost too big: %s. number: %s, message length: %d" % (str(cost), number_to, len(text)))

        try:
            sms_sender.send(values)
        except Exception, ex:
            raise RuntimeError("Error sending sms: %s" % str(ex))

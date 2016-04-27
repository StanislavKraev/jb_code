# -*- coding: utf-8 -*-
from datetime import datetime
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
#noinspection PyUnresolvedReferences
from email.MIMEBase import MIMEBase
from email.header import Header
from email import Encoders
from flask.templating import render_template
from celery import current_app as celery
from flask.globals import current_app
from fw.async_tasks import core_tasks
from fw.transport.mail import fix_email_addr
from services.partners.models import BankPartnersObject, BankPartnerRequestObject

celery.config_from_envvar('CELERY_CONFIG_MODULE')

def _send_email_raw(addr_to, email_type, subject="", addr_from="", attach=None, reply_to = None, **tmpl_data):
    mailer = celery.conf.get('MAILER')

    config = celery.conf.get('config')
    with celery.conf['flask_app']().app_context():
        html_text = tmpl_data.get('html_text', None)
        if html_text is None:
            html_text = render_template('email/%s.html' % email_type, **tmpl_data)

        plain_text = tmpl_data.get('plain_text', None)
        if plain_text is None:
            plain_text = render_template('email/%s.text' % email_type, **tmpl_data)

        subject_text = subject or tmpl_data.get('subject_text', None)
        if not subject_text:
            subject_text = render_template('email/%s.subject' % email_type, **tmpl_data)

        reply_to = fix_email_addr(reply_to or config['mailer_reply_to'])
        if reply_to:
            addr_from = reply_to
        else:
            addr_from = fix_email_addr(addr_from or config['mailer_smtp_user'])
        addr_to = fix_email_addr(addr_to)
        message_id = smtplib.email.Utils.make_msgid()

        msg = MIMEMultipart()
        msg['To'] = addr_to
        msg['From'] = addr_from
        msg['Date'] = smtplib.email.Utils.formatdate(localtime = 1)
        msg['Subject'] = Header(subject_text, 'utf-8')
        msg['Message-ID'] = message_id
        msg.add_header('reply-to', reply_to)

        msg_internal = MIMEMultipart('alternative')

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(plain_text, 'plain', 'utf-8')
        part2 = MIMEText(html_text, 'html', 'utf-8')
        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg_internal.attach(part1)
        msg_internal.attach(part2)
        msg.attach(msg_internal)
        # attach attachments
        logger = current_app.logger
        if attach:
            if not isinstance(attach, list):
                attach = [attach,]
            for attachment in attach:
                if isinstance(attachment, dict):
                    file_name = attachment['file_name']
                    file_path = attachment['file_path']
                else:
                    file_name = None
                    file_path = attachment

                ext = file_path.split('.')[-1]
                # define application type
                if ext=='pdf':
                    attachFile = MIMEBase('application', 'pdf')
                elif ext=='doc' or ext=='docx':
                    attachFile = MIMEBase('application', 'msword')
                elif ext=='jpg' or ext=='jpeg':
                    attachFile = MIMEBase('image', 'jpeg')
                elif ext=='png':
                    attachFile = MIMEBase('image', 'png')
                else:
                    attachFile = MIMEBase('application', 'octet-stream')
                    # get file
                full_path = file_path
                # load the data into attachment object
                att_file = open(full_path, 'rb')
                attachFile.set_payload(att_file.read())
                att_file.close()
                Encoders.encode_base64(attachFile)
                file_name = file_name or file_path.split('/')[-1]
                try:
                    att_header = Header(file_name.encode('utf-8'), 'utf-8')
                    attachFile.add_header('Content-Disposition', 'attachment; filename="%s"' % att_header)
                except Exception:
                    logger.exception(u"Failed to add utf-8 header")
                    attachFile.add_header('Content-Disposition', 'attachment', file_name)
                # attach it to message
                msg.attach(attachFile)
            # email params

        logger.info(u"Sending %s email to %s. ID:%s" % (email_type, addr_to, message_id))
        mailer.send_email(addr_from, addr_to, msg.as_string())

        return message_id

@celery.task(default_retry_delay=60, max_retries=5)
def send_email(addr_to, email_type, subject="", addr_from="", attach=None, reply_to = None, **tmpl_data):
    return _send_email_raw(addr_to, email_type, subject=subject, addr_from=addr_from, attach=attach, reply_to = reply_to, **tmpl_data)


@celery.task()
def send_email_plugin(batch_id, event_data, addr, email_type, max_retries=0, retry_timeout_seconds=None, silent=False, template_data=None):
    template_data = template_data or {}
    try:
        _send_email_raw(addr, email_type, **template_data)
        if not silent:
            core_tasks.send.delay(batch_id, 'emailer.mail_sent', event_data)
    except Exception, ex:
        try:
            timeout = 0
            if retry_timeout_seconds is not None:
                if isinstance(retry_timeout_seconds, list):
                    timeout = retry_timeout_seconds[0]
                    if len(retry_timeout_seconds) > 1:
                        retry_timeout_seconds = retry_timeout_seconds[1:]
                else:
                    timeout = retry_timeout_seconds
            if max_retries > 0:
                send_email_plugin.apply_async(args=(batch_id, event_data, addr, email_type), kwargs={
                    'max_retries': max_retries - 1,
                    'retry_timeout_seconds': retry_timeout_seconds,
                    'silent': silent,
                    'template_data': template_data}, countdown=timeout)
                return False
            else:
                if not silent:
                        core_tasks.send.delay(batch_id, 'emailer.send_fail', event_data)
        except Exception, ex:
            if not silent:
                core_tasks.send.delay(batch_id, 'emailer.send_fail', event_data)
            raise

@celery.task()
def send_email_to_partner_and_set_result(addr_to, email_type, batch_id, bank_id, bank_contact_phone_general_manager,
                                         bank_contact_phone, send_private_data, **tmpl_data):
    with celery.conf['flask_app']().app_context():
        partner = BankPartnersObject.query.filter_by(id=bank_id).first()
        req = BankPartnerRequestObject.query.filter_by(bank_partner_id=partner.id, batch_id=batch_id).first()
        if not req:
            return False

        status = "success"
        try:
            if isinstance(addr_to, list):
                for addr in addr_to:
                    send_email(addr, email_type, **tmpl_data)
            else:
                send_email(addr_to, email_type, **tmpl_data)
        except Exception, ex:
            logger = current_app.logger
            logger.exception(u"Failed to send email")
            status = "failed"

        BankPartnerRequestObject.query.filter_by(id=req.id, status='sending').update({
            'status': status,
            'sent_date': datetime.utcnow(),
            'bank_contact_phone_general_manager': bank_contact_phone_general_manager,
            'bank_contact_phone': bank_contact_phone,
            'send_private_data': send_private_data
        })

    return status == "success"

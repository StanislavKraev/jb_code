# -*- coding: utf-8 -*-
import smtplib
import codecs
from email.utils import formataddr
import os
import shlex
import subprocess
import tempfile

from flask.templating import render_template
from dateutil.parser import parse as parse_date_time
import imaplib
import logging
import poplib
import uuid

import email
from email.header import decode_header, Header
from common_utils import is32bit


class EmailMessage(object):
    def __init__(self, content, mail_id, body, from_hdr, to_hdr, date_hdr, subject, attachments):
        self.content = content
        self.mail_id = unicode(mail_id)
        self.body = unicode(body)
        self.from_hdr = unicode(from_hdr)
        self.to_hdr = unicode(to_hdr)
        self.date_hdr = date_hdr
        self.subject = unicode(subject)
        self.attachments = attachments

    def save_to_filename(self, filename):
        with open(filename, 'wb') as f:
            f.write(self.content)


class ReceiptMessage(EmailMessage):
    def __init__(self, mail_id, original_mail_id, content, body, from_hdr, to_hdr, date_hdr, subject, attachments):
        super(ReceiptMessage, self).__init__(content, mail_id, body, from_hdr, to_hdr, date_hdr, subject, attachments)
        self.original_mail_id = original_mail_id


class ImapReader(object):
    def __init__(self, domain, port, ssl, user, password):
        self.domain = domain
        self.port = port
        self.ssl = ssl
        self.user = user
        self.password = password

        self._client = None

    def read(self, **kwargs):
        if not self._client:
            # internet connection
            self._client = imaplib.IMAP4(host=self.domain, port=self.port) if not self.ssl else imaplib.IMAP4_SSL(host=self.domain, port=self.port)
            self._client.login(self.user, self.password)
            self._client.select()

        typ, data = self._client.search(None, '(ALL)')

        for num in data[0].split():
            typ, data = self._client.fetch(num, '(BODY.PEEK[])')

            result = get_decoded_email_body(data[0][1])
            if not result:
                continue

            if result[0] == 'receipt':
                mail_id, original_mail_id, content, body, from_hdr, to_hdr, date_hdr, subject, attachments = result[1:]
                yield ReceiptMessage(mail_id, original_mail_id, content, body, from_hdr, to_hdr, date_hdr, subject, attachments)
            else:
                content, mail_id, body, from_hdr, to_hdr, date_hdr, subject, attachments = result
                yield EmailMessage(content, mail_id, body, from_hdr, to_hdr, date_hdr, subject, attachments)

        self._client.close()
        self._client.logout()
        self._client = None


class Pop3Reader(object):
    def __init__(self, domain, port, ssl, user, password, delete_on_receive, proxy):
        self.domain = domain
        self.port = port
        self.ssl = ssl
        self.user = user
        self.password = password
        self.delete_on_receive = delete_on_receive

        self._client = None
        self.proxy = proxy

    def read(self, tester = None):
        with self.proxy:
            if not self._client:
                # internet connection
                self._client = poplib.POP3(host=self.domain, port=self.port) if not self.ssl else poplib.POP3_SSL(host=self.domain, port=self.port)
                self._client.user(self.user)
                self._client.pass_(self.password)

        numMessages, msgBytes = self._client.stat()
        for i in range(numMessages):
            if tester is not None:
                hdr, message, octets = self._client.top(i + 1, 0)
                result = get_decoded_email_body('\r\n'.join(message))
                if not result:
                    continue
                mail_id = result[1]
                if not tester(mail_id):
                    continue

            hdr, message, octets = self._client.retr(i + 1)
            result = get_decoded_email_body('\r\n'.join(message))
            if not result:
                continue
            if self.delete_on_receive:
                self._client.dele(i + 1)
            if result[0] == 'receipt':
                mail_id, original_mail_id, content, body, from_hdr, to_hdr, date_hdr, subject, attachments = result[1:]
                logging.info(u"Got an email read receipt: mail_id:%s, original_mail_id:%s, from_hdr:%s, date_hdr:%s" % (unicode(mail_id), unicode(original_mail_id), unicode(from_hdr), unicode(date_hdr)))
                yield ReceiptMessage(mail_id, original_mail_id, content, body, from_hdr, to_hdr, date_hdr, subject, attachments)
            else:
                content, mail_id, body, from_hdr, to_hdr, date_hdr, subject, attachments = result
                logging.info(u"Got an email: mail_id:%s, from_hdr:%s, date_hdr:%s" % (unicode(mail_id), unicode(from_hdr), unicode(date_hdr)))
                yield EmailMessage(content, mail_id, body, from_hdr, to_hdr, date_hdr, subject, attachments)

        self._client.quit()
        self._client = None


def get_decoded_header(header, try_charset = None):

    result_list = []
    items = decode_header(header)
    for subject, encoding in items:

        if encoding is None:
            try:
                unicode(subject)
                result_list.append(subject)
            except Exception:
                if try_charset:
                    result_list.append(subject.decode(try_charset))
                result_list.append(subject)
        else:
            result_list.append(subject.decode(encoding))
    return u" ".join(result_list)

class EmailAttachment(object):

    def __init__(self, filename, content):
        self.filename = filename
        self.content = content

def get_email_attachment(message_part):
    charset = message_part.get_content_charset()
    content_type = message_part.get_content_type()
    filename = message_part.get_filename('')

    content_type, subtype = content_type.split('/')

    try:
        if content_type == 'text':
            if not filename:
                logging.warn(u'Skipping attachment without name')
                return
            if not charset:
                return EmailAttachment(filename, message_part.get_payload(decode=True))
            return EmailAttachment(filename, unicode(message_part.get_payload(decode=True), str(charset), "ignore"))
        if content_type in ('application', 'audio', 'image', 'video'):
            if not filename:
                logging.warn(u'Skipping attachment without name')
                return
            return EmailAttachment(filename, message_part.get_payload(decode=True))
        if content_type in ('multipart', 'message'):
            filename = unicode(uuid.uuid1()) + '.eml'
            return EmailAttachment(filename, message_part.as_string(unixfrom=True))
    except Exception:
        logging.exception(u"Failed to get mail attachment")

def parse_simple_email(msg):
    text = None
    html = None

    for part in msg.get_payload():
        if part.get_content_charset() is None:
            continue

        charset = part.get_content_charset()
        content_type = part.get_content_type()

        if content_type == 'text/plain':
            text = unicode(part.get_payload(decode=True), str(charset), "ignore")

        if content_type == 'text/html':
            html = unicode(part.get_payload(decode=True), str(charset), "ignore")

    return text, html

def parse_mixed_email(msg):
    text = ""
    html = ""
    attachments = []

    for part in msg.get_payload():
        content_disposition = (part.get('Content-Disposition') or '').strip()
        content_type = part.get_content_type()
        charset = part.get_content_charset()

        if content_type == 'multipart/alternative':
            text, html = parse_simple_email(part)
        elif content_disposition.startswith('inline') or content_disposition.startswith('attachment'):
            attachment = get_email_attachment(part)
            if not attachment:
                logging.warn(u'Failed to get attachment from part %s' % part.as_string())
            attachments.append(attachment)
        elif content_type == 'text/plain':
            text = unicode(part.get_payload(decode=True), str(charset), "ignore")
        elif content_type == 'text/html':
            html = unicode(part.get_payload(decode=True), str(charset), "ignore")

    return text, html, attachments

def parse_report_email(msg):
    for part in msg.get_payload():
        content_type = part.get_content_type()

        if content_type == 'message/disposition-notification':
            notification_payload = part.get_payload()[0]
            charset = notification_payload.get_content_charset()
            for header_name, header_val in notification_payload._headers:
                header_name = header_name.lower()
                if header_name == 'original-message-id':
                    receipt_message_id = get_decoded_header(header_val, charset)
                    return receipt_message_id


def get_decoded_email_body(message_body):
    msg = email.message_from_string(message_body)

    if 'message-id' not in msg:
        logging.error(u'Message without id!')
        return
    mail_id = unicode(msg['message-id'])

    from_hdr = ""
    to_hdr = ""
    date_hdr = ""
    subject = ""
    attachments = []

    #print('-' * 40 + '  ' + subject + '  ' + '-' * 40)
    root_content_type = msg.get_content_type()
    charset = msg.get_content_charset()

    for header_name, header_val in msg._headers:
        header_name = header_name.lower()
        if header_name == 'date':
            date_hdr = parse_date_time(header_val)  # Fri, 21 Feb 2014 17:04:36 +0400
        elif header_name == 'subject':
            subject = get_decoded_header(header_val, charset)
        elif header_name == 'from':
            from_hdr = get_decoded_header(header_val, charset)
        elif header_name == 'to':
            to_hdr = get_decoded_header(header_val, charset)


    text = ''
    html = ''

    if msg.is_multipart():

        if root_content_type == 'multipart/alternative':   # simple email (html + plain text)
            text, html = parse_simple_email(msg)
        elif root_content_type == 'multipart/mixed':       # email with attachments
            text, html, attachments = parse_mixed_email(msg)
        elif root_content_type == 'multipart/related':       # email with attachments
            text, html, attachments = parse_mixed_email(msg)
        elif root_content_type == 'multipart/report':       # probably return receipt
            receipt_original_message_id = parse_report_email(msg)
            return 'receipt', mail_id, receipt_original_message_id, msg.as_string(True), '', from_hdr, to_hdr, date_hdr, subject, attachments
        else:
            logging.warn(u'Unsupported mail root content type: %s' % root_content_type)
            return None

    elif root_content_type == 'text/plain':
        text = unicode(msg.get_payload(decode=True), str(charset), "ignore")
    elif root_content_type == 'text/html':
        html = unicode(msg.get_payload(decode=True), str(charset), "ignore")

    body = text or html
#    print('body: %s\r\nnumber of attachments: %d' % (body[:400], len(attachments)))
    return msg.as_string(True), mail_id, body, from_hdr, to_hdr, date_hdr, subject, attachments

def create_temp_attachment(template, **template_data):
    html_text = render_template(template, **template_data)

    t_file = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".html")
    t_file_name = t_file.name
    t_file.close()

    with codecs.open(t_file.name, 'wb', 'utf-8') as fo:
        fo.write(html_text)

    t_file_out = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".pdf")
    full_name = t_file_out.name
    t_file_out.close()

    # convert html to pdf
    rasterize_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../rasterize.js'))
    phantom_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../phantomjs%s' % ('32' if is32bit() else '')))
    subprocess.call(shlex.split('%s %s %s %s A4' % (phantom_path, rasterize_path, t_file_name, full_name)))
    os.unlink(t_file_name)

    return full_name

def fix_email_addr(addr):
    if u'<' in addr and u'>' in addr:
        try:
            name, addr = addr.split(u'<')
            addr = addr.replace(u'>', u"").strip()
            name = name.strip()
            return  formataddr((str(Header(name, 'utf-8')), addr))
        except Exception:
            pass
    return addr

def raw_email_address(addr):
    if u'<' in addr and '>' in addr:
        try:
            name, addr = addr.split(u'<')
            addr = addr.replace(u'>', u"").strip()
            return  addr
        except Exception:
            pass
    return addr

def get_email_reader(settings, config, proxy):
    domain = settings.source_email_host
    port = settings.source_email_port
    ssl = settings.source_email_use_ssl
    user = settings.source_email_user
    password = settings.source_email_password
    delete_on_receive = settings.source_email_delete_on_receive

    #    if config['source_email_is_imap']:
    #        return ImapReader(domain, port, ssl, user, password)
    #

    return Pop3Reader(domain, port, ssl, user, password, delete_on_receive, proxy)

class Mailer(object):

    def __init__(self, server, user, password):
        self.server = server
        self.user = user
        self.password = password

    def send_email(self, addr_from, addr_to, message):
        s = smtplib.SMTP(self.server)
        s.starttls()
        s.login(self.user, self.password)
        s.sendmail(addr_from, addr_to, message)
        s.quit()

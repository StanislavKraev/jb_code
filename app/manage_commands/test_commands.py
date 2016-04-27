# -*- coding: utf-8 -*-
# noinspection PyUnresolvedReferences
from email.MIMEBase import MIMEBase
from email.header import Header
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fw.documents.db_fields import BatchDocumentDbObject
from fw.documents.enums import BatchStatusEnum
from fw.transport.mail import Mailer

from manage_commands import BaseManageCommand

class CheckThatDocRecTypeFieldResidesInTheOnlyOneFounderInP11001DocumentOfBatch(BaseManageCommand):
    NAME = "check_single_rcf"

    def push_error(self, batch_id):
        self.logger.error(u"Batch %s has more than one documents_recipient_type mark in founders" % batch_id)

    def run(self):
        self.logger.info(u"Test that documents recipient type is in the only one founder")
        self.logger.info(u'=' * 50)

        invalid_batches = []
        batch_id_set = set()
        for doc in BatchDocumentDbObject.query.filter(BatchDocumentDbObject.batch.status.in_([BatchStatusEnum.BS_FINALISED,
                                                                                         BatchStatusEnum.BS_EDITED,
                                                                                         BatchStatusEnum.BS_NEW]),
                                                      BatchDocumentDbObject.document_type == "P11001"):
            batch_id = doc.batch.id
            if batch_id not in batch_id_set:
                batch_id_set.add(batch_id)
                if not doc.data:
                    continue

                founders = doc.data.get('founders', [])
                if not founders:
                    continue

                mark = False
                for founder in founders:
                    if founder and 'documents_recipient_type' in founder:
                        if mark:
                            self.push_error(batch_id)
                            invalid_batches.append(batch_id)
                        mark = True

        if invalid_batches:
            message = "Warning! Following batches has invalid founders (multiple documents_recipient_type marks): %s" % ', '.join(invalid_batches)

            mailer = Mailer(self.config['mailer_server'], self.config['mailer_smtp_user'], self.config['mailer_smtp_password'])
            for addr in ('kraevst@yandex.ru', 'kas@rocketscienceacademy.org'):
                msg = MIMEMultipart()
                msg['To'] = addr
                msg['From'] = self.config['mailer_smtp_user']
                msg['Date'] = smtplib.email.Utils.formatdate(localtime = 1)
                msg['Subject'] = Header("Warning! Some batches has invalid founders", 'utf-8')

                msg_internal = MIMEMultipart('alternative')

                # Record the MIME types of both parts - text/plain and text/html.
                part1 = MIMEText(message, 'plain', 'utf-8')
                part2 = MIMEText("<html><body>%s</body></html>" % message, 'html', 'utf-8')
                # Attach parts into message container.
                # According to RFC 2046, the last part of a multipart message, in this case
                # the HTML message, is best and preferred.
                msg_internal.attach(part1)
                msg_internal.attach(part2)
                msg.attach(msg_internal)

                mailer.send_email(self.config['mailer_smtp_user'], addr, msg.as_string())

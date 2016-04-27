# -*- coding: utf-8 -*-
from datetime import datetime

from common_utils import get_russian_month_skl
from fw.auth.user_manager import UserManager
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject, PrivatePersonDbObject, CompanyDbObject
from fw.documents.enums import DocumentBatchTypeEnum, DocumentTypeEnum
from fw.documents.fields.doc_fields import PrivatePerson, CompanyObject
from manage_commands import BaseManageCommand, get_single
from fw.async_tasks import send_email
from services.llc_reg.documents.enums import DocumentDeliveryTypeStrEnum
from template_filters import utm_args


class SendRegMailCommand(BaseManageCommand):
    NAME = "send_llc_reg_mail"

    def run(self):
        self.logger.info(u"Отправка письма о регистрации компании")
        self.logger.info(u'=' * 50)

        batch_id = get_single(u'Batch id: ')

        batch = DocumentBatchDbObject.query.filter_by(id=batch_id, batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC).first()
        if not batch:
            self.logger.info(u'Batch not found')
            return

        if not batch.result_fields or 'ifns_reg_info' not in batch.result_fields:
            self.logger.info(u'Company not registered')
            return

        reg_info = batch.result_fields['ifns_reg_info']
        if 'status' not in reg_info or reg_info['status'] != 'registered' or not reg_info['reg_date'] or not reg_info['ogrn']:
            self.logger.info(u'Company not registered')
            return

        ogrn = reg_info['ogrn']
        reg_date = reg_info['reg_date'].strptime("%d.%m.%Y")

        recipient = batch._owner.email
        if not recipient:
            self.logger.info(u'Company owner has no email')
            return

        short_name = batch.data.get('short_name', u"")
        doc_rec_type = batch.data.get('obtain_way', None)

        ifns_book_doc_receive_url = "%s://%s/ip/?id=%s" % (self.config['WEB_SCHEMA'], self.config['DOMAIN'], batch_id)
        ifns_book_doc_receive_url = utm_args(ifns_book_doc_receive_url, 'ifns_ip_reg_success', batch._owner_id) + u"#page=obtaining"
        ifns_book_doc_receive_url = UserManager.make_auth_url(ifns_book_doc_receive_url, batch._owner).get_url(self.config)

        docs_recipient_fio = u""
        if doc_rec_type == DocumentDeliveryTypeStrEnum.DDT_ISSUE_TO_THE_APPLICANT:
            doc = BatchDocumentDbObject.query.filter_by(batch=batch,
                                                        document_type=DocumentTypeEnum.DT_P11001).first()
            if doc:
                founders = doc.data['founders']
                for founder in founders:
                    if founder.get('documents_recipient_type', '') != '':
                        person = founder.get('person', None)
                        if person and '_id' in person:
                            person_obj = PrivatePersonDbObject.query.filter_by(
                                id=person['_id']).scalar()
                            if person_obj:
                                pp = PrivatePerson.db_obj_to_field(person_obj)
                                if pp:
                                    docs_recipient_fio = pp.full_name
                        else:
                            company = founder.get('company', None)
                            if company:
                                company_db_object = CompanyDbObject.query.filter_by(
                                    id=company['_id']).scalar()
                                if company_db_object:
                                    cc = CompanyObject.db_obj_to_field(company_db_object)
                                    if cc and cc.general_manager and cc.general_manager.initialized:
                                        docs_recipient_fio = cc.general_manager.full_name
        elif doc_rec_type == DocumentDeliveryTypeStrEnum.DDT_ISSUE_TO_THE_APPLICANT_OR_AGENT:
            doc = BatchDocumentDbObject.query.filter_by(batch=batch,
                                                        document_type=DocumentTypeEnum.DT_DOVERENNOST_OBTAIN).first()

            if doc:
                doc_obtain_person = doc.data.get('doc_obtain_person', None)
                if doc_obtain_person and '_id' in doc_obtain_person:
                    person_obj = PrivatePersonDbObject.query.filter_by(
                        id=doc_obtain_person['_id']).scalar()
                    if person_obj:
                        pp = PrivatePerson.db_obj_to_field(person_obj)
                        if pp:
                            docs_recipient_fio = pp.full_name

        send_email.send_email(recipient,
            'ifns_llc_reg_success',
            short_name=short_name,
            doc_rec_by_email=(doc_rec_type == DocumentDeliveryTypeStrEnum.DDT_SEND_BY_MAIL),
            doc_rec_by_responsible=(
                doc_rec_type == DocumentDeliveryTypeStrEnum.DDT_ISSUE_TO_THE_APPLICANT_OR_AGENT),
            ifns_book_doc_receive_url=ifns_book_doc_receive_url,
            schema=self.config['WEB_SCHEMA'],
            domain=self.config['DOMAIN'],
            ogrn=ogrn,
            docs_ready_date=u"%d %s %s года" % (
                reg_date.day, get_russian_month_skl(reg_date.month), reg_date.year),
            docs_recipient_fio=docs_recipient_fio,
            obtain_person_fio=u"",
            service_startup=datetime.utcnow() < datetime(2015, 6, 1),
            user_id=str(batch._owner_id))
        self.logger.info(u'Sent %s to %s' % ('ifns_llc_reg_success', recipient))

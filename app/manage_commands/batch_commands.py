# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
import json
from bson.objectid import ObjectId
from flask import current_app
import requests
from common_utils import get_russian_month_skl
from fw.auth.models import AuthUser
from fw.async_tasks import send_email, rendering
from fw.auth.user_manager import UserManager
from fw.db.sql_base import db as sqldb
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import DocumentBatchDbObject, PrivatePersonDbObject, CompanyDbObject, BatchDocumentDbObject
from fw.documents.enums import BatchStatusEnum, DocumentBatchTypeEnum, DocumentTypeEnum
from fw.documents.fields.complex_doc_fields import ObjectRefField
from fw.documents.fields.doc_fields import PrivatePerson, CompanyObject
from fw.monitoring_utils.zabbix_sender import zabbixed
from manage_commands import BaseManageCommand, get_single
from services.ifns import ifns_manager
from services.ifns.data_model.enums import IfnsRegStatusEnum
from services.ip_reg.documents.enums import IPDocumentDeliveryTypeStrEnum
from services.llc_reg.documents.enums import RegistrationWay, IfnsServiceEnum, DocumentDeliveryTypeStrEnum
from services.llc_reg.documents.general_doc_fields import FounderObject
import html5lib
from template_filters import utm_args


class CheckBatchIfnsRegStatusCommand(BaseManageCommand):
    NAME = "check_batch_ifns_reg_status"

    @zabbixed('check_ifns_reg', (1, 0))
    def run(self):
        #        self.logger.info(u"Проверка статуса регистрации компаний")
        #        self.logger.info(u'=' * 50)

        is_production = not self.config['STAGING'] and not self.config['DEBUG']
        days_30 = timedelta(days=30)
        # get list of testers
        from services.ifns.data_model.models import IfnsBookingObject

        # and exclude their batches
        query = DocumentBatchDbObject.query.filter(
            DocumentBatchDbObject.status == BatchStatusEnum.BS_FINALISED,
            DocumentBatchDbObject.paid == True,
            DocumentBatchDbObject.finalisation_date >= datetime.now() - days_30
        )
        if is_production:
            query = query.join(AuthUser).filter(AuthUser.is_tester==False)

        skip_statuses = (IfnsRegStatusEnum.IRS_REGISTERED, IfnsRegStatusEnum.IRS_REGISTRATION_DECLINED)
        for batch in query:
            status = (batch.result_fields or {}).get('ifns_reg_info', {}).get('status', 'unknown')
            if status in skip_statuses:
                continue

            batch_id = batch.id
            # self.logger.info(u"%s" % unicode(batch_id))

            ifns = (batch.result_fields or {}).get('ifns', None)

            #self.logger.info(u"ifns: %s" % ifns)
            ifns_data = ifns_manager.get_ifns_data(ifns)
            if ifns_data and ifns_data.rou and 'code' in ifns_data.rou:
                ifns = ifns_data.rou['code']

            full_name = ""
            short_name = ""
            if batch.batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC:
                full_name = batch.data.get('full_name', None)
                short_name = batch.data.get('short_name', None)
            elif batch.batch_type == DocumentBatchTypeEnum.DBT_NEW_IP:
                try:
                    reg_responsible_person = batch.data.get('person', None)
                    person_field = ObjectRefField()
                    person_field.parse_raw_value(reg_responsible_person, {}, api_data=False, update=False)
                    full_name = person_field.full_name
                    short_name = person_field.short_name
                except Exception:
                    self.logger.exception(u"Failed to parse IP person")
            else:
                self.logger.exception(u"Unknown batch type for batch %s" % str(batch['_id']))

            doc_rec_type = batch.data.get('obtain_way', None)
            application_form = batch.data.get('registration_way', None)
            if batch.batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC:
                applicant_fio = u""
            elif batch.batch_type == DocumentBatchTypeEnum.DBT_NEW_IP:
                applicant_fio = full_name
            for doc in batch._documents:
                if doc.document_type == DocumentTypeEnum.DT_REGISTRATION_FEE_INVOICE:
                    founder_applicant = doc.data.get('founder_applicant', None)
                    if founder_applicant:
                        try:
                            founder_app_field = FounderObject()
                            founder_app_field.parse_raw_value(founder_applicant, {}, api_data=False, update=False)
                            applicant_fio = founder_app_field.full_name
                        except Exception:
                            self.logger.exception(u"Failed to parse founder object")
                    break

            if application_form == RegistrationWay.RW_RESPONSIBLE_PERSON:
                reg_responsible_person = batch.data.get('reg_responsible_person', None)
                if reg_responsible_person:
                    try:
                        reg_responsible_person_field = ObjectRefField()
                        reg_responsible_person_field.parse_raw_value(
                            reg_responsible_person, {}, api_data=False, update=False)
                        applicant_fio = reg_responsible_person_field.full_name
                    except Exception:
                        self.logger.exception(u"Failed to parse person")

            ifns_booking = IfnsBookingObject.query.filter_by(
                batch_id=batch_id,
                service_id=IfnsServiceEnum.IS_REG_COMPANY,
                _discarded=False
            ).first()
            if ifns_booking:
                dt = ifns_booking.date
                if dt and is_production and datetime.now() < dt:
                    self.logger.info(u"Too early - skip")
                    continue

            # self.logger.info(u"Checking batch %s" % unicode(batch_id))
            date_from = batch.finalisation_date - timedelta(days=5)
            date_to = date_from + timedelta(days=30)
            result = current_app.external_tools.get_ifns_registrations(
                full_name,
                date_from=date_from,
                date_to=date_to,
                ifns=ifns,
                service_nalog_ru_url=self.config['SERVICE_NALOG_RU_URL'],
                logger=self.logger) or []

            if not result:
                # self.logger.info(u"No reservations for batch %s" % unicode(batch_id))
                continue
            else:
                for item in result:
                    try:
                        self.logger.info(u"Found reservation info for batch %s (%s)" % (
                            batch_id,
                            json.dumps(item, default=lambda x: unicode(x))
                        ))
                        if 'status' not in item:
                            continue
                        status = item['status']
                        batch_result_fields = batch.result_fields or {}

                        if status == 'registered' and ('ogrn' in item or 'ogrnip' in item):
                            ogrn = item.get('ogrn')
                            ogrnip = item.get('ogrnip')
                            reg_date = None
                            try:
                                reg_date = item.get('reg_date', None)
                                if reg_date:
                                    reg_date = datetime.strptime(reg_date, "%d.%m.%Y")
                            except Exception:
                                self.logger.exception(u"Failed to convert reg_date")
                            reg_info = {
                                'status': 'registered',
                                'reg_date': reg_date,
                            }
                            if ogrn:
                                reg_info['ogrn'] = ogrn
                            elif ogrnip:
                                reg_info['ogrnip'] = ogrnip

                            booking = IfnsBookingObject.query.filter_by(
                                batch_id=batch_id,
                                service_id=IfnsServiceEnum.IS_REG_COMPANY,
                                _discarded=False
                            ).first()
                            if booking:
                                booking.reg_info = reg_info
                                sqldb.session.commit()

                            batch_result_fields['ifns_reg_info'] = {
                                'status': 'registered',
                                'reg_date': reg_date,
                                'full_name': full_name
                            }
                            if ogrn:
                                batch_result_fields['ifns_reg_info']['ogrn'] = ogrn
                            elif ogrnip:
                                batch_result_fields['ifns_reg_info']['ogrnip'] = ogrnip

                            DocumentBatchDbObject.query.filter_by(id=batch.id).update({
                                'result_fields': batch_result_fields
                            })
                            sqldb.session.commit()
                            recipient = batch._owner.email or u""
                            obtain_person_fio = u""
                            if not recipient:
                                self.logger.warn(
                                    u"Failed to send ifns reg notify to user %s - no email address" % batch._owner_id)
                            else:
                                docs_recipient_fio = ""
                                # Batch Type specific logic
                                if batch.batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC:
                                    # TODO: This should be incapsulated
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
                                                                obtain_person_fio = pp.full_name
                                                    else:
                                                        company = founder.get('company', None)
                                                        if company:
                                                            company_db_object = CompanyDbObject.query.filter_by(
                                                                id=company['_id']).scalar()
                                                            if company_db_object:
                                                                cc = CompanyObject.db_obj_to_field(company_db_object)
                                                                if cc and cc.general_manager and cc.general_manager.initialized:
                                                                    obtain_person_fio = cc.general_manager.full_name
                                    ifns_book_doc_receive_url = "%s://%s/ooo/?id=%s" % (self.config['WEB_SCHEMA'], self.config['DOMAIN'], unicode(batch_id))
                                    ifns_book_doc_receive_url = utm_args(ifns_book_doc_receive_url, "ifns_llc_reg_success", batch._owner_id) + u"#page=obtaining"
                                    ifns_book_doc_receive_url = UserManager.make_auth_url(ifns_book_doc_receive_url, batch._owner).get_url(self.config)

                                    send_email.send_email.delay(
                                        recipient,
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
                                        obtain_person_fio=obtain_person_fio,
                                        service_startup=datetime.now() < datetime(2015, 6, 1),
                                        user_id=str(batch._owner_id)
                                    )
                                elif batch.batch_type == DocumentBatchTypeEnum.DBT_NEW_IP:

                                    if doc_rec_type == IPDocumentDeliveryTypeStrEnum.IP_DDT_RESPONSIBLE_PERSON:
                                        for doc in BatchDocumentDbObject.query.filter(
                                                        BatchDocumentDbObject.batch == batch,
                                                BatchDocumentDbObject.document_type.in_((
                                                        DocumentTypeEnum.DT_IP_DOV_FILING_RECEIVING_DOCS,
                                                        DocumentTypeEnum.DT_IP_DOV_RECEIVING_DOCS))):
                                            person = doc.data.get('ip_responsible_person', None)
                                            if person and '_id' in person:
                                                person_obj = PrivatePersonDbObject.query.filter_by(
                                                    id=person['_id']).scalar()
                                                if person_obj:
                                                    pp = PrivatePerson.db_obj_to_field(person_obj)
                                                    if pp:
                                                        docs_recipient_fio = pp.full_name
                                                        break

                                    ifns_book_doc_receive_url = "%s://%s/ip/?id=%s" % (self.config['WEB_SCHEMA'], self.config['DOMAIN'], batch_id)
                                    ifns_book_doc_receive_url = utm_args(ifns_book_doc_receive_url, 'ifns_ip_reg_success', batch._owner_id) + u"#page=obtaining"
                                    ifns_book_doc_receive_url = UserManager.make_auth_url(ifns_book_doc_receive_url, batch._owner).get_url(self.config)

                                    send_email.send_email.delay(
                                        recipient,
                                        'ifns_ip_reg_success',
                                        short_name=short_name,
                                        doc_rec_by_email=(doc_rec_type == IPDocumentDeliveryTypeStrEnum.IP_DDT_MAIL),
                                        doc_rec_by_responsible=(
                                            doc_rec_type == IPDocumentDeliveryTypeStrEnum.IP_DDT_RESPONSIBLE_PERSON),
                                        ifns_book_doc_receive_url=ifns_book_doc_receive_url,
                                        schema=self.config['WEB_SCHEMA'],
                                        domain=self.config['DOMAIN'],
                                        ogrnip=ogrnip,
                                        docs_ready_date=u"%d %s %s года" % (
                                            reg_date.day, get_russian_month_skl(reg_date.month), reg_date.year),
                                        docs_recipient_fio=docs_recipient_fio,
                                        obtain_person_fio=obtain_person_fio,
                                        service_startup=datetime.now() < datetime(2015, 6, 1),
                                        user_id=str(batch._owner_id)
                                    )
                            self.notify_admin(True, short_name, batch_id, application_form, doc_rec_type, applicant_fio,
                                              recipient, ogrn=ogrn, ogrnip=ogrnip, batch_type=batch.batch_type)
                        elif status == 'registration_declined':
                            reg_date = None
                            try:
                                reg_date = item.get('reg_date', None)
                                if reg_date:
                                    reg_date = datetime.strptime(reg_date, "%d.%m.%Y")
                            except Exception:
                                self.logger.exception(u"Failed to convert reg_date")

                            IfnsBookingObject.query.filter_by(
                                batch_id=batch_id,
                                service_id=IfnsServiceEnum.IS_REG_COMPANY,
                                _discarded=False).update({
                                    'reg_info': {
                                        'status': 'registration_declined',
                                        'reg_date': reg_date
                                    }
                                })
                            sqldb.session.commit()
                            batch_result_fields['ifns_reg_info'] = {
                                'status': 'registration_declined',
                                'reg_date': reg_date,
                                'full_name': full_name
                            }
                            recipient = batch._owner.email or u""
                            if not recipient:
                                self.logger.warn(
                                    u"Failed to send ifns reg notify to user %s - no email address" % batch._owner_id)
                            else:
                                if batch.batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC:
                                    ifns_book_doc_receive_url = "%s://%s/ooo/?id=%s" % (self.config['WEB_SCHEMA'], self.config['DOMAIN'], batch_id)
                                    ifns_book_doc_receive_url = utm_args(ifns_book_doc_receive_url, 'ifns_llc_reg_fail', batch._owner_id) + u"#page=refusing"
                                    ifns_book_doc_receive_url = UserManager.make_auth_url(ifns_book_doc_receive_url, batch._owner).get_url(self.config)

                                    send_email.send_email.delay(
                                        recipient,
                                        'ifns_llc_reg_fail',
                                        short_name=short_name,
                                        doc_rec_by_email=(doc_rec_type == DocumentDeliveryTypeStrEnum.DDT_SEND_BY_MAIL),
                                        ifns_book_doc_receive_url=ifns_book_doc_receive_url,
                                        schema=self.config['WEB_SCHEMA'],
                                        domain=self.config['DOMAIN'],
                                        user_id=batch._owner_id
                                    )
                                elif batch.batch_type == DocumentBatchTypeEnum.DBT_NEW_IP:
                                    ifns_book_doc_receive_url = "%s://%s/ip/?id=%s" % (self.config['WEB_SCHEMA'], self.config['DOMAIN'], batch_id)
                                    ifns_book_doc_receive_url = utm_args(ifns_book_doc_receive_url, 'ifns_ip_reg_fail', batch._owner_id) + u"#page=refusing"
                                    ifns_book_doc_receive_url = UserManager.make_auth_url(ifns_book_doc_receive_url, batch._owner).get_url(self.config)
                                    send_email.send_email.delay(
                                        recipient,
                                        'ifns_ip_reg_fail',
                                        short_name=short_name,
                                        doc_rec_by_email=(doc_rec_type == IPDocumentDeliveryTypeStrEnum.IP_DDT_MAIL),
                                        ifns_book_doc_receive_url=ifns_book_doc_receive_url,
                                        schema=self.config['WEB_SCHEMA'],
                                        domain=self.config['DOMAIN'],
                                        user_id=batch._owner_id
                                    )
                            DocumentBatchDbObject.query.filter_by(id=batch.id).update({
                                'result_fields': batch_result_fields
                            })
                            sqldb.session.commit()
                            self.notify_admin(False, short_name, batch_id, application_form, doc_rec_type,
                                              applicant_fio, recipient, batch_type=batch.batch_type)
                        elif status == 'progress':
                            IfnsBookingObject.query.filter_by(
                                batch_id=batch_id,
                                service_id=IfnsServiceEnum.IS_REG_COMPANY,
                                _discarded=False
                            ).update({'reg_info': {
                                    'status': 'progress',
                                    'reg_date': item.get('reg_date', None)
                                }
                            })
                            batch_result_fields['ifns_reg_info'] = {
                                'status': 'progress',
                                'reg_date': item.get('reg_date', None),
                                'full_name': full_name
                            }
                            DocumentBatchDbObject.query.filter_by(id=batch.id).update({
                                'result_fields': batch_result_fields
                            })
                            sqldb.session.commit()
                        else:
                            raise Exception()

                        break
                    except Exception:
                        self.logger.exception(u"Failed to handle result")

    def notify_admin(self, is_success_reg, company_short_name, batch_id, application_form, obtain_form, applicant_fio,
                     user_email, ogrn=None, ogrnip=None, batch_type=None):
        application_form_rus = RegistrationWay._NAMES.get(application_form, u"<неизвестно>")
        obtain_form_rus = DocumentDeliveryTypeStrEnum._NAMES.get(obtain_form, u"<неизвестно>")
        recipient_list = self.config['YURIST_EMAIL_LIST']
        for recipient in recipient_list:
            send_email.send_email.delay(
                recipient,
                'admin_notify_llc_ifns_reg' if batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC else 'admin_notify_ip_ifns_reg',
                short_name=company_short_name,
                success_reg=is_success_reg,
                ogrn=ogrn,
                ogrnip=ogrnip,
                batch_id=batch_id,
                application_form_rus=application_form_rus,
                obtain_form_rus=obtain_form_rus,
                applicant_fio=applicant_fio,
                user_email=user_email
            )


class RebuildBatchCommand(BaseManageCommand):
    NAME = "rebuild_batch"

    def run(self):
        self.logger.info(u"Перегенерация пакета документов")
        self.logger.info(u'=' * 50)

        batch_id = get_single(u'batch id: ')
        try:
            ObjectId(batch_id)
        except Exception:
            self.logger.error(u"Invalid batch id")
            return False

        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).scalar()
        if not batch:
            self.logger.error(u"Batch not found")
            return False

        if batch.status == BatchStatusEnum.BS_FINALISED:

            batch.status = BatchStatusEnum.BS_BEING_FINALISED
            sqldb.session.commit()
            async_result = rendering.render_batch.delay(batch_id)

            if not async_result.ready():
                batch.current_task_id = async_result.id
                sqldb.session.commit()

            return True
        elif batch.status == BatchStatusEnum.BS_EDITED:
            manager = BatchManager.init(batch)
            manager.finalize_batch(self.config, self.logger, batch)
            return True
        self.logger.error(u"Invalid current batch status")
        return False


class BuildDocumentCommand(BaseManageCommand):
    NAME = "rebuild_document"

    def run(self):
        self.logger.info(u"Перегенерация документа")
        self.logger.info(u'=' * 50)

        doc_id = get_single(u'document id: ')
        doc = BatchDocumentDbObject.query.filter_by(id=doc_id).scalar()
        if not doc:
            self.logger.error(u"Failed to find document")
            return False
        batch = doc.batch
        rendering.render_batch_document.delay(batch.id, doc_id)

        self.logger.error(u"Started document render")
        return False


class SendBatchDocumentsToEmailCommand(BaseManageCommand):
    NAME = "email_batch_docs"

    def run(self):
        self.logger.info(u"Отправка пакета документов на email")
        self.logger.info(u'=' * 50)

        batch_id = get_single(u'batch id: ')
        email = get_single(u'email: ')
        try:
            ObjectId(batch_id)
        except Exception:
            self.logger.error(u"Invalid batch id")
            return False

        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).scalar()
        if not batch:
            self.logger.error(u"Batch not found")
            return False

        if batch.status == BatchStatusEnum.BS_FINALISED:
            total_attachments = BatchManager.get_batch_rendered_docs(batch, current_app.config, current_app.logger)
            send_email.send_email.delay(email, 'email_batch_docs', attach=total_attachments)
            return True
        self.logger.error(u"Invalid current batch status")
        return True


class GetFssNumberCommand(BaseManageCommand):
    NAME = "get_fss_number"

    @staticmethod
    def get_fss_number(logger):
        from copy import copy
        days_30 = timedelta(days=30)
        for batch in DocumentBatchDbObject.query.filter(
            DocumentBatchDbObject.batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC,
            DocumentBatchDbObject.status == BatchStatusEnum.BS_FINALISED,
            DocumentBatchDbObject.paid == True,
            DocumentBatchDbObject.deleted == False,
            DocumentBatchDbObject.finalisation_date >= datetime.utcnow() - days_30
        ).join(AuthUser).filter(AuthUser.is_tester == False):
            if batch.result_fields and 'fss_number' in batch.result_fields and batch.result_fields['fss_number']:
                continue
            if batch.data and 'inn' not in batch.data:
                continue

            batch_id = batch.id
            inn = batch.data['inn']
            fss_response = requests.get("http://fz122.fss.ru/index.php?service=28&inn=%s" % str(inn))
            if fss_response.status_code != 200:
                logger.warn("Failed to get fss data for batch %s with inn %s" % (batch_id, str(inn)))
                continue
            else:
                # parse the data
                content = fss_response.text
                root = html5lib.parse(content, treebuilder='lxml', namespaceHTMLElements=False)
                tds = root.xpath('//tr[@bgcolor="#BFD6C8"]/td')
                if len(tds) != 6:
                    logger.warn(
                        "Failed to locate proper cell in table; batch %s with inn %s" % (batch_id, inn))
                    continue
                else:
                    fss_number = tds[3].text
                    if not fss_number.isdigit():
                        logger.warn(
                            "Fss number is not digit: %s ; batch %s with inn %s" % (fss_number, batch_id, inn))
                        continue
                    else:
                        fss_number = int(fss_number)
                        new_fields = copy(batch.result_fields)
                        new_fields["fss_number"] = fss_number
                        DocumentBatchDbObject.query.filter_by(id=batch_id).update({'result_fields': new_fields})
                        sqldb.session.commit()
        return True

    def run(self):
        self.logger.info(u"Забор номеров ФСС")
        self.logger.info(u'=' * 50)

        return GetFssNumberCommand.get_fss_number(self.logger)


class SetDateCommand(BaseManageCommand):
    NAME = "set_date"

    def run(self):
        self.logger.info(u"Set date")
        batch_id = get_single(u'batch id: ')
        for doc in BatchDocumentDbObject.query.filter_by(batch_id=batch_id, deleted=False):
            if doc.data and 'doc_date' in doc.data:
                d = doc.data
                d['doc_date'] = datetime(2015, 6, 13)
                BatchDocumentDbObject.query.filter_by(id=doc.id).update({'data':d})
                self.logger.info('updated %s' % doc.document_type)
        sqldb.session.commit()


def _check_id(obj_type, obj_id):
    type_cls_map = {
        'person': PrivatePersonDbObject,
        'company': CompanyDbObject
    }

    obj = type_cls_map[obj_type].query.filter_by(id=obj_id).scalar()
    return obj is not None


def _get_invalid_refs(data):
    result = []
    if isinstance(data, dict):
        if len(data) == 2 and '_id' in data and 'type' in data:
            if not _check_id(data['type'], data['_id']):
                result.append(data)
        for subkey, subval in data.items():
            result.extend(_get_invalid_refs(subval))
    elif isinstance(data, list) or isinstance(data, tuple):
        for i in data:
            result.extend(_get_invalid_refs(i))
    return result


class FindInvalidRefsCommand(BaseManageCommand):
    NAME = "find_invalid_refs"

    def run(self):
        self.logger.info(u"Looking for invalid references to persons/companies")
        invalid_refs = {}
        invalid_refs_set = set()
        for batch in DocumentBatchDbObject.query.filter_by(deleted=False, _broken=False):
            data = batch.data
            docs = batch._documents

            invalid_refs[batch.id] = {}
            r = _get_invalid_refs(data or {}) or []
            if r:
                invalid_refs[batch.id][None] = r
                for i in r:
                    invalid_refs_set.add(i['_id'])
            for doc in docs:
                r = _get_invalid_refs(doc.data or {}) or []
                if r:
                    invalid_refs[batch.id][doc.id] = r
                    for i in r:
                        invalid_refs_set.add(i['_id'])
            if not invalid_refs[batch.id]:
                del invalid_refs[batch.id]

        print(json.dumps(invalid_refs, indent=1))
        print(json.dumps(list(invalid_refs_set), indent=1))


def _replace_ids(data, replace_map):
    if isinstance(data, basestring):
        if data in replace_map:
            return replace_map[data]
        return data
    if isinstance(data, list) or isinstance(data, tuple):
        result = []
        for i in data:
            result.append(_replace_ids(i, replace_map))
        return result
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            result[k] = _replace_ids(v, replace_map)
        return result
    return data

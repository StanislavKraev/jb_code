# -*- coding: utf-8 -*-
from datetime import datetime
import pytils
import common_utils
from fw.documents.batch_manager import BatchManager
from fw.documents.enums import DocumentTypeEnum, DocumentBatchTypeEnum
from fw.db.sql_base import db as sqldb
from services.pay.models import PayInfoObject, PurchaseServiceType


class OsagoBatchManager(BatchManager):

    BATCH_TYPE = DocumentBatchTypeEnum.DBT_OSAGO

    DOC_TITLES = {
        DocumentTypeEnum.DT_OSAGO_MAIL_LIST: u"Опись ценного письма для ОСАГО",
        DocumentTypeEnum.DT_OSAGO_PRETENSION: u"Претензия по ОСАГО",
        DocumentTypeEnum.DT_OSAGO_DOCUMENTS_CLAIM: u"Заявление на выдачу документов по ОСАГО",
        DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISSION_DOCS: u"Доверенность на подачу документов в страховую",
        DocumentTypeEnum.DT_OSAGO_TRUST_OBTAIN_DOCS: u"Доверенность на получение документов из страховой",
        DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISION_OBTAIN_DOCS: u"Доверенность на подачу и получение документов из страховой",

        DocumentTypeEnum.DT_OSAGO_CLAIM_COURT_ABSENT: u"Заявление об отсутствии на суде",
        DocumentTypeEnum.DT_OSAGO_CLAIM_ALL_EXECUTION_ACT: u"Завление на выдачу ИЛ ко всем",
        DocumentTypeEnum.DT_OSAGO_CLAIM_GUILTY_EXECUTION_ACT: u"Завление на выдачу ИЛ к виновнику",
        DocumentTypeEnum.DT_OSAGO_CLAIM_INSURANCE_EXECUTION_ACT: u"Завление на выдачу ИЛ к страховой",
        DocumentTypeEnum.DT_OSAGO_LAWSUIT: u"Иск",
        DocumentTypeEnum.DT_OSAGO_COURT_MAIL_LIST: u"Опись для ценного письма"
    }

    def get_title(self, doc_type):
        return OsagoBatchManager.DOC_TITLES.get(doc_type, '')

    def get_last_modified_batch_caption(self, batch_db):
        if not batch_db:
            return u""

        dt = batch_db.data.get('crash_date', None)
        if not dt:
            return u""
        return pytils.dt.ru_strftime(u"%d %B %Y г.", inflected=True, date=dt)

    def get_batch_caption(self, batch_db):
        if not batch_db:
            return u""

        data = batch_db.data
        dt = data.get('crash_date', None)
        return u"Возмещение по ОСАГО, дата аварии: %s" % common_utils.get_russian_date(dt) if dt else u"Возмещение по ОСАГО"

    @staticmethod
    def cancel_batch_finalization(batch_db_obj, config, logger):
        pass

    def finalize_batch(self, config, logger, batch):
        return False

    def get_stage(self, batch):
        state_map = {
            'pretension': 'preparation',
            'generating_pretension': 'preparation',
            'claim': 'submission',
            'generating_claim': 'submission',
            'court': 'submission',
        }
        return state_map.get(batch.status, 'submission')

    @staticmethod
    def check_and_fix_osago_payments(batch):
        if batch.creation_date >= datetime(2015, 10, 7):
            return

        if batch.status == 'claim':
            pay_count = PayInfoObject.query.filter_by(batch=batch).count()
            if pay_count < 1:
                new_pay_info = PayInfoObject(
                    user=batch._owner,
                    batch=batch,
                    pay_record_id=0,
                    payment_provider=0,
                    service_type=PurchaseServiceType.OSAGO_PART1
                )
                sqldb.session.add(new_pay_info)
                sqldb.session.commit()
        elif batch.status == 'court':
            pay_count = PayInfoObject.query.filter_by(batch=batch).count()
            if pay_count < 1:
                new_pay_info = PayInfoObject(
                    user=batch._owner,
                    batch=batch,
                    pay_record_id=0,
                    payment_provider=0,
                    service_type=PurchaseServiceType.OSAGO_PART1
                )
                sqldb.session.add(new_pay_info)
                sqldb.session.commit()
            if pay_count < 2:
                new_pay_info = PayInfoObject(
                    user=batch._owner,
                    batch=batch,
                    pay_record_id=0,
                    payment_provider=0,
                    service_type=PurchaseServiceType.OSAGO_PART2
                )
                sqldb.session.add(new_pay_info)
                sqldb.session.commit()

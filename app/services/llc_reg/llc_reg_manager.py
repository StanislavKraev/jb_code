# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import pytz
from fw.api import errors
from fw.api.base_handlers import error_tree_to_list
from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import RFRegionsEnum
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentTypeEnum, BatchStatusEnum, DocumentBatchTypeEnum, UserDocumentStatus
from fw.documents.fields.doc_fields import DocumentBatch, UserDocument
from fw.documents.schema.schema_transform import transform_with_schema
from fw.storage.file_storage import FileStorage
from services.pay.models import PayInfoObject, PurchaseServiceType
from services.pay.subs_manager import SubscriptionManager


class LlcRegBatchManager(BatchManager):
    FIRST_STAGE_DOCS = {
        DocumentTypeEnum.DT_P11001,
        DocumentTypeEnum.DT_ARTICLES,
        DocumentTypeEnum.DT_ACT,
        DocumentTypeEnum.DT_USN,
        DocumentTypeEnum.DT_DECISION,
        DocumentTypeEnum.DT_PROTOCOL,
        DocumentTypeEnum.DT_ESHN,
        DocumentTypeEnum.DT_CONTRACT,
        DocumentTypeEnum.DT_REGISTRATION_FEE_INVOICE,
        DocumentTypeEnum.DT_DOVERENNOST,
        DocumentTypeEnum.DT_DOVERENNOST_OBTAIN,
        DocumentTypeEnum.DT_SOGLASIE_SOBSTVENNIKOV,
        DocumentTypeEnum.DT_GARANT_LETTER_ARENDA,
        DocumentTypeEnum.DT_GARANT_LETTER_SUBARENDA
    }

    THIRD_STAGE_DOCS = {
        DocumentTypeEnum.DT_GENERAL_MANAGER_CONTRACT,
        DocumentTypeEnum.DT_GENERAL_MANAGER_ORDER,
        DocumentTypeEnum.DT_ACCOUNTANT_CONTRACT,
        DocumentTypeEnum.DT_ACCOUNTANT_ORDER,
        DocumentTypeEnum.DT_FSS_CLAIM,
        DocumentTypeEnum.DT_PFR_CLAIM,
        DocumentTypeEnum.DT_ROSSTAT_CLAIM,
        DocumentTypeEnum.DT_FOUNDERS_LIST,
        DocumentTypeEnum.DT_COMPANY_DETAILS,
        DocumentTypeEnum.DT_ACCOUNTANT_IMPOSITION_ORDER
    }

    DOC_TITLES = {
        DocumentTypeEnum.DT_P11001: u"Заявление о государственной регистрации (форма Р11001)",
        DocumentTypeEnum.DT_ARTICLES: u"Устав",
        DocumentTypeEnum.DT_PROTOCOL: u"Протокол собрания учредителей",
        DocumentTypeEnum.DT_DECISION: u"Решение единственного учредителя",
        DocumentTypeEnum.DT_ACT: u"Акт оценки имущества",
        DocumentTypeEnum.DT_USN: u"Заявление о переходе на УСН",
        DocumentTypeEnum.DT_ESHN: u"Заявление о переходе на ЕСХН",
        DocumentTypeEnum.DT_CONTRACT: u"Договор об учреждении юридического лица",
        DocumentTypeEnum.DT_REGISTRATION_FEE_INVOICE: u"Квитанция на уплату госпошлины",
        DocumentTypeEnum.DT_DOVERENNOST: u"Доверенность на подачу документов",
        DocumentTypeEnum.DT_DOVERENNOST_OBTAIN: u"Доверенность на получение документов",
        DocumentTypeEnum.DT_SOGLASIE_SOBSTVENNIKOV: u"Согласие других собствеников жилья",
        DocumentTypeEnum.DT_GARANT_LETTER_ARENDA: u"Образец гарантийного письма (аренда от собственника)",
        DocumentTypeEnum.DT_GARANT_LETTER_SUBARENDA: u"Образец гарантийного письма (помещение в субаренду)",

        DocumentTypeEnum.DT_GENERAL_MANAGER_CONTRACT: u"Трудовой договор с руководителем",
        DocumentTypeEnum.DT_GENERAL_MANAGER_ORDER: u"Приказ о вступлении в должность",
        DocumentTypeEnum.DT_ACCOUNTANT_CONTRACT: u"Трудовой договор с бухгалтером",
        DocumentTypeEnum.DT_ACCOUNTANT_ORDER: u"Приказ о приеме на работу бухгалтера",
        DocumentTypeEnum.DT_FSS_CLAIM: u"заявление в ФСС",
        DocumentTypeEnum.DT_PFR_CLAIM: u"заявление в ПФР",
        DocumentTypeEnum.DT_ROSSTAT_CLAIM: u"заявление в Росстат",
        DocumentTypeEnum.DT_FOUNDERS_LIST: u"Список участников",
        DocumentTypeEnum.DT_COMPANY_DETAILS: u"Реквизиты компании",
        DocumentTypeEnum.DT_ACCOUNTANT_IMPOSITION_ORDER: u"Приказ о возложении обязанностей бухгалтера на директора",

        DocumentTypeEnum.DT_DOV_OLD: u"Доверенность на подачу-получение документов"
    }

    def __init__(self):
        pass

    @staticmethod
    def get_batch_reg_address(batch_id):
        doc = BatchDocumentDbObject.query.filter_by(batch_id=batch_id, document_type=DocumentTypeEnum.DT_ARTICLES).first()
        if doc and doc.data:
            return doc.data.get('address', None)

    def merge_docs(self, batch_status, current_docs_db_models, new_docs_db_models, changed_field_names):
        merged_docs = []
        unused_docs = []

        if batch_status != BatchStatusEnum.BS_FINALISED:
            return new_docs_db_models, current_docs_db_models

        doc_fields_map = {}
        for doc in current_docs_db_models:
            doc_type = doc.document_type
            ds = DocRequisitiesStorage.get_schema(doc_type)
            doc_fields_map[doc_type] = set([f['name'] for f in ds['fields']]) #set(doc.data.keys())

        modified_doc_types_set = set()
        for field_name in changed_field_names:
            for cur_doc_type in doc_fields_map:
                if field_name in doc_fields_map[cur_doc_type]:
                    modified_doc_types_set.add(cur_doc_type)

        added_doc_types = set()
        for doc in current_docs_db_models:
            doc_type = doc.document_type
            if doc_type in LlcRegBatchManager.FIRST_STAGE_DOCS:
                merged_docs.append(doc)
                added_doc_types.add(doc_type)
            elif doc_type not in LlcRegBatchManager.FIRST_STAGE_DOCS and doc_type not in modified_doc_types_set:
                merged_docs.append(doc)
                added_doc_types.add(doc_type)

        for doc in new_docs_db_models:
            doc_type = doc.document_type

            if doc_type not in LlcRegBatchManager.FIRST_STAGE_DOCS and \
               doc.status != UserDocumentStatus.DS_RENDERED and doc_type not in added_doc_types:
                merged_docs.append(doc)

        for doc in current_docs_db_models:
            if doc.document_type not in added_doc_types:
                unused_docs.append(doc)

        return merged_docs, unused_docs

    def update_batch(self, batch_id, new_batch, current_user_id, config, logger):
        current_batch_db_object = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner_id=current_user_id,
                                                                        deleted=False).first()
        if not current_batch_db_object:
            raise errors.BatchNotFound()

        batch_status = current_batch_db_object.status
        if batch_status not in (BatchStatusEnum.BS_NEW, BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_FINALISED):
            logger.warn(u"Can't update batch %s in status %s" % (unicode(batch_id), unicode(batch_status)))
            raise errors.DocumentBatchUpdateError()

        try:
            current_batch = DocumentBatch.db_obj_to_field(current_batch_db_object)
        except Exception:
            logger.fatal(u"Failed to validate batch from DB!")
            raise

        current_fields = current_batch.data.value
        assert isinstance(current_fields, dict)

        # STEP 1: make new data and metadata
        #         and collect changed fields names
        new_batch_db = new_batch.get_db_object()
        merged_fields, changed_field_names = self._merge_raw_fields(current_batch_db_object.data, new_batch_db.data)

        current_batch_db_object._metadata = new_batch_db._metadata
        current_batch_db_object.data = merged_fields
        sqldb.session.commit()

        if current_batch_db_object.status == BatchStatusEnum.BS_FINALISED:
            if 'full_name' in changed_field_names and current_batch_db_object.paid:
                raise errors.PaidBatchUpdateError()

        # STEP 2: make document set from data and schema
        try:
            new_field_set, new_docs, changed_field_names = self.make_docs_for_new_data(
                current_batch.data.value,
                new_batch.data.value,
                current_batch_db_object,
                BatchManager.get_batch_document_fields(current_batch_db_object),
                logger=logger
            )
        except Exception, ex:
            logger.exception(u"Failed to update batch with new values")
            current_batch_db_object.error_info = {"error": u"unknown error (%s)" % str(ex)}
            sqldb.session.commit()
            raise

        current_docs_db_models = [doc for doc in current_batch_db_object._documents]
        new_docs_db_models = [BatchDocumentDbObject(**new_doc.get_db_object_data()) for new_doc in new_docs]

        merged_docs, unused_db_docs = self.merge_docs(current_batch_db_object.status,
                                                      current_docs_db_models, new_docs_db_models,
                                                      changed_field_names)
        for doc in merged_docs:
            doc.batch = current_batch_db_object
            doc._owner_id = current_user_id

        for doc in unused_db_docs:
            BatchDocumentDbObject.query.filter_by(id=doc.id).delete()

        sqldb.session.commit()

        # STEP 3: combine old and new documents
        error_info = None
        try:
            current_batch.update_db_obj(current_batch_db_object, current_batch.get_db_object_data(), False)
            current_batch_db_object._metadata = new_batch_db._metadata
            current_batch_db_object.data = merged_fields
            sqldb.session.commit()

            # STEP 5: make result fields
            result_fields = self.make_result_fields(current_batch, new_field_set)

            result_fields["general_manager_caption_genitive"] = u"генерального директора"
            if current_batch_db_object.status == BatchStatusEnum.BS_FINALISED:
                if 'inn' in changed_field_names and 'fss_number' in result_fields:
                    del result_fields['fss_number']

            current_batch_db_object.result_fields = result_fields
            current_batch_db_object.error_info = None
            sqldb.session.commit()
        except Exception, ex:
            logger.exception(u"Failed to update batch with new values")
            current_batch_db_object.error_info = {"error": u"unknown error"}
            sqldb.session.commit()
            raise errors.DocumentBatchUpdateError()

        if current_batch_db_object.status in (BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_FINALISED):
            error_ext = self.get_batch_errors(current_batch_db_object, logger)
            if error_ext:
                error_info = {'error_ext': error_ext}
                current_batch_db_object.error_info = error_info
                sqldb.session.commit()

        current_batch = DocumentBatch.db_obj_to_field(current_batch_db_object)
        struct = current_batch.get_api_structure()

        if error_info:
            struct['error_info'] = error_info
        elif 'error_info' in struct:
            del struct['error_info']

        return {'result': struct}

    def make_docs_from_batch_fields(self, field_set, current_batch_db_object=None):
        batch_descriptor = DocRequisitiesStorage.get_batch_descriptor(DocumentBatchTypeEnum.DBT_NEW_LLC)
        docs = []
        fields = field_set

        doc_in_batch = lambda doc_type_, batch_: any([doc_.document_type == doc_type_ for doc_ in batch_._documents])

        batch_doc_types = batch_descriptor.get('doc_types', [])
        for doc_type in batch_doc_types:
            if doc_type in self.THIRD_STAGE_DOCS and not doc_in_batch(doc_type, current_batch_db_object):
                continue

            result_fields = current_batch_db_object.result_fields or {}
            ifns_reg_status = result_fields.get('ifns_reg_info', {}).get('status', '')
            if ifns_reg_status == 'registered' and doc_type in self.FIRST_STAGE_DOCS:
                continue

            doc = self.get_doc_schema(doc_type)

            doc_data = doc
            new_doc = {
                "document_type": doc_data['doc_name'],
                "creation_date": datetime.utcnow(),
                "status": UserDocumentStatus.DS_NEW,
                "rendered_docs": []
            }
            data = transform_with_schema(fields, doc_data)

            if data is not None:
                user_doc = UserDocument.parse_raw_value(new_doc, api_data=False)
                user_doc.data.value = data
                user_doc.data.initialized = True
                docs.append(user_doc)

        return docs

    def finalize_batch(self, config, logger, batch):
        if batch.status not in (BatchStatusEnum.BS_NEW, BatchStatusEnum.BS_EDITED):
            return False

        batch_id = batch.id

        docs = batch._documents or []
        error_info = batch.error_info or {}
        exc_list = []

        types_of_invalid_docs = set()
        for doc in docs:
            try:
                user_doc = UserDocument.db_obj_to_field(doc)
                user_doc.validate(strict=True)
            except Exception, ex:
                logger.exception(u"Failed to validate document %s" % doc.document_type)
                types_of_invalid_docs.add(doc.document_type)
                exc_list.append(ex)

        allowed_invalid_docs = (DocumentTypeEnum.DT_GENERAL_MANAGER_CONTRACT,
                                DocumentTypeEnum.DT_GENERAL_MANAGER_CONTRACT)   # todo: ???
        if exc_list:
            next_exc = errors.DocumentBatchFinalizationError()
            for ex in exc_list:
                if getattr(ex, 'ext_data', None):
                    next_exc.ext_data.extend(ex.ext_data)
            if next_exc.ext_data:
                error_list = error_tree_to_list(next_exc.ext_data)
                for error in error_list:
                    if 'field' in error and error['field'].startswith('data.'):
                        error['field'] = error['field'][5:]
                error_info['error_ext'] = error_list

            batch.error_info = error_info

            if not all([doc_type in allowed_invalid_docs for doc_type in types_of_invalid_docs]):
                batch.status = BatchStatusEnum.BS_EDITED
                sqldb.session.commit()
                return {"result": False}

            for doc in docs:
                if doc.document_type in types_of_invalid_docs:
                    BatchDocumentDbObject.query.filter_by(id=doc.id).delete()
        else:
            batch.error_info = None

        batch.status = BatchStatusEnum.BS_BEING_FINALISED
        sqldb.session.commit()

        try:
            DocumentBatch.db_obj_to_field(batch)
        except Exception:
            logger.exception(u"Failed to finalize: rolling back")

            batch.status = BatchStatusEnum.BS_EDITED
            sqldb.session.commit()
            return False

        last_change_dt = datetime.utcnow()
        batch.last_change_dt = last_change_dt

        if not batch.paid:
            subs = SubscriptionManager.get_user_active_subscription(batch._owner.id)
            if subs:
                batch.paid = True
                pay_info = PayInfoObject(
                    user=batch._owner,
                    batch=batch,
                    pay_record_id=subs.pay_record_id,
                    payment_provider=subs.payment_provider,
                    service_type=PurchaseServiceType.LLC_AUTO_PURCHASE
                )
                sqldb.session.add(pay_info)

        sqldb.session.commit()
        try:
            logger.debug(u"Adding rendering task for batch %s" % unicode(batch.id))
            from fw.async_tasks import rendering

            async_result = rendering.render_batch.delay(str(batch.id))

            if not async_result.ready():
                batch.current_task_id = unicode(async_result.id)
                batch.batch_rendering_start = datetime.now()
                logger.debug(u"Task id: %s" % unicode(async_result.id))
                sqldb.session.commit()

                if not batch.paid:
                    self.check_and_send_not_paid_user_notification(batch_id, config, logger)
        except Exception:
            logger.exception(u"Failed to queue task")
            batch.status = BatchStatusEnum.BS_EDITED
            sqldb.session.commit()

        return True

    @staticmethod
    def check_and_send_not_paid_user_notification(batch_id, config, logger):
        last_change_dt = datetime.utcnow()
        eta = datetime.utcnow()
        eta = eta.replace(tzinfo=pytz.utc)
        timezone_name = BatchManager.get_batch_timezone(batch_id) or "Europe/Moscow"
        eta = datetime.astimezone(eta, pytz.timezone(timezone_name))
        eta += timedelta(seconds=config['NOT_PAID_BATCH_NOTIFY_TIMEOUT_SECONDS'])

        try:
            not_paid_batch_notify_desired_time = config['NOT_PAID_BATCH_NOTIFY_DESIRED_TIME']
            if not_paid_batch_notify_desired_time:
                desired_time = datetime.strptime(not_paid_batch_notify_desired_time, "%H:%M")
                dt = eta.replace(hour=desired_time.hour, minute=desired_time.minute)
                if dt < eta:
                    dt += timedelta(days=1)
                eta = dt
            eta = eta.astimezone(pytz.utc).replace(tzinfo=None)
        except Exception:
            logger.exception(u"Failed to calculate correct send time")

        from fw.async_tasks import not_paid_check_send

        not_paid_check_send.not_paid_check_and_send.apply_async(kwargs={
            'batch_id': str(batch_id),
            'last_change_dt_str': last_change_dt.strftime("%Y-%m-%dT%H:%M:%S")
        }, eta=eta)

    @staticmethod
    def get_founder_applicant(batch_db, logger=None):
        doc = BatchDocumentDbObject.query.filter_by(batch=batch_db, document_type=DocumentTypeEnum.DT_P11001).first()
        if doc and doc.data and 'founders' in doc.data:
            founders = doc.data['founders']
            for founder in founders:
                if 'documents_recipient_type' in founder:
                    return founder
        logger.error(u"Failed to get founder applicant")

    @staticmethod
    def get_reg_responsible_object(batch_db, logger=None):
        data = batch_db.data

        try:
            if 'registration_way' not in data:
                return

            if data['registration_way'] == 'responsible_person':
                return data['reg_responsible_person']
            else:
                return data.get('reg_responsible_founder', None)
        except Exception:
            if logger:
                logger.exception(u"Failed to get registration responsible object")

    def get_title(self, doc_type):
        return LlcRegBatchManager.DOC_TITLES.get(doc_type, '')

    def get_batch_caption(self, batch):
        if not batch:
            return u""

        company_name = (batch.data or {}).get('short_name')
        return u"Создание ООО «%s»" % company_name if company_name else u"Создание ООО"

    def get_last_modified_batch_caption(self, batch_db):
        if not batch_db:
            return u""

        company_name = (batch_db.data or {}).get('short_name')
        return company_name if company_name else u""

    def get_stage(self, batch_db):
        company_registered = False
        if batch_db.result_fields:
            result_fields = batch_db.result_fields
            if 'ifns_reg_info' in result_fields:
                ifns_reg_info = result_fields['ifns_reg_info']
                if 'status' in ifns_reg_info and ifns_reg_info['status'] == 'registered':
                    company_registered = True
        return 'preparation' if batch_db.status != BatchStatusEnum.BS_FINALISED else \
            ('submission' if not company_registered else
             'running')

    def definalize_batch(self, config, logger, batch, force):
        if batch.status != BatchStatusEnum.BS_FINALISED:
            return False

        result_fields = batch.result_fields or {}
        ifns_reg_status = result_fields.get('ifns_reg_info', {}).get('status', '')
        if ifns_reg_status == 'registered':
            raise errors.DocumentBatchDefinalizationError()

        for doc in BatchDocumentDbObject.query.filter_by(batch=batch):
            if doc.file:
                file_obj = doc.file
                doc.file = None
                FileStorage.remove_file(file_obj.id, config)

        batch.status = BatchStatusEnum.BS_EDITED
        batch.ifns_reg_info = None
        batch.last_change_dt = datetime.utcnow()
        sqldb.session.commit()

        from services.ifns import ifns_manager
        from services.notarius import notarius_manager
        from services.yurist import yurist_manager

        yurist_manager.cancel_check(batch, config, logger)
        notarius_manager.discard_booking(batch, config, logger)
        ifns_manager.discard_booking(batch, logger)

        return True

    def create_batch(self, owner):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
            data={},
            _owner=owner,
            status=BatchStatusEnum.BS_NEW,
            paid=False
        )

        return new_batch

    @staticmethod
    def get_batch_timezone(batch_id):
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id, deleted=False).scalar()
        if not batch or not batch.result_fields:
            return

        registration_address = batch.result_fields.get('registration_address', None)
        if not registration_address or 'region' not in registration_address:
            return

        region = registration_address['region']
        return RFRegionsEnum.get_time_zone(region)

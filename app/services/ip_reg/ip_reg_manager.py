# -*- coding: utf-8 -*-
from datetime import datetime
from fw.api import errors
from fw.db.sql_base import db as sqldb
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import DocumentBatchDbObject, PrivatePersonDbObject, BatchDocumentDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentTypeEnum, BatchStatusEnum, DocumentBatchTypeEnum
from fw.documents.fields.doc_fields import DocumentBatch, PrivatePerson
from fw.storage.file_storage import FileStorage
from template_filters import declension


class IpRegBatchManager(BatchManager):

    DOC_TITLES = {
        DocumentTypeEnum.DT_P21001: u"Заявление о государственной регистрации (форма Р21001)",
        DocumentTypeEnum.DT_IP_STATE_DUTY: u'Квитанция на уплату госпошлины',
        DocumentTypeEnum.DT_IP_DOV_FILING_DOCS: u'Доверенность на подачу документов',
        DocumentTypeEnum.DT_IP_DOV_RECEIVING_DOCS: u'Доверенность на получение документов',
        DocumentTypeEnum.DT_IP_DOV_FILING_RECEIVING_DOCS: u'Доверенность на получение и подачу документов',
        DocumentTypeEnum.DT_IP_USN_CLAIM: u'Заявление о переходе на УСН',
        DocumentTypeEnum.DT_IP_ESHN_CLAIM: u'Заявление о переходе на ЕСХН',
        DocumentTypeEnum.DT_IP_LETTER_INVENTORY: u'Опись для ценного письма'
    }

    def update_batch(self, batch_id, new_batch, current_user_id, config, logger):
        current_batch_db_object = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner_id=current_user_id,
                                                                        deleted=False).first()
        if not current_batch_db_object:
            raise errors.BatchNotFound()

        batch_status = current_batch_db_object.status
        if batch_status not in (BatchStatusEnum.BS_NEW, BatchStatusEnum.BS_EDITED):
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

        # STEP 2: make document set from data and schema
        try:
            new_field_set, new_docs, _ = self.make_docs_for_new_data(
                current_batch.data.value,
                new_batch.data.value,
                current_batch_db_object,
                BatchManager.get_batch_document_fields(current_batch_db_object)
            )
        except errors.DocumentBatchUpdateError, ex:
            logger.exception(u"Failed to update batch with new values")
            current_batch_db_object.error_info = {"error": u"unknown error (%s)" % str(ex)}
            sqldb.session.commit()
            raise

        current_docs_db_models = [doc for doc in current_batch_db_object._documents]
        new_docs_db_models = [BatchDocumentDbObject(**new_doc.get_db_object_data()) for new_doc in new_docs]

        merged_docs, unused_db_docs = self.merge_docs(current_docs_db_models, new_docs_db_models, config)
        for doc in merged_docs:
            doc.batch = current_batch_db_object
            doc._owner_id = current_user_id

        for doc in unused_db_docs:
            BatchDocumentDbObject.query.filter_by(id=doc.id).delete()

        sqldb.session.commit()

        error_info = None
        try:
            current_batch_db_object._metadata = new_batch_db._metadata
            current_batch_db_object.data = merged_fields

            # STEP 4: make result fields
            current_batch_db_object.result_fields = self.make_result_fields(current_batch, new_field_set)
            current_batch_db_object.error_info = None
            sqldb.session.commit()

        except Exception, ex:
            logger.exception(u"Failed to update batch with new values")
            current_batch_db_object.error_info = {"error": u"unknown error"}
            sqldb.session.commit()
            raise errors.DocumentBatchUpdateError()

        if current_batch_db_object.status == BatchStatusEnum.BS_EDITED:
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

    def get_title(self, doc_type):
        return IpRegBatchManager.DOC_TITLES.get(doc_type, '')

    def get_last_modified_batch_caption(self, batch_db):
        if not batch_db:
            return u""

        pp_data = batch_db.data.get('person')
        if pp_data and '_id' in pp_data:
            person_db = PrivatePersonDbObject.query.filter_by(id=pp_data['_id']).first()
            if person_db:
                person = PrivatePerson.db_obj_to_field(person_db)
                full_name_decl = declension(person.get_full_name(), 'gen')
                parts = full_name_decl.split(' ')
                if len(parts) in (2, 3):
                    surname_decl = parts[0].strip()
                    short_name = person.get_short_name()
                    parts = short_name.split(' ')
                    if len(parts) in (2, 3):
                        return surname_decl + u" " + u" ".join(parts[1:])
                return declension(person.get_short_name(), 'gen')

        return u""

    def get_batch_caption(self, batch_db):
        if not batch_db:
            return u""

        pp_data = batch_db.data.get('person')
        if pp_data and '_id' in pp_data:
            person_db = PrivatePersonDbObject.query.filter_by(id=pp_data['_id']).first()
            if person_db:
                person = PrivatePerson.db_obj_to_field(person_db)
                return u"Создание ИП «%s»" % person.get_short_name() if person else u"Создание ИП"

        return u"Создание ИП"

    def get_stage(self, batch_db):
        company_registered = False
        batch_data = batch_db.data
        if 'result_fields' in batch_data:
            result_fields = batch_data['result_fields']
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

        for doc in BatchDocumentDbObject.query.filter_by(batch=batch):
            if doc.file:
                file_obj = doc.file
                doc.file = None
                FileStorage.remove_file(file_obj.id, config)

        batch.status = BatchStatusEnum.BS_EDITED
        batch.ifns_reg_info = None,
        batch.last_change_dt = datetime.utcnow()
        sqldb.session.commit()
        return True

    def create_batch(self, owner):
        new_batch = DocumentBatchDbObject(
            batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
            data={},
            _owner=owner,
            status=BatchStatusEnum.BS_NEW,
            paid=True
        )

        return new_batch

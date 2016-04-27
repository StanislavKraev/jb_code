# -*- coding: utf-8 -*-
from datetime import datetime

from fw.api import errors
from fw.db.sql_base import db as sqldb
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import BatchStatusEnum, DocumentBatchTypeEnum, DocumentTypeEnum
from fw.documents.fields.doc_fields import DocumentBatch


class TestSvcManager(BatchManager):

    DOC_TITLES = {
        DocumentTypeEnum.DT_TEST_DOC_1: u'Тестовый документ 1',
        DocumentTypeEnum.DT_TEST_DOC_2: u'Тестовый документ 2',
        DocumentTypeEnum.DT_TEST_DOC_3: u'Тестовый документ 3'
    }

    BATCH_TYPE = DocumentBatchTypeEnum.DBT_TEST_TYPE

    # def update_batch(self, batch_id, new_batch, current_user_id, db, config, logger):
    #     current_batch_db_object = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner_id=current_user_id,
    #                                                                     deleted=False).first()
    #     if not current_batch_db_object:
    #         raise errors.BatchNotFound()
    #
    #     batch_status = current_batch_db_object.status
    #     # if batch_status not in (BatchStatusEnum.BS_NEW, BatchStatusEnum.BS_EDITED):   # todo
    #     #     logger.warn(u"Can't update batch %s in status %s" % (unicode(batch_id), unicode(batch_status)))
    #     #     raise errors.DocumentBatchUpdateError()
    #
    #     try:
    #         current_batch = DocumentBatch.db_obj_to_field(current_batch_db_object)
    #     except Exception:
    #         logger.fatal(u"Failed to validate batch from DB!")
    #         raise
    #
    #     current_fields = current_batch.data.value
    #     assert isinstance(current_fields, dict)
    #
    #     # STEP 1: make new data and metadata
    #     #         and collect changed fields names
    #     new_batch_db = new_batch.get_db_object()
    #     merged_fields, changed_field_names = self._merge_raw_fields(current_batch_db_object.data, new_batch_db.data)
    #
    #     current_batch_db_object._metadata = new_batch_db._metadata
    #     current_batch_db_object.data = merged_fields
    #     sqldb.session.commit()
    #
    #     # STEP 2: make document set from data and schema
    #     try:
    #         new_field_set, new_docs, _ = self.make_docs_for_new_data(
    #             current_batch.data.value,
    #             new_batch.data.value,
    #             current_batch_db_object,
    #             current_batch._documents.values
    #         )
    #     except errors.DocumentBatchUpdateError, ex:
    #         logger.exception(u"Failed to update batch with new values")
    #         current_batch_db_object.error_info = {"error": u"unknown error (%s)" % str(ex)}
    #         sqldb.session.commit()
    #         raise
    #
    #     current_docs_db_models = [doc for doc in current_batch_db_object._documents]
    #     new_docs_db_models = [BatchDocumentDbObject(**new_doc.get_db_object_data()) for new_doc in new_docs]
    #
    #     merged_docs, unused_db_docs = self.merge_docs(current_docs_db_models, new_docs_db_models, config)
    #     for doc in merged_docs:
    #         doc.batch = current_batch_db_object
    #         doc._owner_id = current_user_id
    #
    #     for doc in unused_db_docs:
    #         BatchDocumentDbObject.query.filter_by(id=doc.id).delete()
    #
    #     sqldb.session.commit()
    #
    #     # STEP 3: combine old and new documents
    #     error_info = None
    #     try:
    #         current_batch_db_object.metadata = new_batch_db.metadata
    #         current_batch_db_object.data = merged_fields
    #
    #         # STEP 5: make result fields
    #         current_batch_db_object.result_fields = self.make_result_fields(current_batch, new_field_set)
    #         current_batch_db_object.error_info = None
    #         sqldb.session.commit()
    #     except Exception, ex:
    #         logger.exception(u"Failed to update batch with new values")
    #         current_batch_db_object.error_info = {"error": u"unknown error"}
    #         sqldb.session.commit()
    #         raise errors.DocumentBatchUpdateError()
    #
    #     error_ext = self.get_batch_errors(current_batch_db_object, logger)
    #     if error_ext:
    #         error_info = {'error_ext': error_ext}
    #     else:
    #         error_info = None
    #     current_batch_db_object.error_info = error_info
    #     sqldb.session.commit()
    #
    #     self.check_transition(current_batch_db_object)
    #
    #     current_batch = DocumentBatch.db_obj_to_field(current_batch_db_object)
    #     struct = current_batch.get_api_structure()
    #
    #     if error_info:
    #         struct['error_info'] = error_info
    #     elif 'error_info' in struct:
    #         del struct['error_info']
    #
    #     return {'result': struct}

    def get_title(self, doc_type):
        return TestSvcManager.DOC_TITLES.get(doc_type, '')

    def get_batch_caption(self, batch):
        return u"Тестовый батч"

    def get_stage(self, batch):
        return 'unknown'

    def definalize_batch(self, config, logger, batch, force):
        if batch.status != BatchStatusEnum.BS_FINALISED:
            return False

        batch.status = BatchStatusEnum.BS_EDITED
        batch.ifns_reg_info = None,
        batch.last_change_dt = datetime.utcnow()
        sqldb.session.commit()
        return True


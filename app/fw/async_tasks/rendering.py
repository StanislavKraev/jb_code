# -*- coding: utf-8 -*-
import json
import os
import sys
from copy import copy
from datetime import datetime

from celery.exceptions import SoftTimeLimitExceeded
from celery import current_app as celery
from celery import current_task
from sqlalchemy.orm import make_transient

from fw.api.base_handlers import error_tree_to_list
from fw.async_tasks import send_email
from fw.async_tasks.scheduler import CeleryScheduler
from fw.auth.user_manager import UserManager
from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject, DocGroupRenderTaskCheck, \
    PrivatePersonDbObject, DocumentFilesObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import UserDocumentStatus, BatchStatusEnum, DocumentBatchTypeEnum
from fw.documents.fields.doc_fields import UserDocument, PrivatePerson
from fw.monitoring_utils import zabbix_sender
from fw.storage.file_storage import FileStorage
from fw.storage.models import FileObject
from template_filters import utm_args

celery.config_from_envvar('CELERY_CONFIG_MODULE')


class BatchTaskFileIdHolder(object):
    def __init__(self, task_id, config, batch):
        self.task_id = task_id
        self.config = config
        self.file_name = os.path.join(os.path.dirname(self.config['celery_tasks_dir']), unicode(self.task_id))
        self.batch = batch
        self.unbind = False

    def __enter__(self):
        if not os.path.exists(self.file_name):
            try:
                with open(self.file_name, 'w') as f:
                    f.write(str(self.task_id))
            except Exception:
                pass
        return self

    def __exit__(self, *args):
        if self.file_name and os.path.exists(self.file_name):
            try:
                os.unlink(self.file_name)
            except Exception:
                pass

        if self.unbind:
            return
        self.batch.current_task_id = None
        sqldb.session.commit()

    def exists(self):
        return os.path.exists(self.file_name)


class FakeTaskHolder(object):
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def exists(self):
        return True


# noinspection PyProtectedMember
def render_single_document(db_doc, doc_title, watermark, config, logger, task_id, render_doc_file):
    doc_id = db_doc.id

    doc_type = db_doc.document_type
    owner = db_doc._owner
    if not db_doc:
        logger.info(u"Exit 1")
        return False

    from fw.documents.doc_builder import DocBuilder

    if db_doc._celery_task_id is None:
        db_doc._celery_task_started = datetime.utcnow()
        db_doc._celery_task_id = task_id
        sqldb.session.commit()
    elif db_doc._celery_task_id != task_id:
        if db_doc._celery_task_started and abs((datetime.utcnow() - db_doc._celery_task_started).total_seconds()) > 60:
            db_doc._celery_task_started = datetime.utcnow()
            db_doc._celery_task_id = task_id
            sqldb.session.commit()
        else:
            logger.info(u"Exit 2")
            return False

    user_doc = UserDocument.db_obj_to_field(db_doc)
    try:
        doc_data = user_doc.get_db_object_data()["data"]
        db_doc.status = UserDocumentStatus.DS_RENDERING
        db_doc.tried_to_render = True
        sqldb.session.commit()
        result = DocBuilder.process(doc_data, doc_type, config, owner.id, add_watermark=watermark, render_doc_file=render_doc_file)
        if result:
            current_doc = BatchDocumentDbObject.query.filter_by(id=doc_id).scalar()
            if not current_doc or current_doc._celery_task_id != task_id:
                logger.warn(u"Failed to set result: user document has been captured by another task")
                logger.info(u"Exit 3")
                return False

            for doc_file in db_doc.files:
                old_file_id = doc_file.id
                FileStorage.remove_file(old_file_id, config)
                db_doc.files.remove(doc_file)

            file_id = None
            for file_id in result:
                new_doc_file = DocumentFilesObject(doc_id=doc_id, files_id=file_id)
                sqldb.session.add(new_doc_file)

            if file_id:
                updated_count = BatchDocumentDbObject.query.filter_by(id=doc_id, _celery_task_id=task_id).update({
                    'status': UserDocumentStatus.DS_RENDERED,
                    'caption': doc_title,
                    'pages_count': FileStorage.get_pdf_file_page_count(file_id, config)
                })
                if not updated_count:
                    logger.warn(u"Failed to set result: user document has been captured by another task 2")
                    logger.info(u"Exit 4")
                    sqldb.session.rollback()
                    return False

            sqldb.session.commit()
            logger.info(u"Exit 5")
            return True
        else:
            raise Exception(u"Failed to generate document %s" % doc_type)
    except Exception, ex:
        logger.exception(u"Failed to render document %s" % doc_type)
        db_doc.status = UserDocumentStatus.DS_RENDERING_FAILED
        sqldb.session.commit()
        try:
            error_message = ex.message if isinstance(ex.message, unicode) else unicode(ex.message, errors='ignore')
            logger.exception(error_message)
        except Exception:
            logger.error(u"Failed to make error")
    finally:
        try:
            if BatchDocumentDbObject.query.filter_by(id=doc_id, _celery_task_id=task_id).update({
                '_celery_task_id': None,
                '_celery_task_started': None
            }):
                sqldb.session.commit()
        except Exception:
            current_doc = BatchDocumentDbObject.query.filter_by(id=doc_id).scalar()
            logger.error(u"Failed to reset task id! Document object in db: %s" %
                         json.dumps(current_doc.__dict__, indent=1, default=lambda x: unicode(x), ensure_ascii=False))
    logger.info(u"Exit 6")
    return False


def render_batch_raw(batch_db_object_id, render_only_failed_docs=False):
    request = current_task.request
    config = celery.conf.get('config')
    eager = celery.conf['CELERY_ALWAYS_EAGER']
    app = celery.conf['flask_app']()
    logger = app.logger

    from fw.documents.batch_manager import BatchManager
    with app.app_context():
        batch_db_object = DocumentBatchDbObject.query.filter_by(id=batch_db_object_id).first()
        if not batch_db_object:
            logger.error(u"Failed to find batch with id %s in collection %s in db %s" % (
                batch_db_object_id, DocumentBatchDbObject.COLLECTION_NAME, config['db_name']))
            return False

        batch_db_object.current_task_id = request.id
        batch_db_object.batch_rendering_start = datetime.utcnow()
        sqldb.session.commit()

        task_holder = BatchTaskFileIdHolder(request.id, config, batch_db_object) if not eager else FakeTaskHolder()
        with task_holder as task_file:
            logger.info(u"Generating documents for batch %s" % batch_db_object_id)

            try:
                batch_type = batch_db_object.batch_type

                batch_manager = BatchManager.init(batch_db_object)
                batch_descriptor = DocRequisitiesStorage.get_batch_descriptor(batch_type)
                doc_types_allowed_to_deferred_rendering = batch_descriptor.get('deferred_render_docs', [])

                watermark = None if batch_db_object.paid else "notpaid_watermark.png"

                has_errors = False
                failed_doc_types = set()
                for doc in batch_db_object._documents:
                    # if not task_file.exists():
                    #     logger.warning(u"Task with id %s has been revoked" % request.id)
                    #     batch_db_object.status = BatchStatusEnum.BS_EDITED
                    #     sqldb.session.commit()
                    #     return True

                    doc_type = doc.document_type
                    if render_only_failed_docs and doc.status != UserDocumentStatus.DS_RENDERING_FAILED:
                        continue

                    render_doc_file = batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC and batch_db_object.paid
                    if not render_single_document(doc, batch_manager.get_title(doc_type), watermark,
                                                  config, logger, request.id, render_doc_file):
                        has_errors = True
                        if doc_type not in doc_types_allowed_to_deferred_rendering:
                            if not render_only_failed_docs:
                                batch_db_object.status = BatchStatusEnum.BS_EDITED
                                batch_db_object.error_info = {
                                    "error_ext": [{
                                        "field": "",
                                        "error_code": 0,
                                        "message": u"Failed to render document %s" % doc_type
                                    }]
                                }
                            sqldb.session.commit()

                            return False
                    failed_doc_types.add(doc_type)

                if not render_only_failed_docs:
                    batch_db_object.finalisation_count += 1
                    batch_db_object.status = BatchStatusEnum.BS_FINALISED
                    if batch_db_object.batch_rendering_start:
                        try:
                            dt = datetime.utcnow() - batch_db_object.batch_rendering_start
                            fs = dt.total_seconds() + dt.microseconds / 1000000.
                            zabbix_sender.send('celery_max_time', fs)
                        except Exception:
                            pass
                    batch_db_object.finalisation_date = datetime.utcnow()
                    CeleryScheduler.remove("not_finalised_check_and_send%s" % str(batch_db_object_id))
                    try:
                        if batch_db_object.batch_rendering_start:
                            dt = datetime.utcnow() - batch_db_object.batch_rendering_start
                            seconds = dt.total_seconds()
                            zabbix_sender.send("celery_max_time", seconds)
                    except Exception:
                        pass
                sqldb.session.commit()

                if has_errors:
                    if len(failed_doc_types) == 1 and failed_doc_types.pop() in ('reg_fee_invoice', 'ip_reg_fee_invoice'):
                        from services.ifns import ifns_manager
                        if ifns_manager.if_gp_pay_working():
                            logger.error(u"Invalid fee invoice render attempt (service.nalog.ru is working). Cancelling!")
                            batch_db_object.status = BatchStatusEnum.BS_EDITED
                            sqldb.session.commit()
                            return False
                    async_result = render_batch.apply_async((batch_db_object_id,), {'render_only_failed_docs': True}, countdown=300)
                    if not async_result.ready():
                        task_file.unbind = True
                        new_task_id = unicode(async_result.id)
                        batch_db_object.current_task_id = new_task_id
                        batch_db_object.batch_rendering_start = datetime.utcnow()
                        logger.debug(u"Task id: %s" % new_task_id)
                        sqldb.session.commit()
            except Exception:
                logger.exception(u"Failed to render batch %s" % batch_db_object_id)
                if not render_only_failed_docs:
                    batch_db_object.status = BatchStatusEnum.BS_EDITED
                    sqldb.session.commit()

        if render_only_failed_docs and batch_db_object.paid:
            user = batch_db_object._owner
            addr_to = user.email or ""
            if not addr_to:
                logger.warning(u"Failed to send email: user %s has no email" % unicode(user.id))
            else:
                documents = BatchManager.get_shared_links_to_rendered_docs(batch_db_object, config, logger)

                if batch_db_object.batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC:
                    go_further_url = u"%s://%s/ooo/?id=%s" % (
                        config['WEB_SCHEMA'], config['DOMAIN'], batch_db_object_id)
                    go_further_url = utm_args(go_further_url, 'deferred_docs_ready', user.id) + u"#page=documents"
                    go_further_url = UserManager.make_auth_url(go_further_url, user).get_url(config)

                    short_name = batch_db_object.data.get('short_name', "")
                    send_email.send_email.delay(addr_to, "deferred_docs_ready",
                                                go_further_url=go_further_url,
                                                short_name=short_name,
                                                schema=config['WEB_SCHEMA'],
                                                domain=config['DOMAIN'],
                                                docs=documents,
                                                user_id=str(user.id)
                                                )
                elif batch_db_object.batch_type == DocumentBatchTypeEnum.DBT_NEW_IP:
                    go_further_url = u"%s://%s/ip/?id=%s" % (
                        config['WEB_SCHEMA'], config['DOMAIN'], batch_db_object_id)
                    go_further_url = utm_args(go_further_url, 'deferred_ip_docs_ready', user.id) + u"#page=documents"
                    go_further_url = UserManager.make_auth_url(go_further_url, user).get_url(config)
                    short_name = ""
                    try:
                        pp_data = batch_db_object.data.get('person')
                        if pp_data and '_id' in pp_data:
                            person_db = PrivatePersonDbObject.query.filter_by(id=pp_data['_id']).scalar()
                            if person_db:
                                person = PrivatePerson.db_obj_to_field(person_db)
                                short_name = person.get_short_name()
                    except Exception:
                        logger.exception(u"Failed to get batch caption")

                    send_email.send_email.delay(addr_to, "deferred_ip_docs_ready",
                                                go_further_url=go_further_url,
                                                short_name=short_name,
                                                schema=config['WEB_SCHEMA'],
                                                domain=config['DOMAIN'],
                                                docs=documents,
                                                user_id=str(user.id)
                                                )

    return True


# noinspection PyProtectedMember
@celery.task()
def render_batch(batch_db_object_id, render_only_failed_docs=False):
    return render_batch_raw(batch_db_object_id, render_only_failed_docs)


@celery.task()
def render_document_preview(document_object_id):
    document_object_id = document_object_id
    config = celery.conf.get('config')
    request = current_task.request
    sys.path.append(os.path.normpath(os.path.abspath(os.path.dirname(__name__))))

    logger = celery.log.get_default_logger()

    with celery.conf['flask_app']().app_context():
        db_doc = BatchDocumentDbObject.query.filter_by(id=document_object_id).scalar()
        if not db_doc or db_doc.status not in (UserDocumentStatus.DS_NEW,
                                               UserDocumentStatus.DS_RENDERING_FAILED,
                                               UserDocumentStatus.DS_RENDERING) \
           or db_doc._celery_task_id not in (None, request.id):
            return False

        from fw.documents.batch_manager import BatchManager

        batch_manager = BatchManager.init(db_doc.batch)
        doc_caption = batch_manager.get_batch_caption(db_doc.batch)
        return render_single_document(db_doc, doc_caption, 'preview_watermark.png', config, logger, request.id)


@celery.task()
def render_batch_document(batch_db_object_id, doc_id):
    config = celery.conf.get('config')
    app = celery.conf['flask_app']()
    with app.app_context():
        return render_batch_document_raw(batch_db_object_id, doc_id, config)


@celery.task()
def render_document_plugin(batch_id, event_data):
    doc_id = event_data['doc_id']
    from fw.documents.batch_manager import BatchManager
    config = celery.conf.get('config')
    app = celery.conf['flask_app']()
    logger = celery.log.get_default_logger()
    with app.app_context():
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).scalar()
        if not batch:
            BatchManager.handle_event(batch_id, "doc_render_fail", event_data, logger, config=config)
            batch_group_gen_check_task.delay()
            raise Exception("Batch not found: %s" % batch_id)
        try:
            render_batch_document_raw(batch_id, doc_id, config)
            doc = BatchDocumentDbObject.query.filter_by(id=doc_id).scalar()
            assert(doc)
            event = "doc_render_success" if doc.status == UserDocumentStatus.DS_RENDERED else "doc_render_fail"
            logger.info(u"render_document_plugin event %s for document %s" % (event, doc.id))
            BatchManager.handle_event(batch_id, event, event_data, logger, config=config)
            batch_group_gen_check_task.delay()
        except Exception:
            zabbix_sender.send("celery_failures", 1)
            BatchManager.handle_event(batch_id, "doc_render_fail", event_data, logger, config=config)
            batch_group_gen_check_task.delay()
            raise


@celery.task()
def batch_group_gen_check_task():
    from fw.documents.batch_manager import BatchManager
    app = celery.conf['flask_app']()
    logger = celery.log.get_default_logger()
    with app.app_context():
        for batch_check in DocGroupRenderTaskCheck.query.filter_by(check_completed=False):
            logger.info(u"Checking check %s" % str(batch_check.id))
            batch = DocumentBatchDbObject.query.filter_by(id=batch_check.batch_id).scalar()
            if not batch:
                BatchManager.handle_event(batch_check.batch_id, "doc_group_render_fail", {}, logger, config=app.config)
                raise Exception("Batch not found: %s" % batch_check.batch_id)
            doc_id_list = batch_check.doc_id_list
            all_rendered = True
            logger.info(u"Checking. Doc id list length: %s" % str(len(doc_id_list)))
            for doc_id in doc_id_list:
                doc = BatchDocumentDbObject.query.filter_by(id=doc_id).scalar()
                logger.info(u"Checking doc %s." % str(doc_id))
                if not doc or doc.status == UserDocumentStatus.DS_RENDERING_FAILED or \
                   doc._celery_task_id and abs((datetime.utcnow() - doc._celery_task_started).total_seconds()) > 60:
                    res = DocGroupRenderTaskCheck.query.filter_by(id=batch_check.id, check_completed=False).update({
                        'check_completed': True
                    })
                    sqldb.session.commit()
                    logger.info(u"Checking -> checked %s." % str(res))
                    if res:
                        all_rendered = False
                        logger.info(u"Checking: handling doc_group_render_fail for %s" % str(batch_check.batch_id))
                        BatchManager.handle_event(batch_check.batch_id, "doc_group_render_fail", batch_check.event_data, logger, config=app.config)
                    break
                if doc.status != UserDocumentStatus.DS_RENDERED:
                    logger.info(u"Checking: doc %s is not rendered" % str(doc.id))
                    all_rendered = False
            if all_rendered:
                logger.info(u"Checking: All rendered")
                res = DocGroupRenderTaskCheck.query.filter_by(id=batch_check.id, check_completed=False).update({
                    'check_completed': True
                })
                sqldb.session.commit()
                if res:
                    BatchManager.handle_event(batch_check.batch_id, "doc_group_render_success", batch_check.event_data, logger, config=app.config)

    return True


def render_batch_document_raw(batch_db_object_id, doc_id, config):
    start_time = datetime.utcnow()
    request_id = current_task.request.id
    logger = celery.log.get_default_logger()
    logger.info(u"Starting rendering document %s of %s" % (doc_id, batch_db_object_id))
    target_document = BatchDocumentDbObject.query.filter_by(id=doc_id).scalar()
    if not target_document:
        logger.warn(u" - O_o - ")
        return False

    if celery.conf['CELERY_ALWAYS_EAGER']:
        request_id = "test"
        target_document._celery_task_id = request_id
        target_document._celery_task_started = start_time

    logger.info(u"doc type of %s is %s" % (doc_id, target_document.document_type))
    if target_document and target_document.status == UserDocumentStatus.DS_RENDERING:
        assert(target_document._celery_task_id)
        assert(target_document._celery_task_started)
        if target_document._celery_task_id != request_id:
            logger.info(u" - B - ")
            if abs((datetime.utcnow() - target_document._celery_task_started).total_seconds()) < 60:
                logger.info(u" - C - ")
                logger.info(
                    u"Task for rendering %s of %s is already being run. Exiting..." % (doc_id, batch_db_object_id))
                return True

        result = BatchDocumentDbObject.query.filter_by(id=doc_id, status=UserDocumentStatus.DS_RENDERING).update(
            {
                '_celery_task_id': request_id,
                '_celery_task_started': start_time
            }
        )
        sqldb.session.commit()

        if not result:
            logger.error(u"Failed to change status of document being rendered into RENDERING state. \n"
                         u"Probably document is being generated now already 1")
            return True

    logger.info(u" - F - ")
    batch_db_object = DocumentBatchDbObject.query.filter_by(id=batch_db_object_id).scalar()
    if not batch_db_object:
        logger.error(u"Failed to find batch with id %s" % batch_db_object_id)
        return True

    from fw.documents.batch_manager import BatchManager

    owner_id = batch_db_object._owner_id

    logger.info(u" - I - ")
    if target_document.file:
        file_obj = target_document.file
        target_document.file = None
        FileStorage.remove_file(file_obj.id, config)

    BatchDocumentDbObject.query.filter_by(id=target_document.id).update({
        'file_id': None,
        'status': UserDocumentStatus.DS_RENDERING,
        'data': {},
        '_celery_task_id': request_id,
        '_celery_task_started': start_time,
        'tried_to_render': True
    })
    sqldb.session.commit()
    target_document = BatchDocumentDbObject.query.filter_by(id=target_document.id).scalar()
    logger.info(u" - J updated %s - " % target_document.id)

    try:
        target_document = UserDocument.db_obj_to_field(target_document)
        _ = batch_db_object.data
        detached_batch = batch_db_object
        sqldb.session.expunge(detached_batch)
        make_transient(detached_batch)

        target_document_data = BatchManager.make_document(detached_batch, target_document.document_type.db_value())
        batch_db_object = DocumentBatchDbObject.query.filter_by(id=batch_db_object_id).scalar()

        logger.info(u" - T - ")
        if not target_document_data:
            logger.info(u" - U - ")
            BatchDocumentDbObject.query.filter_by(id=doc_id, _celery_task_id=request_id).update({
                'status': UserDocumentStatus.DS_RENDERING_FAILED,
                '_celery_task_id': None,
                '_celery_task_started': None
            })
            sqldb.session.commit()
            return True

        target_document.data.value = target_document_data
        target_document.data.initialized = True

        doc_data = target_document.get_db_object_data()["data"]
        result = BatchDocumentDbObject.query.filter_by(id=doc_id, _celery_task_id=request_id).update({'data': doc_data})
        sqldb.session.commit()

        # batch_descriptor = DocRequisitiesStorage.get_batch_descriptor(batch_db_object.batch_type)
        # validator_condition_schema = batch_descriptor.get('validation_condition', None)
        # from fw.documents.schema.var_construction import VarConstructorFactory
        # validator_condition = VarConstructorFactory.make_constructor(validator_condition_schema) if validator_condition_schema else None
        #
        # validation_type = ValidationTypeEnum.VT_STRICT
        #
        # if validator_condition:
        #     context = {
        #         '<document>': target_document,
        #         '<batch>': batch_db_object
        #     }
        #     validation_type = validator_condition.build(context)
        #
        # if validation_type != ValidationTypeEnum.VT_NO:
        #     target_document.validate(strict=(validation_type == ValidationTypeEnum.VT_STRICT))

        target_document.validate(strict=True)
        logger.info(u" - V - ")
    except Exception, ex:
        logger.info(u" - W - ")
        logger.exception(u"Failed to make document %s from batch %s" % (doc_id, batch_db_object_id))
        ext_data = []
        if getattr(ex, 'ext_data', None):
            ext_data.extend(ex.ext_data)
        if ext_data:
            error_info_ext = error_tree_to_list(ext_data)
            error_info_ext = [{
                'field': '.'.join(i['field'].split('.')[1:]) if '.' in i['field'] else i['field'],
                'error_code': i['error_code']
            } for i in error_info_ext]
            if not batch_db_object.error_info or 'error_ext' not in batch_db_object.error_info:
                batch_db_object.error_info = {
                    'error_ext': error_info_ext
                }
            else:
                error_info_fields_set = set([i['field'] for i in batch_db_object.error_info['error_ext']])
                merged_error_info = copy(batch_db_object.error_info)
                for i in error_info_ext:
                    if i['field'] not in error_info_fields_set:
                        merged_error_info['error_ext'].append({
                            'field': i['field'],
                            'error_code': i['error_code']
                        })
                sqldb.session.commit()
                batch_db_object.error_info = merged_error_info

        logger.info(u" - pre YY -> XX: %s - " % str(doc_id))

        result = BatchDocumentDbObject.query.filter_by(id=doc_id, _celery_task_id=request_id).update({
            'status': UserDocumentStatus.DS_RENDERING_FAILED,
            '_celery_task_id': None,
            '_celery_task_started': None
        })
        sqldb.session.commit()
        if not result:
            logger.warn(u"Failed to mark rendering document as failed")
            logger.info(u" - X - ")

        logger.info(u" - XX - ")
        return True

    logger.info(u" - Y - ")

    if not result:
        logger.error(u"Failed to update document %s in batch %s: suddenly document not found" % (
            doc_id, batch_db_object_id))
        return True

    assert target_document
    assert doc_id

    logger.info(u" - AA doc_id= %s - " % doc_id)
    try:

        try:
            from fw.documents.doc_builder import DocBuilder

            result = DocBuilder.process(doc_data, target_document.document_type.db_value(), config, owner_id, add_watermark=None) # TODO: watermark logic for not-paid batches, preview documents
            if result:
                logger.info(u" - BB - ")
                first_file_id = result[0]
                assert first_file_id
                file_obj = FileObject.query.filter_by(id=first_file_id).first()
                if file_obj:
                    logger.info(u" - BB file_obj = %s - " % first_file_id)
                    BatchDocumentDbObject.query.filter_by(id=doc_id, _celery_task_id=request_id).update({
                        'status': UserDocumentStatus.DS_RENDERED,
                        'pages_count': FileStorage.get_pdf_file_page_count(first_file_id, config)
                    })
                    DocumentFilesObject.query.filter_by(doc_id=doc_id).delete()

                    for file_id in result:
                        new_doc_file = DocumentFilesObject(
                            doc_id=doc_id,
                            files_id=file_id
                        )
                        sqldb.session.add(new_doc_file)
            else:
                logger.info(u" - CC - ")
                raise Exception("Failed to generate document %s" % doc_id)
        except Exception, ex:
            logger.info(u" - DD - ")
            logger.exception(u"Failed to render document %s" % doc_id)

            result = BatchDocumentDbObject.query.filter_by(id=doc_id,
                                                           _celery_task_id=request_id).update(
            {
                'status': UserDocumentStatus.DS_RENDERING_FAILED,
                '_celery_task_id': None,
                '_celery_task_started': None
            })
            if not result:
                logger.warn(u"Failed to mark document %s as failed to render" % doc_id)
            sqldb.session.commit()

            return True

        BatchDocumentDbObject.query.filter_by(id=doc_id,
                                              _celery_task_id=request_id).update(
            {
                'status': UserDocumentStatus.DS_RENDERED,
                '_celery_task_id': None,
                '_celery_task_started': None
            }
        )
        sqldb.session.commit()
        logger.info(u" - EE - ")
    except SoftTimeLimitExceeded:
        logger.info(u" - FF - ")
        logger.exception(u"Did not have time to complete rendering. Exiting")
        result = BatchDocumentDbObject.query.filter_by(id=doc_id,
                                                       _celery_task_id=request_id).update(
        {
            'status': UserDocumentStatus.DS_RENDERING_FAILED,
            '_celery_task_id': None,
            '_celery_task_started': None

        })
        sqldb.session.commit()
        if not result:
            logger.warn(u"Failed to mark document %s as failed" % doc_id)
        return True
    logger.info(u" - GG - ")
    return True

@celery.task()
def touch_batch_plugin(batch_id, event_data):
    from fw.documents.batch_manager import BatchManager
    config = celery.conf.get('config')
    app = celery.conf['flask_app']()
    logger = celery.log.get_default_logger()
    with app.app_context():
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).scalar()
        if not batch:
            raise Exception("Batch not found: %s" % batch_id)
        BatchManager.handle_event(batch_id, "batch_manager.touch", event_data, logger, config=config)
    return True

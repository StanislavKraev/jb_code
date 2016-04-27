# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import json
import codecs
import subprocess
import tempfile
import os
import re

from flask import current_app, Blueprint
from flask_login import login_required, current_user
from sqlalchemy.orm import make_transient, joinedload
from common_utils import remove_task_id_run_file

from fw.api import errors
from fw.api.args_validators import validate_arguments, BoolTypeValidator, EnumValidator, IntValidator, JsonValidator, \
    ArgumentValidator
from fw.api.base_handlers import api_view
from fw.async_tasks import rendering
from fw.async_tasks.scheduler import CeleryScheduler
from fw.db.sql_base import db as sqldb
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import BatchStatusEnum, DocumentBatchTypeEnum, UserDocumentStatus, DocumentTypeEnum
from fw.documents.fields.doc_fields import DocumentBatch
from fw.storage.file_storage import FileStorage
from fw.utils.time_utils import calc_fixed_time_not_earlier

MAX_PREVIEW_RENDERING_DURATION_SECONDS = 60

documents_bp = Blueprint('documents', __name__)

def _finalize_batch(batch):
    batch_status = batch.status
    if batch_status == BatchStatusEnum.BS_FINALISED:
        return {"result": True}

    if batch_status not in (BatchStatusEnum.BS_NEW, BatchStatusEnum.BS_EDITED):
        raise errors.DocumentBatchFinalizationError()

    docs = batch._documents
    if not docs:
        return {"result": False}

    batch_manager = BatchManager.init(batch)

    try:
        if not batch_manager.finalize_batch(current_app.config, current_app.logger, batch):
            raise errors.DocumentBatchFinalizationError()
    except Exception:
        current_app.logger.exception(u"Finalisation error")
        return {"result": False}

    return {"result": True}

@documents_bp.route('/batch/finalise/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator())
def finalize_batch(batch_id=None):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch:
        raise errors.BatchNotFound()
    return _finalize_batch(batch)


@documents_bp.route('/batch/finalise/cancel/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator())
def cancel_batch_finalization(batch_id=None):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch:
        raise errors.BatchNotFound()
    if batch.status != BatchStatusEnum.BS_BEING_FINALISED:
        return {"result": True}

    try:
        BatchManager.cancel_batch_finalization(batch, current_app.config, current_app.logger)
    except Exception:
        current_app.logger.exception(u"Failed to cancel batch finalization.")
        return {"result": False}

    return {"result": True}


@documents_bp.route('/batch/unfinalise/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator(), force=BoolTypeValidator(required=False))
def unfinalize_batch(batch_id=None, force=False):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).scalar()
    if not batch:
        raise errors.BatchNotFound()
    if batch.status not in (BatchStatusEnum.BS_FINALISED,):
        raise errors.DocumentBatchDefinalizationError()

    if batch.current_task_id:
        from celery import app as celery
        current_app.logger.debug(u"There are task id: %s" % unicode(batch.current_task_id))
        celery.default_app.control.revoke(batch.current_task_id)
        remove_task_id_run_file(current_app.config, batch.current_task_id)
        batch.current_task_id = None
        batch.batch_rendering_start = None
        sqldb.session.commit()

    batch_manager = BatchManager.init(batch)
    try:
        if not batch_manager.definalize_batch(current_app.config, current_app.logger, batch, force):
            raise errors.DocumentBatchDefinalizationError()
    except Exception:
        batch.status = BatchStatusEnum.BS_FINALISED
        sqldb.session.commit()
        raise errors.DocumentBatchDefinalizationError()

    return {"result": True}


@documents_bp.route('/batch/create/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_type=EnumValidator(DocumentBatchTypeEnum))
def batch_create(batch_type=None):
    try:
        DocRequisitiesStorage.get_batch_descriptor(batch_type)
    except Exception:
        raise errors.InvalidParameterValue('batch_type')

    batch_manager = BatchManager.init(batch_type=batch_type)
    new_batch = batch_manager.create_batch(current_user)
    sqldb.session.add(new_batch)
    sqldb.session.commit()
    doc_batch = DocumentBatch.db_obj_to_field(new_batch)
    return {'result': doc_batch.get_api_structure()}


@documents_bp.route('/batch/', methods=['GET'])
@api_view
@login_required
@validate_arguments(
    count=IntValidator(min_val=0, required=False),
    offset=IntValidator(min_val=0, required=False),
    batch_id=ArgumentValidator(required=False),
    finalised=BoolTypeValidator(required=False)
)
def get_batch(count=None, offset=None, batch_id=None, finalised=None):
    batch_api_structures = []

    broken_batch_ids = []
    if batch_id:
        batch_db_obj = DocumentBatchDbObject.query.filter_by(id=batch_id,
                                                             _owner=current_user,
                                                             _broken=False, deleted=False).first()
        if not batch_db_obj:
            raise errors.BatchNotFound()
        sqldb.session.expunge(batch_db_obj)
        make_transient(batch_db_obj)
        total = 1
        result_count = 1
        if 1:
            try:
                batch_api_structures.append(DocumentBatch.db_obj_to_field(batch_db_obj).get_api_structure())
            except Exception:
                current_app.logger.exception(u"Set batch _broken")
                broken_batch_ids.append(batch_id)
    else:
        query = DocumentBatchDbObject.query.filter_by(_owner=current_user, _broken=False, deleted=False).options(joinedload(DocumentBatchDbObject._documents))

        if finalised is not None:
            query = query.filter_by(status=BatchStatusEnum.BS_FINALISED) if finalised else query.filter(
                DocumentBatchDbObject.status != BatchStatusEnum.BS_FINALISED)
        query = query.order_by(DocumentBatchDbObject.creation_date.desc())
        total = query.count()
        if count is not None:
            query = query.limit(count)
        if offset is not None:
            query = query.offset(offset)
        result_count = query.count()
        has_broken = False
        with current_app.model_cache_context:
            for item in query:
                batch_id = item.id
                sqldb.session.expunge(item)
                make_transient(item)

                for doc in item._documents:
                    current_app.model_cache_context.add(BatchDocumentDbObject.__tablename__, doc.id, doc)
                if 1:
                    try:
                        batch_api_structures.append(
                            DocumentBatch.db_obj_to_field(item).get_api_structure(db_obj=item))
                    except Exception:
                        current_app.logger.exception(u"Set batch _broken %s" % unicode(item.id))
                        broken_batch_ids.append(batch_id)
                        has_broken = True
                        continue
        if has_broken:
            for batch_id in broken_batch_ids:
                batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
                if batch:
                    batch._broken = True
            sqldb.session.commit()

    result = {
        'result': {
            'total': total,
            'count': result_count,
            'batches': batch_api_structures
        }
    }
    return result


@documents_bp.route('/batch/status/', methods=['GET'])
@api_view
@login_required
@validate_arguments(
    batch_id=ArgumentValidator(required=True),
)
def get_batch_status(batch_id=None):
    batch_db_obj = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch_db_obj:
        raise errors.BatchNotFound()
    batch = DocumentBatch.db_obj_to_field(batch_db_obj)
    result = {
        'result': batch.get_api_structure(skip_documents=True)
    }
    return result


@documents_bp.route('/batch/delete/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator())
def batch_delete(batch_id=None):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch:
        raise errors.BatchNotFound()
    batch.deleted = True
    sqldb.session.commit()

    return {'result': True}


def schedule_notification_email(batch_id):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, deleted=False, finalisation_count=0).scalar()
    if not batch or batch.status not in (BatchStatusEnum.BS_NEW, BatchStatusEnum.BS_EDITED):
        return

    mail_type = 'please_finalise'
    if mail_type in (batch.sent_mails or []):
        return False

    user = batch._owner
    if not user or not user.email:
        return

    manager = BatchManager.init(batch)
    timezone_name = manager.get_batch_timezone(batch_id) or "Europe/Moscow"

    desired_time = current_app.config['NOT_PAID_BATCH_NOTIFY_DESIRED_TIME']
    timeout_td = timedelta(seconds=current_app.config['NOT_PAID_BATCH_NOTIFY_TIMEOUT_SECONDS'])
    dt = calc_fixed_time_not_earlier(datetime.utcnow(), desired_time, timeout_td, timezone_name)

    CeleryScheduler.post(
        "fw.async_tasks.not_paid_check_send.not_finalised_check_and_send",
        task_id="not_finalised_check_and_send%s" % str(batch_id),
        force_replace_task=True,
        kwargs={
            'batch_id': str(batch_id),
            'last_change_dt_str': batch.last_change_dt.strftime("%Y-%m-%dT%H:%M:%S")
        },
        eta=dt
    )


@documents_bp.route('/batch/update/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator(), batch=JsonValidator())
def batch_update(batch_id=None, batch=None):
    with current_app.model_cache_context:
        current_batch_db_object = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user,
                                                                        deleted=False).first()
        if not current_batch_db_object:
            raise errors.BatchNotFound()

        if current_batch_db_object.status == BatchStatusEnum.BS_BEING_FINALISED:
            current_app.logger.debug(u"Updating batch during finalization - cancelling finalization")

            try:
                BatchManager.cancel_batch_finalization(current_batch_db_object,
                                                       current_app.config, current_app.logger)
            except Exception:
                current_app.logger.exception(u"Failed to cancel batch finalisation")
                DocumentBatchDbObject.query.filter_by(id=batch_id, status=BatchStatusEnum.BS_BEING_FINALISED).update(
                    {'status': BatchStatusEnum.BS_EDITED})
                sqldb.session.commit()
                raise errors.DocumentBatchUpdateError()

        manager = BatchManager.init(current_batch_db_object)

        batch_type = current_batch_db_object.batch_type
        batch['batch_type'] = batch_type
        if 'metadata' in batch:
            batch['_metadata'] = batch['metadata']

        new_batch = DocumentBatch.parse_raw_value(batch, api_data=True)

        new_batch_api_data = manager.update_batch(batch_id, new_batch, current_user.id,
                                                  current_app.config, current_app.logger)

        DocumentBatchDbObject.query.filter_by(id=batch_id).update({'last_change_dt': datetime.utcnow()})
        sqldb.session.commit()
        if batch_type == DocumentBatchTypeEnum.DBT_NEW_LLC:
            schedule_notification_email(batch_id)
        return new_batch_api_data


@documents_bp.route('/batch/document/state/', methods=['GET'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator(), document_id=ArgumentValidator())
def get_document_preview_status(batch_id=None, document_id=None):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch:
        raise errors.BatchNotFound()

    doc = BatchDocumentDbObject.query.filter_by(batch=batch, id=document_id).first()
    if not doc:
        raise errors.DocumentNotFound()

    links = {
        'pdf': FileStorage.get_url(doc.file, current_app.config),
        'jpeg': []
    } if doc.file else {
        'pdf': None,
        'jpeg': []
    }

    return {
        'result': {
            'state': doc.status,
            'links': links,
            'document_id': unicode(document_id)
        }
    }


@documents_bp.route('/batch/document/render/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator(), document_id=ArgumentValidator())
def render_document_preview(batch_id=None, document_id=None):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch:
        raise errors.BatchNotFound()

    doc = BatchDocumentDbObject.query.filter_by(batch=batch, id=document_id).scalar()
    if not doc:
        return errors.DocumentNotFound()

    async_result = rendering.render_document_preview.apply_async((document_id,), countdown=2)
    if not async_result.ready():
        task_id = str(async_result.id)
        doc.status = UserDocumentStatus.DS_RENDERING
        doc._celery_task_id = task_id                   # override (capture) document by new task
        doc._celery_task_started = datetime.utcnow()
        current_app.logger.debug(u"Render preview task id: %s" % task_id)
        sqldb.session.commit()
    return {"result": True}


@documents_bp.route('/batch/update_metadata/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator(), batch=JsonValidator())
def batch_update_metadata(batch_id=None, batch=None):
    current_batch_db_object = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user,
                                                                    deleted=False).first()
    if not current_batch_db_object:
        raise errors.BatchNotFound()

    current_batch_db_object._metadata = batch.get('metadata', {})
    sqldb.session.commit()
    current_batch = DocumentBatch.db_obj_to_field(current_batch_db_object)
    return {'result': current_batch.get_api_structure()}


def get_reg_fee_data(path):
    temp_file_out = tempfile.NamedTemporaryFile(mode="w+", suffix=".txt")
    output_file_name = temp_file_out.name
    temp_file_out.close()
    p = subprocess.Popen(['pdftotext', path, output_file_name], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    rc = p.returncode
    if rc is not 0:
        current_app.logger.error(u"Failed to executed pdftotext (%s, %s)" % (out, err))
        return
    if not os.path.exists(output_file_name):
        current_app.logger.error(u"No file were generated")
        return

    with codecs.open(output_file_name, 'r', 'utf-8') as f:
        content = f.read().split(u'линия отрыва')[0].strip().replace('\r', '')
    while '  ' in content:
        content = content.replace('  ', ' ')

    pos = content.rfind(u'Индекс док.')
    if pos == -1:
        return

    part1 = content[:pos]
    part2 = content[pos:]
    doc_index = u""
    applicant = u""
    fio = u""
    address = u""
    inn = u""
    kbk = u""
    f106 = u""
    f107 = u""
    f110 = u""
    cost = u""
    bik = u""
    # account1 = u""
    account2 = u""
    inn_ul = u""
    kpp = u""
    oktmo = u""
    receiver = u""
    receiver_bank = u""

    part1_parts = part1.split('\n\n')
    for part in part1_parts:
        part = part.replace('\n', ' ')
        part = part.strip()
        if not part:
            continue
        #current_app.logger.debug(u"Part: %s" % part)
        match = re.match(u'\(101\)\s*(\d+).*', part)
        if match:
            applicant = match.groups()[0]
            continue
        match = re.match(u'Индекс док\.\s*(\d+).*', part)
        if match:
            doc_index = match.groups()[0]
            continue
        match = re.match(u'ФИО\s*(.*)', part)
        if match:
            fio = match.groups()[0]
            continue
        match = re.match(u'Адрес\s*(.*)', part)
        if match:
            address = match.groups()[0]
            continue
        match = re.match(u'ИНН\s*(\d{12}).*', part)
        if match:
            inn = match.groups()[0]
            continue
        match = re.match(u'КБК\s*(\d+).*', part)
        if match:
            kbk = match.groups()[0]
            continue
        match = re.match(u'.*\(106\)\s*(\w{1,3}).*', part)
        if match:
            f106 = match.groups()[0]

        match = re.match(u'.*\s*\(110\)\s*(\d+).*', part)
        if match:
            f110 = match.groups()[0]

        match = re.match(u'.*Сумма\s*(\d+).*', part)
        if match:
            cost = match.groups()[0]
        match = re.match(u'.*БИК\s*(\d+).*', part)
        if match:
            bik = match.groups()[0]
        match = re.match(u'.*Сч\.. (\d+).*Сч\.. (\d+)\D+.*', part)
        if match:
            account1 = match.groups()[0]
            account2 = match.groups()[1]
        match = re.match(u'.*ИНН\s*(\d{10}).*', part)
        if match:
            inn_ul = match.groups()[0]
        match = re.match(u'.*КПП\s*(\d{9}).*', part)
        if match:
            kpp = match.groups()[0]
        match = re.match(u'.*ОКТМО\s*(\d{7,10}).*', part)
        if match:
            oktmo = match.groups()[0]
        match = re.match(u'.*\(107\)\s*(\d{1,2}\.\d{1,2}\.\d{4}).*', part)
        if match:
            f107 = match.groups()[0]

        match = re.match(u'.*ОКТМО\s*(\d{7,10}).*', part)
        if match:
            oktmo = match.groups()[0]
            continue

        match = re.match(u'Банк получателя\s*(.*)\s*Получатель\s*(.*)', part)
        if match:
            receiver_bank = match.groups()[0]
            receiver = match.groups()[0]

    part2_parts = part2.split('\n\n')
    for part in part2_parts:
        part = part.replace('\n', ' ')
        part = part.strip()
        if not part:
            continue
        #current_app.logger.debug(u"Part[2]: %s" % part)
        match = re.match(u'КБК\s*(\d+).*', part)
        if match:
            kbk = match.groups()[0]
            continue
        match = re.match(u'.*\(106\)\s*([АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЪЭЮЯ]{1,3}).*', part)
        if match:
            f106 = match.groups()[0]
            continue

        match = re.match(u'.*\s*\(110\)\s*(\d+).*', part)
        if match:
            f110 = match.groups()[0]

        match = re.match(u'.*Банк получателя\s*(.*)\s*Получатель\s*(.*)', part)
        if match:
            receiver_bank = match.groups()[0]
            receiver = match.groups()[0]

    try:
        os.unlink(output_file_name)
    except Exception:
        current_app.logger.warn(u"Failed to remove file %s" % output_file_name)

    return {
        u"Индекс документа": doc_index,
        u"Платильщик": {
            u"ФИО": fio,
            u"Адрес": address,
            u"ИНН": inn
        },
        u"Получатель": {
            u"Банк получателя": receiver_bank,
            u"Получатель": receiver,
            u"БИК": bik,
            u"Сч.№": account2,
            u"ИНН": inn_ul,
            u"КПП": kpp
        },
        u"Параметры платежа": {
            u"Сумма": cost,
            u"ОКТМО": oktmo,
            u"КБК": kbk,
            u"(101) Статус": applicant,
            u"(107) Налоговый период": f107,
            u"(106) Основание платежа": f106,
            u"(110) Тип платежа": f110
        }
    }


@documents_bp.route('/batch/invoice_data/', methods=['GET'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator())
def get_batch_reg_fee_invoice_data(batch_id=None):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).scalar()
    if not batch:
        raise errors.BatchNotFound()

    if batch.status != BatchStatusEnum.BS_FINALISED:
        return {"result": None, "message": "document batch is not finalized"}

    for doc in batch._documents:
        if doc.document_type in (DocumentTypeEnum.DT_REGISTRATION_FEE_INVOICE,
                                 DocumentTypeEnum.DT_IP_STATE_DUTY) and doc.status==UserDocumentStatus.DS_RENDERED:
            file_obj = doc.file
            if not file_obj:
                return {"result": None, "message": "failed to find file object for document with id %s" % doc.id}
            path = FileStorage.get_path(file_obj, current_app.config)
            if not path or not os.path.exists(path):
                return {"result": None, "message": "file %s not found" % path}
            res = get_reg_fee_data(path)
            if not res:
                return {"result": None, "message": "Failed to get reg fee data"}
            return {"result": res}

    return {"result": None, "message": "rendered document not found"}


@documents_bp.route('/batch/render_document/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator(), document_type=ArgumentValidator())
def render_batch_documents(batch_id=None, document_type=None):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch:
        raise errors.BatchNotFound()
    batch_manager = BatchManager.init(batch)

    document_types = json.loads(document_type)
    if not isinstance(document_types, list) and not isinstance(document_types, tuple):
        raise errors.InvalidParameterValue('document_type')

    doc_type_set = set()
    for doc_type in document_types:
        if not batch_manager.check_doc_type_support(batch.batch_type, doc_type):
            raise errors.InvalidParameterValue('document_type')
        doc_type_set.add(doc_type)

    action_descriptor = {
        'plugin': 'doc_builder',
        'action': 'render_group'
    }

    event_data = {
        'doc_types': list(doc_type_set),
        'batch_id': batch.id
    }

    BatchManager.perform_action(action_descriptor, batch, event_data, current_app.logger, current_app.config)
    return {"result": True}


@documents_bp.route('/batch/render_document/state/', methods=['GET'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator(), document_types=ArgumentValidator())
def get_render_batch_documents_state(batch_id=None, document_types=None):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch:
        raise errors.BatchNotFound()

    batch_manager = BatchManager.init(batch)
    try:
        document_types = json.loads(document_types)
        if not isinstance(document_types, list) and not isinstance(document_types, tuple):
            raise Exception()
    except Exception:
        raise errors.InvalidParameterValue('document_type')

    doc_type_set = set()
    for doc_type in document_types:
        if not batch_manager.check_doc_type_support(batch.batch_type, doc_type):
            raise errors.InvalidParameterValue('document_type')
        doc_type_set.add(doc_type)

    result = []

    for doc_type in doc_type_set:
        doc_obj = BatchDocumentDbObject.query.filter_by(batch_id=batch_id, document_type=doc_type).first()
        if not doc_obj:
            result.append({
                'state': UserDocumentStatus.DS_NEW,
                'document_type': doc_type
            })
            continue

        doc_info = {
            'state': doc_obj.status,
            'document_type': doc_type
        }

        if doc_obj.status == UserDocumentStatus.DS_RENDERED:
            if doc_obj.file:
                doc_info['links'] = {
                    'pdf': FileStorage.get_url(doc_obj.file, current_app.config),
                    'jpeg': []
                }
                result.append(doc_info)
            else:
                current_app.logger.debug(u"Not found rendered documents for rendered document %s. "
                                         u"Returning as rendering_failed" % doc_type)
                result.append({
                    'state': UserDocumentStatus.DS_RENDERING_FAILED,
                    'document_type': doc_type
                })
        else:
            result.append(doc_info)

    return result


@documents_bp.route('/batch/go_ahead/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator())
def go_ahead(batch_id=None):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch:
        raise errors.BatchNotFound()
    if batch.batch_type != DocumentBatchTypeEnum.DBT_NEW_LLC:
        BatchManager.handle_event(batch_id, 'go_ahead', {
            'batch_id': batch_id
        }, logger=current_app.logger, config=current_app.config)
        return {"result": True}
    return _finalize_batch(batch)


@documents_bp.route('/batch/go_back/', methods=['POST'])
@api_view
@login_required
@validate_arguments(batch_id=ArgumentValidator())
def go_back(batch_id=None):
    batch = DocumentBatchDbObject.query.filter_by(id=batch_id, _owner=current_user, deleted=False).first()
    if not batch:
        raise errors.BatchNotFound()
    if batch.batch_type != DocumentBatchTypeEnum.DBT_NEW_LLC:
        BatchManager.handle_event(batch_id, 'go_back', {
            'batch_id': batch_id
        }, logger=current_app.logger, config=current_app.config)
        return {"result": True}
    raise NotImplementedError()

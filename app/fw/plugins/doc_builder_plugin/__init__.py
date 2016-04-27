# -*- coding: utf-8 -*-
from copy import copy
from datetime import datetime
from flask import current_app
from flask_login import current_user
from fw.async_tasks import rendering
from fw.db.sql_base import db as sqldb
from fw.documents.batch_manager import BatchManager
from fw.documents.db_fields import DocGroupRenderTaskCheck, BatchDocumentDbObject
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import UserDocumentStatus
from fw.documents.schema.schema_transform import transform_with_schema
from fw.monitoring_utils import zabbix_sender
from fw.storage.file_storage import FileStorage

PLUGIN_NAME = 'doc_builder'


def get_actions():
    actions = [{
        'name': 'render_group',
        'async': True,
        'args': [
        {
            'name': 'doc_types',
            'type': 'DocArrayField',
            'cls': 'DocTextField',
            'required': True
        }, {
            'name': 'batch_id',
            'type': 'DocTextField',
            'required': True
        }]
    }, {
        'name': 'render_doc',
        'async': True,
        'args': [
        {
            'name': 'batch_id',
            'type': 'DocTextField',
            'required': True
        }, {
            'name': 'doc_type',
            'type': 'DocTextField',
            'required': True
        }]
    }, {
        'name': 'render_doc_by_id',
        'async': True,
        'args': [
        {
            'name': 'doc_id',
            'type': 'DocTextField',
            'required': True
        }]
    }, {
        'name': 'cancel_doc_render',
        'async': False,
        'args': [
        {
            'name': 'batch_id',
            'type': 'DocTextField',
            'required': True
        }, {
            'name': 'doc_type',
            'type': 'DocTextField',
            'required': True
        }]
    }, {
        'name': 'cancel_doc_render_by_id',
        'async': False,
        'args': [
        {
            'name': 'doc_id',
            'type': 'DocTextField',
            'required': True
        }]
    }]
    return actions

def get_events():
    events = [{
        'name': 'doc_render_success'
    }, {
        'name': 'doc_render_fail'
    }, {
        'name': 'doc_group_render_success'
    }, {
        'name': 'doc_group_render_fail'
    }, {
        'name': 'doc_group_render_canceled'
    }, {
        'name': 'doc_render_canceled'
    }]
    return events

def act(action, batch_db, event_data, plugin_config, logger, config):
    assert batch_db
    descriptors = filter(lambda x: x['name'] == action, get_actions())
    action_descriptor = descriptors[0] if descriptors else None
    if not action_descriptor:
        raise ValueError(u'Invalid action: %s for %s plugin' % (action, PLUGIN_NAME))
    args = action_descriptor['args']
    source_data = copy(event_data)
    data = transform_with_schema(source_data, {"fields": args})

    batch_manager = BatchManager.init(batch_db)

    if action == 'render_group':
        doc_id_list = []
        batch_id = data['batch_id'].db_value()
        doc_types = event_data['doc_types'] if 'doc_types' in event_data else plugin_config.get('doc_types', [])
        assert doc_types

        try:
            all_ready = True
            for doc_type in doc_types:
                doc = BatchDocumentDbObject.query.filter_by(document_type=doc_type, batch_id=batch_id).first()
                if doc:
                    doc.data = {}
                    doc.status = UserDocumentStatus.DS_RENDERING
                    doc.tried_to_render = True
                    if doc.file:
                        file_obj = doc.file
                        doc.file = None
                        FileStorage.remove_file(file_obj.id, current_app.config)
                    sqldb.session.commit()

                else:
                    if not batch_manager.is_document_required(batch_db, doc_type):
                        logger.debug(u"Document %s is not required by its condition. Skipping" % doc_type)
                        continue

                    new_doc = BatchDocumentDbObject(
                        _owner=current_user,
                        document_type=doc_type,
                        batch_id=batch_id,
                        data={},
                        status=UserDocumentStatus.DS_RENDERING,
                        caption=batch_manager.get_title(doc_type),
                        tried_to_render=True
                    )
                    sqldb.session.add(new_doc)
                    sqldb.session.commit()
                    doc = new_doc

                async_result = rendering.render_document_plugin.apply_async((batch_id, {'doc_id': doc.id}), countdown=2)
                if not async_result.ready():
                    all_ready = False
                    BatchDocumentDbObject.query.filter_by(id=doc.id).update({
                        '_celery_task_id': str(async_result.id),
                        '_celery_task_started': datetime.utcnow()
                    })
                    sqldb.session.commit()

                doc_id_list.append(doc.id)

            check_task_info = DocGroupRenderTaskCheck(
                batch_id=batch_id,
                doc_id_list=doc_id_list,
                event_data=event_data
            )
            sqldb.session.add(check_task_info)
            sqldb.session.commit()
            if all_ready:
                rendering.batch_group_gen_check_task.delay()
        except Exception:
            zabbix_sender.send("celery_failures", 1)
            logger.exception(u"Failed to start rendering document group")
            raise
    elif action == 'render_doc':
        pass
    elif action == 'render_doc_by_id':
        pass
    elif action == 'cancel_doc_render':
        pass
    elif action == 'cancel_doc_render_by_id':
        pass
    else:
        raise Exception(u"Invalid action %s for plugin %s" % (action, PLUGIN_NAME))

    # mail_type = data['mail_type'].db_value()
    # target_type = data['target_type'].db_value()
    # target_emails = []
    # if target_type == MailTargetEnum.MTA_BATCH_OWNER:
    #     email = batch_db._owner.email
    #     if email:
    #         target_emails.append(email)
    # elif target_type == MailTargetEnum.MTA_SPECIFIED:
    #     target_emails = data.get('target_email_list', [])
    # else:   #MailTargetEnum.MTA_EVENT_DATA_FIELD
    #     data_field = data.get('event_data_field', None)
    #     if data_field:
    #         email = event_data.get(data_field, None)
    #         if email:
    #             target_emails.append(email)
    #
    # if not target_emails:
    #     core_tasks.send.delay(batch_db.id, '%s:send_fail' % PLUGIN_NAME, event_data)
    #     return False
    #
    # composer = create_composer(mail_type, logger)
    # retry_count = data.get('retry_count')
    # silent = data.get('silent', False)
    # from fw.documents.fields.simple_doc_fields import DocField
    # try:
    #     if isinstance(target_emails, DocField):
    #         target_emails = target_emails.db_value()
    #     if isinstance(retry_count, DocField):
    #         retry_count = retry_count.db_value()
    #     if isinstance(silent, DocField):
    #         silent = silent.db_value()
    #     composer.send_email(target_emails, batch_id, event_data, retry_count, silent=silent)
    # except Exception:
    #     logger.exception(u"Failed to send email")
    #     return False
    return True

def register(class_loader):
    #class_loader.POSSIBLE_LOCATIONS.append('fw.plugins.emailer_plugin.enums')
    pass

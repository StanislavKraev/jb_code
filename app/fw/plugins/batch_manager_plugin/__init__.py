# -*- coding: utf-8 -*-
from copy import copy
from fw.async_tasks import rendering
from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject, DocumentFilesObject
from fw.documents.enums import UserDocumentStatus
from fw.documents.schema.schema_transform import transform_field_with_schema

PLUGIN_NAME = 'batch_manager'


def get_actions():
    actions = [{
        'name': 'set_result_fields',
        'async': False
    }, {
        'name': 'reset_result_fields',
        'async': False
    }, {
        'name': 'remove_documents',
        'async': False
    }, {
        'name': 'set_batch_fields',
        'async': False
    }, {
        'name': 'touch',
        'async': True
    }, {
        'name': 'check_and_fix_osago_payments',
        'async': False
    }]
    return actions

def get_events():
    events = [{
        'name': 'on_field_changed'
    }, {
        'name': 'on_fieldset_changed'
    }]
    return events

def _apply_dict_patch(original, patch):
    for k, v in patch.items():
        if isinstance(v, dict) and k in original and isinstance(original[k], dict):
            original[k] = _apply_dict_patch(original[k], v)
        else:
            original[k] = v
    return original

def _make_result_fields_patch(data, field_name_map):
    patch = {}
    for src, dst in field_name_map.items():
        if '.' in src:
            raise NotImplementedError()
        if src in data:
            patch[dst] = data[src]
    return patch

def act(action, batch_db, event_data, plugin_config, logger, config):
    assert batch_db
    descriptors = filter(lambda x: x['name'] == action, get_actions())
    action_descriptor = descriptors[0] if descriptors else None
    if not action_descriptor:
        raise ValueError(u'Invalid action: %s for %s plugin' % (action, PLUGIN_NAME))

    if action == 'set_result_fields':
        data = copy(event_data)
        if not data:
            logger.warn(u"Empty data in set_result_fields event")
            return True
        field_name_map = plugin_config['field_name_map']
        result_fields_patch = _make_result_fields_patch(data, field_name_map)
        fields = copy(batch_db.result_fields or {})
        batch_db.result_fields = _apply_dict_patch(fields, result_fields_patch)
        sqldb.session.commit()
    elif action == 'reset_result_fields':
        keys = plugin_config['fields']
        if not keys:
            return True
        fields = copy(batch_db.result_fields or {})
        for key in keys:
            if key in fields:
                del fields[key]
        batch_db.result_fields = fields
        sqldb.session.commit()
    elif action == 'remove_documents':
        query = BatchDocumentDbObject.query.filter_by(batch=batch_db)
        if plugin_config and 'doc_types' in plugin_config and isinstance(plugin_config['doc_types'], list):
            query = query.filter(BatchDocumentDbObject.document_type.in_(plugin_config['doc_types']))
        for i in query:
            DocumentFilesObject.query.filter_by(doc_id=i.id).delete()
            BatchDocumentDbObject.query.filter_by(id=i.id).update({
                'status': UserDocumentStatus.DS_NEW,
                '_celery_task_id': None,
                '_celery_task_started': None
            })
            sqldb.session.commit()
    elif action == 'set_batch_fields':
        fields = plugin_config['fields']
        update_dict = {}
        source_data = copy(plugin_config)
        source_data['<batch>'] = batch_db
        source_data['<app_config>'] = config
        source_data['<current_user>'] = batch_db._owner
        source_data['<previous_event_data>'] = event_data
        for field_name, field_descr in fields.items():
            if isinstance(field_descr, dict):
                field_val = transform_field_with_schema(source_data, field_descr).db_value()
            else:
                field_val = field_descr
            update_dict[field_name] = field_val
        DocumentBatchDbObject.query.filter_by(id=batch_db.id).update(update_dict)
        sqldb.session.commit()
    elif action == 'touch':
        rendering.touch_batch_plugin.delay(batch_db.id, {})
    elif action == 'check_and_fix_osago_payments':
        from services.osago.osago_manager import OsagoBatchManager
        OsagoBatchManager.check_and_fix_osago_payments(batch_db)
    else:
        raise Exception(u"Invalid action %s for plugin %s" % (action, PLUGIN_NAME))

    return True

def register(class_loader):
    pass

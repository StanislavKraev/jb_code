# -*- coding: utf-8 -*-
from copy import copy
from datetime import datetime

from fw.async_tasks.scheduler import CeleryScheduler
from fw.documents.address_enums import RFRegionsEnum
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.schema.schema_transform import transform_field_with_schema
from fw.utils.time_utils import calc_fixed_time_not_earlier

PLUGIN_NAME = 'task_scheduler'


def get_events():
    events = [{
        'name': 'schedule'
    }]
    return events

def act(action, batch_db, previous_event_data, plugin_config, logger, config):
    assert batch_db
    if action != 'schedule':
        logger.error(u"Invalid action %s for task_scheduler plugin" % action)
        return False

    descriptor_name, task_to_schedule = plugin_config['action'].split('.')
    descriptor = DocRequisitiesStorage.get_batch_descriptor(descriptor_name)
    assert descriptor
    batch_actions = descriptor.get('actions') or {}
    if task_to_schedule not in batch_actions:
        logger.error(u"Invalid task name %s for task_scheduler plugin" % task_to_schedule)
        return False

    source_data = copy(plugin_config)
    source_data['<batch>'] = batch_db
    source_data['<app_config>'] = config
    source_data['<current_user>'] = batch_db._owner
    source_data['<previous_event_data>'] = previous_event_data

    task_id = plugin_config.get('task_id', None)

    if task_id and isinstance(task_id, dict):
        task_id = transform_field_with_schema(source_data, task_id).db_value()

    dt_type = plugin_config['dt_type']

    event_data = {
        'task_to_schedule': task_to_schedule,
        'dt_type': dt_type,
        '<action_dt>': datetime.utcnow(),
    }

    if dt_type == 'exact_time_every_day':
        dt_format = plugin_config['dt_format']
        dt_exact_time = plugin_config['dt_exact_time']
        dt_time_zone_region = plugin_config.get('dt_time_zone_region', u'Москва')
        dt_not_earlier = plugin_config.get('dt_not_earlier', None)

        if dt_format and isinstance(dt_format, dict):
            dt_format = transform_field_with_schema(source_data, dt_format).db_value()
        if dt_exact_time and isinstance(dt_exact_time, dict):
            dt_exact_time = transform_field_with_schema(source_data, dt_exact_time).db_value()
        if dt_time_zone_region and isinstance(dt_time_zone_region, dict):
            dt_time_zone_region = transform_field_with_schema(source_data, dt_time_zone_region)
            if dt_time_zone_region:
                dt_time_zone_region = dt_time_zone_region.db_value()
        if dt_not_earlier and isinstance(dt_not_earlier, dict):
            dt_not_earlier = transform_field_with_schema(source_data, dt_not_earlier).db_value()

        tz_name = RFRegionsEnum.get_time_zone(dt_time_zone_region) or "Europe/Moscow"
        now = datetime.utcnow()
        dt = calc_fixed_time_not_earlier(now, dt_exact_time, dt_not_earlier - now, tz_name)

        event_data.update({
            'dt': dt,
            'dt_format': dt_format,
            'dt_time_zone_region': dt_time_zone_region,
            'dt_not_earlier': dt_not_earlier,
            'tz_name': tz_name
        })
    else:
        raise NotImplementedError()

    try:
        new_task = CeleryScheduler.post('fw.async_tasks.scheduler.run_scheduled_task', eta=dt, args=(descriptor_name, task_to_schedule, batch_db.id),
                                        task_id=task_id, force_replace_task=True)
        event_data['task_id'] = new_task.id
    except Exception:
        logger.exception(u"Failed to schedule task")
        return False
    return True

def register(class_loader):
    pass

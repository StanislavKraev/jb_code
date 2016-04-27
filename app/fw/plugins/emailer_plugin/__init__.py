# -*- coding: utf-8 -*-
from copy import copy
from datetime import datetime
from fw.async_tasks import core_tasks
from fw.documents.schema.schema_transform import transform_field_with_schema
from fw.plugins.emailer_plugin.enums import MailTargetEnum
from fw.plugins.emailer_plugin.mail_composer import create_composer

PLUGIN_NAME = 'emailer'


def get_events():
    events = [{
        'name': 'mail_sent'
    }, {
        'name': 'send_failed'         # after the last try
    }]
    return events

def act(action, batch_db, previous_event_data, plugin_config, logger, config):
    assert batch_db
    if action != 'send_email':
        logger.error(u"Invalid action %s for emailer plugin" % action)
        return False

    max_retries = plugin_config.get('max_retries', 0)
    retry_timeout_seconds = plugin_config.get('retry_timeout_seconds', 10)
    silent = plugin_config.get('silent', False)
    mail_type = plugin_config.get('mail_type')
    assert mail_type

    recipients = plugin_config.get('recipients', [])

    source_data = copy(plugin_config)
    source_data['<batch>'] = batch_db
    source_data['<app_config>'] = config
    source_data['<current_user>'] = batch_db._owner
    source_data['<previous_event_data>'] = previous_event_data
    if isinstance(recipients, dict):
        recipients = transform_field_with_schema(source_data, recipients).db_value()

    event_data = {
        'recipients': recipients,
        'max_retries': max_retries,
        'retry_timeout_seconds': retry_timeout_seconds,
        'silent': silent,
        'mail_type': mail_type,
        '<action_dt>': datetime.utcnow(),
    }

    if not recipients:
        core_tasks.send.delay(batch_db.id, '%s:send_fail' % PLUGIN_NAME, event_data)
        return False

    template_data = {}
    data_fields = plugin_config.get('data', {})
    for d, dv in data_fields.items():
        template_data[d] = transform_field_with_schema(source_data, dv)

    template_data_raw = {}
    for k, v in template_data.items():
        if v is not None:
            template_data_raw[k] = v.db_value()
    event_data['template_data'] = template_data_raw

    composer = create_composer(mail_type, logger)
    try:
        composer.send_email(recipients, batch_db.id, event_data, max_retries,
                            retry_timeout_seconds=retry_timeout_seconds, silent=silent,
                            template_data=template_data_raw)
    except Exception:
        logger.exception(u"Failed to send email")
        return False
    return True

def register(class_loader):
    class_loader.POSSIBLE_LOCATIONS.append('fw.plugins.emailer_plugin.enums')

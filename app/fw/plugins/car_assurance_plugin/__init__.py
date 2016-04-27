# -*- coding: utf-8 -*-
from fw.documents.batch_manager import BatchManager
from services.car_assurance.async_tasks import get_policy_info_async

PLUGIN_NAME = 'car_assurance'


def get_actions():
    actions = [{
        'name': 'get_policy_info_async',
        'async': True
        # args: policy series, policy number
    }, {
        'name': 'get_policy_info_first_try',
        'async': False
        # args: policy series, policy number
    }]
    return actions

def get_events():
    events = [{
        'name': 'on_policy_info_received'
    }, {
        'name': 'on_policy_info_receive_fail'
    }, {
        'name': 'on_policy_info_receive_timeout'
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
    return patch

def act(action, batch_db, event_data, plugin_config, logger, config):
    assert batch_db
    descriptors = filter(lambda x: x['name'] == action, get_actions())
    action_descriptor = descriptors[0] if descriptors else None
    if not action_descriptor:
        raise ValueError(u'Invalid action: %s for %s plugin' % (action, PLUGIN_NAME))

    if action == 'get_policy_info_async':
        policy_series_field_name = plugin_config['policy_series_field_name']
        policy_number_field_name = plugin_config['policy_number_field_name']

        policy_series = batch_db.data.get(policy_series_field_name, None)
        policy_number = batch_db.data.get(policy_number_field_name, None)

        if not policy_number or not policy_series:
            return False
        get_policy_info_async.delay(policy_series, policy_number, event_data, batch_db.id)
    elif action == 'get_policy_info_first_try':
        policy_series_field_name = plugin_config['policy_series_field_name']
        policy_number_field_name = plugin_config['policy_number_field_name']

        policy_series = batch_db.data.get(policy_series_field_name, None)
        policy_number = batch_db.data.get(policy_number_field_name, None)

        if not policy_number or not policy_series:
            return False
        try:
            get_policy_info_async(policy_series, policy_number, event_data, batch_db.id, async=False, logger=logger)
        except Exception:
            BatchManager.handle_event(batch_db.id, "on_policy_info_receive_fail", event_data, logger, config=config)
            return False
    else:
        raise Exception(u"Invalid action %s for plugin %s" % (action, PLUGIN_NAME))

    return True

def register(class_loader):
    pass

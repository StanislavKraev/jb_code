# -*- coding: utf-8 -*-
import copy
import os

from fw.documents.enums import DocumentTypeEnum, BatchStatusEnum, DocumentBatchTypeEnum, DocumentKindEnum
from fw.documents.field_matchers import SimpleMatcher
from fw.documents.common_schema_fields import SHORT_NAME_FIELD, GENERAL_MANAGER_FIELD


def get_test_resource_name(config, resource_rel_path):
    resources_path = config['resources_path']
    return os.path.join(resources_path, resource_rel_path)

SHORT_NAME_FIELD = copy.copy(SHORT_NAME_FIELD)
SHORT_NAME_FIELD["max_length"] = 40

GENERAL_MANAGER_FIELD_NA = copy.copy(GENERAL_MANAGER_FIELD)
GENERAL_MANAGER_FIELD_NA['required'] = False

SOME_DB_OBJECT = {
    "name": "some_db_object",
    "type": "db_object",
    "required": False
}


def load_data(config):
    TEST_BATCH_SCHEMA = {
        "doc_name": DocumentBatchTypeEnum.DBT_TEST_TYPE,
        "fields": [
            SHORT_NAME_FIELD,
            GENERAL_MANAGER_FIELD_NA,
            SOME_DB_OBJECT,
            {
                "name": "text_field",
                "type": "DocTextField",
                "max_length": 20,
                "min_length": 5,
                "required": False
            },
            {
                "name": "some_text_field",
                "type": "DocTextField",
                "max_length": 20,
                "min_length": 5,
                "required": False
            },
            {
                "name": "restricted_field",
                "type": "DocTextField",
                "modification_condition": {
                    '<batch>->status': 'new'
                },
                "required": False
            }
        ]
    }

    TEST_DOC_1_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_TEST_DOC_1,
        "file_name_template": u"Тестовый документ 1",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "fields": [
            SHORT_NAME_FIELD,
            {
                "name": "some_text_field",
                "type": "DocTextField",
                "max_length": 20,
                "min_length": 5,
                "required": False
            }
        ]
    }

    TEST_DOC_1_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_TEST_DOC_1,
        "template_name": "test_doc_1_template",
        "is_strict": True,
        "pages": [{
            "page_file": [get_test_resource_name(config, "test/test.pdf")],
            "fields": [
                {
                    "name": "field1",
                    "field-length": 10
                }
            ]
        }]
    }

    TEST_DOC_1_MATCHER = {
        "doc_name": DocumentTypeEnum.DT_TEST_DOC_1,
        "template_name": TEST_DOC_1_TEMPLATE['template_name'],
        "fields": {
            "field1": SimpleMatcher(field_name="short_name")
        }
    }

    TEST_DOC_2_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_TEST_DOC_2,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Тестовый документ 2",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "short_name": u"создай второй документ"
        },
        "error_filter": {
            "<document>->tried_to_render": True
        },
        "fields": [
            SHORT_NAME_FIELD,
            {
                "name": "text_field",
                "type": "DocTextField",
                "max_length": 20,
                "min_length": 5,
                "required": False
            }
        ]
    }

    TEST_DOC_2_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_TEST_DOC_2,
        "template_name": "some_doc",
        "file_name": get_test_resource_name(config, "test/test.tex"),
        "is_strict": False
    }

    TEST_DOC_3_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_TEST_DOC_3,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Тестовый документ 3",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "general_manager" : {
                "#not_empty": True
            }
        },
        "validators": [{
            "condition": {
                'general_manager->sex': 'male'
            },
            "error": {
                "field": "test_doc_validation",
                "code": 5
            }
        }],
        "fields": [
            GENERAL_MANAGER_FIELD_NA,
            SOME_DB_OBJECT,
            {
                "name": "ugly_field",
                "type": "calculated",
                "field_type": "DocIntField",
                "required": False,
                "value": {
                    "#div": [{
                        "#field": "general_manager->living_country_code"
                    }, {
                        "#field": "general_manager->living_country_code"
                    }]
                }
            }
        ]
    }

    TEST_DOC_3_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_TEST_DOC_3,
        "template_name": "some_doc",
        "file_name": get_test_resource_name(config, "test/test.tex"),
        "is_strict": False
    }

    TEST_BATCH_RESULT_FIELDS = [{
        "name": "name",
        "type": "calculated",
        "field_type": "DocTextField",
        "required": False,
        "value": {
            "#field": "short_name"
        }
    }]

    TEST_BATCH_DEFER_DOCS = [DocumentTypeEnum.DT_TEST_DOC_2]

    TEST_BATCH_ACTIONS = {                                  # id: action
        'action1': {
            'plugin': 'emailer',
            'action': 'send_email',
            'config': {
                'mail_type': 'simple_mail',
                'target_type': 'batch_owner',
                'retry_count': 3
            }
        },
        'fail_mail_action': {
            'plugin': 'emailer',
            'action': 'send_email',
            'config': {
                'mail_type': 'simple_mail',
                'target_type': 'specified_users',
                'target_email_list': ['admin@domzin.zz'],
                'silent': True                              # do not send any events after email send /send failure
            }                                               # to beat infinite cycle
        }
    }

    TEST_BATCH_TRANSITIONS = [{
        "status": "finalised",
        "condition": {
            "<batch>->status": "new",
            "short_name": u"финализируйся"
        }
    }, {
        "status": "edited",
        "condition": {
            "short_name": u"едитыд"
        }
    }, {
        "status": "after_event",
        "condition": {
            "<batch>->status": "new",
            "<event>": "go_ahead",
            "short_name": u"по событию"
        }
    }, {
        "status": "after_simple_event",
        "condition": {
            "<event>": "simple_event"
        },
        "actions": ["action1"]
    }, {
        "condition": {
            "<event>": "emailer.send_fail"
        },
        "actions": ["fail_mail_action"]
    }, {
        "status": "finalised",
        "condition": {
            "<batch>->status": {
                "#in": ["new", "finalised1"]
            },
            "<event>": "doc_group_render_success"
        }
    }, {
        "status": "edited",
        "condition": {
            "<batch>->status": "new",
            "<event>": "doc_group_render_fail"
        }
    }, {
        "status": "finalised1",
        "condition": {
            "<batch>->status": "new",
            "<event>": "doc_render_success"
        }
    }, {
        "status": "finalised2",
        "condition": {
            "<batch>->status": "new",
            "<event>": "doc_render_fail"
        }
    }]

    return {
        "TEST_BATCH_SCHEMA": TEST_BATCH_SCHEMA,
        "TEST_DOC_1_SCHEMA": TEST_DOC_1_SCHEMA,
        "TEST_DOC_1_TEMPLATE": TEST_DOC_1_TEMPLATE,
        "TEST_DOC_1_MATCHER": TEST_DOC_1_MATCHER,
        "TEST_DOC_2_SCHEMA": TEST_DOC_2_SCHEMA,
        "TEST_DOC_2_TEMPLATE": TEST_DOC_2_TEMPLATE,
        "TEST_DOC_3_SCHEMA": TEST_DOC_3_SCHEMA,
        "TEST_DOC_3_TEMPLATE": TEST_DOC_3_TEMPLATE,
        "TEST_BATCH_RESULT_FIELDS": TEST_BATCH_RESULT_FIELDS,
        "TEST_BATCH_DEFER_DOCS": TEST_BATCH_DEFER_DOCS,
        "TEST_BATCH_TRANSITIONS": TEST_BATCH_TRANSITIONS,
        "TEST_BATCH_ACTIONS": TEST_BATCH_ACTIONS
    }

# -*- coding: utf-8 -*-

import os
import jinja2
from fw.documents.batch_manager import BatchManager
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentBatchTypeEnum, DocumentTypeEnum
from services.test_svc.test_svc_manager import TestSvcManager


def _init_doc_requisities(config):
    from services.test_svc.documents.db_data import load_data
    data = load_data(config)

    templates = (
        "TEST_DOC_1_TEMPLATE",
        "TEST_DOC_2_TEMPLATE",
        "TEST_DOC_3_TEMPLATE",
    )

    for template_name in templates:
        DocRequisitiesStorage.add_template(data[template_name]['doc_name'], data[template_name])

    schemas = (
        "TEST_BATCH_SCHEMA",
        "TEST_DOC_3_SCHEMA",
        "TEST_DOC_2_SCHEMA",
        "TEST_DOC_1_SCHEMA"
    )

    for schema_name in schemas:
        DocRequisitiesStorage.add_schema(data[schema_name]['doc_name'], data[schema_name])

    matchers = (
        "TEST_DOC_1_MATCHER",
    )

    for matcher_name in matchers:
        DocRequisitiesStorage.add_field_matcher(data[matcher_name]['doc_name'], data[matcher_name])

    bd = dict(
        batch_type=DocumentBatchTypeEnum.DBT_TEST_TYPE,
        doc_types=[
            DocumentTypeEnum.DT_TEST_DOC_1,
            DocumentTypeEnum.DT_TEST_DOC_2,
            DocumentTypeEnum.DT_TEST_DOC_3
        ],
        result_fields=data['TEST_BATCH_RESULT_FIELDS'],
        deferred_render_docs=data['TEST_BATCH_DEFER_DOCS'],
        transitions=data['TEST_BATCH_TRANSITIONS'],
        actions=data['TEST_BATCH_ACTIONS'],
        initial_status="new",
        statuses=["new", "finalisation", "finalised", "edited"],
        fields=data["TEST_BATCH_SCHEMA"]['fields']
    )

    DocRequisitiesStorage.add_batch_descriptor(DocumentBatchTypeEnum.DBT_TEST_TYPE, bd)


def register(app, jinja_env, class_loader, **kwargs):
    search_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), u"templates"))
    jinja_env.loader.loaders.append(jinja2.FileSystemLoader(search_path))

    class_loader.POSSIBLE_LOCATIONS.append('services.test_svc.documents.enums')
    class_loader.POSSIBLE_LOCATIONS.append('services.test_svc.documents.ext_methods')
    class_loader.POSSIBLE_LOCATIONS.append('services.test_svc.documents.ext_validators')

    BatchManager.register_manager(DocumentBatchTypeEnum.DBT_TEST_TYPE, TestSvcManager)

    _init_doc_requisities(app.config)

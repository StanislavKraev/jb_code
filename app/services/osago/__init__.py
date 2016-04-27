# -*- coding: utf-8 -*-

import os
import jinja2
from fw.documents.batch_manager import BatchManager
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentBatchTypeEnum, DocumentTypeEnum
from services.osago.osago_manager import OsagoBatchManager


def _init_doc_requisities(config):
    from services.osago.documents.initial_db_data import load_data
    data = load_data(config)

    templates = (
        "OSAGO_MAIL_LIST_TEMPLATE",
        "OSAGO_PRETENSION_TEMPLATE",
        "OSAGO_DOCUMENTS_CLAIM_TEMPLATE",
        "OSAGO_TRUST_SUBMISSION_DOCS_TEMPLATE",
        "OSAGO_TRUST_OBTAIN_DOCS_TEMPLATE",
        "OSAGO_TRUST_SUBMISION_OBTAIN_DOCS_TEMPLATE",
        "OSAGO_CLAIM_COURT_ABSENT_TEMPLATE",
        "OSAGO_CLAIM_ALL_EXECUTION_ACT_TEMPLATE",
        "OSAGO_CLAIM_GUILTY_EXECUTION_ACT_TEMPLATE",
        "OSAGO_CLAIM_INSURANCE_EXECUTION_ACT_TEMPLATE",
        "OSAGO_LAWSUIT_TEMPLATE",
        "OSAGO_OSAGO_COURT_MAIL_LIST_TEMPLATE"
    )

    for template_name in templates:
        DocRequisitiesStorage.add_template(data[template_name]['doc_name'], data[template_name])

    schemas = (
        "OSAGO_SCHEMA",
        "OSAGO_MAIL_LIST_SCHEMA",
        "OSAGO_PRETENSION_SCHEMA",
        "OSAGO_DOCUMENTS_CLAIM_SCHEMA",
        "OSAGO_TRUST_SUBMISSION_DOCS_SCHEMA",
        "OSAGO_TRUST_OBTAIN_DOCS_SCHEMA",
        "OSAGO_TRUST_SUBMISION_OBTAIN_DOCS_SCHEMA",
        "OSAGO_CLAIM_COURT_ABSENT_SCHEMA",
        "OSAGO_CLAIM_ALL_EXECUTION_ACT_SCHEMA",
        "OSAGO_CLAIM_GUILTY_EXECUTION_ACT_SCHEMA",
        "OSAGO_CLAIM_INSURANCE_EXECUTION_ACT_SCHEMA",
        "OSAGO_LAWSUIT_SCHEMA",
        "OSAGO_OSAGO_COURT_MAIL_LIST_SCHEMA"
    )

    for schema_name in schemas:
        DocRequisitiesStorage.add_schema(data[schema_name]['doc_name'], data[schema_name])

    bd = dict(
        batch_type=DocumentBatchTypeEnum.DBT_OSAGO,
        doc_types=[
            DocumentTypeEnum.DT_OSAGO_MAIL_LIST,
            DocumentTypeEnum.DT_OSAGO_PRETENSION,
            DocumentTypeEnum.DT_OSAGO_DOCUMENTS_CLAIM,
            DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISSION_DOCS,
            DocumentTypeEnum.DT_OSAGO_TRUST_OBTAIN_DOCS,
            DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISION_OBTAIN_DOCS,

            DocumentTypeEnum.DT_OSAGO_CLAIM_COURT_ABSENT,
            DocumentTypeEnum.DT_OSAGO_CLAIM_ALL_EXECUTION_ACT,
            DocumentTypeEnum.DT_OSAGO_CLAIM_GUILTY_EXECUTION_ACT,
            DocumentTypeEnum.DT_OSAGO_CLAIM_INSURANCE_EXECUTION_ACT,
            DocumentTypeEnum.DT_OSAGO_LAWSUIT,
            DocumentTypeEnum.DT_OSAGO_COURT_MAIL_LIST
        ],
        result_fields=data['OSAGO_RESULT_FIELDS'],
        fields=data['OSAGO_SCHEMA']['fields'],
        initial_status='pretension',
        actions=data['OSAGO_ACTIONS'],
        transitions=data['OSAGO_TRANSITIONS'],
        validation_condition=data['VALIDATION_CONDITION'],
        fixed_on_states=['generating_pretension', 'generating_claim']
    )

    DocRequisitiesStorage.add_batch_descriptor(DocumentBatchTypeEnum.DBT_OSAGO, bd)


def register(app, jinja_env, class_loader, **kwargs):
    search_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), u"templates"))
    jinja_env.loader.loaders.append(jinja2.FileSystemLoader(search_path))

    class_loader.POSSIBLE_LOCATIONS.append('services.osago.documents')
    class_loader.POSSIBLE_LOCATIONS.append('services.osago.documents.enums')
    class_loader.POSSIBLE_LOCATIONS.append('services.osago.documents.general_doc_fields')

    BatchManager.register_manager(DocumentBatchTypeEnum.DBT_OSAGO, OsagoBatchManager)

    _init_doc_requisities(app.config)

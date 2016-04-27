# -*- coding: utf-8 -*-

import os
import jinja2
from fw.documents.batch_manager import BatchManager
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentBatchTypeEnum, DocumentTypeEnum
from services.ip_reg.ip_reg_manager import IpRegBatchManager


def _init_doc_requisities(config):
    from services.ip_reg.documents.initial_db_data_ip import load_data
    data = load_data(config)

    templates = (
        "P21001_TEMPLATE",
        "IP_DOV_FILING_TEMPLATE",
        "IP_DOV_RECEIVING_TEMPLATE",
        "IP_DOV_FILING_RECEIVING_TEMPLATE",
        "IP_LETTER_INVENTORY_TEMPLATE",
        "IP_USN_TEMPLATE",
        "IP_ESHN_TEMPLATE"
    )

    for template_name in templates:
        DocRequisitiesStorage.add_template(data[template_name]['doc_name'], data[template_name])

    schemas = (
        "P21001_SCHEMA",
        "IP_REG_BATCH_SCHEMA",
        "IP_STATE_DUTY_SCHEMA",
        "IP_DOV_FILING_SCHEMA",
        "IP_DOV_RECEIVING_SCHEMA",
        "IP_DOV_FILING_RECEIVING_SCHEMA",
        "IP_LETTER_INVENTORY_SCHEMA",
        "IP_USN_SCHEMA",
        "IP_ESHN_SCHEMA"
    )

    for schema_name in schemas:
        DocRequisitiesStorage.add_schema(data[schema_name]['doc_name'], data[schema_name])

    matchers = (
        "P21001_MATCHER",
        "IP_USN_MATCHER",
        "IP_ESHN_MATCHER"
    )

    for matcher_name in matchers:
        DocRequisitiesStorage.add_field_matcher(data[matcher_name]['doc_name'], data[matcher_name])

    bd = dict(
        batch_type=DocumentBatchTypeEnum.DBT_NEW_IP,
        doc_types=[
            DocumentTypeEnum.DT_P21001,
            DocumentTypeEnum.DT_IP_STATE_DUTY,
            DocumentTypeEnum.DT_IP_DOV_FILING_DOCS,
            DocumentTypeEnum.DT_IP_DOV_RECEIVING_DOCS,
            DocumentTypeEnum.DT_IP_DOV_FILING_RECEIVING_DOCS,
            DocumentTypeEnum.DT_IP_USN_CLAIM,
            DocumentTypeEnum.DT_IP_ESHN_CLAIM,
            DocumentTypeEnum.DT_IP_LETTER_INVENTORY
        ],
        result_fields=data['IP_REG_RESULT_FIELDS'],
        deferred_render_docs=data['IP_REG_DEFER_DOCS'],
        fields=data['IP_REG_BATCH_SCHEMA']["fields"]
    )

    DocRequisitiesStorage.add_batch_descriptor(DocumentBatchTypeEnum.DBT_NEW_IP, bd)


def register(app, jinja_env, class_loader, **kwargs):
    search_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), u"templates"))
    jinja_env.loader.loaders.append(jinja2.FileSystemLoader(search_path))

    class_loader.POSSIBLE_LOCATIONS.append('services.ip_reg.documents')
    class_loader.POSSIBLE_LOCATIONS.append('services.ip_reg.documents.enums')
    class_loader.POSSIBLE_LOCATIONS.append('services.ip_reg.documents.general_doc_fields')
    class_loader.POSSIBLE_LOCATIONS.append('services.ip_reg.documents.ip_reg_methods')
    class_loader.POSSIBLE_LOCATIONS.append('services.ip_reg.documents.ip_validators')

    BatchManager.register_manager(DocumentBatchTypeEnum.DBT_NEW_IP, IpRegBatchManager)

    _init_doc_requisities(app.config)
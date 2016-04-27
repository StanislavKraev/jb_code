# -*- coding: utf-8 -*-

import os

import jinja2

from fw.documents.batch_manager import BatchManager
from fw.documents.doc_requisites_storage import DocRequisitiesStorage
from fw.documents.enums import DocumentBatchTypeEnum, DocumentTypeEnum
from fw.documents.fields.simple_doc_fields import DocMultiDeclensionField
from services.llc_reg.documents.enums import InitialCapitalDepositTypeEnum
from services.llc_reg.llc_reg_manager import LlcRegBatchManager


def _init_doc_requisities(config):
    from services.llc_reg.documents.initial_db_data import load_data
    from services.llc_reg.documents.third_stage_llc_reg_initial_db_data import load_data as third_stage_load_data
    data = load_data(config)
    data.update(third_stage_load_data(config))

    templates = (
        "P11001_TEMPLATE",
        "ARTICLES_TEMPLATE",
        "ACT_TEMPLATE",
        "USN_TEMPLATE",
        "ESHN_TEMPLATE",
        "DECISION_TEMPLATE",
        "CONTRACT_TEMPLATE",
        "DOVERENNOST_TEMPLATE",
        "DOVERENNOST_OBTAIN_TEMPLATE",
        "PROTOCOL_TEMPLATE",
        "SOGLASIE_SOBSTVENNIKOV_TEMPLATE",
        "GARANT_LETTER_ARENDA_TEMPLATE",
        "GARANT_LETTER_SUBARENDA_TEMPLATE",
        "GENERAL_MANAGER_CONTRACT_TEMPLATE",
        "GENERAL_MANAGER_ORDER_TEMPLATE",
        "ACCOUNTANT_CONTRACT_TEMPLATE",
        "ACCOUNTANT_IMPOSITION_ORDER_TEMPLATE",
        "ACCOUNTANT_ORDER_TEMPLATE",
        "ROSSTAT_CLAIM_TEMPLATE",
        "FSS_CLAIM_TEMPLATE",
        "PFR_CLAIM_TEMPLATE",
        "FOUNDERS_LIST_TEMPLATE",
        "COMPANY_DETAILS_TEMPLATE"
    )

    for template_name in templates:
        DocRequisitiesStorage.add_template(data[template_name]['doc_name'], data[template_name])

    schemas = (
        "P11001_SCHEMA",
        "ARTICLES_SCHEMA",
        "ACT_SCHEMA",
        "USN_SCHEMA",
        "ESHN_SCHEMA",
        "DECISION_SCHEMA",
        "PROTOCOL_SCHEMA",
        "CONTRACT_SCHEMA",
        "REG_FEE_INVOICE_SCHEMA",
        "DOVERENNOST_SCHEMA",
        "DOVERENNOST2_SCHEMA",
        "SOGLASIE_SOBSTVENNIKOV_SCHEMA",
        "GARANT_LETTER_ARENDA_SCHEMA",
        "GARANT_LETTER_SUBARENDA_SCHEMA",
        "LLC_REG_BATCH_SCHEMA",
        "OOO_BANK_PARTNER_APPLICATION_SCHEMA",
        "GENERAL_MANAGER_CONTRACT_SCHEMA",
        "GENERAL_MANAGER_ORDER_SCHEMA",
        "ACCOUNTANT_CONTRACT_SCHEMA",
        "ACCOUNTANT_IMPOSITION_ORDER_SCHEMA",
        "ACCOUNTANT_ORDER_SCHEMA",
        "ROSSTAT_CLAIM_SCHEMA",
        "FSS_CLAIM_SCHEMA",
        "PFR_CLAIM_SCHEMA",
        "FOUNDERS_LIST_SCHEMA",
        "COMPANY_DETAILS_SCHEMA"
    )

    for schema_name in schemas:
        DocRequisitiesStorage.add_schema(data[schema_name]['doc_name'], data[schema_name])

    matchers = (
        "P11001_MATCHER",
        "USN_MATCHER",
        "ESHN_MATCHER",
        "ACCOUNTANT_ORDER_MATCHER"
    )

    for matcher_name in matchers:
        DocRequisitiesStorage.add_field_matcher(data[matcher_name]['doc_name'], data[matcher_name])

    bd = dict(
        batch_type=DocumentBatchTypeEnum.DBT_NEW_LLC,
        doc_types=[
            DocumentTypeEnum.DT_P11001,
            DocumentTypeEnum.DT_ARTICLES,
            DocumentTypeEnum.DT_USN,
            DocumentTypeEnum.DT_DECISION,
            DocumentTypeEnum.DT_PROTOCOL,
            DocumentTypeEnum.DT_ESHN,
            DocumentTypeEnum.DT_CONTRACT,
            DocumentTypeEnum.DT_REGISTRATION_FEE_INVOICE,
            DocumentTypeEnum.DT_DOVERENNOST,
            DocumentTypeEnum.DT_DOVERENNOST_OBTAIN,
            DocumentTypeEnum.DT_SOGLASIE_SOBSTVENNIKOV,
            DocumentTypeEnum.DT_GARANT_LETTER_ARENDA,
            DocumentTypeEnum.DT_GARANT_LETTER_SUBARENDA,
            DocumentTypeEnum.DT_GENERAL_MANAGER_CONTRACT,
            DocumentTypeEnum.DT_GENERAL_MANAGER_ORDER,
            DocumentTypeEnum.DT_ACCOUNTANT_CONTRACT,
            DocumentTypeEnum.DT_ACCOUNTANT_IMPOSITION_ORDER,
            DocumentTypeEnum.DT_ACCOUNTANT_ORDER,
            DocumentTypeEnum.DT_ROSSTAT_CLAIM,
            DocumentTypeEnum.DT_FSS_CLAIM,
            DocumentTypeEnum.DT_PFR_CLAIM,
            DocumentTypeEnum.DT_FOUNDERS_LIST,
            DocumentTypeEnum.DT_COMPANY_DETAILS
        ],
        result_fields=data['LLC_REG_RESULT_FIELDS'],
        deferred_render_docs=data['LLC_REG_DEFER_DOCS'],
        fields=data['LLC_REG_BATCH_SCHEMA']['fields']
    )

    DocRequisitiesStorage.add_batch_descriptor(DocumentBatchTypeEnum.DBT_NEW_LLC, bd)


def register(app, jinja_env, class_loader, **kwargs):
    search_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), u"templates"))
    jinja_env.loader.loaders.append(jinja2.FileSystemLoader(search_path))

    jinja_env.globals.update({
        'DocMultiDeclensionField': DocMultiDeclensionField,
        'InitialCapitalDepositTypeEnum': InitialCapitalDepositTypeEnum
    })

    class_loader.POSSIBLE_LOCATIONS.append('services.llc_reg.documents')
    class_loader.POSSIBLE_LOCATIONS.append('services.llc_reg.documents.enums')
    class_loader.POSSIBLE_LOCATIONS.append('services.llc_reg.documents.general_doc_fields')
    class_loader.POSSIBLE_LOCATIONS.append('services.llc_reg.documents.llc_gov_forms_adapters')
    class_loader.POSSIBLE_LOCATIONS.append('services.llc_reg.documents.llc_validators')

    BatchManager.register_manager(DocumentBatchTypeEnum.DBT_NEW_LLC, LlcRegBatchManager)

    _init_doc_requisities(app.config)

def get_manager_command_locations():
    return [os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), 'manage_commands')))]
# -*- coding: utf-8 -*-
import os

from fw.documents.enums import DocumentTypeEnum, DocumentKindEnum, DocumentBatchTypeEnum
from services.osago.documents.enums import OsagoDocTypeEnum


def _get_test_resource_name(config, resource_rel_path):
    resources_path = config['resources_path']
    return os.path.join(resources_path, resource_rel_path)


def load_data(config):

    REQUIRED_DOCS_FIELD = {
        "#array_mapping": {
            "source_array": [
                OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                OsagoDocTypeEnum.ODT_NOTICE_CRASH,
                OsagoDocTypeEnum.ODT_INSURANCE_DENIAL,
                OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE,
                OsagoDocTypeEnum.ODT_POLICE_STATEMENT,
                OsagoDocTypeEnum.ODT_POLICE_PROTOCOL,
                OsagoDocTypeEnum.ODT_CASE_INITIATION_REFUSAL
            ],
            "filter": [{
                "#not": {
                    "<loop_item>": {
                        "#in": "@docs_got"
                    },
                }
            }, {
                "#not": {
                    "policy_called": False,
                    "<loop_item>": OsagoDocTypeEnum.ODT_CASE_INITIATION_REFUSAL
                }
            }, {
                "#or": [{
                    "police_case": False,
                    "<loop_item>": {
                        "#nin": [OsagoDocTypeEnum.ODT_POLICE_STATEMENT]
                    }
                }, {
                    "police_case": True,
                    "<loop_item>": {
                        "#nin": [OsagoDocTypeEnum.ODT_CASE_INITIATION_REFUSAL]
                    }
                }]
            }, {
                "#or": [{
                    "policy_called": True,
                }, {
                    "policy_called": False,
                    "<loop_item>": {
                        "#nin": [
                            OsagoDocTypeEnum.ODT_INQUIRE_CRASH,
                            OsagoDocTypeEnum.ODT_POLICE_STATEMENT,
                            OsagoDocTypeEnum.ODT_POLICE_PROTOCOL
                        ]
                    }
                }]
            }, {
                "#or": [{
                    "problem_type": "refusal"
                }, {
                    "problem_type": {
                        "#ne": "refusal"
                    },
                    "<loop_item>": {
                        "#nin": [OsagoDocTypeEnum.ODT_INSURANCE_DENIAL]
                    }
                }]
            }]
        }
    }

    FINAL_RESP_PERSON_FIELD = {
        "name": "final_responsible_person",
        "type": "calculated",
        "field_type": "db_object",
        "cls": "PrivatePerson",
        "suppress_validation_errors": True,
        "value": {
            "#cases": {
                "list": [{
                    "conditions": {
                        "court_include": True
                    },
                    "value": {
                        "#field": "responsible_person"
                    }
                }],
                "default": {
                    "value": {
                        "#field": "lawsuit_submission_responsible_person"
                    }
                }
            }
        }
    }

    RESULT_FIELDS_FIELD = {
        "name": "_result_fields",
        "type": "calculated",
        "field_type": "DocJsonField",
        "suppress_validation_errors": True,
        "required": False,
        "value": {
            "#field": "<batch>->result_fields"
        }
    }

    DOC_DATE_FIELD = {
        "name": "doc_date",
        "type": "calculated",
        "field_type": "DocDateTimeField",
        "suppress_validation_errors": True,
        "input_format": "%Y-%m-%d",
        "required": True,
        "value": {
            "#datetime": "#now"
        }
    }

    INSURANCE_ADDRESS_FINAL_FIELD = {
        "name": "insurance_address_final",
        "type": "calculated",
        "suppress_validation_errors": True,
        "field_type": "DocTextField",
        "required": False,
        "value": {
            "#cases": {
                "list": [{
                    "conditions": {
                        "use_other_submission_address": True
                    },
                    "value": {
                        "#field": "submission_address"
                    }
                }],
                "default": {
                    "value": {
                        "#fetch_db_table_row": {
                            "table_name": "car_assurance_branch",
                            "id": "@submission_branch_id",
                            "field_name": "address"
                        }
                    }
                }
            }
        }
    }

    INSURANCE_NAME_FINAL_FIELD = {
        "name": "insurance_name_final",
        "type": "calculated",
        "suppress_validation_errors": True,
        "field_type": "DocTextField",
        "required": False,
        "value": {
            "#cases": {
                "list": [{
                    "conditions": {
                        "other_insurance": True
                    },
                    "value": {
                        "#field": "insurance_name"
                    }
                }],
                "default": {
                    "value": {
                        "#field": "<batch>->result_fields->insurance_name"
                    }
                }
            }
        }
    }

    RESPONSIBLE_PERSON_ADDRESS_FIELD = {
        "name": "responsible_person_address",
        "type": "calculated",
        "suppress_validation_errors": True,
        "field_type": "DocTextField",
        "value": {
            "#cases": {
                "list": [{
                    "conditions": {
                        "obtain_address_type": "other_address"
                    },
                    "value": {
                        "#field": "obtain_address"
                    }
                }, {
                    "conditions": {
                        "obtain_address_type": "owner_address"
                    },
                    "value": {
                        "#field": "victim_owner->address->as_string"
                    }
                }],
                "default": {
                    "value": {
                        "#field": "responsible_person->address->as_string"
                    }
                }
            }
        }
    }

    OWNER_ADDRESS_FIELD = {
        "name": "owner_address",
        "type": "calculated",
        "field_type": "DocTextField",
        "suppress_validation_errors": True,
        "value": {
            "#cases": {
                "list": [{
                    "conditions": {
                        "submission_way": {
                            "#ne": "responsible_person"
                        }
                    },
                    "value": {
                        "#cases": {
                            "list": [{
                                "conditions": {
                                    "obtain_address_type": "other_address"
                                },
                                "value": {
                                    "#field": "obtain_address"
                                }
                            }],
                            "default": {
                                "value": {
                                    "#field": "victim_owner->address->as_string"
                                }
                            }
                        }
                    }
                }],
                "default": {
                    "value": {
                        "#field": "victim_owner->address->as_string"
                    }
                }
            }
        }
    }

    UNDERPAY_SUM_FIELD = {
        "name": "underpay_sum",
        "type": "calculated",
        "field_type": "DocDecimalField",
        "suppress_validation_errors": True,
        "value": {
            # underpay_sum — размер недоплаты страховой (float — с копейками), рассчитывается по формуле:
            # min(independent_expertise_sum, gibdd ?
            #                                       (< 1.10.2014 ? 120000 : 400000) :
            #                                       (< 1.10.2014 ? 25000 : 50000)) -
            #     (problem_type=refusal ? 0 : compensation_sum)
            "#sub": [{
                "#min": [{
                    "#cases": {
                        "list": [{
                            "conditions": {
                                "policy_called": True
                            },
                            "value": {
                                "#cases": {
                                    "set": {
                                        "datetime_01_10_2014": {
                                            "#datetime": {"year": 2014, "month": 10, "day": 1}
                                        }
                                    },
                                    "list": [{
                                        "conditions": {
                                            "policy_date": {
                                                "#lt": "@datetime_01_10_2014"
                                            }
                                        },
                                        'value': {"#value": 120000}
                                    }],
                                    "default": {"value": {"#value": 400000}}
                                }
                            }
                        }],
                        "default": {
                            "value": {
                                "#cases": {
                                    "set": {
                                        "datetime_01_10_2014": {
                                            "#datetime": {"year": 2014, "month": 10, "day": 1}
                                        }
                                    },
                                    "list": [{
                                        "conditions": {
                                            "policy_date": {
                                                "#lt": "@datetime_01_10_2014"
                                            }
                                        },
                                        'value': {"#value": 25000}
                                    }],
                                    "default": {"value": {"#value": 50000}}
                                }
                            }
                        }
                    }
                }, {
                    "#field": "independent_expertise_sum"
                }]
            }, {
                "#cases": {
                    "list": [{
                        "conditions": {
                            "problem_type": "refusal"
                        },
                        "value": {"#value": 0}
                    }],
                    "default": {
                        "value": {
                            "#field": "compensation_sum"
                        }
                    }
                }
            }]

        }
    }

    OSAGO_MAIL_LIST_TEMPLATE = {
        "template_name": "template_osago1",
        "file_name": _get_test_resource_name(config, "osago/mail_list_template.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_MAIL_LIST
    }

    OSAGO_PRETENSION_TEMPLATE = {
        "template_name": "template_osago2",
        "file_name": _get_test_resource_name(config, "osago/pretension_template.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_PRETENSION
    }

    OSAGO_DOCUMENTS_CLAIM_TEMPLATE = {
        "template_name": "template_osago3",
        "file_name": _get_test_resource_name(config, "osago/documents_claim.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_DOCUMENTS_CLAIM
    }

    OSAGO_TRUST_SUBMISSION_DOCS_TEMPLATE = {
        "template_name": "template_osago4",
        "file_name": _get_test_resource_name(config, "osago/trust_submission_docs.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISSION_DOCS
    }

    OSAGO_TRUST_OBTAIN_DOCS_TEMPLATE = {
        "template_name": "template_osago5",
        "file_name": _get_test_resource_name(config, "osago/trust_submission_docs.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_TRUST_OBTAIN_DOCS
    }

    OSAGO_TRUST_SUBMISION_OBTAIN_DOCS_TEMPLATE = {
        "template_name": "template_osago6",
        "file_name": _get_test_resource_name(config, "osago/trust_submission_docs.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISION_OBTAIN_DOCS
    }

    OSAGO_MAIL_LIST_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_MAIL_LIST,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Опись ценного письма для ОСАГО",
        "conditions": {
            "submission_way": "mail"
        },
        "collections": ["pretension_collection"],
        "batch_statuses": ["pretension"],
        "fields": [
            INSURANCE_NAME_FINAL_FIELD,
            INSURANCE_ADDRESS_FINAL_FIELD,
            {
                "name": "is_claim_created",
                "type": "calculated",
                "suppress_validation_errors": True,
                "field_type": "DocBoolField",
                "value": {
                    "#cases": {
                        "set": {
                            "calc_docs_list": REQUIRED_DOCS_FIELD
                        },
                        "list": [{
                            "conditions": {
                                "calc_docs_list->__len__": {
                                    "#gt": 0
                                }
                            },
                            "value": {
                                "#value": True
                            }
                        }],
                        "default": {
                            "value": {
                                "#value": False
                            }
                        }
                    }
                }
            }, {
                "name": "submission_way",
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": True
            }
        ]
    }

    OSAGO_PRETENSION_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_PRETENSION,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Претензия по ОСАГО",
        "batch_statuses": ["pretension"],
        "collections": ["pretension_collection"],
        "fields": [
            {
                "name": "paid_document",
                "type": "calculated",
                "field_type": "DocBoolField",
                "value": {
                    "#exec": {
                        "module": "osago_reg_methods",
                        "method": "is_paid_document",
                        "args": [{
                            "#field": "<batch_id>"
                        }, {
                            "#field": "<document_type>"
                        }]
                    }
                }
            },
            OWNER_ADDRESS_FIELD,
            RESPONSIBLE_PERSON_ADDRESS_FIELD,
            DOC_DATE_FIELD,
            INSURANCE_NAME_FINAL_FIELD,
            INSURANCE_ADDRESS_FINAL_FIELD,
            RESULT_FIELDS_FIELD,
            {
                "name": "first_claim_date", #дата первого заявления о наступлении аварии в формате ISO_8601 — "2005-08-09T18:31:42"
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            },
            {
                "name": "own_insurance_company",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "policy_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            },
            {
                "name": "independent_expertise_sum",
                "type": "DocDecimalField",
                "required": True
            },
            {
                "name": "independent_expertise_cost",
                "type": "DocDecimalField",
                "required": True
            },
            {
                "name": "insurance_company_region",
                "type": "DocEnumField",
                "enum_cls": "RFRegionsEnum",
                "required": True
            },
            {
                "name": "obtain_address_type",
                "type": "DocEnumField",
                "enum_cls": "ObtainAddressEnum",
                "required": True
            },
            {
                "name": "victim_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True,
                "override_fields_kwargs": {
                    "address": {"required": True},
                    "phone": {"required": True}
                }
            },
            {
                "name": "responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "address": {"required": True},
                    "phone": {"required": True}
                }
            },
            {
                "name": "victim_car_brand",
                "type": "DocTextField",
                "required": True,
                "max_length": 100,
                "min_length": 1
            },
            {
                "name": "victim_car_number",
                "type": "DocTextField",
                "required": True,
                "max_length": 15,
                "allowed_re": ur"^[0-9а-яА-Яa-zA-Z]*$"
            },
            {
                "name": "crash_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            },
            {
                "name": "owner_as_victim_driver",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "victim_driver", #идентификатор физического лица водителя пострадавшего автомобиля
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "guilty_owner", #идентификатор физического лица владельца виновного автомобиля
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False},
                    "address": {"required": True}
                }
            },
            {
                "name": "owner_as_guilty_driver",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "guilty_driver", #идентификатор физического лица водителя виновного автомобиля
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "guilty_car_brand",
                "type": "DocTextField",
                "required": True,
                "max_length": 100,
                "min_length": 1
            },
            {
                "name": "guilty_car_number",
                "type": "DocTextField",
                "required": True,
                "max_length": 15,
                "min_length": 1,
                "allowed_re": ur"^[0-9а-яА-Яa-zA-Z]*$"
            },
            {
                "name": "policy_series",
                "type": "DocTextField",
                "required": True,
                "max_length": 3,
                "min_length": 1
            },
            {
                "name": "policy_number",
                "type": "DocTextField",
                "required": True,
                "max_length": 10,
                "allowed_re": ur"^[0-9]*$",
                "min_length": 1
            },
            {
                "name": "problem_type",
                "type": "DocEnumField",
                "enum_cls": "OsagoReasonEnum",
                "required": True
            },
            {
                "name": "compensation_sum",
                "type": "DocDecimalField",
                "required": False
            },
            {
                "name": "bik_account",
                "type": "DocTextField",
                "required": True,
                "min_length": 9,
                "allowed_re": ur"^[0-9]*$"
            },
            {
                "name": "account_number",
                "type": "DocTextField",
                "required": True,
                "min_length": 20,
                "allowed_re": ur"^[0-9]*$"
            },
            {
                "name": "independent_expertise_number",
                "type": "DocTextField",
                "required": True,
                "max_length": 20,
                "min_length": 0
            },
            {
                "name": "use_other_submission_address",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "submission_address",
                "type": "DocTextField",
                "required": False,
                "min_length": 0
            },
            {
                "name": "other_insurance",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "insurance_name",
                "type": "DocTextField",
                "required": False,
            },
            {
                "name": "submission_branch_id",
                "type": "DocTextField",
                "required": False,
            },
            {
                "name": "obtain_address",
                "type": "DocTextField",
                "required": False
            },
            {
                "name": "bank_info",
                "type": "calculated",
                "field_type": "DocJsonField",
                "error_field_mapping": {
                    "bank_info": "."
                },
                "required": True,
                "value": {
                    "#exec": {
                        "module": "llc_reg_methods",
                        "method": "get_bank_info",
                        "args": [{
                            "#field": "bik_account"
                        }]
                    }
                },
                "validator": {
                    "#set": {
                        "test_bik": {
                            "#field": "value->bik"
                        }
                    },
                    "conditions": [{
                        "test_bik": {
                            "#not_empty": True
                        }
                    }],
                    "error_field": "bik_account"
                }
            },
            {
                "name": "police_case",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "obtain_way",
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": True
            },
            {
                "name": "submission_way",
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": True
            },
            {
                "name": "add_person_to_claim",
                "type": "DocBoolField",
                "required": True
            },
        ],
        "validators": [{
            "condition": {
                "#or": [{
                    "use_other_submission_address": True,
                    "submission_address": {
                        "#empty": False
                    }
                }, {
                    "use_other_submission_address": {
                        "#ne": True
                    }
                }]
            },
            "error": {
                "field": "submission_address",
                "code": 5
            }
        }, {
            "condition": {
                "#or": [{
                    "use_other_submission_address": {
                        "#ne": True
                    },
                    "submission_branch_id": {
                        "#empty": False
                    }
                }, {
                    "use_other_submission_address": {
                        "#ne": False
                    }
                }]
            },
            "error": {
                "field": "submission_branch_id",
                "code": 5
            }
        }, {
            "condition": {
                "#or": [{
                    "obtain_address_type": "other_address",
                    "obtain_address": {
                        "#empty": False
                    }
                }, {
                    "obtain_address_type": {
                        "#ne": "other_address"
                    }
                }]
            },
            "error": {
                "field": "obtain_address",
                "code": 5
            }
        }, {
            "condition": {
                "#or": [{
                    "obtain_address_type": "owner_address",
                    "victim_owner": {
                        "#empty": False
                    }
                }, {
                    "obtain_address_type": {
                        "#ne": "owner_address"
                    }
                }]
            },
            "error": {
                "field": "victim_owner",
                "code": 5
            }
        }, {
            "condition": {
                "#or": [{
                    "obtain_address_type": "responsible_person_address",
                    "responsible_person": {
                        "#empty": False
                    }
                }, {
                    "obtain_address_type": {
                        "#ne": "responsible_person_address"
                    }
                }]
            },
            "error": {
                "field": "responsible_person",
                "code": 5
            }
        }, {
            "condition": {
                "#or": [{
                    "other_insurance": {
                        "#ne": False
                    },
                    "insurance_name": {
                        "#empty": False
                    }
                }, {
                    "other_insurance": False
                }]
            },
            "error": {
                "field": "insurance_id",
                "code": 5
            }
        }, {
            "condition": {
                "#or": [{
                    "owner_as_guilty_driver": {
                        "#ne": True
                    },
                    "guilty_driver": {
                        "#empty": False
                    }
                }, {
                    "owner_as_guilty_driver": {
                        "#ne": False
                    },
                }]
            },
            "error": {
                "field": "guilty_driver",
                "code": 5
            }
        }, {
            "condition": {
                "#or": [{
                    "owner_as_victim_driver": False,
                    "victim_driver": {
                        "#empty": False
                    }
                }, {
                    "owner_as_victim_driver": True
                }]
            },
            "error": {
                "field": "victim_driver",
                "code": 5
            }
        }, {
            "condition": {
                "#or": [{
                    "submission_way": "responsible_person",
                    "court_include": {
                        "#exists": True
                    }
                }, {
                    "submission_way": {
                        "#ne": "responsible_person"
                    }
                }]
            },
            "error": {
                "field": "court_include",
                "code": 4
            }
        }]
    }

    OSAGO_DOCUMENTS_CLAIM_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_DOCUMENTS_CLAIM,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Заявление на выдачу документов по ОСАГО",
        "collections": ["pretension_collection"],
        "conditions": {
            "requested_docs->__len__": {
                "#gt": 0
            },
            "#not": {
                "requested_docs->__len__": 1,
                "act_insurance_case": {
                    "#in": "@requested_docs"
                },
                "problem_type": {
                    "#ne": "underpay"
                }
            }
        },
        "batch_statuses": ["pretension"],
        "fields": [
            OWNER_ADDRESS_FIELD,
            RESPONSIBLE_PERSON_ADDRESS_FIELD,
            INSURANCE_NAME_FINAL_FIELD,
            INSURANCE_ADDRESS_FINAL_FIELD,
            DOC_DATE_FIELD,
            RESULT_FIELDS_FIELD,
        {
            "name": "own_insurance_company",
            "type": "DocBoolField",
            "required": True
        },
        {
            "name": "problem_type",
            "type": "DocEnumField",
            "enum_cls": "OsagoReasonEnum",
            "required": True
        },
        {
            "name": "obtain_address_type",
            "type": "DocEnumField",
            "enum_cls": "ObtainAddressEnum",
            "required": True
        },
        {
            "name": "victim_owner",
            "type": "db_object",
            "cls": "PrivatePerson",
            "required": True
        },
        {
            "name": "police_case",
            "type": "DocBoolField",
            "required": True
        },
        {
            "name": "requested_docs",
            "type": "calculated",
            "suppress_validation_errors": True,
            "field_type": "DocArrayField",
            "cls": "DocEnumField",
            "subfield_kwargs": {
                "enum_cls": "OsagoDocTypeEnum"
            },
            "value": REQUIRED_DOCS_FIELD
        },
        {
            "name": "responsible_person",
            "type": "db_object",
            "cls": "PrivatePerson",
            "required": False
        }, {
            "name": "victim_car_brand",
            "type": "DocTextField",
            "required": True,
            "max_length": 100,
            "min_length": 1
        }, {
            "name": "victim_car_number",
            "type": "DocTextField",
            "required": True,
            "max_length": 15,
            "allowed_re": ur"^[\s0-9а-яА-Яa-zA-Z]*$"
        }, {
            "name": "crash_date",
            "type": "DocDateTimeField",
            "input_format": "%Y-%m-%d",
            "required": True
        }, {
            "name": "obtain_way",
            "type": "DocEnumField",
            "enum_cls": "ApplicationTypeEnum",
            "required": True
        }, {
            "name": "submission_way",
            "type": "DocEnumField",
            "enum_cls": "ApplicationTypeEnum",
            "required": True
        }, {
            "name": "obtain_address",
            "type": "DocTextField",
            "required": False
        }]
    }

    OSAGO_TRUST_SUBMISSION_DOCS_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISSION_DOCS,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Доверенность на подачу документов в страховую",
        "collections": ["pretension_collection"],
        "conditions": {
            "submission_way": "responsible_person",
            "obtain_way": {
                "#ne": "responsible_person"
            }
        },
        "batch_statuses": ["pretension"],
        "fields": [
            DOC_DATE_FIELD,
            INSURANCE_NAME_FINAL_FIELD,
            {
                "name": "victim_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True
            },
            {
                "name": "responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True
            },
            {
                "name": "court_include",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "crash_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            },
            {
                "name": "victim_car_brand",
                "type": "DocTextField",
                "required": True,
                "max_length": 100
            },
            {
                "name": "victim_car_number",
                "type": "DocTextField",
                "required": True,
                "max_length": 15,
                "allowed_re": ur"^[\s0-9а-яА-Яa-zA-Z]*$"
            }
        ]
    }

    OSAGO_TRUST_OBTAIN_DOCS_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_TRUST_OBTAIN_DOCS,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Доверенность на получение документов из страховой",
        "collections": ["pretension_collection"],
        "conditions": {
            "obtain_way": "responsible_person",
            "submission_way": {
                "#ne": "responsible_person"
            }
        },
        "batch_statuses": ["pretension"],
        "fields": [
            DOC_DATE_FIELD,
            INSURANCE_NAME_FINAL_FIELD,
            {
                "name": "victim_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True
            },
            {
                "name": "responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True
            },
            {
                "name": "court_include",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "crash_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            },
            {
                "name": "victim_car_brand",
                "type": "DocTextField",
                "required": True,
                "max_length": 100
            },
            {
                "name": "victim_car_number",
                "type": "DocTextField",
                "required": True,
                "max_length": 15,
                "allowed_re": ur"^[\s0-9а-яА-Яa-zA-Z]*$"
            }
        ]
    }

    OSAGO_TRUST_SUBMISION_OBTAIN_DOCS_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISION_OBTAIN_DOCS,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Доверенность на подачу и получение документов из страховой",
        "collections": ["pretension_collection"],
        "conditions": {
            "obtain_way": "responsible_person",
            "submission_way": "responsible_person"
        },
        "batch_statuses": ["pretension"],
        "fields": [
            DOC_DATE_FIELD,
            INSURANCE_NAME_FINAL_FIELD,
            {
                "name": "victim_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True
            },
            {
                "name": "responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True
            },
            {
                "name": "court_include",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "crash_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            },
            {
                "name": "victim_car_brand",
                "type": "DocTextField",
                "required": True,
                "max_length": 100
            },
            {
                "name": "victim_car_number",
                "type": "DocTextField",
                "required": True,
                "max_length": 15,
                "allowed_re": ur"^[\s0-9а-яА-Яa-zA-Z]*$"
            }
        ]
    }

    OSAGO_CLAIM_COURT_ABSENT_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_CLAIM_COURT_ABSENT,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Заявление об отсутствии на суде",
        "batch_statuses": ["claim"],
        "collections": ["claim_collection"],
        "conditions": {
            'court_attendance': {
                '#ne': 'oneself'
            }
        },
        "fields": [
            {
                "name": "obtain_address_type",
                "type": "DocEnumField",
                "enum_cls": "ObtainAddressEnum",
                "required": False
            },
            {
                "name": "obtain_address",
                "type": "DocTextField",
                "required": False
            },
            {
                "name": "court_attendance",
                "type": "DocEnumField",
                "enum_cls": "CourtAttendanceEnum",
                "required": True
            },
            {
                "name": "other_insurance",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "insurance_name",
                "type": "DocTextField",
                "required": False,
            },
            {
                "name": "insurance_id",
                "type": "DocTextField",
                "required": False,
                "min_length": 0,
                "max_length": 30
            },
            {
                "name": "court_name",
                "type": "DocTextField",
                "max_length": 200,
                "required": True
            },
            {
                "name": "court_address",
                "type": "DocTextField",
                "max_length": 1024,
                "required": True
            },
            {
                "name": "victim_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            },
            {
                "name": "guilty_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "guilty_driver",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "add_person_to_claim",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "lawsuit_submission_way",
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": True
            },
            {
                "name": "court_include",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "lawsuit_submission_responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "address": {"required": True},
                    "phone": {"required": True},
                }
            },
            {
                "name": "responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
            },
            {
                "name": "owner_as_guilty_driver",
                "type": "DocBoolField",
                "required": False
            },
            DOC_DATE_FIELD,
            FINAL_RESP_PERSON_FIELD,
            RESULT_FIELDS_FIELD,
            INSURANCE_ADDRESS_FINAL_FIELD,
            INSURANCE_NAME_FINAL_FIELD,
            {
                "name": "use_other_submission_address",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "submission_address",
                "type": "DocTextField",
                "required": False,
            },
            {
                "name": "lawsuit_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            },
        ]
    }

    OSAGO_CLAIM_COURT_ABSENT_TEMPLATE = {
        "template_name": "template_osago2_1",
        "file_name": _get_test_resource_name(config, "osago/court_absence_claim.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_CLAIM_COURT_ABSENT
    }

    OSAGO_CLAIM_ALL_EXECUTION_ACT_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_CLAIM_ALL_EXECUTION_ACT,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Заявление о выдаче двух ИЛ",
        "conditions": {
            "add_person_to_claim": True
        },
        "collections": ["court_collection"],
        "batch_statuses": ["court"],
        "fields": [
            DOC_DATE_FIELD,
            RESULT_FIELDS_FIELD,
            {
                "name": "lawsuit_number",
                "type": "DocTextField",
                "max_length": 20,
                "min_length": 1,
                "required": True
            },
            {
                "name": "court_name",
                "type": "DocTextField",
                "max_length": 200,
                "required": True
            },
            {
                "name": "court_address",
                "type": "DocTextField",
                "max_length": 1024,
                "required": True
            },
            {
                "name": "lawsuit_submission_way",
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": True
            },
            {
                "name": "victim_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            },
            {
                "name": "obtain_address_type",
                "type": "DocEnumField",
                "enum_cls": "ObtainAddressEnum",
                "required": False
            },
            {
                "name": "obtain_address",
                "type": "DocTextField",
                "required": False
            },
            {
                "name": "court_include",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
            },
            {
                "name": "add_person_to_claim",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "owner_as_guilty_driver",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "guilty_driver",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "guilty_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            INSURANCE_ADDRESS_FINAL_FIELD,
            INSURANCE_NAME_FINAL_FIELD,
            {
                "name": "other_insurance",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "insurance_name",
                "type": "DocTextField",
                "required": False,
            },
            {
                "name": "insurance_id",
                "type": "DocTextField",
                "required": False,
                "min_length": 0,
                "max_length": 30
            },
            {
                "name": "use_other_submission_address",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "submission_address",
                "type": "DocTextField",
                "required": False
            }
        ]
    }

    OSAGO_CLAIM_ALL_EXECUTION_ACT_TEMPLATE = {
        "template_name": "template_osago2_2",
        "file_name": _get_test_resource_name(config, "osago/il_claim_double.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_CLAIM_ALL_EXECUTION_ACT
    }

    OSAGO_CLAIM_GUILTY_EXECUTION_ACT_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_CLAIM_GUILTY_EXECUTION_ACT,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Заявление о получении ИЛ к виновнику",
        "conditions": {
            "add_person_to_claim": True
        },
        "batch_statuses": ["court"],
        "collections": ["court_collection"],
        "fields": [
            DOC_DATE_FIELD,
            RESULT_FIELDS_FIELD,
            {
                "name": "lawsuit_number",
                "type": "DocTextField",
                "max_length": 20,
                "min_length": 1,
                "required": True
            },
            {
                "name": "court_name",
                "type": "DocTextField",
                "max_length": 200,
                "required": True
            },
            {
                "name": "court_address",
                "type": "DocTextField",
                "max_length": 1024,
                "required": True
            },
            {
                "name": "lawsuit_submission_way",
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": True
            },
            {
                "name": "victim_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            },
            {
                "name": "obtain_address_type",
                "type": "DocEnumField",
                "enum_cls": "ObtainAddressEnum",
                "required": False
            },
            {
                "name": "obtain_address",
                "type": "DocTextField",
                "required": False
            },
            {
                "name": "court_include",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
            },
            {
                "name": "add_person_to_claim",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "owner_as_guilty_driver",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "guilty_driver",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "guilty_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            INSURANCE_ADDRESS_FINAL_FIELD,
            INSURANCE_NAME_FINAL_FIELD,
            {
                "name": "other_insurance",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "insurance_name",
                "type": "DocTextField",
                "required": False,
            },
            {
                "name": "insurance_id",
                "type": "DocTextField",
                "required": False,
                "min_length": 0,
                "max_length": 30
            },
            {
                "name": "use_other_submission_address",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "submission_address",
                "type": "DocTextField",
                "required": False
            },
            {
                "name": "guilty_execution_act_responsible_person",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "guilty_execution_act_obtain_way",
                "type": "DocEnumField",
                "enum_cls": "ActObtainWayEnum",
                "required": False
            },
        ],
        "validators": [{
            "condition": {
                "#or": [{
                    "guilty_execution_act_responsible_person": {
                        "#exists": True
                    },
                    "lawsuit_submission_way": "responsible_person"
                }, {
                    "lawsuit_submission_way": {
                        "#ne": "responsible_person"
                    }
                }]
            },
            "error": {
                "field": "guilty_execution_act_responsible_person",
                "code": 4
            }
        }, {
            "condition": {
                "#or": [{
                    "guilty_execution_act_obtain_way": {"#exists": True},
                    "#or": [{
                        "lawsuit_submission_way": "responsible_person",
                        "guilty_execution_act_responsible_person": {"#ne": False}
                    }]

                }, {
                    "#not": {
                        "#or": [{
                            "lawsuit_submission_way": "responsible_person",
                            "guilty_execution_act_responsible_person": {"#ne": False}
                        }]
                    }
                }]
            },
            "error": {
                "field": "guilty_execution_act_obtain_way",
                "code": 4
            }
        }]
    }

    OSAGO_CLAIM_GUILTY_EXECUTION_ACT_TEMPLATE = {
        "template_name": "template_osago2_3",
        "file_name": _get_test_resource_name(config, "osago/il_claim_guilty.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_CLAIM_GUILTY_EXECUTION_ACT
    }

    OSAGO_CLAIM_INSURANCE_EXECUTION_ACT_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_CLAIM_INSURANCE_EXECUTION_ACT,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Заявление о получении ИЛ к страховой",
        "conditions": {},
        "batch_statuses": ["court"],
        "collections": ["court_collection"],
        "fields": [
            DOC_DATE_FIELD,
            RESULT_FIELDS_FIELD,
            {
                "name": "lawsuit_number",
                "type": "DocTextField",
                "max_length": 20,
                "min_length": 1,
                "required": True
            },
            {
                "name": "court_name",
                "type": "DocTextField",
                "max_length": 200,
                "required": True
            },
            {
                "name": "court_address",
                "type": "DocTextField",
                "max_length": 1024,
                "required": True
            },
            {
                "name": "lawsuit_submission_way",
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": True
            },
            {
                "name": "victim_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            },
            {
                "name": "obtain_address_type",
                "type": "DocEnumField",
                "enum_cls": "ObtainAddressEnum",
                "required": False
            },
            {
                "name": "obtain_address",
                "type": "DocTextField",
                "required": False
            },
            {
                "name": "court_include",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
            },
            {
                "name": "add_person_to_claim",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "owner_as_guilty_driver",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "guilty_driver",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "guilty_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            INSURANCE_ADDRESS_FINAL_FIELD,
            INSURANCE_NAME_FINAL_FIELD,
            {
                "name": "other_insurance",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "insurance_name",
                "type": "DocTextField",
                "required": False,
            },
            {
                "name": "insurance_id",
                "type": "DocTextField",
                "required": False,
                "min_length": 0,
                "max_length": 30
            },
            {
                "name": "use_other_submission_address",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "submission_address",
                "type": "DocTextField",
                "required": False
            },
            {
                "name": "insurance_execution_act_responsible_person",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "insurance_execution_act_obtain_way",
                "type": "DocEnumField",
                "enum_cls": "ActObtainWayEnum",
                "required": False
            },

        ],
        "validators": [{
            "condition": {
                "#or": [{
                    "insurance_execution_act_responsible_person": {
                        "#exists": True
                    },
                    "lawsuit_submission_way": "responsible_person"
                }, {
                    "lawsuit_submission_way": {
                        "#ne": "responsible_person"
                    }
                }]
            },
            "error": {
                "field": "insurance_execution_act_responsible_person",
                "code": 4
            }
        }, {
            "condition": {
                "#or": [{
                    "insurance_execution_act_obtain_way": {"#exists": True},
                    "#or": [{
                        "lawsuit_submission_way": "responsible_person",
                        "insurance_execution_act_responsible_person": {"#ne": False}
                    }]

                }, {
                    "#not": {
                        "#or": [{
                            "lawsuit_submission_way": "responsible_person",
                            "insurance_execution_act_responsible_person": {"#ne": False}
                        }]
                    }
                }]
            },
            "error": {
                "field": "insurance_execution_act_obtain_way",
                "code": 4
            }
        }]
        # insurance_execution_act_oneself - required if: не через представителя (lawsuit_submission_way)
        # insurance_execution_act_responsible_person - required if: через представителя (lawsuit_submission_way)
        # insurance_execution_act_obtain_way - required if: (insurance_execution_act_oneself == False && не через представителя) || (через представителя && insurance_execution_act_responsible_person==False)
    }

    OSAGO_CLAIM_INSURANCE_EXECUTION_ACT_TEMPLATE = {
        "template_name": "template_osago2_4",
        "file_name": _get_test_resource_name(config, "osago/il_claim_insurance.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_CLAIM_INSURANCE_EXECUTION_ACT
    }

    OSAGO_LAWSUIT_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_LAWSUIT,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Иск",
        "batch_statuses": ["claim"],
        "collections": ["claim_collection"],
        "fields": [
            {
                "name": "paid_document",
                "type": "calculated",
                "field_type": "DocBoolField",
                "value": {
                    "#exec": {
                        "module": "osago_reg_methods",
                        "method": "is_paid_document",
                        "args": [{
                            "#field": "<batch_id>"
                        }, {
                            "#field": "<document_type>"
                        }]
                    }
                }
            },
            DOC_DATE_FIELD,
            {
                "name": "isk_type",
                "type": "calculated",
                "suppress_validation_errors": True,
                "field_type": "DocTextField",
                "value": {
                    "#cases": {
                        "list": [{
                            "conditions": {
                                "problem_type": "refusal",
                                "policy_called": False
                            },
                            "value": {
                                "#value": "EURO_ISK"
                            }
                        }, {
                            "conditions": {
                                "problem_type": "refusal",
                                "policy_called": True
                            },
                            "value": {
                                "#value": "GIBDD_ISK"
                            }
                        }],
                        "default": {
                            "value": {
                                "#value": "ISK_UNDERPAY"
                            }
                        }
                    }
                }
            },
            {
                "name": "docs_got",
                "type": "DocArrayField",
                "cls": "DocEnumField",
                "subfield_kwargs": {
                    "enum_cls": "OsagoDocTypeEnum"
                },
                "required": False,
                "default": []
            },
            {
                "name": "lawsuit_submission_way",
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": True
            },
            {
                "name": "submission_way",
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": True
            },
            {
                "name": "court_include",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
            },
            {
                "name": "lawsuit_submission_responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "address": {"required": True},
                    "phone": {"required": True},
                }
            },
            {
                "name": "victim_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            },
            {
                "name": "add_person_to_claim",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "court_name",
                "type": "DocTextField",
                "max_length": 200,
                "required": True
            },
            {
                "name": "court_address",
                "type": "DocTextField",
                "max_length": 1024,
                "required": True
            },
            {
                "name": "obtain_address_type",
                "type": "DocEnumField",
                "enum_cls": "ObtainAddressEnum",
                "required": False
            },
            {
                "name": "obtain_address",
                "type": "DocTextField",
                "required": False
            },
            {
                "name": "owner_as_guilty_driver",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "guilty_driver",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "guilty_car_brand",
                "type": "DocTextField",
                "required": False,
                "max_length": 100,
                "min_length": 1
            },
            {
                "name": "guilty_car_number",
                "type": "DocTextField",
                "required": False,
                "max_length": 15,
                "min_length": 1,
                "allowed_re": ur"^[0-9а-яА-Яa-zA-Z]*$"
            },
            RESULT_FIELDS_FIELD,
            INSURANCE_ADDRESS_FINAL_FIELD,
            INSURANCE_NAME_FINAL_FIELD,
            {
                "name": "crash_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": False
            },
            {
                "name": "problem_type",
                "type": "DocEnumField",
                "enum_cls": "OsagoReasonEnum",
                "required": False
            },
            {
                "name": "policy_called",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "victim_car_brand",
                "type": "DocTextField",
                "required": False,
                "max_length": 100,
                "min_length": 1
            },
            {
                "name": "victim_car_number",
                "type": "DocTextField",
                "required": False,
                "max_length": 15,
                "allowed_re": ur"^[0-9а-яА-Яa-zA-Z]*$"
            },
            {
                "name": "victim_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            },
            {
                "name": "owner_as_victim_driver",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "victim_driver",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "guilty_owner",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "own_insurance_company",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "policy_series",
                "type": "DocTextField",
                "required": False,
                "max_length": 3,
                "min_length": 1
            },
            {
                "name": "policy_number",
                "type": "DocTextField",
                "required": False,
                "max_length": 10,
                "allowed_re": ur"^[0-9]*$",
                "min_length": 1
            },
            {
                "name": "refusal_reason",
                "type": "DocEnumField",
                "enum_cls": "OsagoRefusalReasonEnum",
                "required": False
            },
            {
                "name": "independent_expertise_cost",
                "type": "DocDecimalField",
                "required": False
            },
            {
                "name": "independent_expertise_number",
                "type": "DocTextField",
                "required": False,
                "max_length": 20,
                "min_length": 0
            },
            {
                "name": "independent_expertise_sum",
                "type": "DocDecimalField",
                "required": False
            },
            {
                "name": "pretension_answer_got",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "pretension_result",
                "type": "DocEnumField",
                "enum_cls": "PretensionResultEnum",
                "required": True
            },
            {
                "name": "make_lawsuit",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "insurance_returned_docs",
                "type": "DocArrayField",
                "cls": "DocEnumField",
                "subfield_kwargs": {
                    "enum_cls": "OsagoDocTypeEnum"
                },
                "required": False,
                "default": []
            },
            {
                "name": "moral_damages",
                "type": "DocDecimalField",
                "required": False,
                "default": 0
            },
            {
                "name": "notary_costs",
                "type": "DocDecimalField",
                "required": False,
                "default": 0
            },
            {
                "name": "insurance_lawsuit",
                "type": "DocArrayField",
                "cls": "DocEnumField",
                "subfield_kwargs": {
                    "enum_cls": "InsuranceLawsuitEnum"
                },
                "required": True,
                "min_length": 1
            },
            {
                "name": "lawsuit_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            },
            {
                "name": "first_claim_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": False
            },
            {
                "name": "compensation_got",
                "type": "DocDecimalField",
                "required": False,
            },
            {
                "name": "compensation_sum",
                "type": "DocDecimalField",
                "required": False
            },
            {
                "name": "compensation_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": False
            },
            {
                "name": "other_insurance",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "insurance_name",
                "type": "DocTextField",
                "required": False,
            },
            {
                "name": "insurance_id",
                "type": "DocTextField",
                "required": False,
                "min_length": 0,
                "max_length": 30
            },
            {
                "name": "use_other_submission_address",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "submission_address",
                "type": "DocTextField",
                "required": False,
            },
        ],
        "validators": [{
            "condition": {
                "#or": [{
                    "pretension_result": "partial_success",
                    "compensation_got": {
                        "#gt": 0
                    }
                }, {
                    "pretension_result": {
                        "#ne": "partial_success"
                    }
                }]
            },
            "error": {
                "field": "compensation_got",
                "code": 5
            }
        }, {
            "condition": {
                "#or": [{
                    "pretension_result": "partial_success",
                    "compensation_date": {
                        "#empty": False
                    }
                }, {
                    "pretension_result": "success",
                    "make_lawsuit": True,
                    "compensation_date": {
                        "#empty": False
                    }
                }, {
                    "#not": {
                        "#or": [{
                            "pretension_result": "partial_success"
                        }, {
                            "pretension_result": "success",
                            "make_lawsuit": True
                        }]
                    }
                }]
            },
            "error": {
                "field": "compensation_date",
                "code": 5
            }
        }, {
            "condition": {
                "#or": [{
                    "submission_way": "responsible_person",
                    "court_include": {
                        "#exists": True
                    }
                }, {
                    "submission_way": {
                        "#ne": "responsible_person"
                    }
                }]
            },
            "error": {
                "field": "court_include",
                "code": 4
            }
        }, {
            "condition": {
                "#or": [{
                    "lawsuit_submission_way": "responsible_person",
                    "responsible_person": {
                        "#empty": False
                    }
                }, {
                    "lawsuit_submission_way": {
                        "#ne": "responsible_person"
                    }
                }]
            },
            "error": {
                "field": "responsible_person",
                "code": 5
            }
        }, {
            "condition": {
                "#or": [{
                    "lawsuit_submission_way": "responsible_person",
                    "#not": {
                        "submission_way": "responsible_person",
                        "court_include": True,
                    },
                    "lawsuit_submission_responsible_person": {
                        "#empty": False
                    }
                }, {
                    "#not": {
                        "lawsuit_submission_way": "responsible_person",
                        "#not": {
                            "submission_way": "responsible_person",
                            "court_include": True,
                        },
                    }
                }]
            },
            "error": {
                "field": "lawsuit_submission_responsible_person",
                "code": 5
            }
        }]
    }

    OSAGO_LAWSUIT_TEMPLATE = {
        "template_name": "template_osago2_4",
        "file_name": _get_test_resource_name(config, "osago/isk.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_LAWSUIT
    }

    OSAGO_OSAGO_COURT_MAIL_LIST_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OSAGO_COURT_MAIL_LIST,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Опись для ценного письма",
        "conditions": {
            "lawsuit_submission_way": "mail"
        },
        "batch_statuses": ["claim"],
        "collections": ["claim_collection"],
        "fields": [
            {
                "name": "court_name",
                "type": "DocTextField",
                "max_length": 200,
                "required": True
            },
            {
                "name": "court_address",
                "type": "DocTextField",
                "max_length": 1024,
                "required": True
            },
            {
                "name": "lawsuit_submission_way",
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": True
            },
            RESULT_FIELDS_FIELD
        ]
    }

    OSAGO_OSAGO_COURT_MAIL_LIST_TEMPLATE = {
        "template_name": "template_osago2_4",
        "file_name": _get_test_resource_name(config, "osago/court_mail_list.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_OSAGO_COURT_MAIL_LIST
    }
    ################################################################################################################

    OSAGO_SCHEMA = {
        "doc_name": DocumentBatchTypeEnum.DBT_OSAGO,
        "fields": [
            {
                "name": "crash_date",           # дата аварии без времени в формате ISO_8601 — "2005-08-09T18:31:42"
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            },
            {
                "name": "policy_called",        # признак вызова ГИБДД на место проишествия
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "all_have_osago",       # признак наличия у всех полисов ОСАГО
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "own_insurance_company",# признак обращения в собственную страховую
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "have_osago",           # признак отсутствия полиса у конкретной стороны
                "type": "DocEnumField",
                "enum_cls": "CrashSubjectEnum",
                "required": False
            },
            {
                "name": "problem_type",         # тип проблемы: отказ или недоплата
                "type": "DocEnumField",
                "enum_cls": "OsagoReasonEnum",
                "required": False
            },
            {
                "name": "refusal_reason",       # причина отказа
                "type": "DocEnumField",
                "enum_cls": "OsagoRefusalReasonEnum",
                "required": False
            },
            {
                "name": "notice_has_mistakes",  # признак того, что в извещении были ошибки
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "got_cash",             # признак того, что страховая возместила деньгами
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "victim_owner", #идентификатор физического лица владельца пострадавшего автомобиля
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            },
            {
                "name": "owner_as_victim_driver", #(true/false) признак того, что владелец автомобиля был за рулем пострадавшей машины
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "victim_driver", #идентификатор физического лица водителя пострадавшего автомобиля
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "victim_car_brand", #марка пострадавшего автомобиля (строка, до 100 символов)
                "type": "DocTextField",
                "required": False,
                "max_length": 100
            },
            {
                "name": "victim_car_number", #автомобильный номер пострадавшего автомобиля (русские или латинские буквы и цифры, строка, до 10 символов)
                "type": "DocTextField",
                "required": False,
                "max_length": 15,
                "allowed_re": ur"^[0-9а-яА-Яa-zA-Z]*$"
            },
            {
                "name": "guilty_owner", #идентификатор физического лица владельца виновного автомобиля
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False},
                    "address": {"required": True}
                }
            },
            {
                "name": "owner_as_guilty_driver", #(true/false) признак того, что владелец автомобиля был за рулем виновной машины
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "guilty_driver", #идентификатор физического лица водителя виновного автомобиля
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "birthdate": {"required": False},
                    "birthplace": {"required": False}
                }
            },
            {
                "name": "guilty_car_brand", #марка виновного автомобиля (строка, до 100 символов)
                "type": "DocTextField",
                "required": False,
                "max_length": 100,
                "min_length": 0
            },
            {
                "name": "guilty_car_number", #автомобильный номер виновного автомобиля (русские или латинские буквы и цифры, строка, до 10 символов)
                "type": "DocTextField",
                "required": False,
                "max_length": 15,
                "min_length": 0,
                "allowed_re": ur"^[0-9а-яА-Яa-zA-Z]*$"
            },
            {
                "name": "other_victims", #массив других пострадавших
                "type": "DocArrayField",
                "cls": "CarWithDriver",
                "required": False
            },
            {
                "name": "insurance_company_region", #регион, в котором обращались за возмещением (см. субъекты РФ)
                "type": "DocEnumField",
                "enum_cls": "RFRegionsEnum",
                "required": False
            },
            {
                "name": "policy_series", #серия страхового полиса (строка, 3 символа)
                "type": "DocTextField",
                "required": False,
                "max_length": 3,
                "allowed_re": ur"^[0-9]*$",
                "min_length": 0
            },
            {
                "name": "policy_number", #номер полиса, по которому обращались в страховую (10 цифр)
                "type": "DocTextField",
                "required": False,
                "max_length": 10,
                "allowed_re": ur"^[0-9]*$",
                "min_length": 0
            },
            {
                "name": "other_insurance", #(true/false) признак ошибки автоматического определения страховой
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "insurance_name", # название страховой компании для подготовки претензии
                "type": "DocTextField",
                "required": False,
            },
            {
                "name": "insurance_id", # идентификатор страховой компании (строка до 20 символов)
                "type": "DocTextField",
                "required": False,
                "min_length": 0,
                "max_length": 30
            },
            {
                "name": "other_date", #(true/false) признак ошибки автоматического определения даты полиса
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "policy_date", #дата выдачи полиса ОСАГО без времени в формате ISO_8601 — "2005-08-09T18:31:42"
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": False
            },
            {
                "name": "first_claim_date", #дата первого заявления о наступлении аварии в формате ISO_8601 — "2005-08-09T18:31:42"
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": False
            },
            {
                "name": "independent_expertise_number", #номер незавизимой экспертизы (строка, до 20 символов)
                "type": "DocTextField",
                "required": False,
                "max_length": 20,
                "min_length": 0
            },
            {
                "name": "independent_expertise_sum", #ущерб, насчитанный независимой экспертизы (число с копейками — float)
                "type": "DocDecimalField",
                "required": True
            },
            {
                "name": "independent_expertise_cost", #стоимость независимой экспертизы (число с копейками — float)
                "type": "DocDecimalField",
                "required": True
            },
            {
                "name": "compensation_sum", #сумма компенсации от страховой (число с копейками — float)
                "type": "DocDecimalField",
                "required": True
            },
            {
                "name": "add_person_to_claim", #(true/false) добавить в иск физическое лицо
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "docs_got", #список документов на руках (значения: euro, act_crash, act_review, act_insurance, insurance_denial, insurance_repair_cost, police_act, police_statement, police_protocol)
                "type": "DocArrayField",
                "cls": "DocEnumField",
                "subfield_kwargs": {
                    "enum_cls": "OsagoDocTypeEnum"
                },
                "required": False,
                "default": []
            },
            {
                "name": "insurance_case_number", #номер страхового дела (до 20 цифр)
                "type": "DocTextField",
                "required": False,
                "max_length": 20,
                "min_length": 0
            },
            {
                "name": "submission_way", #способ подачи претензии в страховую (oneself, responsible_person, mail)
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": False
            },
            {
                "name": "submission_branch_id", # идентификатор филиала страховой для подачи претензии
                "type": "DocTextField",
                "required": False,
            },
            {
                "name": "use_other_submission_address", #(true/false) использовать другой адрес для подачи документов
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "submission_address", #адрес в России
                "type": "DocTextField",
                "required": False,
            },
            {
                "name": "obtain_way", #способ получения (oneself, responsible_person, mail)
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum",
                "required": False
            },
            {
                "name": "responsible_person", #идентификатор физического лица доверенного лица подающего (для подачи и/или полчуения через представителя)
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            },
            {
                "name": "court_include", #(true/false) признак включения представлений интересов в доверенность
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "obtain_address_type", #тип адрес, на который будет получен ответ (owner_address, responsible_person_address, other_address)
                "type": "DocEnumField",
                "enum_cls": "ObtainAddressEnum",
                "required": False
            },
            {
                "name": "obtain_address", #адрес в России
                "type": "DocTextField",
                "required": False
            },
            {
                "name": "bik_account", # БИК банка для перечисления средств
                "type": "DocTextField",
                "required": False,
                "min_length": 9,
                "allowed_re": ur"^[0-9]*$"
            },
            {
                "name": "account_number", # номер расчетного счета
                "type": "DocTextField",
                "required": False,
                "min_length": 20,
                "allowed_re": ur"^[0-9]*$"
            },
            {
                "name": "police_case",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "pretension_result", # —  результат поданной претензии (success, refuse, partial_success, unknown)
                "type": "DocEnumField",
                "enum_cls": "PretensionResultEnum"
            },
            {
                "name": "make_lawsuit", # — (true/false) признак подачи иска
                "type": "DocBoolField"
            },
            {
                "name": "compensation_got", # — сумма компенсации от страховой после претензии (число с копейками)
                "type": "DocDecimalField"
            },
            {
                "name": "compensation_date", # — дата перечисления компенсации без времени в формате ISO_8601 — "2005-08-09T18:31:42"
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d"
            },
            {
                "name": "pretension_answer_got", # — (true/false) признак того, что страховая прислала ответ на претензию
                "type": "DocBoolField"
            },
            {
                "name": "lawsuit_date", # — дата в иске без времени в формате ISO_8601 — "2005-08-09T18:31:42"
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d"
            },
            {
                "name": "insurance_lawsuit", #[] — список претензий в иске к страховой, значения:
                "type": "DocArrayField",
                "cls": "DocEnumField",
                "subfield_kwargs": {
                    "enum_cls": "InsuranceLawsuitEnum"
                }
            },
            {
                "name": "moral_damages", # — сумма для компенсации морального ущерба  (число с копейками)
                "type": "DocDecimalField"
            },
            {
                "name": "notary_costs", # — сумма нотариальных затрат  (число с копейками)
                "type": "DocDecimalField"
            },
            {
                "name": "home_court", # — (true/false) признак подачи иска по месту регистрации исца
                "type": "DocBoolField"
            },
            {
                "name": "court_name", # — наименование суда (до 200 символов)
                "type": "DocTextField",
                "max_length": 200
            },
            {
                "name": "court_address", # — адрес суда (до 1024 символов)
                "type": "DocTextField",
                "max_length": 1024
            },
            {
                "name": "lawsuit_submission_way", # — способ подачи документов в суд (oneself, mail, responsible_person)
                "type": "DocEnumField",
                "enum_cls": "ApplicationTypeEnum"
            },
            {
                "name": "lawsuit_submission_responsible_person", # —  идентификатор физического лица доверенного лица, подающего иск
                "type": "db_object",
                "cls": "PrivatePerson"
            },
            {
                "name": "insurance_returned_docs", #[] — список до сих пор не полученных документов (см. выше docs_got)
                "type": "DocArrayField",
                "cls": "DocEnumField",
                "subfield_kwargs": {
                    "enum_cls": "OsagoDocTypeEnum"
                }
            },
            {
                "name": "court_attendance", # — кто будет присутствовать на суде (oneself/nobody/responsible_person)
                "type": "DocEnumField",
                "enum_cls": "CourtAttendanceEnum"
            },
            {
                "name": "attached_to_lawsuit_docs_pagecount", #[] — список документов с количеством страниц
                "type": "DocArrayField",
                "cls": "DocLawSuitDocPageCount"
            },
            {
                "name": "lawsuit_number", # — номер судебного дела (до 20 символов)
                "type": "DocTextField",
                "min_length": 1,
                "max_length": 20
            },
            {
                "name": "insurance_execution_act_responsible_person", # — (true/false) признак того, что ИЛ к страховой надо выдать на представителю
                "type": "DocBoolField"
            },
            {
                "name": "insurance_execution_act_obtain_way", # — способ получения ИЛ к страховой (oneself, mail, responsible_person, no_obtain)
                "type": "DocEnumField",
                "enum_cls": "ActObtainWayEnum"
            },
            {
                "name": "guilty_execution_act_responsible_person", # — (true/false) признак того, что ИЛ к виновнику надо выдать на представителю
                "type": "DocBoolField"
            },
            {
                "name": "guilty_execution_act_obtain_way", # — способ получения ИЛ к виновнику (oneself, mail, responsible_person, no_obtain)
                "type": "DocEnumField",
                "enum_cls": "ActObtainWayEnum"
            }
        ]
    }

    ALSV = {
        "#max": [{
            "#value": 0
        }, {
            "#sub": [{
                "#field": "independent_expertise_sum"
            }, {
                "#cases": {
                    "list": [{
                        "conditions": {
                            "policy_called": True
                        },
                        "value": {
                            "#cases": {
                                "set": {
                                    "datetime_01_10_2014": {
                                        "#datetime": {"year": 2014, "month": 10, "day": 1}
                                    }
                                },
                                "list": [{
                                    "conditions": {
                                        "policy_date": {
                                            "#lt": "@datetime_01_10_2014"
                                        }
                                    },
                                    'value': {"#value": 120000}
                                }],
                                "default": {"value": {"#value": 400000}}
                            }
                        }
                    }],
                    "default": {
                        "value": {
                            "#cases": {
                                "set": {
                                    "datetime_01_10_2014": {
                                        "#datetime": {"year": 2014, "month": 10, "day": 1}
                                    }
                                },
                                "list": [{
                                    "conditions": {
                                        "policy_date": {
                                            "#lt": "@datetime_01_10_2014"
                                        }
                                    },
                                    'value': {"#value": 25000}
                                }],
                                "default": {"value": {"#value": 50000}}
                            }
                        }
                    }
                }
            }]
        }]
    }

    LFV = {
        "#cases": {
            "set": {
                "_above_limits_sum": ALSV
            },
            "list": [{
                "conditions": {
                    "_above_limits_sum": {
                        "#lte": 20000
                    }
                },
                "value": {                  # max(0,04 * above_limits_sum, 400);
                    "#max": [{
                        "#mul": [{
                            "#value": 0.04
                        }, {
                            "#field": "_above_limits_sum"
                        }]
                    }, {
                        "#value": 400
                    }]
                }
            }, {
                "conditions": {
                    "_above_limits_sum": {
                        "#gt": 20000,
                        "#lte": 100000
                    }
                },
                "value": {                  # 800 + 0,03 * (above_limits_sum - 20 000);
                    "#sum": [{
                        "#value": 800
                    }, {
                        "#mul": [{
                            "#value": 0.03
                        }, {
                            "#sub": [{
                                "#field": "_above_limits_sum"
                            }, {
                                "#value": 20000
                            }]
                        }]
                    }]
                }
            }, {
                "conditions": {
                    "_above_limits_sum": {
                        "#gt": 100000,
                        "#lte": 200000
                    }
                },
                "value": {                  # 3 200 + 0,02 * (above_limits_sum - 100 000);
                    "#sum": [{
                        "#value": 3200
                    }, {
                        "#mul": [{
                            "#value": 0.02
                        }, {
                            "#sub": [{
                                "#field": "_above_limits_sum"
                            }, {
                                "#value": 100000
                            }]
                        }]
                    }]
                }
            }, {
                "conditions": {
                    "_above_limits_sum": {
                        "#gt": 200000,
                        "#lte": 1000000
                    }
                },
                "value": {                  # 5 200 + 0,01 * (above_limits_sum - 200 000);
                    "#sum": [{
                        "#value": 5200
                    }, {
                        "#mul": [{
                            "#value": 0.01
                        }, {
                            "#sub": [{
                                "#field": "_above_limits_sum"
                            }, {
                                "#value": 200000
                            }]
                        }]
                    }]
                }
            }],
            "default": {
                "value": {                  # min(13 200 + 0,005 * (above_limits_sum - 1 000 000), 60 000 рублей);
                    "#min": [{
                        "#sum": [{
                            "#value": 13200
                        }, {
                            "#mul": [{
                                "#value": 0.005
                            }, {
                                "#sub": [{
                                    "#field": "_above_limits_sum"
                                }, {
                                    "#value": 1000000
                                }]
                            }]
                        }]
                    }, {
                        "#value": 60000
                    }]
                }
            }
        }
    }

    _2_if_add_person_to_claim_else_1 = {
        "#cases": {
            "list": [
                {"conditions": {"add_person_to_claim": False}, "value": 1},
            ],
            "default": 2
        }
    }

    get_lawsuit_doc_page_count = lambda doc_name: {
        "#sum": [{
            "#value": 0
        }, {
            "#aggregate": {
                "field": {
                    "#array_mapping": {
                        "array_source_field": {
                            "#field": "attached_to_lawsuit_docs_pagecount"
                        },
                        "filter": {
                            "<loop_item>->page": doc_name
                        }
                    }

                },
                "attr": "pagecount",
                "operator": "add"
            }
        }]
    }

    OSAGO_RESULT_FIELDS = [
        UNDERPAY_SUM_FIELD,
        {
            "name": "above_limits_sum",
            "type": "calculated",
            "required": False,
            "field_type": "DocDecimalField",
            "suppress_validation_errors": True,
            "value": ALSV
        },
        {
            "name": "insurance_name",   # название страховой компании для подготовки претензии
            "type": "DocTextField",
            "required": False,
        },
        {
            "name": "insurance_id",     # идентификатор страховой компании (строка до 20 символов)
            "type": "DocTextField",
            "required": False,
            "min_length": 1,
            "max_length": 30
        },
        {
            "name": "policy_date",      #дата выдачи полиса ОСАГО без времени в формате ISO_8601 — "2005-08-09T18:31:42"
            "type": "DocDateTimeField",
            "input_format": "%Y-%m-%d",
            "required": False
        },
        {
            "name": "region_prepositional",
            "type": "calculated",
            "field_type": "DocTextField",
            'value': {
                "#morpher": {
                    "word": "@insurance_company_region",
                    "case": "pra"                       # предложный падеж
                }
            }
        }, {
            "name": "responsible_person_dative",
            "type": "calculated",
            "field_type": "DocTextField",
            'value': {
                "#morpher": {
                    "word": {
                        "#field": "responsible_person->full_name"
                    },
                    "case": "dat"                       # дательный падеж
                }
            }
        },
        {
            "name": "region",
            "type": "calculated",
            "field_type": "DocEnumField",
            "enum_cls": "RFRegionsEnum",
            "required": False,
            "value": {
                "#field": "insurance_company_region"
                # "#cases": {
                #     "set": {
                #         "db_submission_address": {
                #             "#fetch_db_table_row": {
                #                 "table_name": "car_assurance_branch",
                #                 "id": "@submission_branch_id",
                #                 "field_name": "address"
                #             }
                #         }
                #     },
                #     "list": [{
                #         "conditions": {
                #             "use_other_submission_address": True
                #         },
                #         "value": {
                #             "#field": "submission_address->region"
                #         }
                #     }],
                #     "default": {
                #         "value": {
                #             "#field": "db_submission_address->region"
                #         }
                #     }
                # }
            }
        },
        {
            "name": "limits_sum",
            "type": "calculated",
            "required": False,
            "field_type": "DocDecimalField",
            "suppress_validation_errors": True,
            "value": {
                "#cases": {
                    "list": [{
                        "conditions": {
                            "policy_called": True
                        },
                        "value": {
                            "#cases": {
                                "set": {
                                    "datetime_01_10_2014": {
                                        "#datetime": {"year": 2014, "month": 10, "day": 1}
                                    }
                                },
                                "list": [{
                                    "conditions": {
                                        "policy_date": {
                                            "#lt": "@datetime_01_10_2014"
                                        }
                                    },
                                    'value': {"#value": 120000}
                                }],
                                "default": {"value": {"#value": 400000}}
                            }
                        }
                    }],
                    "default": {
                        "value": {
                            "#cases": {
                                "set": {
                                    "datetime_01_10_2014": {
                                        "#datetime": {"year": 2014, "month": 10, "day": 1}
                                    }
                                },
                                "list": [{
                                    "conditions": {
                                        "policy_date": {
                                            "#lt": "@datetime_01_10_2014"
                                        }
                                    },
                                    'value': {"#value": 25000}
                                }],
                                "default": {"value": {"#value": 50000}}
                            }
                        }
                    }
                }
            }
        },
        {
            "name": "legal_fee",
            "type": "calculated",
            "required": False,
            "field_type": "DocDecimalField",
            "value": LFV
        },
        {
            "name": "insurance_penalty",
            "type": "calculated",
            "required": False,
            "field_type": "DocDecimalField",
            "depends_on": ["underpay_sum"],
            "value": {
                "#max": [{
                    "#value": 0
                }, {
                    "#cases": {
                        "set": {
                            "_count_days": {
                                "#cases": {
                                    "set": {
                                        "_lawsuit_date_or_today": {
                                            "#cases": {
                                                "list": [{
                                                    "conditions": {"lawsuit_date": {"#empty": True}},
                                                    "value": {"#datetime": "#now"}
                                                }],
                                                "default": {"value": {"#field": "lawsuit_date"}}
                                            }
                                        },
                                        "_first_claim_date_or_today": {
                                            "#cases": {
                                                "list": [{
                                                    "conditions": {"first_claim_date": {"#empty": True}},
                                                    "value": {"#datetime": "#now"}
                                                }],
                                                "default": {"value": {"#field": "first_claim_date"}}
                                            }
                                        },
                                        "_compensation_date_or_today": {
                                            "#cases": {
                                                "list": [{
                                                    "conditions": {"compensation_date": {"#empty": True}},
                                                    "value": {"#datetime": "#now"}
                                                }],
                                                "default": {"value": {"#field": "compensation_date"}}
                                            }
                                        }
                                    },
                                    "list": [{
                                        "conditions": {
                                            "pretension_result": "success",
                                            "make_lawsuit": True
                                        },
                                        "value": {
                                            "#sub": [{
                                                "#field": "_compensation_date_or_today"
                                            }, {
                                                "#field": "_first_claim_date_or_today"
                                            }, {
                                                "#timedelta": {
                                                    "days": 20
                                                }
                                            }]
                                        }
                                    }],
                                    "default": {
                                        "value": {
                                            "#sub": [{
                                                "#field": "_lawsuit_date_or_today"
                                            }, {
                                                "#field": "_first_claim_date_or_today"
                                            }, {
                                                "#timedelta": {
                                                    "days": 20
                                                }
                                            }]
                                        }
                                    }
                                }
                            },
                            "_count_days_compensation": {
                                "#cases": {
                                    "set": {
                                        "_compensation_date_or_today": {
                                            "#cases": {
                                                "list": [{
                                                    "conditions": {"compensation_date": {"#empty": True}},
                                                    "value": {"#datetime": "#now"}
                                                }],
                                                "default": {"value": {"#field": "compensation_date"}}
                                            }
                                        }
                                    },
                                    "list": [{
                                        "conditions": {
                                            "first_claim_date": {"#empty": True}
                                        },
                                        "value": {"#timedelta": {"days": 0}}
                                    }],
                                    "default": {
                                        "value": {
                                            "#sub": [{
                                                "#field": "_compensation_date_or_today"
                                            }, {
                                                "#field": "first_claim_date"
                                            }, {
                                                "#timedelta": {
                                                    "days": 20
                                                }
                                            }]
                                        }
                                    }
                                }
                            },
                            "_lawsuit_date_sub_compensation_date": {
                                "#cases": {
                                    "set": {
                                        "_compensation_date_or_today": {
                                            "#cases": {
                                                "list": [{
                                                    "conditions": {"compensation_date": {"#empty": True}},
                                                    "value": {"#datetime": "#now"}
                                                }],
                                                "default": {"value": {"#field": "compensation_date"}}
                                            }
                                        },
                                        "_lawsuit_date_or_today": {
                                            "#cases": {
                                                "list": [{
                                                    "conditions": {"lawsuit_date": {"#empty": True}},
                                                    "value": {"#datetime": "#now"}
                                                }],
                                                "default": {"value": {"#field": "lawsuit_date"}}
                                            }
                                        },
                                    },
                                    "list": [],
                                    "default": {
                                        "value": {
                                            "#sub": [{"#field": "_lawsuit_date_or_today"}, {"#field": "_compensation_date_or_today"}]
                                        }
                                    }
                                }

                            }
                        },
                        "list": [{
                            "conditions": {
                                "compensation_got": {"#gt": 0},
                                "pretension_result": "partial_success"
                            },
                            "value": {
                                "#sum": [{
                                    "#mul": [{
                                        "#value": 0.01
                                    }, {
                                        "#field": "underpay_sum"
                                    }, {
                                        "#field": "_count_days_compensation->days"
                                    }]
                                }, {
                                    "#mul": [{
                                        "#value": 0.01
                                    }, {
                                        "#sub": [{
                                            "#field": "underpay_sum"
                                        }, {
                                            "#field": "compensation_got"
                                        }]
                                    }, {
                                        "#field": "_lawsuit_date_sub_compensation_date->days"
                                    }]
                                }]
                            }
                        }],
                        "default": {
                            "value": {
                                "#mul": [{
                                    "#value": 0.01
                                }, {
                                    "#field": "underpay_sum"
                                }, {
                                    "#field": "_count_days->days"
                                }]
                            }
                        }
                    }
                }]
            }
        },
        {
            "name": "lawsuit_cost",
            "type": "calculated",
            "required": False,
            "field_type": "DocDecimalField",
            "depends_on": ["insurance_penalty", "legal_fee", "above_limits_sum", "underpay_sum"],
            "value": {
                "#sum": [{
                    "#cases": {
                        "list": [{
                            "conditions": {
                                "insurance_underpay_lawsuit": {
                                    "#in": "@insurance_lawsuit"
                                }
                            },
                            "value": {
                                "#cases": {
                                    "list": [{
                                        "conditions": {
                                            "compensation_got": {
                                                "#gt": 0
                                            },
                                            "pretension_result": "partial_success"
                                        },
                                        "value": {
                                            "#sub": [{
                                                "#field": "underpay_sum"
                                            }, {
                                                "#field": "compensation_got"
                                            }]
                                        }
                                    }],
                                    "default": {
                                        "value": {
                                            "#cases": {
                                                "list": [{
                                                    "conditions": {
                                                        "pretension_result": "success",
                                                        "make_lawsuit": True
                                                    },
                                                    "value": {
                                                        "#value": 0
                                                    }
                                                }],
                                                "default": {
                                                    "value": {
                                                        "#field": "underpay_sum"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }],
                        "default": {
                            "value": {"#value": 0}
                        }
                    }
                }, {
                    "#cases": {
                        "list": [{
                            "conditions": {
                                "insurance_penalty_lawsuit": {
                                    "#in": "@insurance_lawsuit"
                                }
                            },
                            "value": {
                                "#field": "insurance_penalty"
                            }
                        }],
                        "default": {
                            "value": {"#value": 0}
                        }
                    }
                }, {
                    "#cases": {
                        "list": [{
                            "conditions": {
                                "insurance_expertise_cost_lawsuit": {
                                    "#in": "@insurance_lawsuit"
                                }
                            },
                            "value": {
                                "#field": "independent_expertise_cost"
                            }
                        }],
                        "default": {
                            "value": {"#value": 0}
                        }
                    }
                }, {
                    "#cases": {
                        "list": [{
                            "conditions": {
                                "moral_damages": {
                                    "#gt": 0
                                }
                            },
                            "value": {
                                "#field": "moral_damages"
                            }
                        }],
                        "default": {
                            "value": {"#value": 0}
                        }
                    }
                }, {
                    "#cases": {
                        "list": [{
                            "conditions": {
                                "notary_costs": {
                                    "#gt": 0
                                }
                            },
                            "value": {
                                "#field": "notary_costs"
                            }
                        }],
                        "default": {
                            "value": {"#value": 0}
                        }
                    }
                }, {
                    "#cases": {
                        "list": [{
                            "conditions": {
                                "add_person_to_claim": True
                            },
                            "value": {
                                "#sum": [{
                                    "#field": "legal_fee"
                                }, {
                                    "#field": "above_limits_sum"
                                }]
                            }
                        }],
                        "default": {
                            "value": {"#value": 0}
                        }
                    }
                }]
            }
        },
        {
            "name": "insufficient_docs",
            "type": "calculated",
            "field_type": "DocArrayField",
            "required": False,
            "cls": "DocEnumField",
            "subfield_kwargs": {
                "enum_cls": "OsagoDocTypeEnum"
            },
            "value": {
                "#array_mapping": {
                    "source_array": REQUIRED_DOCS_FIELD,
                    "filter": [{
                        "#not": {
                            "<loop_item>": OsagoDocTypeEnum.ODT_ACT_INSURANCE_CASE,
                            "problem_type": {"#ne": "underpay"}
                        }
                    }]
                }
            }
        },
        {
            "name": "attached_to_lawsuit_docs",
            "type": "calculated",
            "field_type": "DocArrayField",
            "required": False,
            "cls": "DocEnumField",
            "subfield_kwargs": {
                "enum_cls": "OsagoDocTypeEnum"
            },
            "value": {
                "#make_array": [{
                    "value": "inquire_crash",
                    "conditions": {
                        "#or": [{
                            "inquire_crash": {
                                "#in": "@docs_got"
                            }
                        }, {
                            "inquire_crash": {
                                "#in": "@insurance_returned_docs"
                            }
                        }]
                    }
                }, {
                    "value": "notice_crash",
                    "conditions": {
                        "#or": [{
                            "notice_crash": {
                                "#in": "@docs_got"
                            }
                        }, {
                            "notice_crash": {
                                "#in": "@insurance_returned_docs"
                            }
                        }]
                    }
                }, {
                    "value": "act_insurance_case",
                    "conditions": {
                        "#or": [{
                            "act_insurance_case": {
                                "#in": "@docs_got"
                            }
                        }, {
                            "act_insurance_case": {
                                "#in": "@insurance_returned_docs"
                            }
                        }]
                    }
                }, {
                    "value": "insurance_denial",
                    "conditions": {
                        "#or": [{
                            "insurance_denial": {
                                "#in": "@docs_got"
                            }
                        }, {
                            "insurance_denial": {
                                "#in": "@insurance_returned_docs"
                            }
                        }],
                        "problem_type": "refusal"
                    }
                }, {
                    "value": "police_statement",
                    "conditions": {
                        "#or": [{
                            "police_statement": {
                                "#in": "@docs_got"
                            }
                        }, {
                            "police_statement": {
                                "#in": "@insurance_returned_docs"
                            }
                        }],
                        "police_case": True
                    }
                }, {
                    "value": "police_protocol",
                    "conditions": {
                        "#or": [{
                            "police_protocol": {
                                "#in": "@docs_got"
                            }
                        }, {
                            "police_protocol": {
                                "#in": "@insurance_returned_docs"
                            }
                        }]
                    }
                }, {
                    "value": "case_init_refusal",
                    "conditions": {
                        "#or": [{
                            "case_init_refusal": {
                                "#in": "@docs_got"
                            }
                        }, {
                            "case_init_refusal": {
                                "#in": "@insurance_returned_docs"
                            }
                        }],
                        "police_case": False
                    }
                }, {
                    "value": "pretension_answer",
                    "conditions": {
                        "pretension_answer_got": True
                    }
                }, {
                    "value": "notary_pay_act",
                    "conditions": {
                        "notary_costs": {
                            "#gt": 0
                        }
                    }
                }, {
                    "value": "bank_statement",
                    "conditions": {
                        "#or": [{
                            "problem_type":"underpay",
                        }, {
                            "pretension_result": "partial_success",
                        }, {
                            "pretension_result": "success"
                        }]
                    }
                },
                    "policy_osago",
                    "expertise_contract",
                    "expertise_report"]
            }
        }, {
            "name": "court_lawsuit_docs",
            "type": "calculated",
            "field_type": "DocArrayField",
            "cls": "CourtLawsuitDocInfo",
            "depends_on": ["add_person_to_claim","attached_to_lawsuit_docs", "insufficient_docs"],
            "value": {
                "#make_array": [{
                    '#object': {
                        "doc_name": "lawsuit",
                        "originals": 1,
                        "copies": {
                            "#cases": {
                                "list": [
                                    {"conditions": {"add_person_to_claim": False, "lawsuit_submission_way": "mail"}, "value": 1},
                                    {"conditions": {"add_person_to_claim": True, "lawsuit_submission_way": {"#ne": "mail"}}, "value": 3},
                                ],
                                "default": 2
                            }
                        },
                        "title": u"Исковое заявление"
                    },
                }, {
                    "conditions": {
                        "court_attendance": "nobody"
                    },
                    "value": {
                        '#object': {
                            "doc_name": "claim_court_absent",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Заявление об отсутствии на заседании",
                            "pagecount": 1
                        }
                    }
                }, {
                    "conditions": {
                        "lawsuit_submission_way": "mail"
                    },
                    "value": {
                        '#object': {
                            "doc_name": "victim_owner_passport_copy",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Нотариально заверенная копия паспорта владельца авто",
                            "pagecount": 0      # not needed
                        }
                    }
                }, {
                    "conditions": {
                        "inquire_crash": {"#in": "@attached_to_lawsuit_docs"}
                    },
                    "value": {
                        '#object': {
                            "doc_name": "inquire_crash",
                            "originals": 1,
                            "copies": _2_if_add_person_to_claim_else_1,
                            "title": u"Справка о дорожно-транспортном происшествии",
                            "pagecount": get_lawsuit_doc_page_count("inquire_crash")
                        }
                    }
                }, {
                    "conditions": {
                        "police_protocol": {"#in": "@attached_to_lawsuit_docs"}
                    },
                    "value": {
                        '#object': {
                            "doc_name": "police_protocol",
                            "originals": 1,
                            "copies": _2_if_add_person_to_claim_else_1,
                            "title": u"Протокол об административном правонарушении",
                            "pagecount": get_lawsuit_doc_page_count("police_protocol")
                        }
                    }
                }, {
                    "conditions": {
                        "police_statement": {"#in": "@attached_to_lawsuit_docs"}
                    },
                    "value": {
                        '#object': {
                            "doc_name": "police_statement",
                            "originals": 1,
                            "copies": _2_if_add_person_to_claim_else_1,
                            "title": u"Постановление по делу об административном правонарушении",
                            "pagecount": get_lawsuit_doc_page_count("police_statement")
                        }
                    }
                }, {
                    "conditions": {
                        "case_init_refusal": {"#in": "@attached_to_lawsuit_docs"}
                    },
                    "value": {
                        '#object': {
                            "doc_name": "case_init_refusal",
                            "originals": 1,
                            "copies": _2_if_add_person_to_claim_else_1,
                            "title": u"Определение об отказе в возбуждении дела об административном правонарушении",
                            "pagecount": get_lawsuit_doc_page_count("case_init_refusal")
                        }
                    }
                }, {
                    "conditions": {
                        "notice_crash": {"#in": "@attached_to_lawsuit_docs"}
                    },
                    "value": {
                        '#object': {
                            "doc_name": "notice_crash",
                            "originals": 1,
                            "copies": _2_if_add_person_to_claim_else_1,
                            "title": u"Извещение о дорожно-транспортном происшествии",
                            "pagecount": get_lawsuit_doc_page_count("notice_crash")
                        }
                    }
                }, {
                    "conditions": {
                        "insurance_denial": {"#in": "@attached_to_lawsuit_docs"}
                    },
                    "value": {
                        '#object': {
                            "doc_name": "insurance_denial",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Отказ в выплате страхового возмещения",
                            "pagecount": get_lawsuit_doc_page_count("insurance_denial")
                        }
                    }
                }, {
                    "conditions": {
                        "act_insurance_case": {"#in": "@attached_to_lawsuit_docs"}
                    },
                    "value": {
                        '#object': {
                            "doc_name": "act_insurance_case",
                            "originals": 1,
                            "copies": _2_if_add_person_to_claim_else_1,
                            "title": u"Акт о страховом случае",
                            "pagecount": get_lawsuit_doc_page_count("act_insurance_case")
                        }
                    }
                }, {
                    '#object': {
                        "doc_name": "expertise_report",
                        "originals": 1,
                        "copies": _2_if_add_person_to_claim_else_1,
                        "title": {
                            "#sum": [{
                                "#value": u"Отчет независимой экспертизы №"
                            }, {
                                "#field": "independent_expertise_number"
                            }]
                        },
                        "pagecount": get_lawsuit_doc_page_count("expertise_report")
                    },
                }, {
                    '#object': {
                        "doc_name": "expertise_contract",
                        "originals": 1,
                        "copies": _2_if_add_person_to_claim_else_1,
                        "title": u"Договор о проведении независимой экспертизы",
                        "pagecount": get_lawsuit_doc_page_count("expertise_contract")
                    },
                }, {
                    '#object': {
                        "doc_name": "expertise_receipt",
                        "originals": 1,
                        "copies": _2_if_add_person_to_claim_else_1,
                        "title": u"Квитанция об оплате независимой экспертизы",
                        "pagecount": 0      # not needed
                    },
                }, {
                    "conditions": {
                        "submission_way": "mail"
                    },
                    "value": {
                        '#object': {
                            "doc_name": "pretension_mail_receipt",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Квитанция об оплате почтового отправления (претензии) в страховую",
                            "pagecount": 0      # not needed
                        }
                    }
                }, {
                    "conditions": {
                        "submission_way": "mail"
                    },
                    "value": {
                        '#object': {
                            "doc_name": "pretension_mail_list",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Опись документов, направленных в страховую (с отметкой почты)",
                            "pagecount": {
                                "#rendered_doc_count": "osago_mail_list"
                            }
                        }
                    }
                }, {
                    "conditions": {
                        "submission_way": "mail"
                    },
                    "value": {
                        '#object': {
                            "doc_name": "pretension_mail_notify",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Уведомление о вручении почтового отправления (претензии) с подтверждением получения",
                            "pagecount": 0      # not needed
                        }
                    }
                }, {
                    "conditions": {
                        "submission_way": "mail"
                    },
                    "value": {
                        '#object': {
                            "doc_name": "pretension",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Подписаный экземпляр претензии в страховую",
                            "pagecount": {
                                "#rendered_doc_count": "osago_pretension"
                            }
                        }
                    }
                }, {
                    "conditions": {
                        "submission_way": {"#ne": "mail"}
                    },
                    "value": {
                        '#object': {
                            "doc_name": "pretension_insurance_note",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Претензия  с отметкой страховой о получении",
                            "pagecount": {
                                "#rendered_doc_count": "osago_pretension"
                            }
                        }
                    }
                }, {
                    "conditions": {
                        "submission_way": "mail",
                        "insufficient_docs": {
                            "#not_empty": True
                        }
                    },
                    "value": {
                        '#object': {
                            "doc_name": "documents_claim",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Подписанный экземпляр заявления в страховую о выдаче документов",
                            "pagecount": {
                                "#rendered_doc_count": "osago_documents_claim"
                            }
                        }
                    }
                }, {
                    "conditions": {
                        "submission_way": {"#ne": "mail"},
                        "insufficient_docs": {
                            "#not_empty": True
                        }
                    },
                    "value": {
                        '#object': {
                            "doc_name": "documents_claim_insurance_note",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Заявление в страховую о выдаче документов с отметкой страховой о получении",
                            "pagecount": {
                                "#rendered_doc_count": "osago_documents_claim"
                            }
                        }
                    }
                }, {
                    "conditions": {
                        "pretension_answer_got": True
                    },
                    "value": {
                        '#object': {
                            "doc_name": "pretension_answer",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Ответ страховой на претензию",
                            "pagecount": get_lawsuit_doc_page_count("pretension_answer")
                        }
                    }
                }, {
                    '#object': {
                        "doc_name": "policy_osago_copy",
                        "originals": 0,
                        "copies": _2_if_add_person_to_claim_else_1,
                        "title": u"Копия полиса ОСАГО",
                        "pagecount": get_lawsuit_doc_page_count("policy_osago")
                    },
                }, {
                    '#object': {
                        "doc_name": "car_certificate",
                        "originals": 1,
                        "copies": 0,
                        "title": u"Свидетельство о регистрации ТС",
                        "pagecount": 0      # not needed
                    },
                }, {
                    '#object': {
                        "doc_name": "car_passport",
                        "originals": 1,
                        "copies": 0,
                        "title": u"Паспорт ТС",
                        "pagecount": 0      # not needed
                    },
                }, {
                    "conditions": {
                        "add_person_to_claim": True
                    },
                    "value": {
                        '#object': {
                            "doc_name": "legal_fee_receipt",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Квитанция об оплате государственной пошлины за суд",
                            "pagecount": 0      # not needed
                        }
                    }
                }, {
                    "conditions": {
                        "lawsuit_submission_way": "responsible_person"
                    },
                    "value": {
                        '#object': {
                            "doc_name": "trust_court_representation",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Нотариально заверенная доверенность на представительство в суде",
                            "pagecount": 0      # not needed
                        }
                    }
                }, {
                    "conditions": {
                        "submission_way": "responsible_person"
                    },
                    "value": {
                        '#object': {
                            "doc_name": "trust_submision_obtain_docs",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Нотариально заверенная доверенность на представительство в страховой",
                            "pagecount": 0      # not needed
                        }
                    }
                }, {
                    "conditions": {
                        "submission_way": "responsible_person",
                        "court_include": True
                    },
                    "value": {
                        '#object': {
                            "doc_name": "trust_insurance_court",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Нотариально заверенная доверенность на представительство в страховой и в суде",
                            "pagecount": 0      # not needed
                        }
                    }
                }, {
                    "conditions": {
                        "lawsuit_submission_way": "mail"
                    },
                    "value": {
                        '#object': {
                            "doc_name": "mail_docs_list",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Опись документов, которые направляются в суд, с отметкой почты",
                            "pagecount": 1      # todo!!!
                        }
                    }
                }, {
                    "conditions": {
                        "#or": [{
                            "problem_type": "underpay"
                        }, {
                            "compensation_got": {
                                "#gt": 0
                            }
                        }]
                    },
                    "value": {
                        '#object': {
                            "doc_name": "bank_statement",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Банковские документы, подтверждающие оплату страхового возмещения",
                            "pagecount": get_lawsuit_doc_page_count("bank_statement")
                        }
                    }
                }, {
                    "conditions": {
                        "notary_costs": {
                            "#gt": 0
                        }
                    },
                    "value": {
                        '#object': {
                            "doc_name": "notary_pay_act",
                            "originals": 1,
                            "copies": 0,
                            "title": u"Документы, подтверждающие оплату нотариальных услуг",
                            "pagecount": get_lawsuit_doc_page_count("notary_pay_act")
                        }
                    }
                }]
            }
        }
    ]

    OSAGO_ACTIONS = {
        'set_policy_info': {
            'plugin': 'batch_manager',
            'action': 'set_result_fields',
            'config': {
                'field_name_map': {
                    'insurance_id': 'insurance_id',
                    'insurance_name': 'insurance_name',
                    'policy_date': 'policy_date'
                }
            }
        },
        'generate_first_stage_docs': {
            'plugin': 'doc_builder',
            'action': 'render_group',
            'config': {
                'doc_types': [
                    DocumentTypeEnum.DT_OSAGO_MAIL_LIST,
                    DocumentTypeEnum.DT_OSAGO_PRETENSION,
                    DocumentTypeEnum.DT_OSAGO_DOCUMENTS_CLAIM,
                    DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISSION_DOCS,
                    DocumentTypeEnum.DT_OSAGO_TRUST_OBTAIN_DOCS,
                    DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISION_OBTAIN_DOCS
                ]
            }
        },
        'generate_second_stage_docs': {
            'plugin': 'doc_builder',
            'action': 'render_group',
            'config': {
                'doc_types': [
                    DocumentTypeEnum.DT_OSAGO_CLAIM_COURT_ABSENT,
                    DocumentTypeEnum.DT_OSAGO_LAWSUIT,
                    DocumentTypeEnum.DT_OSAGO_COURT_MAIL_LIST
                ]
            }
        },
        'generate_third_stage_docs': {
            'plugin': 'doc_builder',
            'action': 'render_group',
            'config': {
                'doc_types': [
                    DocumentTypeEnum.DT_OSAGO_CLAIM_ALL_EXECUTION_ACT,
                    DocumentTypeEnum.DT_OSAGO_CLAIM_GUILTY_EXECUTION_ACT,
                    DocumentTypeEnum.DT_OSAGO_CLAIM_INSURANCE_EXECUTION_ACT
                ]
            }
        },
        'get_policy_info_first_try': {
            'plugin': 'car_assurance',
            'action': 'get_policy_info_first_try',
            'config': {
                'policy_series_field_name': 'policy_series',
                'policy_number_field_name': 'policy_number'
            }
        },
        'get_policy_info_async': {
            'plugin': 'car_assurance',
            'action': 'get_policy_info_async',
            'config': {
                'policy_series_field_name': 'policy_series',
                'policy_number_field_name': 'policy_number'
            }
        },
        'reset_policy_info': {
            'plugin': 'batch_manager',
            'action': 'reset_result_fields',
            'config': {
                'fields': ['insurance_id', 'insurance_name', 'policy_date']
            }
        },
        'touch': {
            'plugin': 'batch_manager',
            'action': 'touch',
            'config': {}
        },
        'check_and_fix_payments': {
            'plugin': 'batch_manager',
            'action': 'check_and_fix_osago_payments',
            'config': {}
        },
        'remove_pretension_documents': {
            'plugin': 'batch_manager',
            'action': 'remove_documents',
            'config': {
                'doc_types': [
                    DocumentTypeEnum.DT_OSAGO_MAIL_LIST,
                    DocumentTypeEnum.DT_OSAGO_PRETENSION,
                    DocumentTypeEnum.DT_OSAGO_DOCUMENTS_CLAIM,
                    DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISSION_DOCS,
                    DocumentTypeEnum.DT_OSAGO_TRUST_OBTAIN_DOCS,
                    DocumentTypeEnum.DT_OSAGO_TRUST_SUBMISION_OBTAIN_DOCS
                ]
            }
        },
        'remove_claim_documents': {
            'plugin': 'batch_manager',
            'action': 'remove_documents',
            'config': {
                'doc_types': [
                    DocumentTypeEnum.DT_OSAGO_CLAIM_COURT_ABSENT,
                    DocumentTypeEnum.DT_OSAGO_LAWSUIT,
                    DocumentTypeEnum.DT_OSAGO_COURT_MAIL_LIST
                ]
            }
        },
        'remove_court_documents': {
            'plugin': 'batch_manager',
            'action': 'remove_documents',
            'config': {
                'doc_types': [
                    DocumentTypeEnum.DT_OSAGO_CLAIM_ALL_EXECUTION_ACT,
                    DocumentTypeEnum.DT_OSAGO_CLAIM_GUILTY_EXECUTION_ACT,
                    DocumentTypeEnum.DT_OSAGO_CLAIM_INSURANCE_EXECUTION_ACT,
                ]
            }
        },
        'send_docs_to_user': {
            'plugin': 'emailer',
            'action': 'send_email',
            'condition': {
                "<batch>->_owner->email": {
                    "#validator": {
                        "cls": "EmailAddressValidator",
                        "valid": True
                    }
                },
                "<batch>->paid": True
            },
            'config': {
                'mail_type': 'osago_docs_ready',
                'max_retries': 5,
                'retry_timeout_seconds': [5, 10, 60, 300, 300],
                'recipients': {
                    "field_type": "DocArrayField",
                    "cls": "DocTextField",
                    "value": {
                        "#make_array": [{
                            "#field": "<batch>->_owner->email"
                        }]
                    }
                },
                'data': {
                    'crash_date': {
                        "field_type": "DocDateTimeField",
                        "value": {
                            '#field': '<batch>->data->crash_date'
                        }
                    },
                    'service_schema': {
                        "field_type": "DocTextField",
                        "value": {
                            "#field": "<app_config>->WEB_SCHEMA"
                        }
                    },
                    'service_domain': {
                        "field_type": "DocTextField",
                        "value": {
                            "#field": "<app_config>->DOMAIN"
                        }
                    },
                    'user_id': {
                        "field_type": "DocTextField",
                        "value": {
                            "#field": "<current_user>->uuid"
                        }
                    },
                    'batch_id': {
                        "field_type": "DocTextField",
                        "value": {
                            "#field": "<batch>->id"
                        }
                    },
                    'docs': {
                        "field_type": "DocArrayField",
                        "cls": "DocJsonField",
                        "value": {
                            "#field": "<batch>->rendered_docs"
                        }
                    }
                }
            }
        },
        'notify_admin_on_send_docs_to_user_fail': {
            'plugin': 'emailer',
            'action': 'send_email',
            'config': {
                'mail_type': 'on_send_docs_to_user_fail',
                'max_retries': 20,
                'retry_timeout_seconds': [10, 30, 60, 120, 300, 600, 1200, 3600],
                'recipients': {
                    "field_type": "DocArrayField",
                    "cls": "DocTextField",
                    "value": {
                        "#field": "<app_config>->ADMIN_EMAIL_LIST"
                    }
                },
                'data': {
                    'user_id': {
                        "field_type": "DocTextField",
                        "value": {
                            "#field": "<previous_event_data>->template_data->user_id"
                        }
                    },
                    'mail_type': {
                        "field_type": "DocTextField",
                        "value": {
                            "#field": "<previous_event_data>->mail_type"
                        }
                    },
                    'action_dt': {
                        "field_type": "DocDateTimeField",
                        "value": {
                            "#field": "<previous_event_data>-><action_dt>"
                        }
                    }
                }
            }
        },
        'schedule_please_finalise_osago_send': {
            'plugin': 'task_scheduler',
            'action': 'schedule',
            'condition': {
                "<batch>->_owner->email": {
                    "#validator": {
                        "cls": "EmailAddressValidator",
                        "valid": True
                    }
                },
                "<batch>->sent_mails": {
                    "#not_contain": "osago_please_finalise"
                },
                '<batch>->status': 'pretension'
            },
            'config': {
                'action': '%s.send_please_finalise_osago' % DocumentBatchTypeEnum.DBT_OSAGO,
                'task_id': {
                    "field_type": "DocTextField",
                    "value": {
                        "#sum": [{
                            "#value": "osago_please_finalise_"
                        }, {
                            "#field": "<batch>->id"
                        }]
                    }
                },
                'dt_type': 'exact_time_every_day',
                'dt_not_earlier': {
                    "field_type": "DocDateTimeField",
                    "value": {
                        "#sum": [{
                            "#timedelta": {
                                "days": 1
                            }
                        }, {
                            "#datetime": "#now"
                        }]
                    }
                },
                'dt_format': "%H:%M",   # тоже можно в конфиг
                'dt_exact_time': {
                    "field_type": "DocTextField",
                    "value": {
                        "#field": "<app_config>->NOT_PAID_BATCH_NOTIFY_DESIRED_TIME"
                    }
                },
                'dt_time_zone_region': {
                    "field_type": "DocTextField",
                    "value": {
                        "#field": "<batch>->data->insurance_company_region"
                    }
                }
            }
        },
        'send_please_finalise_osago': {
            'plugin': 'emailer',
            'action': 'send_email',
            'condition': {
                "<batch>->_owner->email": {
                    "#validator": {
                        "cls": "EmailAddressValidator",
                        "valid": True
                    }
                },
                "<batch>->sent_mails": {
                    "#not_contain": "osago_please_finalise"
                },
                '<batch>->status': 'pretension'
            },
            'config': {
                'mail_type': 'osago_please_finalise',
                'max_retries': 10,
                'retry_timeout_seconds': 10,
                'recipients': {
                    "field_type": "DocArrayField",
                    "cls": "DocTextField",
                    "value": {
                        "#make_array": [{
                            "#field": "<batch>->_owner->email"
                        }]
                    }
                },
                'data': {
                    'service_schema': {
                        "field_type": "DocTextField",
                        "value": {
                            "#field": "<app_config>->WEB_SCHEMA"
                        }
                    },
                    'service_domain': {
                        "field_type": "DocTextField",
                        "value": {
                            "#field": "<app_config>->DOMAIN"
                        }
                    },
                    'user_id': {
                        "field_type": "DocTextField",
                        "value": {
                            "#field": "<current_user>->uuid"
                        }
                    },
                    'batch_id': {
                        "field_type": "DocTextField",
                        "value": {
                            "#field": "<batch>->id"
                        }
                    }
                }
            }
        },
        'on_sent_please_finalise_osago': {
            'plugin': 'batch_manager',
            'action': 'set_batch_fields',
            'config': {
                'fields': {
                    'sent_mails': {
                        "field_type": "DocArrayField",
                        "cls": "DocTextField",
                        "value": {
                            "#push_to_set": {
                                "source": {
                                    "#field": "<batch>->sent_mails"
                                },
                                "new_item": "osago_please_finalise"
                            }
                        }
                    }
                }
            }
        }
    }

    OSAGO_TRANSITIONS = [
        {
            "status": "generating_pretension",
            "condition": {
                "<batch>->status": "pretension",
                "<event>": "go_ahead",
            },
            "actions": ['generate_first_stage_docs']
        },
        {
            "status": "generating_pretension",
            "condition": {
                "<batch>->status": "claim",
                "<event>": "rerender_pretension",
            },
            "actions": ['generate_first_stage_docs']
        },
        {
            "status": "claim",
            "condition": {
                "<batch>->status": "generating_pretension",
                "<event>": "doc_group_render_success"
            },
            "actions": ['send_docs_to_user', 'check_and_fix_payments']
        },
        {
            "condition": {
                "<event>": "emailer.send_fail",
                "<event_data>->mail_type": "osago_docs_ready"
            },
            "actions": ['notify_admin_on_send_docs_to_user_fail']
        },
        {
            "status": "pretension",
            "condition": {
                "<batch>->status": "generating_pretension",
                "<event>": {
                    "#in": ["doc_group_render_fail", "doc_group_render_canceled"]
                }
            }
        },
        {
            "status": "generating_claim",
            "condition": {
                "<batch>->status": "claim",
                "<event>": "go_ahead",
            },
            "actions": ['generate_second_stage_docs']
        },
        {
            "status": "generating_claim",
            "condition": {
                "<batch>->status": "court",
                "<event>": "rerender_claim",
            },
            "actions": ['generate_second_stage_docs']
        },
        {
            "status": "court",
            "condition": {
                "<batch>->status": "generating_claim",
                "<event>": "doc_group_render_success"
            },
            "actions": ['check_and_fix_payments']
        },
        {
            "status": "claim",
            "condition": {
                "<batch>->status": "generating_claim",
                "<event>": {
                    "#in": ["doc_group_render_fail", "doc_group_render_canceled"]
                }
            },
            "actions": ['check_and_fix_payments']
        },
        {
            "status": "pretension",
            "condition": {
                "<batch>->status": {
                    "#in": ["claim", "generating_pretension"]
                },
                "<event>": "go_back",
            },
            "actions": ['remove_pretension_documents']
        },
        {
            "status": "claim",
            "condition": {
                "<batch>->status": {
                    "#in": ["court", "generating_claim"]
                },
                "<event>": "go_back",
            },
            "actions": ['remove_claim_documents', 'check_and_fix_payments']
        },
        {
            "status": "generating_court",
            "condition": {
                "<batch>->status": {
                    "#in": ["court"]
                },
                "<event>": "go_ahead",
            },
            "actions": ['generate_third_stage_docs']
        },
        {
            "status": "writ",
            "condition": {
                "<batch>->status": {
                    "#in": ["generating_court"]
                },
                "<event>": "doc_group_render_success"
            },
        },
        {
            "status": "court",
            "condition": {
                "<batch>->status": {
                    "#in": ["writ", "generating_court"]
                },
                "<event>": "go_back",
            },
            "actions": ['remove_court_documents', 'check_and_fix_payments']
        },
        {
            "status": "court",
            "condition": {
                "<batch>->status": "generating_court",
                "<event>": {
                    "#in": ["doc_group_render_fail", "doc_group_render_canceled"]
                }
            },
            "actions": ['check_and_fix_payments']
        },
        {
            "condition": {
                "<batch>->status": "pretension",
                "<event>": "batch_manager.on_field_changed",
                "<event_data>->field_name": {
                    "#in": ["policy_number", "policy_series"]
                }
            },
            "actions": ['reset_policy_info'] # , 'get_policy_info_async'
        },
        #     {
        #     "condition": {
        #         "<batch>->status": "pretension",
        #         "<event>": "on_policy_info_receive_timeout",
        #     },
        #     "actions": ['get_policy_info_async']
        # },
        {
            "condition": {
                "<batch>->status": "pretension",
                "<event>": "on_policy_info_received"
            },
            "actions": ['set_policy_info']
        },
        {
            "condition": {
                "<batch>->status": "pretension",
                "<event>": "batch_manager.on_fieldset_changed",
            },
            "actions": ['schedule_please_finalise_osago_send']
        },
        {
            "condition": {
                "<event>": "emailer.mail_sent",
                "<event_data>->mail_type": "osago_please_finalise"
            },
            "actions": ['on_sent_please_finalise_osago']
        },
    ]

    VALIDATION_CONDITION = {
        "#cases": {
            "list": [{
                "conditions": {
                    "<document>->tried_to_render": True
                },
                "value": {"#value": "strict"}
            }],
            "default": {
                "value": {
                    "#value": "yes"
                }
            }
        }
    }

    return {
        "OSAGO_MAIL_LIST_TEMPLATE": OSAGO_MAIL_LIST_TEMPLATE,
        "OSAGO_PRETENSION_TEMPLATE": OSAGO_PRETENSION_TEMPLATE,
        "OSAGO_DOCUMENTS_CLAIM_TEMPLATE": OSAGO_DOCUMENTS_CLAIM_TEMPLATE,
        "OSAGO_TRUST_SUBMISSION_DOCS_TEMPLATE": OSAGO_TRUST_SUBMISSION_DOCS_TEMPLATE,
        "OSAGO_TRUST_OBTAIN_DOCS_TEMPLATE": OSAGO_TRUST_OBTAIN_DOCS_TEMPLATE,
        "OSAGO_TRUST_SUBMISION_OBTAIN_DOCS_TEMPLATE": OSAGO_TRUST_SUBMISION_OBTAIN_DOCS_TEMPLATE,
        "OSAGO_CLAIM_COURT_ABSENT_TEMPLATE": OSAGO_CLAIM_COURT_ABSENT_TEMPLATE,
        "OSAGO_CLAIM_ALL_EXECUTION_ACT_TEMPLATE": OSAGO_CLAIM_ALL_EXECUTION_ACT_TEMPLATE,
        "OSAGO_CLAIM_GUILTY_EXECUTION_ACT_TEMPLATE": OSAGO_CLAIM_GUILTY_EXECUTION_ACT_TEMPLATE,
        "OSAGO_CLAIM_INSURANCE_EXECUTION_ACT_TEMPLATE": OSAGO_CLAIM_INSURANCE_EXECUTION_ACT_TEMPLATE,
        "OSAGO_LAWSUIT_TEMPLATE": OSAGO_LAWSUIT_TEMPLATE,
        "OSAGO_OSAGO_COURT_MAIL_LIST_TEMPLATE": OSAGO_OSAGO_COURT_MAIL_LIST_TEMPLATE,

        "OSAGO_SCHEMA": OSAGO_SCHEMA,

        "OSAGO_MAIL_LIST_SCHEMA": OSAGO_MAIL_LIST_SCHEMA,
        "OSAGO_PRETENSION_SCHEMA": OSAGO_PRETENSION_SCHEMA,
        "OSAGO_DOCUMENTS_CLAIM_SCHEMA": OSAGO_DOCUMENTS_CLAIM_SCHEMA,
        "OSAGO_TRUST_SUBMISSION_DOCS_SCHEMA": OSAGO_TRUST_SUBMISSION_DOCS_SCHEMA,
        "OSAGO_TRUST_OBTAIN_DOCS_SCHEMA": OSAGO_TRUST_OBTAIN_DOCS_SCHEMA,
        "OSAGO_TRUST_SUBMISION_OBTAIN_DOCS_SCHEMA": OSAGO_TRUST_SUBMISION_OBTAIN_DOCS_SCHEMA,
        "OSAGO_CLAIM_COURT_ABSENT_SCHEMA": OSAGO_CLAIM_COURT_ABSENT_SCHEMA,
        "OSAGO_CLAIM_ALL_EXECUTION_ACT_SCHEMA": OSAGO_CLAIM_ALL_EXECUTION_ACT_SCHEMA,
        "OSAGO_CLAIM_GUILTY_EXECUTION_ACT_SCHEMA": OSAGO_CLAIM_GUILTY_EXECUTION_ACT_SCHEMA,
        "OSAGO_CLAIM_INSURANCE_EXECUTION_ACT_SCHEMA": OSAGO_CLAIM_INSURANCE_EXECUTION_ACT_SCHEMA,
        "OSAGO_LAWSUIT_SCHEMA": OSAGO_LAWSUIT_SCHEMA,
        "OSAGO_OSAGO_COURT_MAIL_LIST_SCHEMA": OSAGO_OSAGO_COURT_MAIL_LIST_SCHEMA,

        "OSAGO_RESULT_FIELDS": OSAGO_RESULT_FIELDS,
        "OSAGO_ACTIONS": OSAGO_ACTIONS,
        "OSAGO_TRANSITIONS": OSAGO_TRANSITIONS,
        "VALIDATION_CONDITION": VALIDATION_CONDITION
    }



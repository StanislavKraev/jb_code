# -*- coding: utf-8 -*-
import os
from fw.documents.enums import DocumentTypeEnum, DocumentKindEnum, BatchStatusEnum
from fw.documents.field_matchers import SimpleMatcher, FieldAttributeMatcher, ConstantMatcher
from fw.documents.common_schema_fields import  (SHORT_NAME_FIELD, FULL_NAME_FIELD, ADDRESS_FIELD,
                                                                     GENERAL_MANAGER_FIELD, FOUNDERS_COUNT_FIELD,
                                                                     GENERAL_MANAGER_CAPTION_FIELD,
                                                                     BOARD_OF_DIRECTORS_FIELD, EMPLOYER_FIELD,
                                                                     ADDRESS_TYPE_FIELD, INN_FIELD, KPP_FIELD,
                                                                     OGRN_FIELD, ACCOUNTANT_PERSON_FIELD)
from services.llc_reg.documents.enums import DocumentDeliveryTypeEnum

MAP_OBTAIN_WAY = {
    "field": "obtain_way",
    "map": {
        "founder": DocumentDeliveryTypeEnum.DDT_ISSUE_TO_THE_APPLICANT,
        "responsible_person": DocumentDeliveryTypeEnum.DDT_ISSUE_TO_THE_APPLICANT_OR_AGENT,
        "mail": DocumentDeliveryTypeEnum.DDT_SEND_BY_MAIL
    }
}


def get_test_resource_name(config, resource_rel_path):
    resources_path = config['resources_path']
    return os.path.join(resources_path, resource_rel_path)


def load_data(config):
    GENERAL_MANAGER_CONTRACT_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_GENERAL_MANAGER_CONTRACT,
        "template_name": "general_manager_contract",
        "file_name": get_test_resource_name(config, "general_manager_contract.tex"),
        "is_strict": False,
    }

    GENERAL_MANAGER_CONTRACT_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_GENERAL_MANAGER_CONTRACT,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Трудовой договор с руководителем",
        "conditions": {
            u"has_general_manager_contract": True
        },
        "batch_statuses": [BatchStatusEnum.BS_FINALISED],
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_FIELD,
            GENERAL_MANAGER_FIELD,
            FOUNDERS_COUNT_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            BOARD_OF_DIRECTORS_FIELD,
            EMPLOYER_FIELD,
            ADDRESS_TYPE_FIELD,
            INN_FIELD,
            KPP_FIELD,
            OGRN_FIELD,
            {
                "name": "general_manager_salary",
                "type": "DocCurrencyField",
                "required": True,
                "error_field_mapping": {
                    "general_manager_salary": "."
                },
                "validator": {
                    "conditions": [{
                                       "value": {
                                           "#gt": 0.0
                                       }
                                   }],
                    "error_field": "general_manager_salary"
                }
            }, {
                "name": "general_manager_salary_days",
                "type": "DocArrayField",
                "cls": "DocIntField",
                "required": True,
                "validator": {
                    "conditions": [{
                                       "values": {
                                           "#not_empty": True
                                       }
                                   }]
                }
            }, {
                "name": "general_manager_trial_period",
                "type": "DocIntField",
                "required": True
            }, {
                "name": "general_manager_quit_notify_period",
                "type": "DocIntField",
                "required": True
            }, {
                "name": "general_manager_fixed_working_hours",
                "type": "DocBoolField",
                "required": True
            }, {
                "name": "general_manager_term",
                "type": "DocIntField",
                "min_val": 6,
                "max_val": 60,
                "required": True
            }, {
                "name": "general_manager_contract_number",
                "type": "DocTextField",
                "required": True,
                "min_length": 1
            }, {
                "name": "accountant_contract_number",
                "type": "DocTextField",
                "required": False,
                "min_length": 1,
            }, {
                "name": "general_manager_contract_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            }, {
                "name": "general_manager_has_special_terms",
                "type": "DocBoolField",
                "required": True,
                "default": False
            }, {
                "name": "general_manager_contract_additional_terms",
                "type": "DocAdditionalRightsField",
                "required": False
            }, {
                "name": "general_manager_working_hours",
                "type": "DocWorkingHoursField",
                "required": False,
                "override_fields_kwargs": {
                    "holidays": {
                        "validator": {
                            "conditions": [{
                                               "values": {
                                                   "#not_empty": True
                                               }
                                           }]
                        }
                    }
                }
            }, {
                "name": "reg_date",
                "type": "calculated",
                "field_type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True,
                "suppress_validation_errors": True,
                "value": {
                    "#rendered_doc_field": {
                        "document_type": DocumentTypeEnum.DT_ARTICLES,
                        "value": {
                            "#field": "<document>->doc_date"
                        }
                    }
                }
            }, {
                "name": "has_general_manager_contract",
                "type": "DocBoolField",
                "required": False
            }
        ],
        "validators": [{
                           "condition": {
                               "weekly_hours": {
                                   "#lte": 2400
                               }
                           },
                           "error": {
                               "field": "general_manager_working_hours",
                               "code": 5
                           },
                           "#set": [{
                                        "day_hours_with_lunch": {
                                            "#sub": [{
                                                         "#field": "general_manager_working_hours->finish_working_hours"
                                                     }, {
                                                         "#field": "general_manager_working_hours->start_working_hours"
                                                     }]
                                        }
                                    }, {
                                        "weekly_hours": {
                                            "#mul": [{
                                                         "#sub": [7, {
                                                             "#size": "general_manager_working_hours->holidays"
                                                         }]
                                                     }, {
                                                         "#sub": [{
                                                                      "#div": [{
                                                                                   "#field": "day_hours_with_lunch->total_seconds"
                                                                               }, 60]
                                                                  }, {
                                                                      "#field": "general_manager_working_hours->lunch_time"
                                                                  }]
                                                     }]
                                        }
                                    }]
                       }, {
                           "condition": {
                               "accountant_contract_number": {
                                   "#ne": "@general_manager_contract_number"
                               }
                           },
                           "error": {
                               "field": "general_manager_contract_number",
                               "code": 5
                           }
                       }]
    }

    GENERAL_MANAGER_ORDER_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_GENERAL_MANAGER_ORDER,
        "template_name": "general_manager_order",
        "file_name": get_test_resource_name(config, "general_manager_order.tex"),
        "is_strict": False,
    }

    GENERAL_MANAGER_ORDER_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_GENERAL_MANAGER_ORDER,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Приказ о вступлении в должность",
        "conditions": {
            u"has_general_manager_order": True
        },
        "batch_statuses": [BatchStatusEnum.BS_FINALISED],
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_FIELD,
            GENERAL_MANAGER_FIELD,
            FOUNDERS_COUNT_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            BOARD_OF_DIRECTORS_FIELD,
            ADDRESS_TYPE_FIELD,
            INN_FIELD,
            KPP_FIELD,
            OGRN_FIELD,
            {
                "name": "general_manager_order_date",
                "type": "calculated",
                "field_type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True,
                "suppress_validation_errors": True,
                "value": {
                    "#cases": {
                        "list": [
                            {
                                "conditions": {
                                    "has_general_manager_contract": True
                                },
                                "value": {
                                    "#field": "general_manager_contract_date"
                                }
                            }],
                        "default": {
                            "value": {
                                "#field": "registration_date->next_working_day_p"
                            }
                        }
                    },
                }
            },
            {
                "name": "general_manager_order_number",
                "type": "DocTextField",
                "required": True,
                "max_length": 30,
                "min_length": 1,
                "allowed_re": ur"^[0-9a-zA-Zа-яёА-ЯЁ#\|\-\s]+$",
            },
            {
                "name": "has_general_manager_order",
                "type": "DocBoolField",
                "required": False
            },
            {
                "name": "reshenie_date",
                "type": "calculated",
                "field_type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True,
                "suppress_validation_errors": True,
                "value": {
                    "#rendered_doc_field": {
                        "document_type": DocumentTypeEnum.DT_ARTICLES,
                        "value": {
                            "#field": "<document>->doc_date"
                        }
                    }
                }
            }
        ]
    }

    ACCOUNTANT_CONTRACT_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_ACCOUNTANT_CONTRACT,
        "template_name": "accountant_contract",
        "file_name": get_test_resource_name(config, "accountant_contract.tex"),
        "is_strict": False,
    }

    ACCOUNTANT_CONTRACT_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_ACCOUNTANT_CONTRACT,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Трудовой договор с главным бухгалтером",
        "conditions": {
            u"has_accountant_contract_order": True
        },
        "batch_statuses": [BatchStatusEnum.BS_FINALISED],
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_FIELD,
            ADDRESS_TYPE_FIELD,
            GENERAL_MANAGER_FIELD,
            FOUNDERS_COUNT_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            BOARD_OF_DIRECTORS_FIELD,
            EMPLOYER_FIELD,
            INN_FIELD,
            KPP_FIELD,
            OGRN_FIELD,
            ACCOUNTANT_PERSON_FIELD,
            {
                "name": "accountant_contract_number",
                "type": "DocTextField",
                "required": True,
                "min_length": 1,
            }, {
                "name": "general_manager_contract_number",
                "type": "DocTextField",
                "required": False,
                "min_length": 1
            }, {
                "name": "accountant_start_work",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            },
            {
                "name": "accountant_trial_period",
                "type": "DocIntField",
                "required": True,
            },
            {
                "name": "accountant_salary",
                "type": "DocCurrencyField",
                "required": True,
                "error_field_mapping": {
                    "accountant_salary": "."
                },
                "validator": {
                    "conditions": [{
                                       "value": {
                                           "#gt": 0.0
                                       }
                                   }],
                    "error_field": "accountant_salary"
                }
            },
            {
                "name": "accountant_salary_days",
                "type": "DocArrayField",
                "cls": "DocIntField",
                "required": True,
                "validator": {
                    "conditions": [{
                                       "values": {
                                           "#not_empty": True
                                       }
                                   }]
                }
            },
            {
                "name": "accountant_fixed_working_hours",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "accountant_has_special_terms",
                "type": "DocBoolField",
                "required": True,
                "default": False
            },
            {
                "name": "accountant_contract_additional_terms",
                "type": "DocAdditionalRightsField",
                "required": False
            },
            {
                "name": "accountant_working_hours",
                "type": "DocWorkingHoursField",
                "required": False,
                "override_fields_kwargs": {
                    "holidays": {
                        "validator": {
                            "conditions": [{
                                               "values": {
                                                   "#not_empty": True
                                               }
                                           }]
                        }
                    }
                }
            },
            {
                "name": "accountant_fixed_working_hours",
                "type": "DocBoolField",
                "required": True
            },
            {
                "name": "has_accountant_contract_order",
                "type": "DocBoolField",
                "required": False
            }

        ],
        "validators": [{
                           "condition": {
                               "weekly_hours": {
                                   "#lte": 2400
                               }
                           },
                           "error": {
                               "field": "accountant_working_hours",
                               "code": 5
                           },
                           "#set": [{
                                        "day_hours_with_lunch": {
                                            "#sub": [{
                                                         "#field": "accountant_working_hours->finish_working_hours"
                                                     }, {
                                                         "#field": "accountant_working_hours->start_working_hours"
                                                     }]
                                        }
                                    }, {
                                        "weekly_hours": {
                                            "#mul": [{
                                                         "#sub": [7, {
                                                             "#size": "accountant_working_hours->holidays"
                                                         }]
                                                     }, {
                                                         "#sub": [{
                                                                      "#div": [{
                                                                                   "#field": "day_hours_with_lunch->total_seconds"
                                                                               }, 60]
                                                                  }, {
                                                                      "#field": "accountant_working_hours->lunch_time"
                                                                  }]
                                                     }]
                                        }
                                    }]
                       },
                       {
                           "condition": {
                               "accountant_contract_number": {
                                   "#ne": "@general_manager_contract_number"
                               }
                           },
                           "error": {
                               "field": "accountant_contract_number",
                               "code": 5
                           }
                       }]
    }

    ACCOUNTANT_IMPOSITION_ORDER_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_ACCOUNTANT_IMPOSITION_ORDER,
        "template_name": "accountant_imposition_order",
        "file_name": get_test_resource_name(config, "accountant_imposition_order.tex"),
        "is_strict": False,
    }

    ACCOUNTANT_IMPOSITION_ORDER_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_ACCOUNTANT_IMPOSITION_ORDER,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Приказ о возложении обязанностей бухгалтера на директора",
        "conditions": {
            u"general_manager_as_accountant": True
        },
        "batch_statuses": [BatchStatusEnum.BS_FINALISED],
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_FIELD,
            GENERAL_MANAGER_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            OGRN_FIELD,
            INN_FIELD,
            KPP_FIELD,
            {
                "name": "general_manager_contract_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": False
            },
            {
                "name": "general_manager_contract_date_calc",
                "type": "calculated",
                "field_type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True,
                "error_field_mapping": {
                    "general_manager_contract_date_calc": "general_manager_contract_date",
                },
                "value": {
                    "#cases": {
                        "list": [
                            {
                                "conditions": {
                                    "has_general_manager_contract": True
                                },
                                "value": {
                                    "#field": "general_manager_contract_date"
                                }
                            }],
                        "default": {
                            "value": {
                                "#field": "registration_date->next_working_day_p"
                            }
                        }
                    },
                }
            },
            {
                "name": "general_manager_as_accountant_order_number",
                "type": "DocTextField",
                "max_length": 30,
                "min_length": 1,
                "allowed_re": ur"^[0-9a-zA-Zа-яёА-ЯЁ#\|\-\s]+$",
                "required": True
            }
        ]
    }

    ACCOUNTANT_ORDER_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_ACCOUNTANT_ORDER,
        "template_name": "accountant_order",
        "is_strict": True,
        "pages": [
            {
                "page_file": get_test_resource_name(config, "job_order.pdf"),
                "fields": [
                    {
                        "name": "company_full_name",
                        "field-length": 100,
                        "text-align": "left",
                    }, {
                        "name": "doc_number",
                        "field-length": 20,
                        "text-align": "left",
                    }, {
                        "name": "doc_date1",
                        "field-length": 10,
                        "text-align": "left"
                    }, {
                        "name": "work_start_date",
                        "field-length": 10,
                        "text-align": "left"
                    }, {
                        "name": "fio",
                        "field-length": 100,
                        "text-align": "left"
                    }, {
                        "name": "tabel_number",
                        "field-length": 20,
                        "text-align": "left"
                    }, {
                        "name": "direction",
                        "field-length": 100,
                        "text-align": "left"
                    }, {
                        "name": "title",
                        "field-length": 100,
                        "text-align": "left"
                    }, {
                        "name": "conditions_line1",
                        "field-length": 100,
                        "text-align": "left"
                    }, {
                        "name": "salary_rub",
                        "field-length": 20,
                        "text-align": "left"
                    }, {
                        "name": "salary_cop",
                        "field-length": 3,
                        "text-align": "left"
                    }, {
                        "name": "bonus_rub",
                        "field-length": 20,
                        "text-align": "left"
                    }, {
                        "name": "bonus_cop",
                        "field-length": 3,
                        "text-align": "left"
                    }, {
                        "name": "trial_period_monthes",
                        "field-length": 100,
                        "text-align": "left"
                    }, {
                        "name": "contract_date_day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0"
                    }, {
                        "name": "contract_date_month"
                    }, {
                        "name": "contract_date_year",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0"
                    }, {
                        "name": "contract_number",
                        "field-length": 20,
                        "text-align": "left"
                    }
                ]
            }]
    }

    ACCOUNTANT_ORDER_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_ACCOUNTANT_ORDER,
        "file_name_template": u"Приказ о приёме на работу главного бухгалтера",
        "conditions": {
            u"has_accountant_contract_order": True
        },
        "batch_statuses": [BatchStatusEnum.BS_FINALISED],
        "fields": [
            FULL_NAME_FIELD,
            ACCOUNTANT_PERSON_FIELD,
            {
                "name": "accountant_contract_number",
                "type": "DocTextField",
                "required": True,
                "max_length": 30,
                "min_length": 1,
                "allowed_re": ur"^[0-9a-zA-Zа-яёА-ЯЁ#\|\-\s]+$",
            }, {
                "name": "accountant_start_work",
                "type": "DocDateTimeField",
                "input_format": "%d.%m.%Y",
                "required": True
            }, {
                "name": "accountant_trial_period",
                "type": "DocIntField",
                "required": False
            }, {
                "name": "accountant_salary",
                "type": "DocCurrencyField",
                "required": True
            }, {
                "name": "accountant_order_number",
                "type": "DocTextField",
                "required": True
            }, {
                "name": "accountant_trial_period_text",
                "type": "calculated",
                "field_type": "DocTextField",
                "required": False,
                "suppress_validation_errors": True,
                "value": {
                    "#cases": {
                        "list": [{
                                     "conditions": {
                                         "accountant_trial_period": {
                                             "#empty": True
                                         }
                                     },
                                     "value": {
                                         "#value": u"Без срока испытания"
                                     }
                                 }],
                        "default": {
                            "value": {
                                "#exec": {
                                    "module": "llc_reg_methods",
                                    "method": "num_to_text",
                                    "args": [{
                                                 "#field": "accountant_trial_period"
                                             }]
                                }
                            }
                        }
                    }
                }
            }, {
                "name": "has_accountant_contract_order",
                "type": "DocBoolField",
                "required": False
            }
        ]
    }

    ACCOUNTANT_ORDER_MATCHER = {
        "doc_name": DocumentTypeEnum.DT_ACCOUNTANT_ORDER,
        "template_name": ACCOUNTANT_ORDER_TEMPLATE['template_name'],
        "fields": {
            "company_full_name": SimpleMatcher(field_name="full_name",
                                               prefix=u"Общество с ограниченной ответственностью «",
                                               suffix=u"»"),
            "doc_number": SimpleMatcher(field_name="accountant_order_number"),
            "doc_date1": SimpleMatcher(field_name="accountant_start_work"),
            "work_start_date": SimpleMatcher(field_name="accountant_start_work"),
            "fio": FieldAttributeMatcher(field_name="accountant_person", attr_name="full_name"),
            "tabel_number": ConstantMatcher(value=u""),
            "direction": ConstantMatcher(value=u"Дирекция"),
            "title": ConstantMatcher(value=u"Главный бухгалтер"),
            "conditions_line1": ConstantMatcher(value=u"Постоянно"),
            "salary_rub": FieldAttributeMatcher(field_name="accountant_salary", attr_name="currency_major"),
            "salary_cop": ConstantMatcher(value="00"),
            "bonus_rub": ConstantMatcher(value=""),
            "bonus_cop": ConstantMatcher(value=""),
            "trial_period_monthes": SimpleMatcher(field_name="accountant_trial_period_text"),
            "contract_date_day": FieldAttributeMatcher(field_name="accountant_start_work", attr_name="day"),
            "contract_date_month": FieldAttributeMatcher(field_name="accountant_start_work", attr_name="month",
                                                         adapter="MonthRusNameDeclAdapter"),
            "contract_date_year": FieldAttributeMatcher(field_name="accountant_start_work", attr_name="year"),
            "contract_number": SimpleMatcher(field_name="accountant_contract_number")
        }
    }

    ROSSTAT_CLAIM_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_ROSSTAT_CLAIM,
        "template_name": "rosstat_claim",
        "file_name": get_test_resource_name(config, "rosstat_claim.tex"),
        "is_strict": False,
    }

    ROSSTAT_CLAIM_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_ROSSTAT_CLAIM,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Заявление в Росстат",
        "batch_statuses": [BatchStatusEnum.BS_FINALISED],
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_FIELD,
            GENERAL_MANAGER_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            INN_FIELD,
            KPP_FIELD,
            OGRN_FIELD,
            {
                "name": "day_after_registration",
                "type": "calculated",
                "field_type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True,
                "suppress_validation_errors": True,
                "value": {
                    "#field": "registration_date->next_working_day_p"
                }
            },
        ]
    }

    FSS_CLAIM_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_FSS_CLAIM,
        "template_name": "fss_claim",
        "file_name": get_test_resource_name(config, "fss_claim.tex"),
        "is_strict": False,
    }

    FSS_CLAIM_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_FSS_CLAIM,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Заявление в ФСС",
        "batch_statuses": [BatchStatusEnum.BS_FINALISED],
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_FIELD,
            GENERAL_MANAGER_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            INN_FIELD,
            KPP_FIELD,
            OGRN_FIELD,
            {
                "name": "day_after_registration",
                "type": "calculated",
                "field_type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True,
                "suppress_validation_errors": True,
                "value": {
                    "#field": "registration_date->next_working_day_p"
                }
            },
        ]
    }

    PFR_CLAIM_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_PFR_CLAIM,
        "template_name": "pfr_claim",
        "file_name": get_test_resource_name(config, "pfr_claim.tex"),
        "is_strict": False,
    }

    PFR_CLAIM_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_PFR_CLAIM,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Заявление в ПФР",
        "batch_statuses": [BatchStatusEnum.BS_FINALISED],
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_FIELD,
            GENERAL_MANAGER_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            INN_FIELD,
            KPP_FIELD,
            OGRN_FIELD,
            {
                "name": "day_after_registration",
                "type": "calculated",
                "field_type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True,
                "suppress_validation_errors": True,
                "value": {
                    "#field": "registration_date->next_working_day_p"
                }
            },
        ]
    }

    FOUNDERS_LIST_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_FOUNDERS_LIST,
        "template_name": "founders_list",
        "file_name": get_test_resource_name(config, "founders_list.tex"),
        "is_strict": False,
    }

    FOUNDERS_LIST_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_FOUNDERS_LIST,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Список участников",
        "batch_statuses": [BatchStatusEnum.BS_FINALISED],
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_FIELD,
            GENERAL_MANAGER_FIELD,
            FOUNDERS_COUNT_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            BOARD_OF_DIRECTORS_FIELD,
            OGRN_FIELD,
            {
                "name": "founders_list_date",
                "type": "calculated",
                "field_type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True,
                "suppress_validation_errors": True,
                "value": {
                    "#cases": {
                        "list": [
                            {
                                "conditions": {
                                    "has_general_manager_contract": True
                                },
                                "value": {
                                    "#field": "general_manager_contract_date"
                                }
                            }],
                        "default": {
                            "value": {
                                "#field": "registration_date->next_working_day_p"
                            }
                        }
                    },
                }
            },
            {
                "name": "registration_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": True
            },
            {
                "name": "founders",
                "type": "calculated",
                "field_type": "DocArrayField",
                "cls": "FounderObject",
                "required": True,
                "subfield_kwargs": {
                    "error_field_mapping": {
                        "company": "founder",
                        "person": "founder",
                        "documents_recipient_type": "",  # suppress error
                        "share": "share.",
                        "nominal_capital": "nominal_capital."
                    }
                },
                "value": {
                    "#array_mapping": {
                        "array_source_field": {
                            "#field": "founders"
                        },
                        "target_items": {
                            "#object": {
                                "founder_type": {
                                    "#value_map": {
                                        "field": {
                                            "#array_item_field": "founder->type"
                                        },
                                        "map": {
                                            "person": 1,
                                            "company": 2
                                        }
                                    }
                                },
                                "nominal_capital": {
                                    "#array_item_field": "nominal_capital"
                                },
                                "share": {
                                    "#object": {
                                        "type": {
                                            "#field": "share_type",
                                        },
                                        "value": {
                                            "#array_item_field": "share"
                                        }
                                    }
                                },
                                "person": {
                                    "#cases": {
                                        "set": {
                                            "cur_founder_type": {
                                                "#array_item_field": "founder->type"
                                            }
                                        },
                                        "list": [{
                                                     "conditions": {
                                                         "cur_founder_type": "person"
                                                     },
                                                     "value": {
                                                         "#array_item_field": "founder"
                                                     }
                                                 }],
                                        "default": {
                                            "value": None
                                        }
                                    }
                                },
                                "company": {
                                    "#cases": {
                                        "set": {
                                            "cur_founder_type": {
                                                "#array_item_field": "founder->type"
                                            }
                                        },
                                        "list": [{
                                                     "conditions": {
                                                         "cur_founder_type": "company"
                                                     },
                                                     "value": {
                                                         "#array_item_field": "founder"
                                                     }
                                                 }],
                                        "default": {
                                            "value": None
                                        }
                                    }
                                },
                                "documents_recipient_type": {
                                    "#cases": {
                                        "set": {
                                            "cur_founder_ref": {
                                                "#array_item_field": "founder"
                                            },
                                            "cur_founders_count": {
                                                "#size": "founders"
                                            }
                                        },
                                        "list": [
                                            {
                                                "conditions": {
                                                    "cur_founders_count": 1
                                                },
                                                "value": {
                                                    "#value_map": MAP_OBTAIN_WAY
                                                }
                                            }, {
                                                "conditions": {
                                                    "cur_founders_count": {
                                                        "#gt": 1
                                                    },
                                                    "obtain_way": "founder",
                                                    "cur_founder_ref": "@doc_obtain_founder"
                                                },
                                                "value": {
                                                    "#value_map": MAP_OBTAIN_WAY
                                                }
                                            }, {
                                                "conditions": {
                                                    "cur_founders_count": {
                                                        "#gt": 1
                                                    },
                                                    "obtain_way": "responsible_person",
                                                    "cur_founder_ref": "@selected_moderator"
                                                },
                                                "value": {
                                                    "#value_map": MAP_OBTAIN_WAY
                                                }
                                            }, {
                                                "conditions": {
                                                    "cur_founders_count": {
                                                        "#gt": 1
                                                    },
                                                    "obtain_way": "mail",
                                                    "cur_founder_ref": "@selected_moderator"
                                                },
                                                "value": {
                                                    "#value_map": MAP_OBTAIN_WAY
                                                }
                                            }
                                        ],
                                        "default": {
                                            "value": None
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "validator": {
                    "#set": {
                        "total_share": {
                            "#aggregate": {
                                "field": "values",
                                "attr": "share.normal",
                                "operator": "add"
                            }
                        },
                        "founders_count": {
                            "#size": "values"
                        }
                    },
                    "conditions": [{
                                       "#or": [{
                                                   "total_share": {
                                                       "#almost_equal": 1
                                                   }
                                               }, {
                                                   "values": {
                                                       "#size": 0
                                                   }
                                               }],
                                       "founders_count": {
                                           "#gt": 0
                                       }
                                   }],
                    "error_field": "founders"
                }
            },
            {
                "name": "starter_capital",
                "type": "calculated",
                "field_type": "CompanyStarterCapitalField",
                "required": True,
                "override_fields_kwargs": {
                    "value": {
                        "override_fields_kwargs": {
                            "value": {
                                "min_val": 10000
                            }
                        }
                    }
                },
                "value": {
                    "#object": {
                        "capital_type": 1,
                        "value": {
                            "#field": "starter_capital->value"
                        }
                    }
                }
            }
        ]
    }

    COMPANY_DETAILS_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_COMPANY_DETAILS,
        "template_name": "company_details",
        "file_name": get_test_resource_name(config, "company_details.tex"),
        "is_strict": False,
    }

    COMPANY_DETAILS_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_COMPANY_DETAILS,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Реквизиты компании",
        "batch_statuses": [BatchStatusEnum.BS_FINALISED],
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_FIELD,
            GENERAL_MANAGER_FIELD,
            FOUNDERS_COUNT_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            BOARD_OF_DIRECTORS_FIELD,
            INN_FIELD,
            KPP_FIELD,
            {
                "name": "actual_address",
                "type": "DocAddressField",
                "required": True,
            },
            {
                "name": "ogrn",
                "type": "calculated",
                "field_type": "DocTextField",
                "value": {
                    "#field": "<batch>->result_fields->ifns_reg_info->ogrn"
                }
            }, {
                "name": "bank_bik",
                "type": "DocTextField",
                "min_length": 9,
                "max_length": 9,
                "required": True
            }, {
                "name": "bank_account",
                "type": "DocTextField",
                "min_length": 20,
                "max_length": 20,
                "required": True
            }, {
                "name": "bank_info",
                "type": "calculated",
                "field_type": "DocJsonField",
                # "suppress_validation_errors" : True,
                "error_field_mapping": {
                    "bank_info": "."
                },
                "required": True,
                "value": {
                    "#exec": {
                        "module": "llc_reg_methods",
                        "method": "get_bank_info",
                        "args": [{
                                     "#field": "bank_bik"
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
                    "error_field": "bank_bik"
                }
            }, {
                "name": "company_email",
                "type": "DocTextField",
                "required": False
            }, {
                "name": "company_site",
                "type": "DocTextField",
                "required": False
            }, {
                "name": "company_phone",
                "type": "DocPhoneNumberField",
                "required": False
            }
        ]
    }

    return {
        'GENERAL_MANAGER_CONTRACT_SCHEMA': GENERAL_MANAGER_CONTRACT_SCHEMA,
        'GENERAL_MANAGER_CONTRACT_TEMPLATE': GENERAL_MANAGER_CONTRACT_TEMPLATE,
        'GENERAL_MANAGER_ORDER_SCHEMA': GENERAL_MANAGER_ORDER_SCHEMA,
        'GENERAL_MANAGER_ORDER_TEMPLATE': GENERAL_MANAGER_ORDER_TEMPLATE,
        'ACCOUNTANT_CONTRACT_SCHEMA': ACCOUNTANT_CONTRACT_SCHEMA,
        'ACCOUNTANT_CONTRACT_TEMPLATE': ACCOUNTANT_CONTRACT_TEMPLATE,
        'ACCOUNTANT_IMPOSITION_ORDER_SCHEMA': ACCOUNTANT_IMPOSITION_ORDER_SCHEMA,
        'ACCOUNTANT_IMPOSITION_ORDER_TEMPLATE': ACCOUNTANT_IMPOSITION_ORDER_TEMPLATE,
        'ACCOUNTANT_ORDER_SCHEMA': ACCOUNTANT_ORDER_SCHEMA,
        'ACCOUNTANT_ORDER_TEMPLATE': ACCOUNTANT_ORDER_TEMPLATE,
        'ACCOUNTANT_ORDER_MATCHER': ACCOUNTANT_ORDER_MATCHER,
        'ROSSTAT_CLAIM_SCHEMA': ROSSTAT_CLAIM_SCHEMA,
        'ROSSTAT_CLAIM_TEMPLATE': ROSSTAT_CLAIM_TEMPLATE,
        'FSS_CLAIM_SCHEMA': FSS_CLAIM_SCHEMA,
        'FSS_CLAIM_TEMPLATE': FSS_CLAIM_TEMPLATE,
        'PFR_CLAIM_SCHEMA': PFR_CLAIM_SCHEMA,
        'PFR_CLAIM_TEMPLATE': PFR_CLAIM_TEMPLATE,
        'FOUNDERS_LIST_SCHEMA': FOUNDERS_LIST_SCHEMA,
        'FOUNDERS_LIST_TEMPLATE': FOUNDERS_LIST_TEMPLATE,
        'COMPANY_DETAILS_SCHEMA': COMPANY_DETAILS_SCHEMA,
        'COMPANY_DETAILS_TEMPLATE': COMPANY_DETAILS_TEMPLATE
    }
# -*- coding: utf-8 -*-
from copy import deepcopy
import copy
import os
from fw.documents.enums import DocumentTypeEnum, BatchStatusEnum, DocumentKindEnum, TaxType, DocumentBatchTypeEnum
from fw.documents.field_matchers import MultilineFieldMatcher, ConcatFieldAttributeMatcher, FieldSetMatcher, \
    ConstantMatcher, SimpleMatcher, ArrayAttributeMatcher
from fw.documents.field_matchers import FieldAttributeMatcher
from fw.documents.fields.doc_fields import CompanyObject
from fw.documents.template_renderer import RenderingVariants
from fw.documents.common_schema_fields import (ADDRESS_FIELD, GENERAL_MANAGER_CAPTION_FIELD,
                                               FULL_NAME_FIELD, JOB_MAIN_CODE_FIELD, JOB_CODE_ARRAY_FIELD,
                                               STARTER_CAPITAL_FIELD,
                                               USE_FOREIGN_COMPANY_NAME_FIELD,
                                               USE_NATIONAL_LANGUAGE_COMPANY_NAME_FIELD, FOREIGN_FULL_NAME_FIELD,
                                               FOREIGN_SHORT_NAME_FIELD, FOREIGN_LANGUAGE_FIELD,
                                               NATIONAL_LANGUAGE_FIELD,
                                               NATIONAL_LANGUAGE_FULL_NAME_FIELD, NATIONAL_LANGUAGE_SHORT_NAME_FIELD,
                                               SHORT_NAME_FIELD, GENERAL_MANAGER_FIELD, FOUNDERS_COUNT_FIELD,
                                               BOARD_OF_DIRECTORS_FIELD, ADDRESS_TYPE_FIELD, ADDRESS_TYPE_FIELD_NR,
                                               DOC_DATE_FIELD_TODAY, DOC_DATE_OR_TODAY)
from services.llc_reg.documents.enums import DocumentDeliveryTypeEnum, FounderTypeEnum, JSCMemberTypeEnum, \
    DocumentDeliveryTypeStrEnum, RegistrationWay, AddressType


def get_test_resource_name(config, resource_rel_path):
    resources_path = config['resources_path']
    return os.path.join(resources_path, resource_rel_path)


def load_data(config):
    FOUNDERS_REF_LIST_TEMP_VARIABLE = {
        "#array_mapping": {
            "array_source_field": {
                "#field": "founders"
            },
            "target_items": {
                "#cases": {
                    "set": {
                        "cur_founder_type": {
                            "#array_item_field": "founder_type"
                        }
                    },
                    "list": [{
                                 "conditions": {
                                     "cur_founder_type": 1
                                 },
                                 "value": {
                                     "#array_item_field": "person->_id"
                                 }
                             }, {
                                 "conditions": {
                                     "cur_founder_type": 2
                                 },
                                 "value": {
                                     "#array_item_field": "company->_id"
                                 }
                             }],
                    "default": {
                        "value": None
                    }}}}}

    ADDRESS_FIELD_WITH_OKATO = deepcopy(ADDRESS_FIELD)
    ADDRESS_FIELD_WITH_OKATO['override_fields_kwargs']['okato'] = {
        'required': True
    }
    ADDRESS_FIELD_WITH_OKATO['required'] = True

    MAP_OBTAIN_WAY = {
        "field": "obtain_way",
        "map": {
            "founder": DocumentDeliveryTypeEnum.DDT_ISSUE_TO_THE_APPLICANT,
            "responsible_person": DocumentDeliveryTypeEnum.DDT_ISSUE_TO_THE_APPLICANT_OR_AGENT,
            "mail": DocumentDeliveryTypeEnum.DDT_SEND_BY_MAIL
        }
    }
    FOUNDER_APPLICANT_FIELD = {
        "name": "founder_applicant",
        "type": "calculated",
        "field_type": "FounderObject",
        "required": False,
        "suppress_validation_errors": True,
        "override_fields_kwargs": {
            "documents_recipient_type": {
                "required": True
            }
        },
        "value": {
            "#set": {
                "selected_founder": {
                    "#pick_array_item": {
                        "array_field": "founders",
                        "conditions": {
                            "#or": [{
                                        "founders|size": 1,
                                    }, {
                                        "founders|size": {
                                            "#gt": 1
                                        },
                                        "obtain_way": "responsible_person",
                                        "<loop_item>->founder": "@selected_moderator"
                                    }, {
                                        "founders|size": {
                                            "#gt": 1
                                        },
                                        "obtain_way": "founder",
                                        "<loop_item>->founder": "@doc_obtain_founder"
                                    }, {
                                        "founders|size": {
                                            "#gt": 1
                                        },
                                        "obtain_way": "mail",
                                        "<loop_item>->founder": "@selected_moderator"
                                    }]
                        }
                    }
                }
            },
            "#object": {
                "founder_type": {
                    "#value_map": {
                        "field": "selected_founder->founder->type",
                        "map": {
                            "person": 1,
                            "company": 2
                        }
                    }
                },
                "company": {
                    "#object": {
                        "type": "CompanyObject",
                        "_id": {
                            "#cases": {
                                "list": [{
                                             "conditions": {
                                                 "selected_founder->founder->type": "company"
                                             },
                                             "value": {
                                                 "#field": "selected_founder->founder->_id"
                                             }
                                         }],
                                "default": {
                                    "value": ""
                                }
                            }
                        }
                    }
                },
                "person": {
                    "#object": {
                        "type": "PrivatePerson",
                        "_id": {
                            "#cases": {
                                "list": [{
                                             "conditions": {
                                                 "selected_founder->founder->type": "person"
                                             },
                                             "value": {
                                                 "#field": "selected_founder->founder->_id"
                                             }
                                         }],
                                "default": {
                                    "value": ""
                                }
                            }
                        }
                    }
                },
                "nominal_capital": {
                    "#field": "selected_founder->nominal_capital",
                },
                "share": {
                    "#object": {
                        "type": {
                            "#field": "share_type"
                        },
                        "value": {
                            "#field": "selected_founder->share"
                        }
                    }
                },
                "documents_recipient_type": {
                    "#value_map": MAP_OBTAIN_WAY
                }
            }
        }
    }

    FOUNDERS_FIELD = {
        "name": "founders",
        "type": "calculated",
        "field_type": "DocArrayField",
        "cls": "FounderObject",
        "depends_on": ["founder_applicant"],
        "required": True,
        "subfield_kwargs": {
            "error_field_mapping": {
                "company": "founder",
                "person": "founder",
                "documents_recipient_type": "",  # suppress error
                "share": "founder.share.",
                "nominal_capital": "founder.nominal_capital."
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
                        },
                        "duplicate_fio": {
                            "#exec": {
                                "module": "llc_reg_methods",
                                "method": "check_founder_has_same_fio",
                                "kwargs": {
                                    "founders": {
                                        "#field": "founders"
                                    },
                                    "founder": {
                                        "#array_item_field": "founder"
                                    }
                                }
                            }
                        },
                        "is_starter_capital_dividable": {
                            "#exec": {
                                "module": "llc_reg_methods",
                                "method": "is_starter_capital_dividable",
                                "kwargs": {
                                    "founder_share": {
                                        "#array_item_field": "share"
                                    },
                                    "starter_capital": {
                                        "#field": "starter_capital->value->value"
                                    },
                                    "share_type": {
                                        "#field": "share_type"
                                    }
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
                           }, {
                               "founders_count": {
                                   "#lte": 50
                               }
                           }],
            "error_field": ""
        }
    }

    P11001_TEMPLATE = {
        "template_name": "P11001_template",
        "doc_name": DocumentTypeEnum.DT_P11001,
        "is_strict": True,
        "pages": [
            {
                "page_file": get_test_resource_name(config, "11001/pg_0001.pdf"),
                "array_fields": [
                    {
                        "name": "page1-polnoe_naimenovanie__line{{item}}",
                        "count": 6,
                        "field-length": 40,
                        "case": "upper"
                    }, {
                        "name": "page1-sokr_naimenovanie__line{{item}}",
                        "count": 4,
                        "field-length": 40,
                        "case": "upper"
                    },
                    {
                        "name": "page1-district_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    },
                ],
                "fields": [
                    {
                        "name": "page1-subject_code",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    },
                    {
                        "name": "page1-pocht_index",
                        "field-length": 6,
                        "text-align": "right",
                        "space-filler": u"0",
                    },
                    {
                        "name": "page1-district_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page1-city_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page1-city_name",
                        "field-length": 28,
                        "text-align": "left",
                        "case": "upper"
                    }
                ]
            },
            {
                "page_file": get_test_resource_name(config, "11001/pg_0002.pdf"),
                "fields": [
                    {
                        "name": "page2-nas_punkt_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page2-street_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page2-house_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page2-house_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page2-corpus_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page2-corpus_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page2-office_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page2-office_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page2-nach_capital_type",
                        "field-length": 1
                    }, {
                        "name": "page2-akc_obchestvo_member_type",
                        "field-length": 1
                    }, {
                        "name": "page2-nach_capital_value__currency-maj",
                        "field-length": 15,
                        "text-align": "right"
                    }, {
                        "name": "page2-nach_capital_value__currency-min",
                        "field-length": 4,
                        "text-align": "left"
                    }
                ],
                "array_fields": [
                    {
                        "name": "page2-nas_punkt_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    }, {
                        "name": "page2-street_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    },
                ]
            },
            {
                "page_file": get_test_resource_name(config, "11001/pg_0003.pdf"),
                "multiple": True,
                "array_field": "founders",
                "array_item_filter": {
                    "founder_type": FounderTypeEnum.FT_COMPANY
                },
                "fields": [
                    {
                        "name": "page3-ogrn",
                        "field-length": 13
                    }, {
                        "name": "page3-inn",
                        "field-length": 10
                    }, {
                        "name": "page3-nominal_part_value__currency-maj",
                        "field-length": 15,
                        "text-align": "right"
                    }, {
                        "name": "page3-nominal_part_value__currency-min",
                        "field-length": 4,
                        "text-align": "left"
                    }, {
                        "name": "page3-razmer_doli__percent-maj",
                        "field-length": 3,
                        "text-align": "right"
                    }, {
                        "name": "page3-razmer_doli__percent-min",
                        "field-length": 15,
                        "text-align": "left"
                    }, {
                        "name": "page3-razmer_doli__decimal-maj",
                        "field-length": 1,
                        "text-align": "right"
                    }, {
                        "name": "page3-razmer_doli__decimal-min",
                        "field-length": 15,
                        "text-align": "left"
                    }, {
                        "name": "page3-razmer_doli__fraction-maj",
                        "field-length": 15,
                        "text-align": "right"
                    }, {
                        "name": "page3-razmer_doli__fraction-min",
                        "field-length": 15,
                        "text-align": "left"
                    }, {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }
                ],
                "array_fields": [
                    {
                        "name": "page3-polnoe_naimenovanie__line{{item}}",
                        "count": 6,
                        "field-length": 40,
                        "case": "upper"
                    }
                ]
            },
            # {
            #                "page_file": get_test_resource_name(config, "11001/pg_0004.pdf"),
            #                "multiple" : True,
            #                "array_field" : "founders",
            #                "array_item_filter" : {
            #                    "founder_type" : FounderTypeEnum.FT_FOREIGN_COMPANY
            #                },
            #                "fields": [
            #                        {
            #                        "name": "page4-inn",
            #                        "field-length": 10
            #                    }, {
            #                        "name" : "page4-reg_number",
            #                        "field-length": 25
            #                    },{
            #                        "name" : "page4-country_code",
            #                        "field-length": 3,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name": "page4-reg_date__day",
            #                        "field-length": 2,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name": "page4-reg_date__month",
            #                        "field-length": 2,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name": "page4-reg_date__year",
            #                        "field-length": 4
            #                    }, {
            #                        "name": "page4-nominal_part_value__currency-maj",
            #                        "field-length": 15,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page4-nominal_part_value__currency-min",
            #                        "field-length": 4,
            #                        "text-align": "left"
            #                    }, {
            #                        "name": "page4-part_value__percent-maj",
            #                        "field-length": 3,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page4-part_value__percent-min",
            #                        "field-length": 15,
            #                        "text-align": "left"
            #                    }, {
            #                        "name": "page4-part_value__decimal-maj",
            #                        "field-length": 1,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page4-part_value__decimal-min",
            #                        "field-length": 15,
            #                        "text-align": "left"
            #                    }, {
            #                        "name": "page4-part_value__fraction-left",
            #                        "field-length": 15,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page4-part_value__fraction-right",
            #                        "field-length": 15,
            #                        "text-align": "left"
            #                    }, {
            #                        "name" : "$page",
            #                        "field-length": 3,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }
            #                ],
            #                "array_fields": [
            #                        {
            #                        "name": "page4-full_name__line{{item}}",
            #                        "count": 6,
            #                        "field-length": 40,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page4-reg_organ_name__line{{item}}",
            #                        "count": 4,
            #                        "field-length": 40,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page4-address__line{{item}}",
            #                        "count": 4,
            #                        "field-length": 40,
            #                        "case": "upper"
            #                    }
            #                ]
            #            },
            {
                "page_file": [get_test_resource_name(config, "11001/pg_0005.pdf"),
                              get_test_resource_name(config, "11001/pg_0006.pdf")],
                "multiple": True,
                "array_field": "founders",
                "array_item_filter": {
                    "founder_type": FounderTypeEnum.FT_PERSON
                },
                "fields": [
                    {
                        "name": "page5-surname",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page5-name",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page5-patronymic",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page5-inn",
                        "field-length": 12
                    }, {
                        "name": "page5-birth_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page5-birth_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page5-birth_date__year",
                        "field-length": 4
                    }, {
                        "name": "page5-ogrnip",
                        "field-length": 15
                    }, {
                        "name": "page5-doc_type",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page5-doc_number",
                        "field-length": 25
                    }, {
                        "name": "page5-issue_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page5-issue_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page5-issue_date__year",
                        "field-length": 4
                    }, {
                        "name": "page5-subdivision_code__left",
                        "field-length": 3,
                        "text-align": "left",
                    }, {
                        "name": "page5-subdivision_code__right",
                        "field-length": 3,
                        "text-align": "right",
                    }, {
                        "name": "page6-subject_code",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page6-postal_index",
                        "field-length": 6,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page6-district_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page6-city_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page6-city_name",
                        "field-length": 28,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page6-nas_punkt_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page6-street_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page6-building_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page6-building_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page6-korpus_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page6-korpus_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page6-flat_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page6-flat_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page6-living_country_code",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page6-nominal_part_value__currency-maj",
                        "field-length": 15,
                        "text-align": "right"
                    }, {
                        "name": "page6-nominal_part_value__currency-min",
                        "field-length": 4,
                        "text-align": "left"
                    }, {
                        "name": "page6-part_value__percent-maj",
                        "field-length": 3,
                        "text-align": "right"
                    }, {
                        "name": "page6-part_value__percent-min",
                        "field-length": 15,
                        "text-align": "left"
                    }, {
                        "name": "page6-part_value__decimal-maj",
                        "field-length": 1,
                        "text-align": "right"
                    }, {
                        "name": "page6-part_value__decimal-min",
                        "field-length": 15,
                        "text-align": "left"
                    }, {
                        "name": "page6-part_value__fraction-left",
                        "field-length": 15,
                        "text-align": "right"
                    }, {
                        "name": "page6-part_value__fraction-right",
                        "field-length": 15,
                        "text-align": "left"
                    }, {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }
                ],
                "array_fields": [
                    {
                        "name": "page6-nas_punkt_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    }, {
                        "name": "page6-street_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    }, {
                        "name": "page5-birth_place__line{{item}}",
                        "count": 2,
                        "field-length": 40,
                        "case": "upper"
                    }, {
                        "name": "page5-issuer__line{{item}}",
                        "count": 3,
                        "field-length": [34, 40, 40],
                        "case": "upper"
                    }, {
                        "name": "page6-district_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    }, {
                        "name": "page6-living_address__line{{item}}",
                        "count": 2,
                        "field-length": 40,
                        "case": "upper"
                    }
                ],
            },

            #                {
            #                "page_file": [get_test_resource_name(config, "11001/pg_0007.pdf"), get_test_resource_name(config, "11001/pg_0008.pdf")],
            #                "multiple" : True,
            #                "array_field" : "founders",
            #                "array_item_filter" : {
            #                    "founder_type" : FounderTypeEnum.FT_GOV,
            #                    "company.id.initialized" : True
            #                },
            #                "fields": [
            #                        {
            #                        "name" : "page7-uchreditel_type",
            #                        "field-length": 1,
            #                        }, {
            #                        "name" : "page7-uchreditel_subject_code",
            #                        "field-length" : 2,
            #                        "text-align" : "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name": "page7-nominal_part_value__currency-maj",
            #                        "field-length": 15,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page7-nominal_part_value__currency-min",
            #                        "field-length": 4,
            #                        "text-align": "left"
            #                    }, {
            #                        "name": "page7-nominal_part_value__percent-maj",
            #                        "field-length": 3,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page7-nominal_part_value__percent-min",
            #                        "field-length": 15,
            #                        "text-align": "left"
            #                    }, {
            #                        "name": "page7-nominal_part_value__decimal-maj",
            #                        "field-length": 1,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page7-nominal_part_value__decimal-min",
            #                        "field-length": 15,
            #                        "text-align": "left"
            #                    }, {
            #                        "name": "page7-nominal_part_value__fraction-left",
            #                        "field-length": 15,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page7-nominal_part_value__fraction-right",
            #                        "field-length": 15,
            #                        "text-align": "left"
            #                    }, {
            #                        "name": "page8-ogrn",
            #                        "field-length": 13
            #                    }, {
            #                        "name": "page8-inn",
            #                        "field-length": 10
            #                    }, {
            #                        "name" : "$page",
            #                        "field-length": 3,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }
            #                ],
            #                "array_fields" : [
            #                        {
            #                        "name": "page7-uchreditel_munic_obraz_name__line{{item}}",
            #                        "count": 4,
            #                        "field-length": 40,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page8-full_name__line{{item}}",
            #                        "count": 6,
            #                        "field-length": 40,
            #                        "case": "upper"
            #                    }
            #                ]
            #            },

            #                {
            #                "page_file": [get_test_resource_name(config, "11001/pg_0007.pdf"),
            #                              get_test_resource_name(config, "11001/pg_0008.pdf"),
            #                              get_test_resource_name(config, "11001/pg_0009.pdf")],
            #                "multiple" : True,
            #                "array_field" : "founders",
            #                "array_item_filter" : {
            #                    "founder_type" : FounderTypeEnum.FT_GOV,
            #                    "person.id.initialized" : True
            #                },
            #                "fields": [
            #                        {
            #                        "name" : "page7-uchreditel_type",
            #                        "field-length": 1,
            #                        }, {
            #                        "name" : "page7-uchreditel_subject_code",
            #                        "field-length" : 2,
            #                        "text-align" : "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name": "page7-nominal_part_value__currency-maj",
            #                        "field-length": 15,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page7-nominal_part_value__currency-min",
            #                        "field-length": 4,
            #                        "text-align": "left"
            #                    }, {
            #                        "name": "page7-nominal_part_value__percent-maj",
            #                        "field-length": 3,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page7-nominal_part_value__percent-min",
            #                        "field-length": 15,
            #                        "text-align": "left"
            #                    }, {
            #                        "name": "page7-nominal_part_value__decimal-maj",
            #                        "field-length": 1,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page7-nominal_part_value__decimal-min",
            #                        "field-length": 15,
            #                        "text-align": "left"
            #                    }, {
            #                        "name": "page7-nominal_part_value__fraction-left",
            #                        "field-length": 15,
            #                        "text-align": "right"
            #                    }, {
            #                        "name": "page7-nominal_part_value__fraction-right",
            #                        "field-length": 15,
            #                        "text-align": "left"
            #                    },{
            #                        "name" : "$page",
            #                        "field-length": 3,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name" : "page8-surname",
            #                        "field-length" : 35,
            #                        "text-align" : "left",
            #                        "case" : "upper"
            #                    }, {
            #                        "name" : "page8-name",
            #                        "field-length" : 35,
            #                        "text-align" : "left",
            #                        "case" : "upper"
            #                    }, {
            #                        "name" : "page8-patronymic",
            #                        "field-length" : 35,
            #                        "text-align" : "left",
            #                        "case" : "upper"
            #                    }, {
            #                        "name": "page8-person_inn",
            #                        "field-length": 12
            #                    }, {
            #                        "name": "page8-birth_date__day",
            #                        "field-length": 2,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name": "page8-birth_date__month",
            #                        "field-length": 2,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name": "page8-birth_date__year",
            #                        "field-length": 4
            #                    }, {
            #                        "name" : "page9-doc_type_code",
            #                        "field-length": 2,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name": "page9-doc_number",
            #                        "field-length": 25
            #                    }, {
            #                        "name": "page9-doc_issue_date__day",
            #                        "field-length": 2,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name": "page9-doc_issue_date__month",
            #                        "field-length": 2,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name": "page9-doc_issue_date__year",
            #                        "field-length": 4
            #                    }, {
            #                        "name" : "page9-doc_issuer_subdivision_code__left",
            #                        "field-length": 3,
            #                        "text-align": "left",
            #                        }, {
            #                        "name" : "page9-doc_issuer_subdivision_code__right",
            #                        "field-length": 3,
            #                        "text-align": "right",
            #                        }, {
            #                        "name" : "page9-subject_code",
            #                        "field-length" : 2,
            #                        "text-align" : "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name" : "page9-postal_index",
            #                        "field-length" : 6,
            #                        "text-align" : "right",
            #                        "space-filler" : u"0",
            #                        }, {
            #                        "name" : "page9-district_type",
            #                        "field-length" : 10,
            #                        "text-align" : "left",
            #                        "case" : "upper"
            #                    }, {
            #                        "name" : "page9-city_type",
            #                        "field-length" : 10,
            #                        "text-align" : "left",
            #                        "case" : "upper"
            #                    }, {
            #                        "name" : "page9-city_name",
            #                        "field-length" : 28,
            #                        "text-align" : "left",
            #                        "case" : "upper"
            #                    }, {
            #                        "name": "page9-nas_punkt_type",
            #                        "field-length": 10,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-street_type",
            #                        "field-length": 10,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-house_type",
            #                        "field-length": 10,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-house_number",
            #                        "field-length": 8,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-corpus_type",
            #                        "field-length": 10,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-corpus_number",
            #                        "field-length": 8,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-flat_type",
            #                        "field-length": 10,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-flat_number",
            #                        "field-length": 8,
            #                        "case": "upper"
            #                    }, {
            #                        "name" : "page9-living_country_code",
            #                        "field-length": 3,
            #                        "text-align": "right",
            #                        "space-filler" : u"0",
            #                        }
            #                ],
            #                "array_fields" : [
            #                        {
            #                        "name": "page7-uchreditel_munic_obraz_name__line{{item}}",
            #                        "count": 4,
            #                        "field-length": 40,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-nas_punkt_name__line{{item}}",
            #                        "count": 2,
            #                        "field-length": [28, 40],
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-street_name__line{{item}}",
            #                        "count": 2,
            #                        "field-length": [28, 40],
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page8-birth_place__{{item}}",
            #                        "count": 2,
            #                        "field-length": 40,
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-doc_issuer__line{{item}}",
            #                        "count": 3,
            #                        "field-length": [34, 40, 40],
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-district_name__line{{item}}",
            #                        "count": 2,
            #                        "field-length": [28, 40],
            #                        "case": "upper"
            #                    }, {
            #                        "name": "page9-living_address__line{{item}}",
            #                        "count": 2,
            #                        "field-length": 40,
            #                        "case": "upper"
            #                    }
            #                ]
            #            },
            {
                "page_file": get_test_resource_name(config, "11001/pg_0010.pdf"),
                "multiple": True,
                "array_field": "uit",
                "fields": [
                    {
                        "name": "page10-invest_fond_uprav_company_ogrn",
                        "field-length": 13
                    }, {
                        "name": "page10-invest_fond_uprav_company_inn",
                        "field-length": 10
                    }, {
                        "name": "page10-nominal_value__currency_maj",
                        "field-length": 15,
                        "text-align": "right"
                    }, {
                        "name": "page10-nominal_value__currency_min",
                        "field-length": 4,
                        "text-align": "left"
                    }, {
                        "name": "page10-nominal_value__percent_maj",
                        "field-length": 3,
                        "text-align": "right"
                    }, {
                        "name": "page10-nominal_value__percent_min",
                        "field-length": 15,
                        "text-align": "left"
                    }, {
                        "name": "page10-nominal_value__decimal_maj",
                        "field-length": 1,
                        "text-align": "right"
                    }, {
                        "name": "page10-nominal_value__decimal_min",
                        "field-length": 15,
                        "text-align": "left"
                    }, {
                        "name": "page10-nominal_value__fraction_maj",
                        "field-length": 15,
                        "text-align": "right"
                    }, {
                        "name": "page10-nominal_value__fraction_min",
                        "field-length": 15,
                        "text-align": "left"
                    }, {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page8-surname",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }
                ],
                "array_fields": [
                    {
                        "name": "page10-invest_fond_name__line{{item}}",
                        "count": 6,
                        "field-length": 40,
                        "case": "upper"
                    }, {
                        "name": "page10-invest_fond_uprav_company_full_name__line{{item}}",
                        "count": 6,
                        "field-length": 40,
                        "case": "upper"
                    }]
            }, {
                "page_file": [get_test_resource_name(config, "11001/pg_0011.pdf"),
                              get_test_resource_name(config, "11001/pg_0012.pdf")],
                "fields": [
                    {
                        "name": "page11-surname",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page11-name",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page11-patronymic",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page11-inn",
                        "field-length": 12
                    }, {
                        "name": "page11-birth_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page11-birth_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page11-birth_date__year",
                        "field-length": 4
                    }, {
                        "name": "page11-doc_type_code",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page11-doc_number",
                        "field-length": 25
                    }, {
                        "name": "page11-doc_issue_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page11-doc_issue_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page11-doc_issue_date__year",
                        "field-length": 4
                    }, {
                        "name": "page11-doc_issuer_subdivision_code__left",
                        "field-length": 3,
                        "text-align": "left",
                    }, {
                        "name": "page11-doc_issuer_subdivision_code__right",
                        "field-length": 3,
                        "text-align": "right",
                    }, {
                        "name": "page12-subject_code",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page12-postal_index",
                        "field-length": 6,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page12-district_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page12-city_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page12-city_name",
                        "field-length": 28,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page12-nas_punkt_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page12-street_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page12-house_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page12-house_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page12-corpus_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page12-corpus_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page12-flat_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page12-flat_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page12-living_country_code",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page12-phone_number",
                        "field-length": 20,
                    }, {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }
                ],
                "array_fields": [
                    {
                        "name": "page12-nas_punkt_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    }, {
                        "name": "page12-street_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    }, {
                        "name": "page11-birth_place__line{{item}}",
                        "count": 2,
                        "field-length": 40,
                        "case": "upper"
                    }, {
                        "name": "page11-doc_issuer__line{{item}}",
                        "count": 3,
                        "field-length": [34, 40, 40],
                        "case": "upper"
                    }, {
                        "name": "page12-district_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    }, {
                        "name": "page12-living_address__line{{item}}",
                        "count": 2,
                        "field-length": 40,
                        "case": "upper"
                    }, {
                        "name": "page11-title__line{{item}}",
                        "count": 2,
                        "field-length": 80,
                        "case": "upper"
                    }
                ],
            }, {
                "variants": {
                    "type": RenderingVariants.TYPE_RENDER_FIRST_MATCHING,
                    "cases": [{
                                  "page_file": [get_test_resource_name(config, "11001/pg_0013.pdf"),
                                                get_test_resource_name(config, "11001/pg_0014.pdf")],
                                  "field_matcher_set": "%page_Je-set-1",
                                  "conditions": {
                                      "management_company.company.id.initialized": True
                                  }
                              }, {
                                  "page_file": [get_test_resource_name(config, "11001/pg_0013.pdf"),
                                                get_test_resource_name(config, "11001/pg_0014.pdf"),
                                                get_test_resource_name(config, "11001/pg_0015.pdf")],
                                  "field_matcher_set": "%page_Je-set-3",
                                  "conditions": {
                                      "management_company.foreign_company.id.initialized": True,
                                      "management_company.russian_agent.id.initialized": True
                                  }
                              }, {
                                  "page_file": [get_test_resource_name(config, "11001/pg_0013.pdf"),
                                                get_test_resource_name(config, "11001/pg_0014.pdf")],
                                  "field_matcher_set": "%page_Je-set-2",
                                  "conditions": {
                                      "management_company.foreign_company.id.initialized": True
                                  }
                              }]
                },
                "fields": [
                    {
                        "name": "page13-ogrn",
                        "field-length": 13
                    }, {
                        "name": "page13-inn",
                        "field-length": 10
                    }, {
                        "name": "page13-reg_number",
                        "field-length": 25
                    }, {
                        "name": "page13-country_code",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page13-reg_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page13-reg_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page13-reg_date__year",
                        "field-length": 4
                    }, {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page14-subject_code",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page14-postal_index",
                        "field-length": 6,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page14-district_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page14-city_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page14-city_name",
                        "field-length": 28,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page14-nas_punkt_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page14-street_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page14-house_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page14-house_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page14-corpus_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page14-corpus_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page14-flat_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page14-flat_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page14-phone_number",
                        "field-length": 20,
                    }, {
                        "name": "page14-surname",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page14-name",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page14-patronymic",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page14-inn",
                        "field-length": 12
                    }, {
                        "name": "page14-birth_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page14-birth_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page14-birth_date__year",
                        "field-length": 4
                    }, {
                        "name": "page15-doc_type_code",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page15-doc_number",
                        "field-length": 25
                    }, {
                        "name": "page15-doc_issue_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page15-doc_issue_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page15-doc_issue_date__year",
                        "field-length": 4
                    }, {
                        "name": "page15-doc_issuer_subdivision_code__left",
                        "field-length": 3,
                        "text-align": "left",
                    }, {
                        "name": "page15-doc_issuer_subdivision_code__right",
                        "field-length": 3,
                        "text-align": "right",
                    }, {
                        "name": "page15-subject_code",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page15-postal_index",
                        "field-length": 6,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page15-district_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page15-city_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page15-city_name",
                        "field-length": 28,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page15-nas_punkt_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page15-street_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page15-house_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page15-house_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page15-corpus_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page15-corpus_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page15-flat_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page15-flat_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page15-living_country_code",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page15-phone_number",
                        "field-length": 20,
                    }
                ],
                "array_fields": [{
                                     "name": "page13-full_name__line{{item}}",
                                     "count": 6,
                                     "field-length": 40,
                                     "case": "upper"
                                 }, {
                                     "name": "page13-reg_organ_name__line{{item}}",
                                     "count": 4,
                                     "field-length": 40,
                                     "case": "upper"
                                 }, {
                                     "name": "page13-reg_organ_address__line{{item}}",
                                     "count": 3,
                                     "field-length": 40,
                                     "case": "upper"
                                 }, {
                                     "name": "page13-predstav_full_name__line{{item}}",
                                     "count": 6,
                                     "field-length": 40,
                                     "case": "upper"
                                 }, {
                                     "name": "page14-nas_punkt_name__line{{item}}",
                                     "count": 2,
                                     "field-length": [28, 40],
                                     "case": "upper"
                                 }, {
                                     "name": "page14-street_name__line{{item}}",
                                     "count": 2,
                                     "field-length": [28, 40],
                                     "case": "upper"
                                 }, {
                                     "name": "page14-district_name__line{{item}}",
                                     "count": 2,
                                     "field-length": [28, 40],
                                     "case": "upper"
                                 }, {
                                     "name": "page15-nas_punkt_name__line{{item}}",
                                     "count": 2,
                                     "field-length": [28, 40],
                                     "case": "upper"
                                 }, {
                                     "name": "page15-street_name__line{{item}}",
                                     "count": 2,
                                     "field-length": [28, 40],
                                     "case": "upper"
                                 }, {
                                     "name": "page14-birth_place__line{{item}}",
                                     "count": 2,
                                     "field-length": 40,
                                     "case": "upper"
                                 }, {
                                     "name": "page15-doc_issuer__line{{item}}",
                                     "count": 3,
                                     "field-length": [34, 40, 40],
                                     "case": "upper"
                                 }, {
                                     "name": "page15-district_name__line{{item}}",
                                     "count": 2,
                                     "field-length": [28, 40],
                                     "case": "upper"
                                 }, {
                                     "name": "page15-living_address__line{{item}}",
                                     "count": 2,
                                     "field-length": 40,
                                     "case": "upper"
                                 }]
            }, {
                "conditions": {
                    "manager.id.initialized": True
                },
                "page_file": [get_test_resource_name(config, "11001/pg_0016.pdf"),
                              get_test_resource_name(config, "11001/pg_0017.pdf")],
                "fields": [
                    {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page16-ogrnip",
                        "field-length": 15
                    }, {
                        "name": "page16-surname",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page16-name",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page16-patronymic",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page16-inn",
                        "field-length": 12
                    }, {
                        "name": "page16-birth_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page16-birth_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page16-birth_date__year",
                        "field-length": 4
                    }, {
                        "name": "page16-doc_type_code",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page16-doc_type_number",
                        "field-length": 25
                    }, {
                        "name": "page16-doc_issue_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page16-doc_issue_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page16-doc_issue_date__year",
                        "field-length": 4
                    }, {
                        "name": "page16-doc_issuer_subdivision_code__left",
                        "field-length": 3,
                        "text-align": "left",
                    }, {
                        "name": "page16-doc_issuer_subdivision_code__right",
                        "field-length": 3,
                        "text-align": "right",
                    }, {
                        "name": "page17-subject_code",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page17-postal_index",
                        "field-length": 6,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page17-district_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page17-city_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page17-city_name",
                        "field-length": 28,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page17-nas_punkt_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page17-street_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page17-house_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page17-house_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page17-corpus_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page17-corpus_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page17-flat_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page17-flat_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page17-phone_number",
                        "field-length": 20,
                    }
                ],
                "array_fields": [{
                                     "name": "page16-birth_place__line{{item}}",
                                     "count": 2,
                                     "field-length": 40,
                                     "case": "upper"
                                 }, {
                                     "name": "page16-doc_issuer__line{{item}}",
                                     "count": 3,
                                     "field-length": [34, 40, 40],
                                     "case": "upper"
                                 }, {
                                     "name": "page17-nas_punkt_name__line{{item}}",
                                     "count": 2,
                                     "field-length": [28, 40],
                                     "case": "upper"
                                 }, {
                                     "name": "page17-street_name__line{{item}}",
                                     "count": 2,
                                     "field-length": [28, 40],
                                     "case": "upper"
                                 }, {
                                     "name": "page17-district_name__line{{item}}",
                                     "count": 2,
                                     "field-length": [28, 40],
                                     "case": "upper"
                                 }
                ]
            }, {
                "page_file": get_test_resource_name(config, "11001/pg_0018.pdf"),
                "fields": [
                    {
                        "name": "page18-main_job_code__part1",
                        "field-length": 2,
                        "text-align": "left",
                    }, {
                        "name": "page18-main_job_code__part2",
                        "field-length": 2,
                        "text-align": "center",
                    }, {
                        "name": "page18-main_job_code__part3",
                        "field-length": 2,
                        "text-align": "right",
                    }, {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }
                ],
                "array_fields": [{
                                     "name": "page18-job_code#{{item}}__part1",
                                     "field-length": 2,
                                     "count": 14 * 4,
                                     "text-align": "left",
                                 }, {
                                     "name": "page18-job_code#{{item}}__part2",
                                     "field-length": 2,
                                     "count": 14 * 4,
                                     "text-align": "center",
                                 }, {
                                     "name": "page18-job_code#{{item}}__part3",
                                     "field-length": 2,
                                     "count": 14 * 4,
                                     "text-align": "right",
                                 }]
            }, {
                "page_file": get_test_resource_name(config, "11001/pg_0019.pdf"),
                "conditions": {
                    "holder_share.holder_type": JSCMemberTypeEnum.JSCMT_REGISTRATOR,
                    "holder_share.company.id.initialized": True
                },
                "fields": [
                    {
                        "name": "page19-ogrn",
                        "field-length": 13
                    }, {
                        "name": "page19-inn",
                        "field-length": 10
                    }, {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }
                ],
                "array_fields": [{
                                     "name": "page19-full_name__line{{item}}",
                                     "field-length": 40,
                                     "case": "upper",
                                     "count": 6
                                 }]
            },
            {
                "page_file": get_test_resource_name(config, "11001/pg_0020.pdf"),
                "multiple": True,
                "array_field": "farm_companies",
                "fields": [
                    {
                        "name": "page20-ogrnip",
                        "field-length": 15
                    }, {
                        "name": "page20-surname",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page20-name",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page20-patronymic",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page20-inn",
                        "field-length": 12
                    }, {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }
                ]
            }, {
                "multiple": True,
                "array_field": "founders",
                "sort": {
                    "field": "documents_recipient_type",
                    "order": "desc"
                },
                "variants": {
                    "type": RenderingVariants.TYPE_RENDER_FIRST_MATCHING,
                    "cases": [{  # учредитель - единственное физ. лицо
                                 "page_file": [get_test_resource_name(config, "11001/pg_0022.pdf"),
                                               get_test_resource_name(config, "11001/pg_0024.pdf")],
                                 "field_matcher_set": "%page_N-set-1",
                                 "conditions": {
                                     "founders[].founder_type": FounderTypeEnum.FT_PERSON,
                                     "founders": {
                                         "#size": 1
                                     }
                                 },
                                 }, {
                              # учредитель - физ лицо, кол-во учредителей > 1. при этом есть учредитель-физ лицо, ФИО которого совпадает с данным
                              "page_file": [get_test_resource_name(config, "11001/pg_0022.pdf"),
                                            get_test_resource_name(config, "11001/pg_0024.pdf")],
                              "field_matcher_set": "%page_N-set-2dup",
                              "conditions": {
                                  "founders[].founder_type": FounderTypeEnum.FT_PERSON,
                                  "founders[].duplicate_fio": True
                              }
                              }, {  # учредитель - физ лицо, кол-во учредителей > 1
                                    "page_file": [get_test_resource_name(config, "11001/pg_0022.pdf"),
                                                  get_test_resource_name(config, "11001/pg_0024.pdf")],
                                    "field_matcher_set": "%page_N-set-2",
                                    "conditions": {
                                        "founders[].founder_type": FounderTypeEnum.FT_PERSON,
                                    }
                                    }, {  # единственный учредитель - российское юр. лицо
                                          "page_file": [get_test_resource_name(config, "11001/pg_0022.pdf"),
                                                        get_test_resource_name(config, "11001/pg_0023.pdf"),
                                                        get_test_resource_name(config, "11001/pg_0024.pdf")],
                                          "field_matcher_set": "%page_N-set-5",
                                          "conditions": {
                                              "founders[].founder_type": FounderTypeEnum.FT_COMPANY,
                                              "founders": {
                                                  "#size": 1
                                              }
                                          }
                                          }, {  # учредитель - российское юр. лицо, кол-во учредителей > 1
                                                "page_file": [get_test_resource_name(config, "11001/pg_0022.pdf"),
                                                              get_test_resource_name(config, "11001/pg_0023.pdf"),
                                                              get_test_resource_name(config, "11001/pg_0024.pdf")],
                                                "field_matcher_set": "%page_N-set-3",
                                                "conditions": {
                                                    "founders[].founder_type": FounderTypeEnum.FT_COMPANY,
                                                }
                                                },
                              #                            { # учредитель - иностранное юр. лицо
                              #                         "page_file": [get_test_resource_name(config, "11001/pg_0022.pdf"),
                              #                                       get_test_resource_name(config, "11001/pg_0023.pdf"),
                              #                                       get_test_resource_name(config, "11001/pg_0024.pdf")],
                              #                         "field_matcher_set" : "%page_N-set-4",
                              #                         "conditions" : {
                              #                             "founders[].founder_type" : FounderTypeEnum.FT_FOREIGN_COMPANY,
                              #                            },
                              #                         }
                              ]
                },
                "fields": [
                    {
                        "name": "page22-zayavitel_type",
                        "field-length": 1,
                    }, {
                        "name": "page22-ogrn",
                        "field-length": 13
                    }, {
                        "name": "page22-uchreditel_inn",
                        "field-length": 10
                    }, {
                        "name": "page22-upravlyayuschiy_ogrn",
                        "field-length": 13
                    }, {
                        "name": "page22-upravlyayuschiy_inn",
                        "field-length": 10
                    }, {
                        "name": "page22-zayavitel_surname",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page22-zayavitel_name",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page22-zayavitel_patronymic",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page22-zayavitel_inn",
                        "field-length": 12
                    }, {
                        "name": "page22-zayavitel_birth_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page22-zayavitel_birth_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page22-zayavitel_birth_date__year",
                        "field-length": 4
                    }, {
                        "name": "page23-doc_type",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page23-doc_number",
                        "field-length": 25
                    }, {
                        "name": "page23-doc_issue_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page23-doc_issue_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page23-doc_issue_date__year",
                        "field-length": 4
                    }, {
                        "name": "page23-issuer_subdivision_code__left",
                        "field-length": 3,
                        "text-align": "left",
                    }, {
                        "name": "page23-issuer_subdivision_code__right",
                        "field-length": 3,
                        "text-align": "right",
                    }, {
                        "name": "page23-address_subject_code",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page23-postal_index",
                        "field-length": 6,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page23-address_district_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page23-address_city_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page23-address_city_name",
                        "field-length": 28,
                        "text-align": "left",
                        "case": "upper"
                    }, {
                        "name": "page23-address_nas_punkt_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page23-address_street_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page23-address_house_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page23-address_house_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page23-address_corpus_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page23-address_corpus_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page23-address_flat_type",
                        "field-length": 10,
                        "case": "upper"
                    }, {
                        "name": "page23-address_flat_number",
                        "field-length": 8,
                        "case": "upper"
                    }, {
                        "name": "page23-phone_number",
                        "field-length": 20,
                    }, {
                        "name": "page23-living_country_code",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }, {
                        "name": "page23-email",
                        "field-length": 35,
                        "case": "upper"
                    }, {
                        "name": "page24-document_delivery_type",
                        "field-length": 1
                    }, {
                        "name": "page24-zaveritel_type",
                        "field-length": 1
                    }, {
                        "name": "page24-inn_zaveritelya",
                        "field-length": 12
                    }, {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }
                ], "array_fields": [
                {
                    "name": "page22-uchreditel_full_name__line{{item}}",
                    "count": 6,
                    "field-length": 40,
                    "case": "upper"
                }, {
                    "name": "page22-upravlyayuschiy_full_name__line{{item}}",
                    "count": 6,
                    "field-length": 40,
                    "case": "upper"
                }, {
                    "name": "page22-zayavitel_birth_place__line{{item}}",
                    "count": 2,
                    "field-length": 40,
                    "case": "upper"
                }, {
                    "name": "page23-issuer__line{{item}}",
                    "count": 3,
                    "field-length": [33, 40, 40],
                    "case": "upper"
                }, {
                    "name": "page23-address_nas_punkt_name__line{{item}}",
                    "count": 2,
                    "field-length": [28, 40],
                    "case": "upper"
                }, {
                    "name": "page23-address_street_name__line{{item}}",
                    "count": 2,
                    "field-length": [28, 40],
                    "case": "upper"
                }, {
                    "name": "page23-address_district_name__line{{item}}",
                    "count": 2,
                    "field-length": [28, 40],
                    "case": "upper"
                }, {
                    "name": "page23-living_address__line{{item}}",
                    "count": 2,
                    "field-length": 40,
                    "case": "upper"
                }
            ]}
        ]
    }

    P11001_MATCHER = {
        "doc_name": DocumentTypeEnum.DT_P11001,
        "template_name": P11001_TEMPLATE['template_name'],
        "fields": {
            "page1-polnoe_naimenovanie__line{{item}}": MultilineFieldMatcher(field_name="full_name",
                                                                             prefix=u"Общество с ограниченной ответственностью «",
                                                                             suffix=u"»"),
            "page1-sokr_naimenovanie__line{{item}}": MultilineFieldMatcher(field_name="short_name", prefix=u"ООО «",
                                                                           suffix=u"»"),
            "page1-subject_code": FieldAttributeMatcher(field_name="address", attr_name="region",
                                                        adapter="RFRegionNumberAdapter"),
            "page1-pocht_index": FieldAttributeMatcher(field_name="address", attr_name="index"),
            "page1-district_type": FieldAttributeMatcher(field_name="address", attr_name="district_type",
                                                         adapter="ShortDistrictTypeAdapter"),
            "page1-district_name__line{{item}}": MultilineFieldMatcher(field_name="address",
                                                                       attr_name="district"),
            "page1-city_type": FieldAttributeMatcher(field_name="address", attr_name="city_type",
                                                     adapter="ShortCityTypeAdapter"),
            "page1-city_name": FieldAttributeMatcher(field_name="address", attr_name="city"),

            "page2-nas_punkt_type": FieldAttributeMatcher(field_name="address", attr_name="village_type",
                                                          adapter="ShortVillageTypeAdapter"),
            "page2-nas_punkt_name__line{{item}}": MultilineFieldMatcher(field_name="address",
                                                                        attr_name="village"),
            "page2-street_type": FieldAttributeMatcher(field_name="address", attr_name="street_type",
                                                       adapter="ShortStreetTypeAdapter"),
            "page2-street_name__line{{item}}": MultilineFieldMatcher(field_name="address",
                                                                     attr_name="street"),
            "page2-house_type": FieldAttributeMatcher(field_name="address", attr_name="house_type"),
            "page2-house_number": FieldAttributeMatcher(field_name="address", attr_name="house"),
            "page2-corpus_type": FieldAttributeMatcher(field_name="address", attr_name="building_type"),
            "page2-corpus_number": FieldAttributeMatcher(field_name="address", attr_name="building"),
            "page2-office_type": FieldAttributeMatcher(field_name="address", attr_name="flat_type"),
            "page2-office_number": FieldAttributeMatcher(field_name="address", attr_name="flat"),
            "page2-nach_capital_type": FieldAttributeMatcher(field_name="starter_capital",
                                                             attr_name="capital_type"),
            "page2-akc_obchestvo_member_type": FieldAttributeMatcher(field_name="holder_share", attr_name="holder_type",
                                                                     adapter="JSCMemberTypeNumberAdapter"),
            "page2-nach_capital_value__currency-maj": FieldAttributeMatcher(field_name="starter_capital",
                                                                            attr_name="value.currency_major"),
            "page2-nach_capital_value__currency-min": FieldAttributeMatcher(field_name="starter_capital",
                                                                            attr_name="value.currency_minor"),

            "page3-ogrn": FieldAttributeMatcher(field_name="founders[]", attr_name="company.ogrn"),
            "page3-inn": FieldAttributeMatcher(field_name="founders[]", attr_name="company.inn"),
            "page3-polnoe_naimenovanie__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                             attr_name="company.qualified_full_name"),
            "page3-nominal_part_value__currency-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="nominal_capital.currency_major"),
            "page3-nominal_part_value__currency-min": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="nominal_capital.currency_minor"),
            "page3-razmer_doli__percent-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="share.percent_major"),
            "page3-razmer_doli__percent-min": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="share.percent_minor"),
            "page3-razmer_doli__decimal-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="share.decimal_major"),
            "page3-razmer_doli__decimal-min": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="share.decimal_minor"),
            "page3-razmer_doli__fraction-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="share.fraction_major"),
            "page3-razmer_doli__fraction-min": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="share.fraction_minor"),

            "page4-full_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                   attr_name="company.full_name"),
            "page4-country_code": FieldAttributeMatcher(field_name="founders[]",
                                                        attr_name="company.country_code"),
            "page4-reg_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                         attr_name="company.registration_date.day"),
            "page4-reg_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                           attr_name="company.registration_date.month"),
            "page4-reg_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                          attr_name="company.registration_date.year"),
            "page4-reg_number": FieldAttributeMatcher(field_name="founders[]",
                                                      attr_name="company.registration_number"),
            "page4-reg_organ_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                        attr_name="company.registration_depart"),
            "page4-address__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                 attr_name="company.generic_address"),
            "page4-inn": FieldAttributeMatcher(field_name="founders[]", attr_name="company.inn"),
            "page4-nominal_part_value__currency-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="nominal_capital.currency_major"),
            "page4-nominal_part_value__currency-min": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="nominal_capital.currency_minor"),
            "page4-part_value__percent-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="share.percent_major"),
            "page4-part_value__percent-min": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="share.percent_minor"),
            "page4-part_value__decimal-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="share.decimal_major"),
            "page4-part_value__decimal-min": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="share.decimal_minor"),
            "page4-part_value__fraction-left": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="share.fraction_major"),
            "page4-part_value__fraction-right": FieldAttributeMatcher(field_name="founders[]",
                                                                      attr_name="share.fraction_minor"),

            "page5-surname": FieldAttributeMatcher(field_name="founders[]", attr_name="person.surname"),
            "page5-name": FieldAttributeMatcher(field_name="founders[]", attr_name="person.name"),
            "page5-patronymic": FieldAttributeMatcher(field_name="founders[]", attr_name="person.patronymic"),
            "page5-inn": FieldAttributeMatcher(field_name="founders[]", attr_name="person.inn"),
            "page5-birth_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                           attr_name="person.birthdate.day"),
            "page5-birth_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                             attr_name="person.birthdate.month"),
            "page5-birth_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                            attr_name="person.birthdate.year"),
            "page5-birth_place__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                     attr_name="person.birthplace"),
            "page5-issuer__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                attr_name="person.passport.issue_depart"),
            "page5-ogrnip": FieldAttributeMatcher(field_name="founders[]", attr_name="person.ogrnip"),
            "page5-doc_type": FieldAttributeMatcher(field_name="founders[]",
                                                    attr_name="person.passport.document_type"),
            "page5-doc_number": ConcatFieldAttributeMatcher(field_name="founders[]",
                                                            attributes=["person.passport.series",
                                                                        "person.passport.number"],
                                                            adapter="InternalPassportAdapter"),
            "page5-issue_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                           attr_name="person.passport.issue_date.day"),
            "page5-issue_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                             attr_name="person.passport.issue_date.month"),
            "page5-issue_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                            attr_name="person.passport.issue_date.year"),
            "page5-subdivision_code__left": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="person.passport.depart_code"),
            "page5-subdivision_code__right": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="person.passport.depart_code"),

            "page6-postal_index": FieldAttributeMatcher(field_name="founders[]",
                                                        attr_name="person.address.index"),
            "page6-subject_code": FieldAttributeMatcher(field_name="founders[]", attr_name="person.address.region",
                                                        adapter="RFRegionNumberAdapter"),
            "page6-district_type": FieldAttributeMatcher(field_name="founders[]",
                                                         attr_name="person.address.district_type",
                                                         adapter="ShortDistrictTypeAdapter"),
            "page6-city_type": FieldAttributeMatcher(field_name="founders[]", attr_name="person.address.city_type",
                                                     adapter="ShortCityTypeAdapter"),
            "page6-city_name": FieldAttributeMatcher(field_name="founders[]",
                                                     attr_name="person.address.city"),
            "page6-nas_punkt_type": FieldAttributeMatcher(field_name="founders[]",
                                                          attr_name="person.address.village_type",
                                                          adapter="ShortVillageTypeAdapter"),
            "page6-street_type": FieldAttributeMatcher(field_name="founders[]", attr_name="person.address.street_type",
                                                       adapter="ShortStreetTypeAdapter"),
            "page6-building_type": FieldAttributeMatcher(field_name="founders[]",
                                                         attr_name="person.address.house_type"),
            "page6-korpus_type": FieldAttributeMatcher(field_name="founders[]",
                                                       attr_name="person.address.building_type"),
            "page6-building_number": FieldAttributeMatcher(field_name="founders[]",
                                                           attr_name="person.address.house"),
            "page6-korpus_number": FieldAttributeMatcher(field_name="founders[]",
                                                         attr_name="person.address.building"),
            "page6-flat_type": FieldAttributeMatcher(field_name="founders[]",
                                                     attr_name="person.address.flat_type"),
            "page6-flat_number": FieldAttributeMatcher(field_name="founders[]",
                                                       attr_name="person.address.flat"),
            "page6-living_country_code": FieldAttributeMatcher(field_name="founders[]",
                                                               attr_name="person.living_country_code"),

            "page6-nominal_part_value__currency-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="nominal_capital.currency_major"),
            "page6-nominal_part_value__currency-min": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="nominal_capital.currency_minor"),
            "page6-part_value__percent-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="share.percent_major"),
            "page6-part_value__percent-min": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="share.percent_minor"),
            "page6-part_value__decimal-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="share.decimal_major"),
            "page6-part_value__decimal-min": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="share.decimal_minor"),
            "page6-part_value__fraction-left": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="share.fraction_major"),
            "page6-part_value__fraction-right": FieldAttributeMatcher(field_name="founders[]",
                                                                      attr_name="share.fraction_minor"),

            "page6-district_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                       attr_name="person.address.district"),
            "page6-nas_punkt_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                        attr_name="person.address.village"),
            "page6-street_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                     attr_name="person.address.street"),
            "page6-living_address__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                        attr_name="person.living_address"),

            "page7-uchreditel_type": FieldAttributeMatcher(field_name="founders[]", attr_name="gov_founder_type",
                                                           adapter="GovernmentFounderTypeNumberAdapter"),
            "page7-uchreditel_subject_code": FieldAttributeMatcher(field_name="founders[]", attr_name="region",
                                                                   adapter="RFRegionNumberAdapter"),
            "page7-uchreditel_munic_obraz_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                     attr_name="name"),
            "page7-nominal_part_value__currency-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="nominal_capital.currency_major"),
            "page7-nominal_part_value__currency-min": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="nominal_capital.currency_minor"),
            "page7-nominal_part_value__percent-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                           attr_name="share.percent_major"),
            "page7-nominal_part_value__percent-min": FieldAttributeMatcher(field_name="founders[]",
                                                                           attr_name="share.percent_minor"),
            "page7-nominal_part_value__decimal-maj": FieldAttributeMatcher(field_name="founders[]",
                                                                           attr_name="share.decimal_major"),
            "page7-nominal_part_value__decimal-min": FieldAttributeMatcher(field_name="founders[]",
                                                                           attr_name="share.decimal_minor"),
            "page7-nominal_part_value__fraction-left": FieldAttributeMatcher(field_name="founders[]",
                                                                             attr_name="share.fraction_major"),
            "page7-nominal_part_value__fraction-right": FieldAttributeMatcher(field_name="founders[]",
                                                                              attr_name="share.fraction_minor"),

            "page8-ogrn": FieldAttributeMatcher(field_name="founders[]", attr_name="company.ogrn"),
            "page8-inn": FieldAttributeMatcher(field_name="founders[]", attr_name="company.inn"),
            "page8-full_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                   attr_name="company.qualified_full_name"),
            "page8-surname": FieldAttributeMatcher(field_name="founders[]", attr_name="person.surname"),
            "page8-name": FieldAttributeMatcher(field_name="founders[]", attr_name="person.name"),
            "page8-patronymic": FieldAttributeMatcher(field_name="founders[]", attr_name="person.patronymic"),
            "page8-birth_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                           attr_name="person.birthdate.day"),
            "page8-birth_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                             attr_name="person.birthdate.month"),
            "page8-birth_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                            attr_name="person.birthdate.year"),
            "page8-birth_place__{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                 attr_name="person.birthplace"),
            "page8-person_inn": FieldAttributeMatcher(field_name="founders[]", attr_name="person.inn"),

            "page9-doc_type_code": FieldAttributeMatcher(field_name="founders[]",
                                                         attr_name="person.passport.document_type"),
            "page9-doc_number": ConcatFieldAttributeMatcher(field_name="founders[]",
                                                            attributes=["person.passport.series",
                                                                        "person.passport.number"],
                                                            adapter="InternalPassportAdapter"),
            "page9-doc_issue_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                               attr_name="person.passport.issue_date.day"),
            "page9-doc_issue_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                                 attr_name="person.passport.issue_date.month"),
            "page9-doc_issue_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                                attr_name="person.passport.issue_date.year"),
            "page9-doc_issuer__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                    attr_name="person.passport.issue_depart"),
            "page9-doc_issuer_subdivision_code__left": FieldAttributeMatcher(field_name="founders[]",
                                                                             attr_name="person.passport.depart_code"),
            "page9-doc_issuer_subdivision_code__right": FieldAttributeMatcher(field_name="founders[]",
                                                                              attr_name="person.passport.depart_code"),

            "page9-postal_index": FieldAttributeMatcher(field_name="founders[]",
                                                        attr_name="person.address.index"),
            "page9-subject_code": FieldAttributeMatcher(field_name="founders[]", attr_name="person.address.region",
                                                        adapter="RFRegionNumberAdapter"),
            "page9-district_type": FieldAttributeMatcher(field_name="founders[]",
                                                         attr_name="person.address.district_type",
                                                         adapter="ShortDistrictTypeAdapter"),
            "page9-district_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                       attr_name="person.address.district"),
            "page9-city_type": FieldAttributeMatcher(field_name="founders[]", attr_name="person.address.city_type",
                                                     adapter="ShortCityTypeAdapter"),
            "page9-street_type": FieldAttributeMatcher(field_name="founders[]", attr_name="person.address.street_type",
                                                       adapter="ShortStreetTypeAdapter"),
            "page9-street_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                     attr_name="person.address.street"),
            "page9-house_type": FieldAttributeMatcher(field_name="founders[]",
                                                      attr_name="person.address.house_type"),
            "page9-house_number": FieldAttributeMatcher(field_name="founders[]",
                                                        attr_name="person.address.house"),
            "page9-corpus_type": FieldAttributeMatcher(field_name="founders[]",
                                                       attr_name="person.address.building_type"),
            "page9-corpus_number": FieldAttributeMatcher(field_name="founders[]",
                                                         attr_name="person.address.building"),
            "page9-flat_type": FieldAttributeMatcher(field_name="founders[]",
                                                     attr_name="person.address.flat_type"),
            "page9-flat_number": FieldAttributeMatcher(field_name="founders[]",
                                                       attr_name="person.address.flat"),
            "page9-nas_punkt_type": FieldAttributeMatcher(field_name="founders[]",
                                                          attr_name="person.address.village_type",
                                                          adapter="ShortVillageTypeAdapter"),
            "page9-nas_punkt_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                        attr_name="person.address.village"),
            "page9-city_name": FieldAttributeMatcher(field_name="founders[]",
                                                     attr_name="person.address.city"),
            "page9-living_country_code": FieldAttributeMatcher(field_name="founders[]",
                                                               attr_name="person.living_country_code"),
            "page9-living_address__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                        attr_name="person.living_address"),

            "page10-invest_fond_name__line{{item}}": MultilineFieldMatcher(field_name="uit[]",
                                                                           attr_name="name"),
            "page10-invest_fond_uprav_company_ogrn": FieldAttributeMatcher(field_name="uit[]",
                                                                           attr_name="company.ogrn"),
            "page10-invest_fond_uprav_company_inn": FieldAttributeMatcher(field_name="uit[]",
                                                                          attr_name="company.inn"),
            "page10-invest_fond_uprav_company_full_name__line{{item}}": MultilineFieldMatcher(field_name="uit[]",
                                                                                              attr_name="company.qualified_full_name"),

            "page10-nominal_value__currency_maj": FieldAttributeMatcher(field_name="uit[]",
                                                                        attr_name="nominal_capital.currency_major"),
            "page10-nominal_value__currency_min": FieldAttributeMatcher(field_name="uit[]",
                                                                        attr_name="nominal_capital.currency_minor"),
            "page10-nominal_value__percent_maj": FieldAttributeMatcher(field_name="uit[]",
                                                                       attr_name="share.percent_major"),
            "page10-nominal_value__percent_min": FieldAttributeMatcher(field_name="uit[]",
                                                                       attr_name="share.percent_minor"),
            "page10-nominal_value__decimal_maj": FieldAttributeMatcher(field_name="uit[]",
                                                                       attr_name="share.decimal_major"),
            "page10-nominal_value__decimal_min": FieldAttributeMatcher(field_name="uit[]",
                                                                       attr_name="share.decimal_minor"),
            "page10-nominal_value__fraction_maj": FieldAttributeMatcher(field_name="uit[]",
                                                                        attr_name="share.fraction_major"),
            "page10-nominal_value__fraction_min": FieldAttributeMatcher(field_name="uit[]",
                                                                        attr_name="share.fraction_minor"),

            "page11-surname": FieldAttributeMatcher(field_name="general_manager", attr_name="surname"),
            "page11-name": FieldAttributeMatcher(field_name="general_manager", attr_name="name"),
            "page11-patronymic": FieldAttributeMatcher(field_name="general_manager", attr_name="patronymic"),
            "page11-inn": FieldAttributeMatcher(field_name="general_manager", attr_name="inn"),
            "page11-birth_date__day": FieldAttributeMatcher(field_name="general_manager",
                                                            attr_name="birthdate.day"),
            "page11-birth_date__month": FieldAttributeMatcher(field_name="general_manager",
                                                              attr_name="birthdate.month"),
            "page11-birth_date__year": FieldAttributeMatcher(field_name="general_manager",
                                                             attr_name="birthdate.year"),
            "page11-birth_place__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                      attr_name="birthplace"),
            "page11-doc_issuer__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                     attr_name="passport.issue_depart"),
            "page11-doc_type_code": FieldAttributeMatcher(field_name="general_manager",
                                                          attr_name="passport.document_type"),
            "page11-doc_number": ConcatFieldAttributeMatcher(field_name="general_manager",
                                                             attributes=["passport.series",
                                                                         "passport.number"],
                                                             adapter="InternalPassportAdapter"),
            "page11-doc_issue_date__day": FieldAttributeMatcher(field_name="general_manager",
                                                                attr_name="passport.issue_date.day"),
            "page11-doc_issue_date__month": FieldAttributeMatcher(field_name="general_manager",
                                                                  attr_name="passport.issue_date.month"),
            "page11-doc_issue_date__year": FieldAttributeMatcher(field_name="general_manager",
                                                                 attr_name="passport.issue_date.year"),
            "page11-doc_issuer_subdivision_code__left": FieldAttributeMatcher(field_name="general_manager",
                                                                              attr_name="passport.depart_code"),
            "page11-doc_issuer_subdivision_code__right": FieldAttributeMatcher(field_name="general_manager",
                                                                               attr_name="passport.depart_code"),
            "page11-title__line{{item}}": MultilineFieldMatcher(field_name="general_manager_caption"),

            "page12-postal_index": FieldAttributeMatcher(field_name="general_manager",
                                                         attr_name="address.index"),
            "page12-subject_code": FieldAttributeMatcher(field_name="general_manager", attr_name="address.region",
                                                         adapter="RFRegionNumberAdapter"),
            "page12-district_type": FieldAttributeMatcher(field_name="general_manager",
                                                          attr_name="address.district_type",
                                                          adapter="ShortDistrictTypeAdapter"),
            "page12-city_type": FieldAttributeMatcher(field_name="general_manager", attr_name="address.city_type",
                                                      adapter="ShortCityTypeAdapter"),
            "page12-city_name": FieldAttributeMatcher(field_name="general_manager", attr_name="address.city"),
            "page12-nas_punkt_type": FieldAttributeMatcher(field_name="general_manager",
                                                           attr_name="address.village_type",
                                                           adapter="ShortVillageTypeAdapter"),
            "page12-street_type": FieldAttributeMatcher(field_name="general_manager", attr_name="address.street_type",
                                                        adapter="ShortStreetTypeAdapter"),
            "page12-house_type": FieldAttributeMatcher(field_name="general_manager",
                                                       attr_name="address.house_type"),
            "page12-corpus_type": FieldAttributeMatcher(field_name="general_manager",
                                                        attr_name="address.building_type"),
            "page12-house_number": FieldAttributeMatcher(field_name="general_manager",
                                                         attr_name="address.house"),
            "page12-corpus_number": FieldAttributeMatcher(field_name="general_manager",
                                                          attr_name="address.building"),
            "page12-flat_type": FieldAttributeMatcher(field_name="general_manager",
                                                      attr_name="address.flat_type"),
            "page12-flat_number": FieldAttributeMatcher(field_name="general_manager",
                                                        attr_name="address.flat"),
            "page12-living_country_code": ConstantMatcher(value="   "),
            "page12-phone_number": FieldAttributeMatcher(field_name="general_manager",
                                                         attr_name="phone.normalised"),
            "page12-district_name__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                        attr_name="address.district"),
            "page12-nas_punkt_name__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                         attr_name="address.village"),
            "page12-street_name__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                      attr_name="address.street"),
            "page12-living_address__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                         attr_name="living_address"),

            "%page_Je-set-1": FieldSetMatcher(fields={  # management company - russian company
                                                        "page13-ogrn": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.ogrn"),
                                                        "page13-inn": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.inn"),
                                                        "page13-full_name__line{{item}}": MultilineFieldMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.qualified_full_name"),

                                                        "page14-postal_index": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.index"),
                                                        "page14-subject_code": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.region",
                                                            adapter="RFRegionNumberAdapter"),
                                                        "page14-district_type": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.district_type",
                                                            adapter="ShortDistrictTypeAdapter"),
                                                        "page14-city_type": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.city_type",
                                                            adapter="ShortCityTypeAdapter"),
                                                        "page14-city_name": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.city"),
                                                        "page14-nas_punkt_type": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.village_type",
                                                            adapter="ShortVillageTypeAdapter"),
                                                        "page14-street_type": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.street_type",
                                                            adapter="ShortStreetTypeAdapter"),
                                                        "page14-house_type": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.house_type"),
                                                        "page14-corpus_type": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.building_type"),
                                                        "page14-house_number": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.house"),
                                                        "page14-corpus_number": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.building"),
                                                        "page14-flat_type": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.flat_type"),
                                                        "page14-flat_number": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.flat"),
                                                        "page14-district_name__line{{item}}": MultilineFieldMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.district"),
                                                        "page14-nas_punkt_name__line{{item}}": MultilineFieldMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.village"),
                                                        "page14-street_name__line{{item}}": MultilineFieldMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.address.street"),
                                                        "page14-phone_number": FieldAttributeMatcher(
                                                            field_name="management_company",
                                                            attr_name="company.phone.normalised"),

                                                        }),
            "%page_Je-set-2": FieldSetMatcher(
                fields={  # management company - foreign company [ + russian branch or agency]
                          "page13-inn": FieldAttributeMatcher(field_name="management_company",
                                                              attr_name="foreign_company.inn"),
                          "page13-full_name__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                                  attr_name="foreign_company.qualified_full_name"),
                          "page13-country_code": FieldAttributeMatcher(field_name="management_company",
                                                                       attr_name="foreign_company.country_code"),
                          "page13-reg_date__day": FieldAttributeMatcher(field_name="management_company",
                                                                        attr_name="foreign_company.registration_date.day"),
                          "page13-reg_date__month": FieldAttributeMatcher(field_name="management_company",
                                                                          attr_name="foreign_company.registration_date.month"),
                          "page13-reg_date__year": FieldAttributeMatcher(field_name="management_company",
                                                                         attr_name="foreign_company.registration_date.year"),
                          "page13-reg_number": FieldAttributeMatcher(field_name="management_company",
                                                                     attr_name="foreign_company.registration_number"),
                          "page13-reg_organ_name__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                                       attr_name="foreign_company.registration_depart"),
                          "page13-reg_organ_address__line{{item}}": MultilineFieldMatcher(
                              field_name="management_company", attr_name="foreign_company.generic_address"),

                          "page13-predstav_full_name__line{{item}}": MultilineFieldMatcher(
                              field_name="management_company",
                              attr_name="russian_branch_or_agency.qualified_full_name"),

                          "page14-postal_index": FieldAttributeMatcher(field_name="management_company",
                                                                       attr_name="russian_branch_or_agency.address.index"),
                          "page14-subject_code": FieldAttributeMatcher(field_name="management_company",
                                                                       attr_name="russian_branch_or_agency.address.region",
                                                                       adapter="RFRegionNumberAdapter"),
                          "page14-district_type": FieldAttributeMatcher(field_name="management_company",
                                                                        attr_name="russian_branch_or_agency.address.district_type",
                                                                        adapter="ShortDistrictTypeAdapter"),
                          "page14-city_type": FieldAttributeMatcher(field_name="management_company",
                                                                    attr_name="russian_branch_or_agency.address.city_type",
                                                                    adapter="ShortCityTypeAdapter"),
                          "page14-city_name": FieldAttributeMatcher(field_name="management_company",
                                                                    attr_name="russian_branch_or_agency.address.city"),
                          "page14-nas_punkt_type": FieldAttributeMatcher(field_name="management_company",
                                                                         attr_name="russian_branch_or_agency.address.village_type",
                                                                         adapter="ShortVillageTypeAdapter"),
                          "page14-street_type": FieldAttributeMatcher(field_name="management_company",
                                                                      attr_name="russian_branch_or_agency.address.street_type",
                                                                      adapter="ShortStreetTypeAdapter"),
                          "page14-house_type": FieldAttributeMatcher(field_name="management_company",
                                                                     attr_name="russian_branch_or_agency.address.house_type"),
                          "page14-corpus_type": FieldAttributeMatcher(field_name="management_company",
                                                                      attr_name="russian_branch_or_agency.address.building_type"),
                          "page14-house_number": FieldAttributeMatcher(field_name="management_company",
                                                                       attr_name="russian_branch_or_agency.address.house"),
                          "page14-corpus_number": FieldAttributeMatcher(field_name="management_company",
                                                                        attr_name="russian_branch_or_agency.address.building"),
                          "page14-flat_type": FieldAttributeMatcher(field_name="management_company",
                                                                    attr_name="russian_branch_or_agency.address.flat_type"),
                          "page14-flat_number": FieldAttributeMatcher(field_name="management_company",
                                                                      attr_name="russian_branch_or_agency.address.flat"),
                          "page14-district_name__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                                      attr_name="russian_branch_or_agency.address.district"),
                          "page14-nas_punkt_name__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                                       attr_name="russian_branch_or_agency.address.village"),
                          "page14-street_name__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                                    attr_name="russian_branch_or_agency.address.street"),
                          "page14-phone_number": FieldAttributeMatcher(field_name="management_company",
                                                                       attr_name="russian_branch_or_agency.phone.normalised"),

                          }),  # management company - foreign company [ + russian person as agent]
            "%page_Je-set-3": FieldSetMatcher(fields={
                "page13-inn": FieldAttributeMatcher(field_name="management_company",
                                                    attr_name="foreign_company.inn"),
                "page13-full_name__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                        attr_name="foreign_company.qualified_full_name"),
                "page13-country_code": FieldAttributeMatcher(field_name="management_company",
                                                             attr_name="foreign_company.country_code"),
                "page13-reg_date__day": FieldAttributeMatcher(field_name="management_company",
                                                              attr_name="foreign_company.registration_date.day"),
                "page13-reg_date__month": FieldAttributeMatcher(field_name="management_company",
                                                                attr_name="foreign_company.registration_date.month"),
                "page13-reg_date__year": FieldAttributeMatcher(field_name="management_company",
                                                               attr_name="foreign_company.registration_date.year"),
                "page13-reg_number": FieldAttributeMatcher(field_name="management_company",
                                                           attr_name="foreign_company.registration_number"),
                "page13-reg_organ_name__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                             attr_name="foreign_company.registration_depart"),
                "page13-reg_organ_address__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                                attr_name="foreign_company.generic_address"),

                "page14-surname": FieldAttributeMatcher(field_name="management_company",
                                                        attr_name="russian_agent.surname"),
                "page14-name": FieldAttributeMatcher(field_name="management_company",
                                                     attr_name="russian_agent.name"),
                "page14-patronymic": FieldAttributeMatcher(field_name="management_company",
                                                           attr_name="russian_agent.patronymic"),
                "page14-inn": FieldAttributeMatcher(field_name="management_company",
                                                    attr_name="russian_agent.inn"),
                "page14-birth_date__day": FieldAttributeMatcher(field_name="management_company",
                                                                attr_name="russian_agent.birthdate.day"),
                "page14-birth_date__month": FieldAttributeMatcher(field_name="management_company",
                                                                  attr_name="russian_agent.birthdate.month"),
                "page14-birth_date__year": FieldAttributeMatcher(field_name="management_company",
                                                                 attr_name="russian_agent.birthdate.year"),
                "page14-birth_place__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                          attr_name="russian_agent.birthplace"),

                "page15-doc_issuer__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                         attr_name="russian_agent.passport.issue_depart"),
                "page15-doc_type_code": FieldAttributeMatcher(field_name="management_company",
                                                              attr_name="russian_agent.passport.document_type"),
                "page15-doc_number": ConcatFieldAttributeMatcher(field_name="management_company",
                                                                 attributes=["russian_agent.passport.series",
                                                                             "russian_agent.passport.number"],
                                                                 adapter="InternalPassportAdapter"),
                "page15-doc_issue_date__day": FieldAttributeMatcher(field_name="management_company",
                                                                    attr_name="russian_agent.passport.issue_date.day"),
                "page15-doc_issue_date__month": FieldAttributeMatcher(field_name="management_company",
                                                                      attr_name="russian_agent.passport.issue_date.month"),
                "page15-doc_issue_date__year": FieldAttributeMatcher(field_name="management_company",
                                                                     attr_name="russian_agent.passport.issue_date.year"),
                "page15-doc_issuer_subdivision_code__left": FieldAttributeMatcher(field_name="management_company",
                                                                                  attr_name="russian_agent.passport.depart_code"),
                "page15-doc_issuer_subdivision_code__right": FieldAttributeMatcher(field_name="management_company",
                                                                                   attr_name="russian_agent.passport.depart_code"),
                "page15-postal_index": FieldAttributeMatcher(field_name="management_company",
                                                             attr_name="russian_agent.address.index"),
                "page15-subject_code": FieldAttributeMatcher(field_name="management_company",
                                                             attr_name="russian_agent.address.region",
                                                             adapter="RFRegionNumberAdapter"),
                "page15-district_type": FieldAttributeMatcher(field_name="management_company",
                                                              attr_name="russian_agent.address.district_type",
                                                              adapter="ShortDistrictTypeAdapter"),
                "page15-city_type": FieldAttributeMatcher(field_name="management_company",
                                                          attr_name="russian_agent.address.city_type",
                                                          adapter="ShortCityTypeAdapter"),
                "page15-city_name": FieldAttributeMatcher(field_name="management_company",
                                                          attr_name="russian_agent.address.city"),
                "page15-nas_punkt_type": FieldAttributeMatcher(field_name="management_company",
                                                               attr_name="russian_agent.address.village_type",
                                                               adapter="ShortVillageTypeAdapter"),
                "page15-street_type": FieldAttributeMatcher(field_name="management_company",
                                                            attr_name="russian_agent.address.street_type",
                                                            adapter="ShortStreetTypeAdapter"),
                "page15-house_type": FieldAttributeMatcher(field_name="management_company",
                                                           attr_name="russian_agent.address.house_type"),
                "page15-corpus_type": FieldAttributeMatcher(field_name="management_company",
                                                            attr_name="russian_agent.address.building_type"),
                "page15-house_number": FieldAttributeMatcher(field_name="management_company",
                                                             attr_name="russian_agent.address.house"),
                "page15-corpus_number": FieldAttributeMatcher(field_name="management_company",
                                                              attr_name="russian_agent.address.building"),
                "page15-flat_type": FieldAttributeMatcher(field_name="management_company",
                                                          attr_name="russian_agent.address.flat_type"),
                "page15-flat_number": FieldAttributeMatcher(field_name="management_company",
                                                            attr_name="russian_agent.address.flat"),
                "page15-living_country_code": FieldAttributeMatcher(field_name="management_company",
                                                                    attr_name="russian_agent.living_country_code"),
                "page15-phone_number": FieldAttributeMatcher(field_name="management_company",
                                                             attr_name="russian_agent.phone.normalised"),
                "page15-district_name__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                            attr_name="russian_agent.address.district"),
                "page15-nas_punkt_name__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                             attr_name="russian_agent.address.village"),
                "page15-street_name__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                          attr_name="russian_agent.address.street"),
                "page15-living_address__line{{item}}": MultilineFieldMatcher(field_name="management_company",
                                                                             attr_name="russian_agent.living_address"),
            }),

            "page16-ogrnip": FieldAttributeMatcher(field_name="manager", attr_name="ogrnip"),
            "page16-surname": FieldAttributeMatcher(field_name="manager", attr_name="surname"),
            "page16-name": FieldAttributeMatcher(field_name="manager", attr_name="name"),
            "page16-patronymic": FieldAttributeMatcher(field_name="manager", attr_name="patronymic"),
            "page16-inn": FieldAttributeMatcher(field_name="manager", attr_name="inn"),
            "page16-birth_date__day": FieldAttributeMatcher(field_name="manager", attr_name="birthdate.day"),
            "page16-birth_date__month": FieldAttributeMatcher(field_name="manager",
                                                              attr_name="birthdate.month"),
            "page16-birth_date__year": FieldAttributeMatcher(field_name="manager",
                                                             attr_name="birthdate.year"),
            "page16-birth_place__line{{item}}": MultilineFieldMatcher(field_name="manager",
                                                                      attr_name="birthplace"),
            "page16-doc_issuer__line{{item}}": MultilineFieldMatcher(field_name="manager",
                                                                     attr_name="passport.issue_depart"),
            "page16-doc_type_code": FieldAttributeMatcher(field_name="manager",
                                                          attr_name="passport.document_type"),
            "page16-doc_type_number": ConcatFieldAttributeMatcher(field_name="manager", attributes=["passport.series",
                                                                                                    "passport.number"],
                                                                  adapter="InternalPassportAdapter"),
            "page16-doc_issue_date__day": FieldAttributeMatcher(field_name="manager",
                                                                attr_name="passport.issue_date.day"),
            "page16-doc_issue_date__month": FieldAttributeMatcher(field_name="manager",
                                                                  attr_name="passport.issue_date.month"),
            "page16-doc_issue_date__year": FieldAttributeMatcher(field_name="manager",
                                                                 attr_name="passport.issue_date.year"),
            "page16-doc_issuer_subdivision_code__left": FieldAttributeMatcher(field_name="manager",
                                                                              attr_name="passport.depart_code"),
            "page16-doc_issuer_subdivision_code__right": FieldAttributeMatcher(field_name="manager",
                                                                               attr_name="passport.depart_code"),

            "page17-postal_index": FieldAttributeMatcher(field_name="manager", attr_name="address.index"),
            "page17-subject_code": FieldAttributeMatcher(field_name="manager", attr_name="address.region",
                                                         adapter="RFRegionNumberAdapter"),
            "page17-district_type": FieldAttributeMatcher(field_name="manager", attr_name="address.district_type",
                                                          adapter="ShortDistrictTypeAdapter"),
            "page17-city_type": FieldAttributeMatcher(field_name="manager", attr_name="address.city_type",
                                                      adapter="ShortCityTypeAdapter"),
            "page17-city_name": FieldAttributeMatcher(field_name="manager", attr_name="address.city"),
            "page17-nas_punkt_type": FieldAttributeMatcher(field_name="manager", attr_name="address.village_type",
                                                           adapter="ShortVillageTypeAdapter"),
            "page17-street_type": FieldAttributeMatcher(field_name="manager", attr_name="address.street_type",
                                                        adapter="ShortStreetTypeAdapter"),
            "page17-house_type": FieldAttributeMatcher(field_name="manager", attr_name="address.house_type"),
            "page17-corpus_type": FieldAttributeMatcher(field_name="manager",
                                                        attr_name="address.building_type"),
            "page17-house_number": FieldAttributeMatcher(field_name="manager", attr_name="address.house"),
            "page17-corpus_number": FieldAttributeMatcher(field_name="manager", attr_name="address.building"),
            "page17-flat_type": FieldAttributeMatcher(field_name="manager", attr_name="address.flat_type"),
            "page17-flat_number": FieldAttributeMatcher(field_name="manager", attr_name="address.flat"),
            "page17-living_country_code": FieldAttributeMatcher(field_name="manager",
                                                                attr_name="living_country_code"),
            "page17-phone_number": FieldAttributeMatcher(field_name="manager", attr_name="phone.normalised"),
            "page17-district_name__line{{item}}": MultilineFieldMatcher(field_name="manager",
                                                                        attr_name="address.district"),
            "page17-nas_punkt_name__line{{item}}": MultilineFieldMatcher(field_name="manager",
                                                                         attr_name="address.village"),
            "page17-street_name__line{{item}}": MultilineFieldMatcher(field_name="manager",
                                                                      attr_name="address.street"),

            "page18-main_job_code__part1": SimpleMatcher(field_name="job_main_code"),
            "page18-main_job_code__part2": SimpleMatcher(field_name="job_main_code"),
            "page18-main_job_code__part3": SimpleMatcher(field_name="job_main_code"),
            "page18-job_code#{{item}}__part1": ArrayAttributeMatcher(field_name="job_code_array",
                                                                     sorted="true"),
            "page18-job_code#{{item}}__part2": ArrayAttributeMatcher(field_name="job_code_array",
                                                                     sorted="true"),
            "page18-job_code#{{item}}__part3": ArrayAttributeMatcher(field_name="job_code_array",
                                                                     sorted="true"),

            "page19-ogrn": FieldAttributeMatcher(field_name="holder_share", attr_name="company.ogrn"),
            "page19-inn": FieldAttributeMatcher(field_name="holder_share", attr_name="company.inn"),
            "page19-full_name__line{{item}}": MultilineFieldMatcher(field_name="holder_share",
                                                                    attr_name="company.qualified_full_name"),

            "page20-ogrnip": FieldAttributeMatcher(field_name="farm_companies[]", attr_name="ogrnip"),
            "page20-surname": FieldAttributeMatcher(field_name="farm_companies[]",
                                                    attr_name="person.surname"),
            "page20-name": FieldAttributeMatcher(field_name="farm_companies[]", attr_name="person.name"),
            "page20-patronymic": FieldAttributeMatcher(field_name="farm_companies[]",
                                                       attr_name="person.patronymic"),
            "page20-inn": FieldAttributeMatcher(field_name="farm_companies[]", attr_name="person.inn"),

            # page21-organization_full_name
            #                page21-title
            #                page21-fio

            "%page_N-set-1": FieldSetMatcher(fields={
                "page22-zayavitel_type": FieldAttributeMatcher(field_name="founders[]", attr_name="founder_type",
                                                               adapter="FounderTypeNumberAdapter"),
                "page24-document_delivery_type": FieldAttributeMatcher(field_name="founders[]",
                                                                       attr_name="documents_recipient_type",
                                                                       adapter="DocumentDeliveryNumberAdapter"),
            }),
            "%page_N-set-2": FieldSetMatcher(fields={
                "page22-zayavitel_type": FieldAttributeMatcher(field_name="founders[]", attr_name="founder_type",
                                                               adapter="FounderTypeNumberAdapter"),

                "page22-zayavitel_surname": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="person.surname"),
                "page22-zayavitel_name": FieldAttributeMatcher(field_name="founders[]",
                                                               attr_name="person.name"),
                "page22-zayavitel_patronymic": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="person.patronymic"),

                "page24-document_delivery_type": FieldAttributeMatcher(field_name="founders[]",
                                                                       attr_name="documents_recipient_type",
                                                                       adapter="DocumentDeliveryNumberAdapter"),
            }),
            "%page_N-set-2dup": FieldSetMatcher(fields={
                "page22-zayavitel_type": FieldAttributeMatcher(field_name="founders[]", attr_name="founder_type",
                                                               adapter="FounderTypeNumberAdapter"),

                "page22-zayavitel_surname": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="person.surname"),
                "page22-zayavitel_name": FieldAttributeMatcher(field_name="founders[]",
                                                               attr_name="person.name"),
                "page22-zayavitel_patronymic": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="person.patronymic"),

                "page22-zayavitel_birth_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                                          attr_name="person.birthdate.day"),
                "page22-zayavitel_birth_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="person.birthdate.month"),
                "page22-zayavitel_birth_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                                           attr_name="person.birthdate.year"),
                "page22-zayavitel_birth_place__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                    attr_name="person.birthplace"),

                "page24-document_delivery_type": FieldAttributeMatcher(field_name="founders[]",
                                                                       attr_name="documents_recipient_type",
                                                                       adapter="DocumentDeliveryNumberAdapter"),
            }),
            "%page_N-set-3": FieldSetMatcher(fields={
                "page22-zayavitel_type": FieldAttributeMatcher(field_name="founders[]", attr_name="founder_type",
                                                               adapter="FounderTypeNumberAdapter"),

                "page22-ogrn": FieldAttributeMatcher(field_name="founders[]", attr_name="company.ogrn"),
                "page22-uchreditel_inn": FieldAttributeMatcher(field_name="founders[]",
                                                               attr_name="company.inn"),
                "page22-uchreditel_full_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                   attr_name="company.qualified_full_name"),

                "page22-zayavitel_surname": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="company.general_manager.surname"),
                "page22-zayavitel_name": FieldAttributeMatcher(field_name="founders[]",
                                                               attr_name="company.general_manager.name"),
                "page22-zayavitel_patronymic": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="company.general_manager.patronymic"),
                "page22-zayavitel_inn": FieldAttributeMatcher(field_name="founders[]",
                                                              attr_name="company.general_manager.inn"),
                "page22-zayavitel_birth_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                                          attr_name="company.general_manager.birthdate.day"),
                "page22-zayavitel_birth_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="company.general_manager.birthdate.month"),
                "page22-zayavitel_birth_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                                           attr_name="company.general_manager.birthdate.year"),
                "page22-zayavitel_birth_place__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                    attr_name="company.general_manager.birthplace"),

                "page23-issuer__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                     attr_name="company.general_manager.passport.issue_depart"),
                "page23-doc_type": FieldAttributeMatcher(field_name="founders[]",
                                                         attr_name="company.general_manager.passport.document_type"),
                "page23-doc_number": ConcatFieldAttributeMatcher(field_name="founders[]",
                                                                 attributes=["company.general_manager.passport.series",
                                                                             "company.general_manager.passport.number"],
                                                                 adapter="InternalPassportAdapter"),
                "page23-doc_issue_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="company.general_manager.passport.issue_date.day"),
                "page23-doc_issue_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                                      attr_name="company.general_manager.passport.issue_date.month"),
                "page23-doc_issue_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="company.general_manager.passport.issue_date.year"),
                "page23-issuer_subdivision_code__left": FieldAttributeMatcher(field_name="founders[]",
                                                                              attr_name="company.general_manager.passport.depart_code"),
                "page23-issuer_subdivision_code__right": FieldAttributeMatcher(field_name="founders[]",
                                                                               attr_name="company.general_manager.passport.depart_code"),
                "page23-postal_index": FieldAttributeMatcher(field_name="founders[]",
                                                             attr_name="company.general_manager.address.index"),
                "page23-address_subject_code": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="company.general_manager.address.region",
                                                                     adapter="RFRegionNumberAdapter"),
                "page23-address_district_type": FieldAttributeMatcher(field_name="founders[]",
                                                                      attr_name="company.general_manager.address.district_type",
                                                                      adapter="ShortDistrictTypeAdapter"),
                "page23-address_city_type": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="company.general_manager.address.city_type",
                                                                  adapter="ShortCityTypeAdapter"),
                "page23-address_city_name": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="company.general_manager.address.city"),
                "page23-address_nas_punkt_type": FieldAttributeMatcher(field_name="founders[]",
                                                                       attr_name="company.general_manager.address.village_type",
                                                                       adapter="ShortVillageTypeAdapter"),
                "page23-address_street_type": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="company.general_manager.address.street_type",
                                                                    adapter="ShortStreetTypeAdapter"),
                "page23-address_house_type": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="company.general_manager.address.house_type"),
                "page23-address_corpus_type": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="company.general_manager.address.building_type"),
                "page23-address_house_number": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="company.general_manager.address.house"),
                "page23-address_corpus_number": FieldAttributeMatcher(field_name="founders[]",
                                                                      attr_name="company.general_manager.address.building"),
                "page23-address_flat_type": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="company.general_manager.address.flat_type"),
                "page23-address_flat_number": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="company.general_manager.address.flat"),
                "page23-living_country_code": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="company.general_manager.living_country_code"),
                "page23-phone_number": FieldAttributeMatcher(field_name="founders[]",
                                                             attr_name="company.general_manager.phone.normalised"),
                "page23-email": FieldAttributeMatcher(field_name="founders[]",
                                                      attr_name="company.general_manager.email"),
                "page23-address_district_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                    attr_name="company.general_manager.address.district"),
                "page23-address_nas_punkt_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                     attr_name="company.general_manager.address.village"),
                "page23-address_street_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                  attr_name="company.general_manager.address.street"),
                "page23-living_address__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                             attr_name="company.general_manager.living_address"),

                "page24-document_delivery_type": FieldAttributeMatcher(field_name="founders[]",
                                                                       attr_name="documents_recipient_type",
                                                                       adapter="DocumentDeliveryNumberAdapter"),
            }),
            "%page_N-set-5": FieldSetMatcher(fields={
                "page22-zayavitel_type": FieldAttributeMatcher(field_name="founders[]", attr_name="founder_type",
                                                               adapter="FounderTypeNumberAdapter"),

                "page22-zayavitel_surname": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="company.general_manager.surname"),
                "page22-zayavitel_name": FieldAttributeMatcher(field_name="founders[]",
                                                               attr_name="company.general_manager.name"),
                "page22-zayavitel_patronymic": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="company.general_manager.patronymic"),
                "page22-zayavitel_inn": FieldAttributeMatcher(field_name="founders[]",
                                                              attr_name="company.general_manager.inn"),
                "page22-zayavitel_birth_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                                          attr_name="company.general_manager.birthdate.day"),
                "page22-zayavitel_birth_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="company.general_manager.birthdate.month"),
                "page22-zayavitel_birth_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                                           attr_name="company.general_manager.birthdate.year"),
                "page22-zayavitel_birth_place__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                    attr_name="company.general_manager.birthplace"),

                "page23-issuer__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                     attr_name="company.general_manager.passport.issue_depart"),
                "page23-doc_type": FieldAttributeMatcher(field_name="founders[]",
                                                         attr_name="company.general_manager.passport.document_type"),
                "page23-doc_number": ConcatFieldAttributeMatcher(field_name="founders[]",
                                                                 attributes=["company.general_manager.passport.series",
                                                                             "company.general_manager.passport.number"],
                                                                 adapter="InternalPassportAdapter"),
                "page23-doc_issue_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="company.general_manager.passport.issue_date.day"),
                "page23-doc_issue_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                                      attr_name="company.general_manager.passport.issue_date.month"),
                "page23-doc_issue_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="company.general_manager.passport.issue_date.year"),
                "page23-issuer_subdivision_code__left": FieldAttributeMatcher(field_name="founders[]",
                                                                              attr_name="company.general_manager.passport.depart_code"),
                "page23-issuer_subdivision_code__right": FieldAttributeMatcher(field_name="founders[]",
                                                                               attr_name="company.general_manager.passport.depart_code"),
                "page23-postal_index": FieldAttributeMatcher(field_name="founders[]",
                                                             attr_name="company.general_manager.address.index"),
                "page23-address_subject_code": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="company.general_manager.address.region",
                                                                     adapter="RFRegionNumberAdapter"),
                "page23-address_district_type": FieldAttributeMatcher(field_name="founders[]",
                                                                      attr_name="company.general_manager.address.district_type",
                                                                      adapter="ShortDistrictTypeAdapter"),
                "page23-address_city_type": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="company.general_manager.address.city_type",
                                                                  adapter="ShortCityTypeAdapter"),
                "page23-address_city_name": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="company.general_manager.address.city"),
                "page23-address_nas_punkt_type": FieldAttributeMatcher(field_name="founders[]",
                                                                       attr_name="company.general_manager.address.village_type",
                                                                       adapter="ShortVillageTypeAdapter"),
                "page23-address_street_type": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="company.general_manager.address.street_type",
                                                                    adapter="ShortStreetTypeAdapter"),
                "page23-address_house_type": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="company.general_manager.address.house_type"),
                "page23-address_corpus_type": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="company.general_manager.address.building_type"),
                "page23-address_house_number": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="company.general_manager.address.house"),
                "page23-address_corpus_number": FieldAttributeMatcher(field_name="founders[]",
                                                                      attr_name="company.general_manager.address.building"),
                "page23-address_flat_type": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="company.general_manager.address.flat_type"),
                "page23-address_flat_number": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="company.general_manager.address.flat"),
                "page23-living_country_code": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="company.general_manager.living_country_code"),
                "page23-phone_number": FieldAttributeMatcher(field_name="founders[]",
                                                             attr_name="company.general_manager.phone.normalised"),
                "page23-email": FieldAttributeMatcher(field_name="founders[]",
                                                      attr_name="company.general_manager.email"),
                "page23-address_district_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                    attr_name="company.general_manager.address.district"),
                "page23-address_nas_punkt_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                     attr_name="company.general_manager.address.village"),
                "page23-address_street_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                  attr_name="company.general_manager.address.street"),
                "page23-living_address__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                             attr_name="company.general_manager.living_address"),

                "page24-document_delivery_type": FieldAttributeMatcher(field_name="founders[]",
                                                                       attr_name="documents_recipient_type",
                                                                       adapter="DocumentDeliveryNumberAdapter"),
            }),
            "%page_N-set-4": FieldSetMatcher(fields={
                "page22-zayavitel_type": FieldAttributeMatcher(field_name="founders[]", attr_name="founder_type",
                                                               adapter="FounderTypeNumberAdapter"),

                "page22-uchreditel_inn": FieldAttributeMatcher(field_name="founders[]",
                                                               attr_name="company.inn"),
                "page22-uchreditel_full_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                   attr_name="company.full_name"),

                "page22-zayavitel_surname": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="person.surname"),
                "page22-zayavitel_name": FieldAttributeMatcher(field_name="founders[]",
                                                               attr_name="person.name"),
                "page22-zayavitel_patronymic": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="person.patronymic"),
                "page22-zayavitel_inn": FieldAttributeMatcher(field_name="founders[]",
                                                              attr_name="person.inn"),
                "page22-zayavitel_birth_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                                          attr_name="person.birthdate.day"),
                "page22-zayavitel_birth_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                                            attr_name="person.birthdate.month"),
                "page22-zayavitel_birth_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                                           attr_name="person.birthdate.year"),
                "page22-zayavitel_birth_place__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                    attr_name="person.birthplace"),

                "page23-issuer__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                     attr_name="person.passport.issue_depart"),
                "page23-doc_type": FieldAttributeMatcher(field_name="founders[]",
                                                         attr_name="person.passport.document_type"),
                "page23-doc_number": ConcatFieldAttributeMatcher(field_name="founders[]",
                                                                 attributes=["person.passport.series",
                                                                             "person.passport.number"],
                                                                 adapter="InternalPassportAdapter"),
                "page23-doc_issue_date__day": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="person.passport.issue_date.day"),
                "page23-doc_issue_date__month": FieldAttributeMatcher(field_name="founders[]",
                                                                      attr_name="person.passport.issue_date.month"),
                "page23-doc_issue_date__year": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="person.passport.issue_date.year"),
                "page23-issuer_subdivision_code__left": FieldAttributeMatcher(field_name="founders[]",
                                                                              attr_name="person.passport.depart_code"),
                "page23-issuer_subdivision_code__right": FieldAttributeMatcher(field_name="founders[]",
                                                                               attr_name="person.passport.depart_code"),
                "page23-postal_index": FieldAttributeMatcher(field_name="founders[]",
                                                             attr_name="person.address.index"),
                "page23-address_subject_code": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="person.address.region",
                                                                     adapter="RFRegionNumberAdapter"),
                "page23-address_district_type": FieldAttributeMatcher(field_name="founders[]",
                                                                      attr_name="person.address.district_type",
                                                                      adapter="ShortDistrictTypeAdapter"),
                "page23-address_city_type": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="person.address.city_type",
                                                                  adapter="ShortCityTypeAdapter"),
                "page23-address_city_name": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="person.address.city"),
                "page23-address_nas_punkt_type": FieldAttributeMatcher(field_name="founders[]",
                                                                       attr_name="person.address.village_type",
                                                                       adapter="ShortVillageTypeAdapter"),
                "page23-address_street_type": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="person.address.street_type",
                                                                    adapter="ShortStreetTypeAdapter"),
                "page23-address_house_type": FieldAttributeMatcher(field_name="founders[]",
                                                                   attr_name="person.address.house_type"),
                "page23-address_corpus_type": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="person.address.building_type"),
                "page23-address_house_number": FieldAttributeMatcher(field_name="founders[]",
                                                                     attr_name="person.address.house"),
                "page23-address_corpus_number": FieldAttributeMatcher(field_name="founders[]",
                                                                      attr_name="person.address.building"),
                "page23-address_flat_type": FieldAttributeMatcher(field_name="founders[]",
                                                                  attr_name="person.address.flat_type"),
                "page23-address_flat_number": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="person.address.flat"),
                "page23-living_country_code": FieldAttributeMatcher(field_name="founders[]",
                                                                    attr_name="person.living_country_code"),
                "page23-phone_number": FieldAttributeMatcher(field_name="founders[]",
                                                             attr_name="person.phone.normalised"),
                "page23-email": FieldAttributeMatcher(field_name="founders[]", attr_name="person.email"),
                "page23-address_district_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                    attr_name="person.address.district"),
                "page23-address_nas_punkt_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                     attr_name="person.address.village"),
                "page23-address_street_name__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                                  attr_name="person.address.street"),
                "page23-living_address__line{{item}}": MultilineFieldMatcher(field_name="founders[]",
                                                                             attr_name="person.living_address"),

                "page24-document_delivery_type": FieldAttributeMatcher(field_name="founders[]",
                                                                       attr_name="documents_recipient_type",
                                                                       adapter="DocumentDeliveryNumberAdapter"),
            })
        }
    }
    P11001_SCHEMA = {"doc_name": DocumentTypeEnum.DT_P11001,
                     "file_name_template": u"Заявление на регистрацию ООО {{short_name}}",
                     "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
                     "fields": [
                         SHORT_NAME_FIELD,
                         FULL_NAME_FIELD,
                         ADDRESS_TYPE_FIELD_NR,
                         ADDRESS_FIELD,
                         GENERAL_MANAGER_CAPTION_FIELD,
                         FOUNDERS_FIELD,
                         STARTER_CAPITAL_FIELD,
                         JOB_MAIN_CODE_FIELD,
                         JOB_CODE_ARRAY_FIELD,
                         GENERAL_MANAGER_FIELD
                     ]}

    ARTICLES_TEMPLATE = {
        "template_name": "soft_template_ustav",
        "file_name": get_test_resource_name(config, "ustav_llc.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_ARTICLES
    }

    ARTICLES_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_ARTICLES,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Устав ООО {{short_name}}",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "validators": [{
                           "condition": {
                               "#or": [{
                                           "use_foreign_company_name": {
                                               "#ne": True
                                           }
                                       }, {
                                           "use_foreign_company_name": True,
                                           "foreign_full_name": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "foreign_full_name",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "use_foreign_company_name": {
                                               "#ne": True
                                           }
                                       }, {
                                           "use_foreign_company_name": True,
                                           "foreign_short_name": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "foreign_short_name",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "use_foreign_company_name": {
                                               "#ne": True
                                           }
                                       }, {
                                           "use_foreign_company_name": True,
                                           "foreign_language": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "foreign_language",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "use_national_language_company_name": {
                                               "#ne": True
                                           }
                                       }, {
                                           "use_national_language_company_name": True,
                                           "national_language_full_name": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "national_language_full_name",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "use_national_language_company_name": {
                                               "#ne": True
                                           }
                                       }, {
                                           "use_national_language_company_name": True,
                                           "national_language_short_name": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "national_language_short_name",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "use_national_language_company_name": {
                                               "#ne": True
                                           }
                                       }, {
                                           "use_national_language_company_name": True,
                                           "national_language": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "national_language",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "board_of_directors": {
                                               "#ne": True
                                           }
                                       }, {
                                           "board_of_directors": True,
                                           "sovet_directorov_num": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "sovet_directorov_num",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "board_of_directors": {
                                               "#ne": True
                                           }
                                       }, {
                                           "board_of_directors": True,
                                           "general_manager_deals_max_amount": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "general_manager_deals_max_amount",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "board_of_directors": {
                                               "#ne": True
                                           }
                                       }, {
                                           "board_of_directors": True,
                                           "board_of_directors_caption": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "board_of_directors_caption",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "board_of_directors": {
                                               "#ne": True
                                           }
                                       }, {
                                           "board_of_directors": True,
                                           "large_property_deals_max_value": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "large_property_deals_max_value",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "board_of_directors": {
                                               "#ne": True
                                           }
                                       }, {
                                           "board_of_directors": True,
                                           "large_property_deals_min_value": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "large_property_deals_min_value",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "board_of_directors": {
                                               "#ne": True
                                           }
                                       }, {
                                           "board_of_directors": True,
                                           "large_deals_min_value": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "large_deals_min_value",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "board_of_directors": {
                                               "#ne": True
                                           }
                                       }, {
                                           "board_of_directors": True,
                                           "large_deals_max_value": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "large_deals_max_value",
                               "code": 4
                           }
                       }],
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            STARTER_CAPITAL_FIELD,
            JOB_MAIN_CODE_FIELD,
            JOB_CODE_ARRAY_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY,
            USE_FOREIGN_COMPANY_NAME_FIELD,
            USE_NATIONAL_LANGUAGE_COMPANY_NAME_FIELD,
            FOREIGN_FULL_NAME_FIELD,
            FOREIGN_SHORT_NAME_FIELD,
            NATIONAL_LANGUAGE_FULL_NAME_FIELD,
            NATIONAL_LANGUAGE_SHORT_NAME_FIELD,
            FOREIGN_LANGUAGE_FIELD,
            NATIONAL_LANGUAGE_FIELD,
            BOARD_OF_DIRECTORS_FIELD,
            FOUNDERS_COUNT_FIELD, {
                "name": "pravo_otchuzhdeniya_type",
                "type": "DocEnumField",
                "enum_cls": "AlienationRightEnum",
                "required": True,
            }, {
                "name": "preimusch_pravo_priobreteniya_doli_time_span",
                "type": "DocIntField",
                "required": True,
                "min_val": 30
            }, {
                "name": "perehod_doli_k_naslednikam_soglasie",
                "type": "DocBoolField",
                "required": True,
            }, {
                "name": "sovet_directorov_num",
                "type": "DocIntField",
                "required": False,
                "even": False
            }, {
                "name": "general_manager_deals_max_amount",
                "type": "DocIntField",
                "required": False
            }, {
                "name": "general_manager_term",
                "type": "DocIntField",
                "min_val": 6,
                "max_val": 60,
                "required": True,
            }, {
                "name": "board_of_directors_caption",
                "type": "DocTextField",
                "required": False,
                "min_length": 1,
                "allowed_re": CompanyObject.RUS_COMPANY_NAME_RE
            }, {
                "name": "large_deals_min_value",
                "type": "DocIntField",
                "min_val": 25,
                "max_val": 100,
                "required": False
            }, {
                "name": "large_deals_max_value",
                "type": "DocIntField",
                "min_val": 25,
                "max_val": 100,
                "required": False
            }, {
                "name": "large_property_deals_max_value",
                "type": "DocIntField",
                "required": False
            }, {
                "name": "large_property_deals_min_value",
                "type": "DocIntField",
                "required": False
            }, {
                "name": "necessary_votes_for_general_meeting_decisions",
                "type": "NecessaryVotesForGeneralMeeting",
                "required": True,
            }, {
                "name": "base_general_manager_document",
                "type": "DocConstField",
                "required": False,
                "value": u"устав"
            }
        ]}

    ACT_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_ACT,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Акт приёма-передачи ООО {{short_name}}",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "founder->properties": {
                "#not_empty": True
            }
        },
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY,
            GENERAL_MANAGER_FIELD,
            FOUNDERS_COUNT_FIELD,
            {
                "name": "founder",
                "type": "FounderObject",
                "required": True,
            }
        ]}

    ACT_TEMPLATE = {
        "template_name": "soft_template_appi",
        "file_name": get_test_resource_name(config, "akt_priema_peredachi.tex"),
        "is_strict": False,
        "doc_name": DocumentTypeEnum.DT_ACT
    }

    USN_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_USN,
        "file_name_template": u"Заявление на УСН ООО {{short_name}}",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "taxation_type": 'usn'
        },
        "fields": [
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY,
            GENERAL_MANAGER_FIELD,
            FOUNDERS_COUNT_FIELD,
            FOUNDER_APPLICANT_FIELD,
            JOB_MAIN_CODE_FIELD,
            FOUNDERS_FIELD, {
                "name": "tax_type",
                "type": "DocEnumField",
                "enum_cls": "UsnTaxType",
                "required": True,
            }
        ],
        "external_validators": ["usn_tax_type"],
    }

    USN_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_USN,
        "template_name": "strict_template1__usn",
        "is_strict": True,
        "pages": [{

                      "variants": {
                          "type": RenderingVariants.TYPE_RENDER_FIRST_MATCHING,
                          "cases": [
                              {  # заявитель - физ. лицо, учредителей 1
                                 "page_file": [get_test_resource_name(config, "new_usn.pdf")],
                                 "field_matcher_set": "%set-1",
                                 "conditions": {
                                     "founder_applicant.founder_type": FounderTypeEnum.FT_PERSON,
                                     "founder_applicant.documents_recipient_type": {
                                         "#ne": None
                                     },
                                     "founders_count": 1
                                 },
                                 }, {  # заявитель - физ. лицо, учредителей > 1
                                       "page_file": [get_test_resource_name(config, "new_usn.pdf")],
                                       "field_matcher_set": "%set-3",
                                       "conditions": {
                                           "founder_applicant.founder_type": FounderTypeEnum.FT_PERSON,
                                           "founder_applicant.documents_recipient_type": {
                                               "#ne": None
                                           }
                                       },
                                       }, {  # заявитель - российское юр. лицо, учредителей 1
                                             "page_file": [get_test_resource_name(config, "new_usn.pdf")],
                                             "field_matcher_set": "%set-2",
                                             "conditions": {
                                                 "founder_applicant.founder_type": FounderTypeEnum.FT_COMPANY,
                                                 "founder_applicant.documents_recipient_type": {
                                                     "#ne": None
                                                 },
                                                 "founders_count": 1
                                             }
                                             }, {  # заявитель - российское юр. лицо, учредителей  > 1
                                                   "page_file": [get_test_resource_name(config, "new_usn.pdf")],
                                                   "field_matcher_set": "%set-4",
                                                   "conditions": {
                                                       "founder_applicant.founder_type": FounderTypeEnum.FT_COMPANY,
                                                       "founder_applicant.documents_recipient_type": {
                                                           "#ne": None
                                                       }
                                                   }
                                                   }, {  # fallback
                                                         "page_file": [get_test_resource_name(config, "new_usn.pdf")],
                                                         "field_matcher_set": "%set-5",
                                                         "conditions": {}
                                                         }]
                      },
                      "array_fields": [
                          {
                              "name": "name_line{{item}}",
                              "count": 4,
                              "field-length": 40,
                              "case": "upper"
                          }, {
                              "name": "applicant-name__line{{item}}",
                              "count": 3,
                              "field-length": 20,
                              "case": "upper"
                          }, {
                              "name": "agent-doc-name__line{{item}}",
                              "field-length": 20,
                              "case": "upper",
                              "count": 2,
                          }
                      ],
                      "fields": [
                          {
                              "name": "inn",
                              "field-length": 12
                          }, {
                              "name": "kpp",
                              "field-length": 9
                          }, {
                              "name": "kod_nalog_organa",
                              "field-length": 4
                          }, {
                              "name": "priznak_zayavitelya",
                              "field-length": 1
                          }, {
                              "name": "perehod",
                              "field-length": 1
                          }, {
                              "name": "god_zayavleniya",
                              "text-align": "right",
                              "field-length": 1
                          }, {
                              "name": "phone",
                              "field-length": 20
                          }, {
                              "name": "applicant-type",
                              "field-length": 1
                          }, {
                              "name": "current-date__day",
                              "field-length": 2,
                              "text-align": "right",
                              "space-filler": u"0",
                          }, {
                              "name": "current-date__month",
                              "field-length": 2,
                              "text-align": "right",
                              "space-filler": u"0",
                          }, {
                              "name": "current-date__year",
                              "field-length": 4
                          }, {
                              "name": "dohod",
                              "field-length": 1
                          }, {
                              "name": "god_podachi_uvedomleniya",
                              "field-length": 2,
                              "text-align": "right"
                          }, {
                              "name": "polucheno_dohodov",
                              "field-length": 9
                          }, {
                              "name": "ostatok",
                              "field-length": 9
                          }
                      ]
                  }]
    }

    USN_MATCHER = {
        "doc_name": DocumentTypeEnum.DT_USN,
        "template_name": USN_TEMPLATE['template_name'],
        "fields": {
            "%set-1": FieldSetMatcher(fields={
                "applicant-name__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                      attr_name="full_name"),
                "agent-doc-name__line{{item}}": ConstantMatcher(value=u"УСТАВ"),
                "phone": FieldAttributeMatcher(field_name="general_manager", attr_name="phone.normalised"),
                "name_line{{item}}": MultilineFieldMatcher(field_name="full_name",
                                                           prefix=u"Общество с ограниченной ответственностью «",
                                                           suffix=u"»"),
                "inn": ConstantMatcher(value=u"————————————"),
                "kpp": ConstantMatcher(value=u"————————————"),
                "polucheno_dohodov": ConstantMatcher(value=u"————————————"),
                "ostatok": ConstantMatcher(value=u"————————————"),
                "kod_nalog_organa": FieldAttributeMatcher(field_name="address", attr_name="ifns_number"),
                "priznak_zayavitelya": ConstantMatcher(value=1),
                "perehod": ConstantMatcher(value=2),
                "god_zayavleniya": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),

                "applicant-type": ConstantMatcher(value=1),
                "current-date__day": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="day"),
                "current-date__month": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="month"),
                "current-date__year": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),

                "dohod": SimpleMatcher(field_name="tax_type", adapter="UsnTaxTypeAdapter"),
                # "dov_page_number" : 1 if applicant_type = 2 else "",
                "god_podachi_uvedomleniya": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
            }),
            "%set-2": FieldSetMatcher(fields={
                "applicant-name__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                      attr_name="full_name"),
                "agent-doc-name__line{{item}}": ConstantMatcher(value=u"УСТАВ"),
                "phone": FieldAttributeMatcher(field_name="general_manager", attr_name="phone.normalised"),
                "name_line{{item}}": MultilineFieldMatcher(field_name="full_name",
                                                           prefix=u"Общество с ограниченной ответственностью «",
                                                           suffix=u"»"),
                "inn": ConstantMatcher(value=u"————————————"),
                "kpp": ConstantMatcher(value=u"————————————"),
                "polucheno_dohodov": ConstantMatcher(value=u"————————————"),
                "ostatok": ConstantMatcher(value=u"————————————"),
                "kod_nalog_organa": FieldAttributeMatcher(field_name="address", attr_name="ifns_number"),
                "priznak_zayavitelya": ConstantMatcher(value=1),
                "perehod": ConstantMatcher(value=2),
                "god_zayavleniya": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),

                "applicant-type": ConstantMatcher(value=1),
                "current-date__day": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="day"),
                "current-date__month": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="month"),
                "current-date__year": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
                "dohod": SimpleMatcher(field_name="tax_type", adapter="UsnTaxTypeAdapter"),
                "god_podachi_uvedomleniya": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
            }),
            "%set-3": FieldSetMatcher(fields={
                "applicant-name__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                      attr_name="full_name"),
                "agent-doc-name__line{{item}}": ConstantMatcher(value=u"УСТАВ"),
                "phone": FieldAttributeMatcher(field_name="general_manager", attr_name="phone.normalised"),
                "name_line{{item}}": MultilineFieldMatcher(field_name="full_name",
                                                           prefix=u"Общество с ограниченной ответственностью «",
                                                           suffix=u"»"),
                "inn": ConstantMatcher(value=u"————————————"),
                "kpp": ConstantMatcher(value=u"————————————"),
                "polucheno_dohodov": ConstantMatcher(value=u"————————————"),
                "ostatok": ConstantMatcher(value=u"————————————"),
                "kod_nalog_organa": FieldAttributeMatcher(field_name="address", attr_name="ifns_number"),
                "priznak_zayavitelya": ConstantMatcher(value=1),
                "perehod": ConstantMatcher(value=2),
                "god_zayavleniya": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),

                "applicant-type": ConstantMatcher(value=1),
                "current-date__day": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="day"),
                "current-date__month": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="month"),
                "current-date__year": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),

                "dohod": SimpleMatcher(field_name="tax_type", adapter="UsnTaxTypeAdapter"),
                "god_podachi_uvedomleniya": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
            }),
            "%set-4": FieldSetMatcher(fields={
                "applicant-name__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                      attr_name="full_name"),
                "agent-doc-name__line{{item}}": ConstantMatcher(value=u"УСТАВ"),
                "phone": FieldAttributeMatcher(field_name="general_manager", attr_name="phone.normalised"),
                "name_line{{item}}": MultilineFieldMatcher(field_name="full_name",
                                                           prefix=u"Общество с ограниченной ответственностью «",
                                                           suffix=u"»"),
                "inn": ConstantMatcher(value=u"————————————"),
                "kpp": ConstantMatcher(value=u"————————————"),
                "polucheno_dohodov": ConstantMatcher(value=u"————————————"),
                "ostatok": ConstantMatcher(value=u"————————————"),
                "kod_nalog_organa": FieldAttributeMatcher(field_name="address", attr_name="ifns_number"),
                "priznak_zayavitelya": ConstantMatcher(value=1),
                "perehod": ConstantMatcher(value=2),
                "god_zayavleniya": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),

                "applicant-type": ConstantMatcher(value=1),
                "current-date__day": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="day"),
                "current-date__month": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="month"),
                "current-date__year": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
                "dohod": SimpleMatcher(field_name="tax_type", adapter="UsnTaxTypeAdapter"),
                "god_podachi_uvedomleniya": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
            }),
            "%set-5": FieldSetMatcher(fields={
                "applicant-name__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                      attr_name="full_name"),
                "agent-doc-name__line{{item}}": ConstantMatcher(value=u"УСТАВ"),
                "phone": FieldAttributeMatcher(field_name="general_manager", attr_name="phone.normalised"),
                "name_line{{item}}": MultilineFieldMatcher(field_name="full_name",
                                                           prefix=u"Общество с ограниченной ответственностью «",
                                                           suffix=u"»"),
                "inn": ConstantMatcher(value=u"————————————"),
                "kpp": ConstantMatcher(value=u"————————————"),
                "polucheno_dohodov": ConstantMatcher(value=u"————————————"),
                "ostatok": ConstantMatcher(value=u"————————————"),
                "kod_nalog_organa": FieldAttributeMatcher(field_name="address", attr_name="ifns_number"),
                "priznak_zayavitelya": ConstantMatcher(value=1),
                "perehod": ConstantMatcher(value=2),
                "god_zayavleniya": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),

                "applicant-type": ConstantMatcher(value=1),
                "current-date__day": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="day"),
                "current-date__month": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="month"),
                "current-date__year": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
                "dohod": SimpleMatcher(field_name="tax_type", adapter="UsnTaxTypeAdapter"),
                "god_podachi_uvedomleniya": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
            })
        }
    }

    DECISION_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_DECISION,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Решение единственного учредителя ООО {{short_name}}",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "founders_count": 1
        },
        "fields": [
            FOUNDER_APPLICANT_FIELD,
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            STARTER_CAPITAL_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY,
            USE_FOREIGN_COMPANY_NAME_FIELD,
            USE_NATIONAL_LANGUAGE_COMPANY_NAME_FIELD,
            FOREIGN_FULL_NAME_FIELD,
            FOREIGN_SHORT_NAME_FIELD,
            NATIONAL_LANGUAGE_FULL_NAME_FIELD,
            NATIONAL_LANGUAGE_SHORT_NAME_FIELD,
            FOREIGN_LANGUAGE_FIELD,
            NATIONAL_LANGUAGE_FIELD,
            FOUNDERS_COUNT_FIELD, {
                "name": "general_manager",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True,
                "override_fields_kwargs": {
                    "phone": {
                        "required": True
                    }
                }
            }
        ]
    }

    DECISION_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_DECISION,
        "template_name": "soft_template_reshenie",
        "file_name": get_test_resource_name(config, "reshenie.tex"),
        "is_strict": False,
    }

    PROTOCOL_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_PROTOCOL,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Протокол ООО {{short_name}}",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "founders_count": {
                "#gt": 1
            }
        },
        "fields": [
            GENERAL_MANAGER_FIELD,
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY,
            FOUNDERS_FIELD,
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            STARTER_CAPITAL_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            USE_FOREIGN_COMPANY_NAME_FIELD,
            USE_NATIONAL_LANGUAGE_COMPANY_NAME_FIELD,
            FOUNDER_APPLICANT_FIELD,
            FOREIGN_FULL_NAME_FIELD,
            FOREIGN_SHORT_NAME_FIELD,
            NATIONAL_LANGUAGE_FULL_NAME_FIELD,
            NATIONAL_LANGUAGE_SHORT_NAME_FIELD,
            FOREIGN_LANGUAGE_FIELD,
            NATIONAL_LANGUAGE_FIELD,
            FOUNDERS_COUNT_FIELD,
            {
                "name": "share_type",
                "type": "DocEnumField",
                "enum_cls": "NumericPartEnum",
                "required": False
            },
            {
                "name": "reg_responsible_founder",
                "type": "db_object",
                "required": False
            },
            {
                "name": "doc_obtain_founder",
                "type": "db_object",
                "required": False
            },
            {
                "name": "registration_way",
                "type": "DocEnumField",
                "enum_cls": "RegistrationWay",
                "required": True
            }, {
                "name": "obtain_way",
                "type": "DocEnumField",
                "enum_cls": "DocumentDeliveryTypeStrEnum",
                "required": True
            }, {
                "name": "selected_secretary",
                "type": "db_object",
                "required": True
            }, {
                "name": "reg_responsible_person",
                "type": "db_object",
                "required": False
            }, {
                "name": "selected_moderator",
                "type": "db_object",
                "required": True
            }, {
                "name": "reg_responsible_person_obj",
                "type": "calculated",
                "field_type": "db_object",
                "required": False,
                "suppress_validation_errors": True,
                "value": {
                    "#cases": {
                        "list": [{
                                     "conditions": {
                                         "registration_way": "some_founders"
                                     },
                                     "value": {
                                         "#field": "reg_responsible_founder"
                                     }
                                 }],
                        "default": {
                            "value": {
                                "#field": "selected_moderator"
                            }
                        }
                    }
                }
            },
            {
                "name":"founders_ref_list",
                "type": "calculated",
                "field_type": "DocArrayField",
                "cls": "DocTextField",
                "value": FOUNDERS_REF_LIST_TEMP_VARIABLE,
                "depends_on": ["founders"],
                "suppress_validation_errors": True,
            }
        ],
        "validators": [{
                           "condition": {
                               "#or": [{
                                           "selected_secretary": {
                                               "#empty": True
                                           }
                                       }, {
                                           "selected_secretary->_id":
                                               {
                                                   "#in": "@founders_ref_list"
                                               }
                                       }]
                           },
                           "error": {
                               "field": "selected_secretary",
                               "code": 5
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "selected_moderator": {
                                               "#empty": True
                                           }
                                       }, {
                                           "selected_moderator->_id":
                                               {
                                                   "#in": "@founders_ref_list"
                                               }
                                       }]
                           },
                           "error": {
                               "field": "selected_moderator",
                               "code": 5
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "registration_way": {
                                               "#ne": "some_founders"
                                           }
                                       }, {
                                           "registration_way": "some_founders",
                                           "reg_responsible_founder->id": {
                                               "#in": "@founders_ref_list"
                                           }
                                       }]
                           },
                           "error": {
                               "field": "reg_responsible_founder",
                               "code": 5
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "registration_way": {
                                               "#ne": "responsible_person"
                                           }
                                       }, {
                                           "registration_way": "responsible_person",
                                           "reg_responsible_person": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "reg_responsible_person",
                               "code": 5
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "reg_responsible_person->_id": {
                                               "#nin": "@founders_ref_list"
                                           }
                                       }, {
                                           "registration_way": {
                                               "#ne": "responsible_person"
                                           }
                                       }]
                           },
                           "error": {
                               "field": "reg_responsible_person",
                               "code": 5
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "doc_obtain_founder->_id": {
                                               "#in": "@founders_ref_list"
                                           }
                                       }, {
                                           "obtain_way": {
                                               "#ne": "founder"
                                           }
                                       }]
                           },
                           "error": {
                               "field": "doc_obtain_founder",
                               "code": 5
                           }
                       },
                       # {
                       #            "condition" : {
                       #                "#or" : [{
                       #                    "share_type" : {
                       #                        "#ne" : "fraction"
                       #                    }
                       #                }, {
                       #                    "share_type" : "fraction",
                       #                    "is_all_divisible" : True
                       #                }]
                       #            },
                       #            "error" : {
                       #                "field" : "capital_divisibility",
                       #                "code" : 5
                       #            },
                       #            "#set" : {
                       #                "is_all_divisible" : {
                       #                    "#aggregate" : {
                       #                        "field" : "founders",
                       #                        "attr" : "is_starter_capital_dividable",
                       #                        "operator" : "and"
                       #                    }
                       #                }
                       #            }
                       #        }
        ]
    }

    PROTOCOL_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_PROTOCOL,
        "template_name": "soft_template_protocol",
        "file_name": get_test_resource_name(config, "protocol.tex"),
        "is_strict": False,
    }

    ESHN_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_ESHN,
        "file_name_template": u"Заявление на ЕСХН ООО {{short_name}}",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "taxation_type": TaxType.TT_ESHN
        },
        "fields": [
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY,
            GENERAL_MANAGER_FIELD,
            FOUNDERS_COUNT_FIELD,
            FOUNDER_APPLICANT_FIELD,
            JOB_MAIN_CODE_FIELD
        ],
        "external_validators": ["eshn_tax_type"],
    }

    ESHN_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_ESHN,
        "template_name": "strict_template1__eshn",
        "is_strict": True,
        "pages": [{

                      "variants": {
                          "type": RenderingVariants.TYPE_RENDER_FIRST_MATCHING,
                          "cases": [
                              {  # заявитель - физ. лицо, "founders_count" : 1
                                 "page_file": [get_test_resource_name(config, "new_eshn.pdf")],
                                 "field_matcher_set": "%set-1",
                                 "conditions": {
                                     "founder_applicant.founder_type": FounderTypeEnum.FT_PERSON,
                                     "founder_applicant.documents_recipient_type": {
                                         "#ne": None
                                     },
                                     "founders_count": 1
                                 }
                                 }, {  # заявитель - российское юр. лицо, "founders_count" : 1
                                       "page_file": [get_test_resource_name(config, "new_eshn.pdf")],
                                       "field_matcher_set": "%set-2",
                                       "conditions": {
                                           "founder_applicant.founder_type": FounderTypeEnum.FT_COMPANY,
                                           "founder_applicant.documents_recipient_type": {
                                               "#ne": None
                                           },
                                           "founders_count": 1
                                       }
                                       }, {  # заявитель - физ. лицо
                                             "page_file": [get_test_resource_name(config, "new_eshn.pdf")],
                                             "field_matcher_set": "%set-3",
                                             "conditions": {
                                                 "founder_applicant.founder_type": FounderTypeEnum.FT_PERSON,
                                                 "founder_applicant.documents_recipient_type": {
                                                     "#ne": None
                                                 }
                                             }
                                             }, {  # заявитель - российское юр. лицо
                                                   "page_file": [get_test_resource_name(config, "new_eshn.pdf")],
                                                   "field_matcher_set": "%set-4",
                                                   "conditions": {
                                                       "founder_applicant.founder_type": FounderTypeEnum.FT_COMPANY,
                                                       "founder_applicant.documents_recipient_type": {
                                                           "#ne": None
                                                       }
                                                   }
                                                   }]
                      },
                      "array_fields": [
                          {
                              "name": "full_name__line{{item}}",
                              "count": 4,
                              "field-length": 40,
                              "case": "upper"
                          }, {
                              "name": "applicant__line{{item}}",
                              "count": 3,
                              "field-length": 20,
                              "case": "upper"
                          }, {
                              "name": "applicant_doc__line{{item}}",
                              "field-length": 20,
                              "case": "upper",
                              "count": 2,
                          },
                      ],
                      "fields": [
                          {
                              "name": "inn",
                              "field-length": 12
                          }, {
                              "name": "kpp",
                              "field-length": 9
                          }, {
                              "name": "ifns",
                              "field-length": 4
                          }, {
                              "name": "priznak_zayavitelya",
                              "field-length": 1
                          }, {
                              "name": "perehod",
                              "field-length": 1
                          }, {
                              "name": "phone",
                              "field-length": 20
                          }, {
                              "name": "applicant_type",
                              "field-length": 1
                          }, {
                              "name": "doc_date__day",
                              "field-length": 2,
                              "text-align": "right",
                              "space-filler": u"0",
                          }, {
                              "name": "doc_date__month",
                              "field-length": 2,
                              "text-align": "right",
                              "space-filler": u"0",
                          }, {
                              "name": "doc_date__year",
                              "field-length": 4
                          }, {
                              "name": "dohod_maj",
                              "field-length": 3
                          }, {
                              "name": "dohod_min",
                              "field-length": 2
                          }, {
                              "name": "dohod_percent",
                              "field-length": 1
                          }
                      ]
                  }]
    }

    ESHN_MATCHER = {
        "doc_name": DocumentTypeEnum.DT_ESHN,
        "template_name": ESHN_TEMPLATE['template_name'],
        "fields": {
            "%set-1": FieldSetMatcher(fields={
                "applicant__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                 attr_name="full_name"),
                "applicant_doc__line{{item}}": ConstantMatcher(value=u"УСТАВ"),
                "phone": FieldAttributeMatcher(field_name="general_manager", attr_name="phone.normalised"),
                "full_name__line{{item}}": MultilineFieldMatcher(field_name="full_name",
                                                                 prefix=u"Общество с ограниченной ответственностью «",
                                                                 suffix=u"»"),
                "inn": ConstantMatcher(value=u"————————————"),
                "kpp": ConstantMatcher(value=u"————————————"),
                "dohod_maj": ConstantMatcher(value=u"————————————"),
                "dohod_min": ConstantMatcher(value=u"————————————"),
                "dohod_percent": ConstantMatcher(value=u"————————————"),
                "ifns": FieldAttributeMatcher(field_name="address", attr_name="ifns_number"),
                "priznak_zayavitelya": ConstantMatcher(value=1),
                "perehod": ConstantMatcher(value=2),
                "applicant_type": ConstantMatcher(value=1),
                "doc_date__day": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="day"),
                "doc_date__month": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="month"),
                "doc_date__year": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
            }),
            "%set-2": FieldSetMatcher(fields={
                "applicant__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                 attr_name="full_name"),
                "applicant_doc__line{{item}}": ConstantMatcher(value=u"УСТАВ"),
                "phone": FieldAttributeMatcher(field_name="general_manager", attr_name="phone.normalised"),
                "full_name__line{{item}}": MultilineFieldMatcher(field_name="full_name",
                                                                 prefix=u"Общество с ограниченной ответственностью «",
                                                                 suffix=u"»"),
                "inn": ConstantMatcher(value=u"————————————"),
                "kpp": ConstantMatcher(value=u"————————————"),
                "dohod_maj": ConstantMatcher(value=u"————————————"),
                "dohod_min": ConstantMatcher(value=u"————————————"),
                "dohod_percent": ConstantMatcher(value=u"————————————"),
                "ifns": FieldAttributeMatcher(field_name="address", attr_name="ifns_number"),
                "priznak_zayavitelya": ConstantMatcher(value=1),
                "perehod": ConstantMatcher(value=2),
                "applicant_type": ConstantMatcher(value=1),
                "doc_date__day": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="day"),
                "doc_date__month": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="month"),
                "doc_date__year": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
            }),
            "%set-3": FieldSetMatcher(fields={
                "applicant__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                 attr_name="full_name"),
                "applicant_doc__line{{item}}": ConstantMatcher(value=u"УСТАВ"),
                "phone": FieldAttributeMatcher(field_name="general_manager", attr_name="phone.normalised"),
                "full_name__line{{item}}": MultilineFieldMatcher(field_name="full_name",
                                                                 prefix=u"Общество с ограниченной ответственностью «",
                                                                 suffix=u"»"),
                "inn": ConstantMatcher(value=u"————————————"),
                "kpp": ConstantMatcher(value=u"————————————"),
                "dohod_maj": ConstantMatcher(value=u"————————————"),
                "dohod_min": ConstantMatcher(value=u"————————————"),
                "dohod_percent": ConstantMatcher(value=u"————————————"),
                "ifns": FieldAttributeMatcher(field_name="address", attr_name="ifns_number"),
                "priznak_zayavitelya": ConstantMatcher(value=1),
                "perehod": ConstantMatcher(value=2),
                "applicant_type": ConstantMatcher(value=1),
                "doc_date__day": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="day"),
                "doc_date__month": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="month"),
                "doc_date__year": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
            }),
            "%set-4": FieldSetMatcher(fields={
                "applicant__line{{item}}": MultilineFieldMatcher(field_name="general_manager",
                                                                 attr_name="full_name"),
                "applicant_doc__line{{item}}": ConstantMatcher(value=u"УСТАВ"),
                "phone": FieldAttributeMatcher(field_name="general_manager", attr_name="phone.normalised"),
                "full_name__line{{item}}": MultilineFieldMatcher(field_name="full_name",
                                                                 prefix=u"Общество с ограниченной ответственностью «",
                                                                 suffix=u"»"),
                "inn": ConstantMatcher(value=u"————————————"),
                "kpp": ConstantMatcher(value=u"————————————"),
                "dohod_maj": ConstantMatcher(value=u"————————————"),
                "dohod_min": ConstantMatcher(value=u"————————————"),
                "dohod_percent": ConstantMatcher(value=u"————————————"),
                "ifns": FieldAttributeMatcher(field_name="address", attr_name="ifns_number"),
                "priznak_zayavitelya": ConstantMatcher(value=1),
                "perehod": ConstantMatcher(value=2),
                "applicant_type": ConstantMatcher(value=1),
                "doc_date__day": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="day"),
                "doc_date__month": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="month"),
                "doc_date__year": FieldAttributeMatcher(field_name="doc_date_or_today", attr_name="year"),
            })
        }
    }

    CONTRACT_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_CONTRACT,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Договор ООО {{short_name}}",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "founders_count": {
                "#gt": 1
            }
        },
        "fields": [
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY,
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            FOUNDERS_FIELD,
            SHORT_NAME_FIELD,
            STARTER_CAPITAL_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            USE_FOREIGN_COMPANY_NAME_FIELD,
            USE_NATIONAL_LANGUAGE_COMPANY_NAME_FIELD,
            FOREIGN_FULL_NAME_FIELD,
            FOREIGN_SHORT_NAME_FIELD,
            FOUNDERS_COUNT_FIELD,
            NATIONAL_LANGUAGE_FULL_NAME_FIELD,
            NATIONAL_LANGUAGE_SHORT_NAME_FIELD,
            FOREIGN_LANGUAGE_FIELD,
            NATIONAL_LANGUAGE_FIELD
        ]
    }

    CONTRACT_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_CONTRACT,
        "template_name": "soft_template_contract",
        "file_name": get_test_resource_name(config, "contract.tex"),
        "is_strict": False
    }

    REG_FEE_INVOICE_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_REGISTRATION_FEE_INVOICE,
        "doc_kind": DocumentKindEnum.DK_DOWNLOADABLE_FILE,
        "file_name_template": u"Квитанция на оплату регистрационной пошлины ООО {{short_name}}",
        "http_method": "post",
        "data_template_name": get_test_resource_name(config, "reg_fee_invoice__data.txt"),
        "url_template_name": get_test_resource_name(config, "reg_fee_invoice__url.txt"),
        "file_name_extension": 'pdf',
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "founder_applicant": {
                "#not_empty": True
            }
        },
        "fields": [
            ADDRESS_TYPE_FIELD,
            FOUNDER_APPLICANT_FIELD,
            ADDRESS_FIELD_WITH_OKATO,
            {
                "name": "address_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "override_fields_kwargs": {
                    "address": {
                        "required": True,
                        "override_fields_kwargs": {
                            "ifns": {
                                "required": True
                            }
                        }
                    }
                }
            }
        ],
        "validators": [{
                           "condition": {
                               "#or": [{
                                           "address_type": {
                                               "#ne": "founder_registration_address"
                                           }
                                       }, {
                                           "address_type": "founder_registration_address",
                                           "address_person": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "address_person",
                               "code": 4
                           }
                       }, {
                           "condition": {
                               "#or": [{
                                           "address_type": {
                                               "#ne": "founder_registration_address"
                                           }
                                       }, {
                                           "address_type": "founder_registration_address",
                                           "address_person->address->okato": {
                                               "#not_empty": True
                                           }
                                       }]
                           },
                           "error": {
                               "field": "address_person.address.okato",
                               "code": 4
                           }
                       }]
    }

    OOO_BANK_PARTNER_APPLICATION_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_OOO_BANK_PARTNER_APPLICATION,
        "doc_kind": DocumentKindEnum.DK_DOWNLOADABLE_FILE,
        "file_name_template": u"заявление на открытие рассчетного счета в банке-партнере",
        "http_method": "post",
        "data_template_name": get_test_resource_name(config, "ooo_bank_partner_application__data.txt"),
        "url_template_name": get_test_resource_name(config, "ooo_bank_partner_application__url.txt"),
        "file_name_extension": 'pdf',
        "fields": [],
        "validators": []
    }

    DOVERENNOST_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_DOVERENNOST,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Доверенность на подачу документов",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "registration_way": RegistrationWay.RW_RESPONSIBLE_PERSON
        },
        "fields": [
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY,
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            FOUNDERS_FIELD,
            FOUNDER_APPLICANT_FIELD, {
                "name": "reg_responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True,
                "override_fields_kwargs": {
                    "address": {
                        "required": True
                    }
                }
            },
            {
                "name":"founders_ref_list",
                "type": "calculated",
                "field_type": "DocArrayField",
                "cls": "DocTextField",
                "depends_on": ["founders"],
                "value": FOUNDERS_REF_LIST_TEMP_VARIABLE,
                "suppress_validation_errors": True,
            }
        ],
        "validators": [{
               "condition": {
                   "#or": [{
                               "reg_responsible_person->_id": {
                                   "#nin": "@founders_ref_list"
                               }
                           }, {
                               "registration_way": {
                                   "#ne": "responsible_person"
                               }
                           }]
               },
               "error": {
                   "field": "reg_responsible_person",
                   "code": 5
               }
           }]
    }

    DOVERENNOST2_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_DOVERENNOST_OBTAIN,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Доверенность на получение документов",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "obtain_way": DocumentDeliveryTypeStrEnum.DDT_ISSUE_TO_THE_APPLICANT_OR_AGENT,
            "#or": [{
                        "registration_way": RegistrationWay.RW_RESPONSIBLE_PERSON,
                        "doc_obtain_person": {
                            "#ne": "@reg_responsible_person"
                        }
                    }, {
                        "registration_way": {
                            "#ne": RegistrationWay.RW_RESPONSIBLE_PERSON
                        }
                    }]
        },
        "fields": [
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY,
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            FOUNDERS_FIELD,
            FOUNDER_APPLICANT_FIELD,
            {
                "name": "doc_obtain_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True,
                "override_fields_kwargs": {
                    "address": {
                        "required": True
                    }
                }
            },
            {
                "name":"founders_ref_list",
                "type": "calculated",
                "field_type": "DocArrayField",
                "cls": "DocTextField",
                "depends_on": ["founders"],
                "value": FOUNDERS_REF_LIST_TEMP_VARIABLE,
                "suppress_validation_errors": True,
            }
        ],
        "validators": [{
                           "condition": {
                               "#or": [{
                                           "doc_obtain_person->_id": {
                                               "#nin": "@founders_ref_list"
                                           }
                                       }, {
                                           "obtain_way": {
                                               "#ne": "responsible_person"
                                           }
                                       }]
                           },
                           "error": {
                               "field": "doc_obtain_person",
                               "code": 5
                           }
                       }]
    }

    DOVERENNOST_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_DOVERENNOST,
        "template_name": "soft_template_doverennost",
        "file_name": get_test_resource_name(config, "doverennost.tex"),
        "is_strict": False,
    }

    DOVERENNOST_OBTAIN_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_DOVERENNOST_OBTAIN,
        "template_name": "soft_template_doverennost",
        "file_name": get_test_resource_name(config, "doverennost.tex"),
        "is_strict": False,
    }

    SOGLASIE_SOBSTVENNIKOV_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_SOGLASIE_SOBSTVENNIKOV,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Заявление - Согласие собственников",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "address_type": AddressType.AT_REAL_ESTATE_ADDRESS,
            "address_other_owner": True
        },
        "fields": [
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY
        ]
    }

    SOGLASIE_SOBSTVENNIKOV_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_SOGLASIE_SOBSTVENNIKOV,
        "template_name": "soft_template_SOGLASIE_SOBSTVENNIKOV",
        "file_name": get_test_resource_name(config, "soglasie_sobstvennikov.tex"),
        "is_strict": False,
    }

    GARANT_LETTER_ARENDA_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_GARANT_LETTER_ARENDA,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Гарантийное письмо (аренда)",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            u"@address_type": {
                "#in": ["office_address"]
            }
        },
        "fields": [
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY
        ]
    }

    GARANT_LETTER_ARENDA_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_GARANT_LETTER_ARENDA,
        "template_name": "soft_template_garant_letter_arenda",
        "file_name": get_test_resource_name(config, "garant_letter_arenda.tex"),
        "is_strict": False,
    }

    GARANT_LETTER_SUBARENDA_SCHEMA = {
        "doc_name": DocumentTypeEnum.DT_GARANT_LETTER_SUBARENDA,
        "doc_kind": DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template": u"Гарантийное письмо (субаренда)",
        "batch_statuses": [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            u"@address_type": {
                "#in": ["office_address"]
            }
        },
        "fields": [
            FULL_NAME_FIELD,
            ADDRESS_TYPE_FIELD_NR,
            ADDRESS_FIELD,
            DOC_DATE_FIELD_TODAY,
            DOC_DATE_OR_TODAY
        ]
    }

    GARANT_LETTER_SUBARENDA_TEMPLATE = {
        "doc_name": DocumentTypeEnum.DT_GARANT_LETTER_SUBARENDA,
        "template_name": "soft_template_garant_letter_subarenda",
        "file_name": get_test_resource_name(config, "garant_letter_subarenda.tex"),
        "is_strict": False
    }

    ################################################################################################################

    LLC_REG_BATCH_SCHEMA = {
        "doc_name": DocumentBatchTypeEnum.DBT_NEW_LLC,
        "fields": [
            SHORT_NAME_FIELD,
            FULL_NAME_FIELD,
            USE_FOREIGN_COMPANY_NAME_FIELD,
            USE_NATIONAL_LANGUAGE_COMPANY_NAME_FIELD,
            FOREIGN_FULL_NAME_FIELD,
            FOREIGN_SHORT_NAME_FIELD,
            NATIONAL_LANGUAGE_FULL_NAME_FIELD,
            NATIONAL_LANGUAGE_SHORT_NAME_FIELD,
            FOREIGN_LANGUAGE_FIELD,
            NATIONAL_LANGUAGE_FIELD,
            GENERAL_MANAGER_CAPTION_FIELD,
            JOB_MAIN_CODE_FIELD,
            JOB_CODE_ARRAY_FIELD,
            GENERAL_MANAGER_FIELD,
            BOARD_OF_DIRECTORS_FIELD,
            DOC_DATE_FIELD_TODAY,
            {
                "name": "lawyer_check",
                "type": "DocBoolField",
                "default": False
            },
            {
                "name": "region",
                "type": "DocEnumField",
                "enum_cls": "RFRegionsEnum",
                "required": True,
            }, {
                "name": "share_type",
                "type": "DocEnumField",
                "enum_cls": "NumericPartEnum",
                "required": True
            }, {
                "name": "starter_capital",
                "type": "DocCurrencyField",
                "required": True
            }, {
                "name": "pravo_otchuzhdeniya_type",
                "type": "DocEnumField",
                "enum_cls": "AlienationRightEnum",
                "required": True
            }, {
                "name": "preimusch_pravo_priobreteniya_doli_time_span",
                "type": "DocIntField",
                "required": True,
                "min_val": 30
            }, {
                "name": "perehod_doli_k_naslednikam_soglasie",
                "type": "DocBoolField",
                "required": True
            }, {
                "name": "sovet_directorov_num",
                "type": "DocIntField",
                "required": False,
                "even": False
            }, {
                "name": "general_manager_deals_max_amount",
                "type": "DocIntField",
                "required": False
            }, {
                "name": "general_manager_term",
                "type": "DocIntField",
                "min_val": 6,
                "max_val": 60,
                "required": True
            }, {
                "name": "board_of_directors_caption",
                "type": "DocTextField",
                "required": False,
                "allowed_re": CompanyObject.RUS_COMPANY_NAME_RE
            }, {
                "name": "large_deals_min_value",
                "type": "DocIntField",
                "min_val": 25,
                "max_val": 100,
                "required": False
            }, {
                "name": "large_deals_max_value",
                "type": "DocIntField",
                "min_val": 25,
                "max_val": 100,
                "required": False
            }, {
                "name": "large_property_deals_max_value",
                "type": "DocIntField",
                "required": False
            }, {
                "name": "large_property_deals_min_value",
                "type": "DocIntField",
                "required": False
            }, {
                "name": "necessary_votes_for_general_meeting_decisions",
                "type": "NecessaryVotesForGeneralMeeting",
                "required": True
            }, {
                "name": "selected_secretary",
                "type": "db_object",
                "required": True
            }, {
                "name": "selected_moderator",
                "type": "db_object",
                "required": True
            }, {
                "name": "tax_type",
                "type": "DocEnumField",
                "enum_cls": "UsnTaxType",
                "required": True
            }, {
                "name": "reg_responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            }, {
                "name": "reg_responsible_founder",
                "type": "db_object",
                "required": False
            }, {
                "name": "doc_obtain_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": True
            }, {
                "name": "doc_obtain_founder",
                "type": "db_object",
                "required": True
            }, {
                "name": "address",
                "type": "DocAddressField",
                "required": True
            }, {
                "name": "address_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            }, {
                "name": "address_other_owner",
                "type": "DocBoolField",
                "default": False
            }, {
                "name": "founders",
                "type": "DocArrayField",
                "cls": "FounderUIObject",
                "required": True
            }, {
                "name": "taxation_type",
                "type": "DocEnumField",
                "enum_cls": "TaxType",
                "required": True
            }, {
                "name": "registration_way",
                "type": "DocEnumField",
                "enum_cls": "RegistrationWay",
                "required": True
            }, {
                "name": "obtain_way",
                "type": "DocEnumField",
                "enum_cls": "DocumentDeliveryTypeStrEnum",
                "required": True
            }, {
                "name": "address_type",
                "type": "DocEnumField",
                "enum_cls": "AddressType",
                "required": True
            }, {
                "name": "has_general_manager_contract",
                "type": "DocBoolField",
                "required": False
            }, {
                "name": "has_general_manager_order",
                "type": "DocBoolField",
                "required": False
            }, {
                "name": "general_manager_contract_number",
                "type": "DocTextField",
                "required": False,
                "min_length": 1
            }, {
                "name": "general_manager_contract_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": False
            }, {
                "name": "general_manager_order_number",
                "type": "DocTextField",
                "required": False,
                "min_length": 1
            }, {
                "name": "general_manager_salary",
                "type": "DocCurrencyField",
                "required": False
            }, {
                "name": "general_manager_salary_days",
                "type": "DocArrayField",
                "cls": "DocIntField",
                "required": False
            }, {
                "name": "general_manager_trial_period",
                "type": "DocIntField",
                "required": False
            }, {
                "name": "general_manager_quit_notify_period",
                "type": "DocIntField",
                "required": False
            }, {
                "name": "general_manager_fixed_working_hours",
                "type": "DocBoolField",
                "required": False
            }, {
                "name": "general_manager_as_accountant",
                "type": "DocBoolField",
                "required": False
            }, {
                "name": "has_accountant_contract_order",
                "type": "DocBoolField",
                "required": False
            }, {
                "name": "accountant_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            }, {
                "name": "accountant_start_work",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": False
            }, {
                "name": "accountant_contract_number",
                "type": "DocTextField",
                "required": False,
                "min_length": 1
            }, {
                "name": "accountant_order_number",
                "type": "DocTextField",
                "required": False,
                "min_length": 1
            }, {
                "name": "accountant_salary",
                "type": "DocCurrencyField",
                "required": False
            }, {
                "name": "accountant_salary_days",
                "type": "DocArrayField",
                "cls": "DocIntField",
                "required": False
            }, {
                "name": "accountant_trial_period",
                "type": "DocIntField",
                "required": False
            }, {
                "name": "accountant_fixed_working_hours",
                "type": "DocBoolField",
                "required": False
            }, {
                "name": "ogrn",
                "type": "DocIntField",
                "min_val": 1000000000000,
                "max_val": 9999999999999,
                "required": False
            }, {
                "name": "inn",
                "type": "DocINNField",
                "required": False
            }, {
                "name": "kpp",
                "type": "DocTextField",
                "min_length": 9,
                "max_length": 9,
                "required": False
            }, {
                "name": "actual_address",
                "type": "DocAddressField",
                "required": False
            }, {
                "name": "bank_bik",
                "type": "DocTextField",
                "min_length": 9,
                "max_length": 9,
                "required": False
            }, {
                "name": "bank_account",
                "type": "DocTextField",
                "min_length": 20,
                "max_length": 20,
                "required": False
            }, {
                "name": "general_manager_working_hours",
                "type": "DocWorkingHoursField",
                "required": False
            }, {
                "name": "accountant_working_hours",
                "type": "DocWorkingHoursField",
                "required": False
            }, {
                "name": "general_manager_contract_additional_terms",
                "type": "DocAdditionalRightsField",
                "required": False
            }, {
                "name": "general_manager_as_accountant_order_number",
                "type": "DocTextField",
                "min_length": 1,
                "required": False
            }, {
                "name": "accountant_has_special_terms",
                "type": "DocBoolField",
                "default": False
            }, {
                "name": "general_manager_has_special_terms",
                "type": "DocBoolField",
                "default": False
            }, {
                "name": "registration_date",
                "type": "DocDateTimeField",
                "input_format": "%Y-%m-%d",
                "required": False
            }, {
                "name": "company_email",
                "type": "DocTextField",
                "min_length": 1,
                "required": False
            }, {
                "name": "company_site",
                "type": "DocTextField",
                "min_length": 10,
                "required": False
            }, {
                "name": "company_phone",
                "type": "DocPhoneNumberField",
                "required": False
            }, {
                "name": "stamp_partner_id",
                "type": "DocTextField",
                "min_length": 1,
                "required": False
            }, {
                "name": "accounts_partner_id",
                "type": "DocTextField",
                "min_length": 1,
                "required": False
            }
        ]
    }

    REGISTRATION_ADDRESS_FIELD = copy.copy(ADDRESS_FIELD)
    REGISTRATION_ADDRESS_FIELD['name'] = 'registration_address'

    LLC_REG_RESULT_FIELDS = [{
                                 "name": "founder_applicant",
                                 "type": "calculated",
                                 "field_type": "db_object",
                                 "required": False,
                                 "value": {
                                     "#set": {
                                         "selected_founder": {
                                             "#pick_array_item": {
                                                 "array_field": "founders",
                                                 "conditions": {
                                                     "#or": [{
                                                                 "founders|size": 1,
                                                             }, {
                                                                 "founders|size": {
                                                                     "#gt": 1
                                                                 },
                                                                 "obtain_way": "responsible_person",
                                                                 "<loop_item>->founder": "@selected_moderator"
                                                             }, {
                                                                 "founders|size": {
                                                                     "#gt": 1
                                                                 },
                                                                 "obtain_way": "founder",
                                                                 "<loop_item>->founder": "@doc_obtain_founder"
                                                             }, {
                                                                 "founders|size": {
                                                                     "#gt": 1
                                                                 },
                                                                 "obtain_way": "mail",
                                                                 "<loop_item>->founder": "@selected_moderator"
                                                             }]
                                                 }
                                             }
                                         }
                                     },
                                     "#object": {
                                         "type": {
                                             "#field": "selected_founder->founder->type"
                                         },
                                         "_id": {
                                             "#field": "selected_founder->founder->_id"
                                         }
                                     }
                                 }
                             }, {
                                 "name": "ifns",
                                 "type": "calculated",
                                 "field_type": "DocIntField",
                                 "required": False,
                                 "depends_on": ["address"],
                                 "value": {
                                     "#cases": {
                                         "list": [{
                                                      "conditions": {
                                                          "address_type": "founder_registration_address"
                                                      },
                                                      "value": {
                                                          "#field": "address_person->address->ifns"
                                                      }
                                                  }, {
                                                      "conditions": {
                                                          "address_type": "general_manager_registration_address",
                                                      },
                                                      "value": {
                                                          "#field": "general_manager->address->ifns"
                                                      }
                                                  }],
                                         "default": {
                                             "value": {
                                                 "#field": "address->ifns"
                                             }
                                         }
                                     }
                                 }
                             },
                             REGISTRATION_ADDRESS_FIELD,
                             {
                                 "name": "first_work_day",
                                 "type": "calculated",
                                 "field_type": "DocDateTimeField",
                                 "input_format": "%Y-%m-%d",
                                 "required": False,
                                 "value": {
                                     "#field": "registration_date->next_working_day_p"
                                 }
                             }
                             # {
                             #        "name" : "ifns_reg_info",
                             #        "type" : "calculated",
                             #        "field_type" : "IfnsRegInfoField",
                             #        "required" : False,
                             #        "value" : {
                             #            "#exec" : {
                             #                "module" : "external_methods.llc_reg_methods",
                             #                "method" : "get_company_registration_info",
                             #                "kwargs" : {
                             #                    "batch_id" : {
                             #                        "#field" : "<batch_id>"
                             #                    }
                             #                }
                             #            }
                             #        }
                             #    }
    ]

    LLC_REG_DEFER_DOCS = [DocumentTypeEnum.DT_REGISTRATION_FEE_INVOICE]

    return {
        "P11001_TEMPLATE": P11001_TEMPLATE,
        "P11001_MATCHER": P11001_MATCHER,
        "P11001_SCHEMA": P11001_SCHEMA,
        "ARTICLES_TEMPLATE": ARTICLES_TEMPLATE,
        "ARTICLES_SCHEMA": ARTICLES_SCHEMA,
        "ACT_SCHEMA": ACT_SCHEMA,
        "ACT_TEMPLATE": ACT_TEMPLATE,
        "USN_TEMPLATE": USN_TEMPLATE,
        "USN_MATCHER": USN_MATCHER,
        "USN_SCHEMA": USN_SCHEMA,
        "ESHN_TEMPLATE": ESHN_TEMPLATE,
        "ESHN_MATCHER": ESHN_MATCHER,
        "ESHN_SCHEMA": ESHN_SCHEMA,
        "DECISION_TEMPLATE": DECISION_TEMPLATE,
        "DECISION_SCHEMA": DECISION_SCHEMA,
        "PROTOCOL_SCHEMA": PROTOCOL_SCHEMA,
        "PROTOCOL_TEMPLATE": PROTOCOL_TEMPLATE,
        "CONTRACT_SCHEMA": CONTRACT_SCHEMA,
        "CONTRACT_TEMPLATE": CONTRACT_TEMPLATE,
        "REG_FEE_INVOICE_SCHEMA": REG_FEE_INVOICE_SCHEMA,
        "DOVERENNOST_SCHEMA": DOVERENNOST_SCHEMA,
        "DOVERENNOST2_SCHEMA": DOVERENNOST2_SCHEMA,
        "DOVERENNOST_TEMPLATE": DOVERENNOST_TEMPLATE,
        "DOVERENNOST_OBTAIN_TEMPLATE": DOVERENNOST_OBTAIN_TEMPLATE,
        "SOGLASIE_SOBSTVENNIKOV_SCHEMA": SOGLASIE_SOBSTVENNIKOV_SCHEMA,
        "SOGLASIE_SOBSTVENNIKOV_TEMPLATE": SOGLASIE_SOBSTVENNIKOV_TEMPLATE,
        "GARANT_LETTER_ARENDA_SCHEMA": GARANT_LETTER_ARENDA_SCHEMA,
        "GARANT_LETTER_ARENDA_TEMPLATE": GARANT_LETTER_ARENDA_TEMPLATE,
        "GARANT_LETTER_SUBARENDA_SCHEMA": GARANT_LETTER_SUBARENDA_SCHEMA,
        "GARANT_LETTER_SUBARENDA_TEMPLATE": GARANT_LETTER_SUBARENDA_TEMPLATE,
        "LLC_REG_BATCH_SCHEMA": LLC_REG_BATCH_SCHEMA,
        "LLC_REG_RESULT_FIELDS": LLC_REG_RESULT_FIELDS,
        "LLC_REG_DEFER_DOCS": LLC_REG_DEFER_DOCS,
        "OOO_BANK_PARTNER_APPLICATION_SCHEMA": OOO_BANK_PARTNER_APPLICATION_SCHEMA
    }



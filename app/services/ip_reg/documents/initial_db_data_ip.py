# -*- coding: utf-8 -*-
import copy
import os
from fw.documents.enums import DocumentTypeEnum, BatchStatusEnum, DocumentKindEnum, DocumentBatchTypeEnum, TaxType
from fw.documents.field_matchers import FieldSetMatcher, FieldAttributeMatcher, MultilineFieldMatcher, \
    ConcatFieldAttributeMatcher, SimpleMatcher, ArrayAttributeMatcher, ConstantMatcher
from fw.documents.common_schema_fields import (ADDRESS_FIELD,
    JOB_MAIN_CODE_FIELD, JOB_CODE_ARRAY_FIELD, DOC_DATE_FIELD, IP_FOUNDER_FIELD, TAXATION_TYPE_FIELD,
    USN_TAX_TYPE_FIELD, IP_OBTAIN_WAY_FIELD, IP_REGISTRATION_WAY_FIELD, IP_REGISTRATION_PERSON_FIELD,
    IP_OBTAIN_PERSON_FIELD, REGISTRATION_PERSON_FIELD, OBTAIN_PERSON_FIELD, IP_SAME_OBTAIN_TRUST_PERSON_FIELD)
from services.ip_reg.documents.enums import IPRegistrationWayEnum


def get_test_resource_name(config, resource_rel_path):
    resources_path = config['resources_path']
    return os.path.join(resources_path, resource_rel_path)


def load_data(config):

    from services.ip_reg.documents.p21001 import get_p21001_template
    P21001_TEMPLATE = get_p21001_template(config)

    P21001_MATCHER ={
        "doc_name" : DocumentTypeEnum.DT_P21001,
        "template_name" : P21001_TEMPLATE['template_name'],
        "fields" : {
            "%page_1-set-rus":                      FieldSetMatcher(fields = { # RUSSIAN CITIZEN
                "page1-surname":                    FieldAttributeMatcher(field_name="person", attr_name="surname"),
                "page1-name":                       FieldAttributeMatcher(field_name="person", attr_name="name"),
                "page1-patronymic":                 FieldAttributeMatcher(field_name="person", attr_name="patronymic"),
                "page1-inn":                        FieldAttributeMatcher(field_name="person", attr_name="inn"),
                "page1-birth_date__day":            FieldAttributeMatcher(field_name="person", attr_name="birthdate.day"),
                "page1-birth_date__month":          FieldAttributeMatcher(field_name="person", attr_name="birthdate.month"),
                "page1-birth_date__year":           FieldAttributeMatcher(field_name="person", attr_name="birthdate.year"),
                "page1-birth_place__line{{item}}":  MultilineFieldMatcher(field_name = "person", attr_name="birthplace"),
                "page1-citizenship":                FieldAttributeMatcher(field_name="person", attr_name="person_type.value"),
                #"page1-citizenship":                FieldAttributeMatcher(field_name="person", attr_name="living_country_code", adapter="CountryCodeRusAdapter"),
                "page1-gender":                     FieldAttributeMatcher(field_name="person", attr_name="sex", adapter="GenderToNumberAdapter"),
                # "page1-surname_latin": FieldAttributeMatcher(field_name="person", attr_name="surname"),
                # "page1-name_latin": FieldAttributeMatcher(field_name="person", attr_name="name"),
                # "page1-patronymic_latin": FieldAttributeMatcher(field_name="person", attr_name="patronymic"),
                # "page1-state_nationality":          FieldAttributeMatcher(field_name="person", attr_name="living_country_code")
            }),
            "%page_1-set-not_rus": FieldSetMatcher(fields = { # NOT RUSSIAN CITIZEN
                # "page1-surname": FieldAttributeMatcher(field_name="person", attr_name="surname"),
                # "page1-name": FieldAttributeMatcher(field_name="person", attr_name="name"),
                # "page1-patronymic": FieldAttributeMatcher(field_name="person", attr_name="patronymic"),
                "page1-inn":                        FieldAttributeMatcher(field_name="person", attr_name="inn"),
                "page1-birth_date__day":            FieldAttributeMatcher(field_name="person", attr_name="birthdate.day"),
                "page1-birth_date__month":          FieldAttributeMatcher(field_name="person", attr_name="birthdate.month"),
                "page1-birth_date__year":           FieldAttributeMatcher(field_name="person", attr_name="birthdate.year"),
                "page1-birth_place__line{{item}}":  MultilineFieldMatcher(field_name = "person", attr_name="birthplace"),
                "page1-citizenship":                FieldAttributeMatcher(field_name="person", attr_name="person_type.value"),
                #"page1-citizenship":                FieldAttributeMatcher(field_name="person", attr_name="living_country_code", adapter="CountryCodeRusAdapter"),
                "page1-gender":                     FieldAttributeMatcher(field_name="person", attr_name="sex", adapter="GenderToNumberAdapter"),
                "page1-surname_latin":              FieldAttributeMatcher(field_name="person", attr_name="surname"),
                "page1-name_latin":                 FieldAttributeMatcher(field_name="person", attr_name="name"),
                "page1-patronymic_latin":           FieldAttributeMatcher(field_name="person", attr_name="patronymic"),
                "page1-state_nationality":          FieldAttributeMatcher(field_name="person", attr_name="living_country_code")
            }),
            # PAGE 2
            "page2-subject_code":                   FieldAttributeMatcher(field_name="person", attr_name="address.region", adapter = "RFRegionNumberAdapter"),
            "page2-district_type":                  FieldAttributeMatcher(field_name="person", attr_name="address.district_type", adapter = "ShortDistrictTypeAdapter"),
            "page2-postal_index":                   FieldAttributeMatcher(field_name="person", attr_name="address.index"),
            "page2-city_type":                      FieldAttributeMatcher(field_name="person", attr_name="address.city_type", adapter = "ShortCityTypeAdapter"),
            "page2-city_name":                      FieldAttributeMatcher(field_name="person", attr_name="address.city"),
            "page2-nas_punkt_type":                 FieldAttributeMatcher(field_name="person", attr_name="address.village_type", adapter = "ShortVillageTypeAdapter"),
            "page2-street_type":                    FieldAttributeMatcher(field_name = "person", attr_name = "address.street_type", adapter = "ShortStreetTypeAdapter"),
            "page2-building_type":                  FieldAttributeMatcher(field_name = "person", attr_name = "address.house_type"),
            "page2-building_number":                FieldAttributeMatcher(field_name = "person", attr_name = "address.house"),
            "page2-korpus_type":                    FieldAttributeMatcher(field_name = "person", attr_name = "address.building_type"),
            "page2-korpus_number":                  FieldAttributeMatcher(field_name = "person", attr_name = "address.building"),
            "page2-flat_type":                      FieldAttributeMatcher(field_name = "person", attr_name = "address.flat_type"),
            "page2-flat_number":                    FieldAttributeMatcher(field_name = "person", attr_name = "address.flat"),
            "page2-doc_type":                       FieldAttributeMatcher(field_name = "person", attr_name = "passport.document_type"),
            "page2-doc_number":                     ConcatFieldAttributeMatcher(field_name="person", attributes = [ "passport.series", "passport.number"], adapter="InternalPassportAdapter"),
            "page2-issue_date__day":                FieldAttributeMatcher(field_name = "person", attr_name = "passport.issue_date.day"),
            "page2-issue_date__month":              FieldAttributeMatcher(field_name = "person", attr_name = "passport.issue_date.month"),
            "page2-issue_date__year":               FieldAttributeMatcher(field_name = "person", attr_name = "passport.issue_date.year"),
            "page2-subdivision_code__left":         FieldAttributeMatcher(field_name = "person", attr_name = "passport.depart_code"),
            "page2-subdivision_code__right":        FieldAttributeMatcher(field_name = "person", attr_name = "passport.depart_code"),
            "page2-nas_punkt_name__line{{item}}":   MultilineFieldMatcher(field_name = "person", attr_name = "address.village"),
            "page2-street_name__line{{item}}":      MultilineFieldMatcher(field_name = "person", attr_name = "address.street"),
            "page2-district_name__line{{item}}":    MultilineFieldMatcher(field_name = "person", attr_name = "address.district"),
            "page2-issuer__line{{item}}":           MultilineFieldMatcher(field_name = "person", attr_name = "passport.issue_depart"),
            # PAGE 3

            # PAGE 4
            "page4-main_job_code__part1" :          SimpleMatcher(field_name = "job_main_code"),
            "page4-main_job_code__part2" :          SimpleMatcher(field_name = "job_main_code"),
            "page4-main_job_code__part3" :          SimpleMatcher(field_name = "job_main_code"),
            "page4-job_code#{{item}}__part1" :      ArrayAttributeMatcher(field_name = "job_code_array", sorted = "true"),
            "page4-job_code#{{item}}__part2" :      ArrayAttributeMatcher(field_name = "job_code_array", sorted = "true"),
            "page4-job_code#{{item}}__part3" :      ArrayAttributeMatcher(field_name = "job_code_array", sorted = "true"),
            # PAGE 5
            "page5-document_delivery_type":         SimpleMatcher(field_name = "obtain_way", adapter = "DocumentObtainNumberAdapter"),
            "page5-phone_number":                   FieldAttributeMatcher(field_name = "person", attr_name="phone.normalised"),
            # "page5-email":                          FieldAttributeMatcher(field_name = "person", attr_name="email")
            # "page5-zaveritel_type":                 FieldAttributeMatcher(field_name = ""),
            # "page5-inn":                            FieldAttributeMatcher(field_name = ""),
        }
    }
    P21001_SCHEMA = {"doc_name" : DocumentTypeEnum.DT_P21001,
                     "file_name_template" : u"Заявление на регистрацию ИП",
                     "batch_statuses" : [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
                        "fields" : [
                            IP_FOUNDER_FIELD,
                            IP_OBTAIN_WAY_FIELD,
                            JOB_MAIN_CODE_FIELD,
                            JOB_CODE_ARRAY_FIELD,
                     ],
                     "validators" : [{
                         "condition" : {
                             "#or" : [{
                                 "person->initialized" : {
                                     "#ne" : True
                                 }
                             }, {
                                 "person->address->initialized" : {
                                     "#ne" : True
                                 }
                             }, {
                                 "person->address->region->initialized" : {
                                     "#ne" : True
                                 }
                             }, {
                                 "region->initialized" : {
                                     "#ne" : True
                                 }
                             }, {
                                 "person->address->region" : "@region"
                             }]
                         },
                         "error" : {
                             "field" : "person.address.region",
                             "code" : 5
                         }
                     }]
    }

    IP_STATE_DUTY_SCHEMA = {
        "doc_name" : DocumentTypeEnum.DT_IP_STATE_DUTY,
        "doc_kind" : DocumentKindEnum.DK_DOWNLOADABLE_FILE,
        "file_name_template" : u"Квитанция на оплату регистрационной пошлины ИП {{person.short_name}}",
        "http_method" : "post",
        "data_template_name" : get_test_resource_name(config, "ip/reg_fee_invoice__data.txt"),
        "url_template_name" : get_test_resource_name(config, "reg_fee_invoice__url.txt"),
        "file_name_extension" : 'pdf',
        "batch_statuses" : [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions" : {
            "person" : {
                "#not_empty" : True
            }
        },
        "fields" : [
            IP_FOUNDER_FIELD
        ]
    }

    IP_DOV_FILING_TEMPLATE = {
        "doc_name" : DocumentTypeEnum.DT_IP_DOV_FILING_DOCS,
        "template_name" : "ip_dov_filing_docs",
        "file_name" : get_test_resource_name(config, "ip/dov_filing_receiving_docs.tex"),
        "is_strict" : False,
    }

    IP_DOV_FILING_SCHEMA = {
        "doc_name" : DocumentTypeEnum.DT_IP_DOV_FILING_DOCS,
        "doc_kind" : DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template" : u"Доверенность на подачу документов",
        "batch_statuses" : [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "validators" : [{
             "condition" : {
                 "ip_responsible_person" : {
                     "#ne" : "@person"
                 }
             },
             "error" : {
                 "field" : "reg_responsible_person",
                 "code" : 5
             }
        }, {
            "condition" : {
                "#or": [{
                    "same_obtain_trust_person": False,
                    "reg_responsible_person" : {
                        "#not_empty" : True
                    }
                }, {
                    "same_obtain_trust_person": True
                }]
            },
            "error" : {
                "field" : "reg_responsible_person",
                "code" : 4
            }
        }, {
            "condition" : {
                "#or" : [{
                    "obtain_way" : {
                        "#ne" : "responsible_person"
                    },
                }, {
                    "obtain_way" : "responsible_person",
                    "#or": [{
                        "same_obtain_trust_person": False,
                        "doc_obtain_person" : {
                            "#not_empty" : True
                        }
                    }, {
                        "same_obtain_trust_person": True
                    }]
                }]
            },
            "error" : {
                "field" : "doc_obtain_person",
                "code" : 4
            }
        }],
        "conditions": {
            "same_obtain_trust_person": False,
            "registration_way": "responsible_person",
        },
        "fields" : [
            IP_FOUNDER_FIELD,
            IP_REGISTRATION_WAY_FIELD,
            IP_REGISTRATION_PERSON_FIELD,
            IP_SAME_OBTAIN_TRUST_PERSON_FIELD,
            DOC_DATE_FIELD,
            {
                "name": "reg_responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "suppress_validation_errors" : {
                    "registration_way": {
                        "#ne" : "responsible_person"
                    }
                }
            },
                {
                "name": "obtain_way",
                "type" : "DocEnumField",
                "enum_cls" : "IPDocumentDeliveryTypeStrEnum",
                "required" : False
            }, {
                "name": "doc_obtain_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "suppress_validation_errors" : True
            }
    ]}

    IP_DOV_RECEIVING_TEMPLATE = {
        "doc_name" : DocumentTypeEnum.DT_IP_DOV_RECEIVING_DOCS,
        "template_name" : "ip_dov_filing_docs",
        "file_name" : get_test_resource_name(config, "ip/dov_filing_receiving_docs.tex"),
        "is_strict" : False,
    }

    IP_DOV_RECEIVING_SCHEMA = {
        "doc_name" : DocumentTypeEnum.DT_IP_DOV_RECEIVING_DOCS,
        "doc_kind" : DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template" : u"Доверенность на получение документов",
        "batch_statuses" : [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions": {
            "#and": [{
                "#or": [{
                    "same_obtain_trust_person": False
                }, {
                    "registration_way": {
                        "#ne": "responsible_person"
                    }
                }],
            }, {
                "obtain_way": "responsible_person",
            }, {
                "#or": [{
                    "reg_responsible_person": {
                        "#ne": "@doc_obtain_person"
                    }

                }, {
                    "doc_obtain_person": {
                        "#empty": True
                    }
                }]
            }]
        },
        "fields" : [
            IP_FOUNDER_FIELD,
            IP_OBTAIN_PERSON_FIELD,
            DOC_DATE_FIELD,
            IP_OBTAIN_WAY_FIELD,
            IP_SAME_OBTAIN_TRUST_PERSON_FIELD,
            {
                "name": "reg_responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False,
                "suppress_validation_errors" : True
            },
                {
                "name": "doc_obtain_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            }, {
                "name": "registration_way",
                "type": "DocEnumField",
                "enum_cls": "IPRegistrationWayEnum",
                "required": False
            }
        ],
        "validators" : [{
            "condition" : {
                "#or": [{
                    "same_obtain_trust_person": False,
                    "doc_obtain_person" : {
                        "#not_empty" : True
                    }
                }, {
                    "same_obtain_trust_person": True,
                    "registration_way": "responsible_person",
                    "reg_responsible_person": {
                        "#empty": True
                    }
                }]
            },
            "error" : {
                "field" : "doc_obtain_person",
                "code" : 4
            }
        }]
    }

    IP_DOV_FILING_RECEIVING_TEMPLATE = {
        "doc_name" : DocumentTypeEnum.DT_IP_DOV_FILING_RECEIVING_DOCS,
        "template_name" : "ip_dov_filing_docs",
        "file_name" : get_test_resource_name(config, "ip/dov_filing_receiving_docs.tex"),
        "is_strict" : False,
    }

    IP_DOV_FILING_RECEIVING_SCHEMA = {
        "doc_name" : DocumentTypeEnum.DT_IP_DOV_FILING_RECEIVING_DOCS,
        "doc_kind" : DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template" : u"Доверенность на получение и подачу документов",
        "batch_statuses" : [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "validators" : [{
            "condition" : {
                "#or": [{
                    "same_obtain_trust_person": True,
                    "reg_responsible_person" : {
                        "#not_empty" : True
                    }
                }, {
                    "same_obtain_trust_person": False
                }]
            },
            "error" : {
                "field" : "reg_responsible_person",
                "code" : 4
            }
        }],
        "conditions": {
            "same_obtain_trust_person": True,
            "registration_way": "responsible_person",
            "obtain_way": "responsible_person",
        },
        "fields" : [
            IP_FOUNDER_FIELD,
            IP_OBTAIN_PERSON_FIELD,
            IP_SAME_OBTAIN_TRUST_PERSON_FIELD,
            DOC_DATE_FIELD,
            IP_OBTAIN_WAY_FIELD,
            IP_REGISTRATION_WAY_FIELD,
            {
                "name": "reg_responsible_person",
                "type": "db_object",
                "cls": "PrivatePerson",
                "required": False
            }
    ]}

    ################################################################################################################

    IP_REG_BATCH_SCHEMA = {
        "doc_name" : DocumentBatchTypeEnum.DBT_NEW_IP,
        "fields" : [
            JOB_MAIN_CODE_FIELD,
            JOB_CODE_ARRAY_FIELD,
            TAXATION_TYPE_FIELD,
            USN_TAX_TYPE_FIELD,
            IP_FOUNDER_FIELD,
            IP_REGISTRATION_WAY_FIELD,
            IP_OBTAIN_WAY_FIELD,
            IP_OBTAIN_PERSON_FIELD,
            IP_REGISTRATION_PERSON_FIELD,
            REGISTRATION_PERSON_FIELD,
            OBTAIN_PERSON_FIELD,
            IP_SAME_OBTAIN_TRUST_PERSON_FIELD
        ]
    }

    REGISTRATION_ADDRESS_FIELD = copy.copy(ADDRESS_FIELD)
    REGISTRATION_ADDRESS_FIELD['name'] = 'registration_address'

    IP_REG_RESULT_FIELDS = [
        {
            "name": "ifns",
            "type": "calculated",
            "field_type": "DocIntField",
            "required": False,
            "value": {
                "#cases" : {
                    "list" : [{
                        "conditions" : {
                            "person->initialized" : True
                        },
                        "value" : {
                            "#field": "person->address->ifns"
                        }
                    }],
                    "default" : {
                        "value" : {
                            "#value": 0,
                        }
                    }
                }
            }
        },
        {
            "name" : "ifns_reg_info",
            "type" : "calculated",
            "field_type" : "IfnsRegInfoField",
            "required" : False,
            "value" : {
                "#cases" : {
                    "list": [{
                        "conditions" : {
                            "person->initialized" : True
                        },
                        "value" : {
                           "#exec" : {
                               "module" : "ip_reg_methods",
                               "method" : "get_company_registration_info",
                               "kwargs" : {
                                   "batch_id" : {
                                       "#field" : "<batch_id>"
                                   }
                               }
                           }
                        }
                    }],
                    "default" : {
                        "value" : {
                            "#value": "",
                        }
                    }
                }
            }
        },
        {
            "name": "person_genitive",
            "type": "calculated",
            "field_type": "DocTextField",
            "required": False,
            "value" : {
                "#cases" : {
                    "list": [{
                        "conditions" : {
                            "person->initialized" : True
                        },
                        "value" : {
                            "#method": {
                                "obj" : "person",
                                "method" : "get_full_name",
                                "kwargs" : {
                                    "declension": "gen",
                                }
                            }
                        }
                    }],
                    "default" : {
                        "value" : {
                            "#value": "",
                        }
                    }
                }
            },
        },
        {
            "name": "person_dative",
            "type": "calculated",
            "field_type": "DocTextField",
            "required": False,
            "value" : {
                "#cases" : {
                    "list": [{
                        "conditions" : {
                            "person->initialized" : True
                        },
                        "value" : {
                            "#method": {
                                "obj" : "person",
                                "method" : "get_full_name",
                                "kwargs" : {
                                    "declension": "dat",
                                }
                            }
                        }
                    }],
                    "default" : {
                        "value" : {
                            "#value": "",
                        }
                    }
                }
            },
        }
    ]

    IP_ESHN_SCHEMA = {
        "doc_name" : DocumentTypeEnum.DT_IP_ESHN_CLAIM,
        "file_name_template" : u"Заявление на ЕСХН",
        "batch_statuses" : [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions" : {
            "taxation_type" : TaxType.TT_ESHN
        },
        "fields" : [
            IP_FOUNDER_FIELD,
            DOC_DATE_FIELD,
            JOB_MAIN_CODE_FIELD
        ],
        "external_validators" : ["ip_eshn_tax_type"]
    }

    IP_ESHN_TEMPLATE = {
        "doc_name" : DocumentTypeEnum.DT_IP_ESHN_CLAIM,
        "template_name" : "strict_template1__ip_eshn",
        "is_strict" : True,
        "pages" : [{
            "page_file": [get_test_resource_name(config, "new_eshn.pdf")],
            "array_fields" : [
                    {
                    "name" : "full_name__line{{item}}",
                    "count" : 4,
                    "field-length" : 40,
                    "case" : "upper"
                }, {
                    "name" : "applicant__line{{item}}",
                    "count" : 3,
                    "field-length" : 20,
                    "case" : "upper"
                }, {
                    "name" : "applicant_doc__line{{item}}",
                    "field-length" : 20,
                    "case" : "upper",
                    "count" : 2,
                    },
            ],
            "fields" : [
                    {
                    "name": "inn",
                    "field-length": 12
                }, {
                    "name": "kpp",
                    "field-length": 9
                }, {
                    "name" : "ifns",
                    "field-length" : 4
                }, {
                    "name" : "priznak_zayavitelya",
                    "field-length" : 1
                }, {
                    "name" : "perehod",
                    "field-length" : 1
                }, {
                    "name" : "phone",
                    "field-length" : 20
                }, {
                    "name" : "applicant_type",
                    "field-length" : 1
                }, {
                    "name" : "doc_date__day",
                    "field-length" : 2,
                    "text-align": "right",
                    "space-filler" : u"0",
                }, {
                    "name" : "doc_date__month",
                    "field-length" : 2,
                    "text-align": "right",
                    "space-filler" : u"0",
                }, {
                    "name" : "doc_date__year",
                    "field-length" : 4
                }, {
                    "name" : "dohod_maj",
                    "field-length" : 3
                }, {
                    "name" : "dohod_min",
                    "field-length" : 2
                }, {
                    "name" : "dohod_percent",
                    "field-length" : 1
                }
            ]
        }]
    }

    IP_ESHN_MATCHER = {
        "doc_name" : DocumentTypeEnum.DT_IP_ESHN_CLAIM,
        "template_name" : IP_ESHN_TEMPLATE['template_name'],
        "fields" : {
                "applicant__line{{item}}" : MultilineFieldMatcher(field_name = "person", attr_name="full_name"),
                # "applicant_doc__line{{item}}" : MultilineFieldMatcher(field_name = "person", attr_name="full_name"),
                "phone" : FieldAttributeMatcher(field_name = "person", attr_name="phone.normalised"),
                "full_name__line{{item}}" : MultilineFieldMatcher(field_name = "person", attr_name="full_name"),
                "inn" : FieldAttributeMatcher(field_name = "person", attr_name="inn", default_value=u"————————————"),
                "kpp" : ConstantMatcher(value=u"————————————"),
                "ifns" : FieldAttributeMatcher(field_name="person", attr_name="address.ifns_number"),
                "priznak_zayavitelya" : ConstantMatcher(value=1),
                "perehod" : ConstantMatcher(value=2),
                "applicant_type" : ConstantMatcher(value=1),
                "doc_date__day" : FieldAttributeMatcher(field_name="doc_date", attr_name="day"),
                "doc_date__month" : FieldAttributeMatcher(field_name="doc_date", attr_name="month"),
                "doc_date__year" : FieldAttributeMatcher(field_name="doc_date", attr_name="year"),
                "dohod_maj" : ConstantMatcher(value=u"————————————"),
                "dohod_min" : ConstantMatcher(value=u"————————————"),
                "dohod_percent" : ConstantMatcher(value=u"————————————")
        }
    }

    IP_USN_SCHEMA = {
        "doc_name" : DocumentTypeEnum.DT_IP_USN_CLAIM,
        "file_name_template" : u"Заявление на УСН",
        "batch_statuses" : [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "conditions" : {
            "taxation_type" : 'usn'
        },
        "fields" : [
            IP_FOUNDER_FIELD,
            DOC_DATE_FIELD,
            JOB_MAIN_CODE_FIELD,
            {
                "name" : "tax_type",
                "type" : "DocEnumField",
                "enum_cls" : "UsnTaxType",
                "required" : True,
            }
        ],
        "external_validators" : ["ip_usn_tax_type"]
    }

    IP_USN_TEMPLATE = {
        "doc_name" : DocumentTypeEnum.DT_IP_USN_CLAIM,
        "template_name" : "strict_template1__ip_usn",
        "is_strict" : True,
        "pages" : [{
            "page_file": get_test_resource_name(config, "new_usn.pdf"),
            "array_fields" : [
                    {
                    "name" : "name_line{{item}}",
                    "count" : 4,
                    "field-length" : 40,
                    "case" : "upper"
                }, {
                    "name" : "applicant-name__line{{item}}",
                    "count" : 3,
                    "field-length" : 20,
                    "case" : "upper"
                }, {
                    "name" : "agent-doc-name__line{{item}}",
                    "field-length" : 20,
                    "case" : "upper",
                    "count" : 2,
                }
            ],
            "fields" : [
                    {
                    "name": "inn",
                    "field-length": 12
                }, {
                    "name": "kpp",
                    "field-length": 9
                }, {
                    "name" : "kod_nalog_organa",
                    "field-length" : 4
                }, {
                    "name" : "priznak_zayavitelya",
                    "field-length" : 1
                }, {
                    "name" : "perehod",
                    "field-length" : 1
                }, {
                    "name" : "god_zayavleniya",
                    "text-align": "right",
                    "field-length" : 1
                }, {
                    "name" : "phone",
                    "field-length" : 20
                }, {
                    "name" : "applicant-type",
                    "field-length" : 1
                }, {
                    "name" : "current-date__day",
                    "field-length" : 2,
                    "text-align": "right",
                    "space-filler" : u"0",
                }, {
                    "name" : "current-date__month",
                    "field-length" : 2,
                    "text-align": "right",
                    "space-filler" : u"0",
                }, {
                    "name" : "current-date__year",
                    "field-length" : 4,
                    "text-align": "right",
                }, {
                    "name" : "dohod",
                    "field-length" : 1
                }, {
                    "name" : "polucheno_dohodov",
                    "field-length" : 9
                }, {
                    "name" : "god_podachi_uvedomleniya",
                    "field-length" : 2,
                    "text-align": "right"
                }, {
                    "name" : "ostatok",
                    "field-length" : 9
                }
            ]
        }],
    }

    IP_USN_MATCHER = {
        "doc_name": DocumentTypeEnum.DT_IP_USN_CLAIM,
        "template_name": IP_USN_TEMPLATE['template_name'],
        "fields": {
            "applicant-name__line{{item}}": MultilineFieldMatcher(field_name = "person", attr_name="full_name"),
            # "agent-doc-name__line{{item}}": MultilineFieldMatcher(field_name = "person", attr_name="full_name"),
            "phone": FieldAttributeMatcher(field_name = "person", attr_name="phone.normalised"),
            "name_line{{item}}": MultilineFieldMatcher(field_name = "person", attr_name="full_name"),
            "inn": FieldAttributeMatcher(field_name = "person", attr_name="inn", default_value=u"————————————"),
            "kpp": ConstantMatcher(value=u"————————————"),
            "polucheno_dohodov" : ConstantMatcher(value=u"————————————"),
            "ostatok" : ConstantMatcher(value=u"————————————"),
            "kod_nalog_organa": FieldAttributeMatcher(field_name="person", attr_name="address.ifns_number"),
            "priznak_zayavitelya": ConstantMatcher(value=1),
            "perehod": ConstantMatcher(value=2),
            "god_zayavleniya": FieldAttributeMatcher(field_name="doc_date", attr_name="year"),

            "applicant-type": ConstantMatcher(value=1),
            "current-date__day": FieldAttributeMatcher(field_name="doc_date", attr_name="day"),
            "current-date__month": FieldAttributeMatcher(field_name="doc_date", attr_name="month"),
            "current-date__year": FieldAttributeMatcher(field_name="doc_date", attr_name="year"),

            "dohod": SimpleMatcher(field_name = "tax_type", adapter = "UsnTaxTypeAdapter"),
            "god_podachi_uvedomleniya" : FieldAttributeMatcher(field_name="doc_date", attr_name="year"),
        }
    }

    IP_LETTER_INVENTORY_SCHEMA = {
        "doc_name" : DocumentTypeEnum.DT_IP_LETTER_INVENTORY,
        "doc_kind" : DocumentKindEnum.DK_TEX_TEMPLATE,
        "file_name_template" : u"Опись для ценного письма",
        "batch_statuses" : [BatchStatusEnum.BS_EDITED, BatchStatusEnum.BS_NEW],
        "fields" : [
            IP_FOUNDER_FIELD,
            IP_REGISTRATION_WAY_FIELD,
            TAXATION_TYPE_FIELD,
            {
                "name" : "ifns_name",
                "type" : "calculated",
                "field_type" : "DocTextField",
                "required" : False,
                "value" : {
                    "#field" : "person->address->ifns_name_safe"
                }
            }, {
                "name" : "ifns_address",
                "type" : "calculated",
                "field_type" : "DocTextField",
                "required" : False,
                "value" : {
                    "#field" : "person->address->ifns_address_safe"
                }
            }, {
                "name" : "usn",
                "type" : "calculated",
                "field_type" : "DocBoolField",
                "required" : False,
                "value" : {
                    "#cases" : {
                        "list" : [{
                            "conditions" : {
                                "taxation_type" : TaxType.TT_USN
                            },
                            "value" : {
                                "#value" : True
                            }
                        }],
                        "default" : {
                            "value" : {
                                "#value" : False
                            }
                        }
                    }
                }
            }, {
                "name" : "eshn",
                "type" : "calculated",
                "field_type" : "DocBoolField",
                "required" : False,
                "value" : {
                    "#cases" : {
                        "list" : [{
                            "conditions" : {
                                "taxation_type" : TaxType.TT_ESHN
                            },
                            "value" : {
                                "#value" : True
                            }
                        }],
                        "default" : {
                            "value" : {
                                "#value" : False
                            }
                        }
                    }
                }
            }
        ],
        "conditions" : {
            "registration_way" : IPRegistrationWayEnum.IP_RW_MAIL
        }
    }

    IP_LETTER_INVENTORY_TEMPLATE = {
        "doc_name" : DocumentTypeEnum.DT_IP_LETTER_INVENTORY,
        "template_name" : "ip_letter_inventory",
        "file_name" : get_test_resource_name(config, "ip/letter_inventory.tex"),
        "is_strict" : False
    }

    IP_REG_DEFER_DOCS = [DocumentTypeEnum.DT_IP_STATE_DUTY]

    return {
        "P21001_TEMPLATE" : P21001_TEMPLATE,
        "P21001_MATCHER" : P21001_MATCHER,
        "P21001_SCHEMA" : P21001_SCHEMA,
        "IP_STATE_DUTY_SCHEMA": IP_STATE_DUTY_SCHEMA,
        "IP_DOV_FILING_SCHEMA": IP_DOV_FILING_SCHEMA,
        "IP_DOV_FILING_TEMPLATE": IP_DOV_FILING_TEMPLATE,
        "IP_DOV_RECEIVING_SCHEMA": IP_DOV_RECEIVING_SCHEMA,
        "IP_DOV_RECEIVING_TEMPLATE": IP_DOV_RECEIVING_TEMPLATE,
        "IP_DOV_FILING_RECEIVING_SCHEMA": IP_DOV_FILING_RECEIVING_SCHEMA,
        "IP_DOV_FILING_RECEIVING_TEMPLATE": IP_DOV_FILING_RECEIVING_TEMPLATE,
        "IP_ESHN_SCHEMA": IP_ESHN_SCHEMA,
        "IP_ESHN_TEMPLATE": IP_ESHN_TEMPLATE,
        "IP_ESHN_MATCHER": IP_ESHN_MATCHER,
        "IP_USN_SCHEMA": IP_USN_SCHEMA,
        "IP_USN_TEMPLATE": IP_USN_TEMPLATE,
        "IP_USN_MATCHER": IP_USN_MATCHER,
        "IP_LETTER_INVENTORY_SCHEMA" : IP_LETTER_INVENTORY_SCHEMA,
        "IP_LETTER_INVENTORY_TEMPLATE" : IP_LETTER_INVENTORY_TEMPLATE,

        "IP_REG_BATCH_SCHEMA" : IP_REG_BATCH_SCHEMA,
        "IP_REG_RESULT_FIELDS" : IP_REG_RESULT_FIELDS,
        "IP_REG_DEFER_DOCS" : IP_REG_DEFER_DOCS
    }



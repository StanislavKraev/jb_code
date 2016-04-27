# -*- coding: utf-8 -*-
import os
from fw.documents.enums import DocumentTypeEnum
from fw.documents.template_renderer import RenderingVariants


def get_test_resource_name(config, resource_rel_path):
    resources_path = config['resources_path']
    return os.path.join(resources_path, resource_rel_path)

def get_p21001_template(config):
    return {
        "doc_name" : DocumentTypeEnum.DT_P21001,
        "template_name": "P21001_template",
        "is_strict": True,
        "pages": [
            {
                "variants": {
                    "type": RenderingVariants.TYPE_RENDER_FIRST_MATCHING,
                    "cases": [{
                                  "page_file": get_test_resource_name(config, "21001/pg_0001.pdf"),
                                  "field_matcher_set": "%page_1-set-rus",
                                  "conditions": {
                                      "person.person_type": 1
                                  }
                              }, {
                                  "page_file": get_test_resource_name(config, "21001/pg_0001.pdf"),
                                  "field_matcher_set": "%page_1-set-not_rus",
                                  "conditions": {
                                      "person.person_type": {"#ne": 1}
                                  }
                              }]
    
                },
                "array_fields": [
                    {
                        "name": "page1-birth_place__line{{item}}",
                        "count": 2,
                        "field-length": [40, 40],
                        "case": "upper"
                    }
                ],
                "fields": [
                    {
                        "name": "page1-surname",
                        "field-length": 34,
                        "text-align": "left",
                        "space-filler": u" ",
                        "case": "upper"
                    },
                    {
                        "name": "page1-name",
                        "field-length": 34,
                        "text-align": "left",
                        "space-filler": u" ",
                        "case": "upper"
                    },
                    {
                        "name": "page1-patronymic",
                        "field-length": 34,
                        "text-align": "left",
                        "space-filler": u" ",
                        "case": "upper"
                    },
                    {
                        "name": "page1-inn",
                        "field-length": 12,
                        "text-align": "left",
                    },
                    {
                        "name": "page1-birth_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    },
                    {
                        "name": "page1-birth_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    },
                    {
                        "name": "page1-birth_date__year",
                        "field-length": 4,
                        "text-align": "right",
                        "space-filler": u"0",
                    },
                    {
                        "name": "page1-citizenship",
                        "field-length": 1,
                        "text-align": "left",
                    },
                    {
                        "name": "page1-gender",
                        "field-length": 1,
                        "text-align": "left",
                    },
                    {
                        "name": "page1-surname_latin",
                        "field-length": 34,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page1-name_latin",
                        "field-length": 34,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page1-patronymic_latin",
                        "field-length": 34,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page1-state_nationality",
                        "field-length": 3,
                        "text-align": "left",
                    },
                    {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }
                ]
            },
            {
                "page_file": get_test_resource_name(config, "21001/pg_0002.pdf"),
                "fields": [
                    {
                        "name": "page2-subject_code",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    },
                    {
                        "name": "page2-district_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page2-postal_index",
                        "field-length": 6,
                        "text-align": "left",
                    },
                    {
                        "name": "page2-city_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page2-city_name",
                        "field-length": 28,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page2-nas_punkt_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page2-street_type",
                        "field-length": 40,
                        "text-align": "left",
                        "case": "upper"
                    },
    
                    {
                        "name": "page2-building_type",
                        "field-length": 10,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page2-building_number",
                        "field-length": 8,
                        "text-align": "left",
                    },
                    {
                        "name": "page2-korpus_type",
                        "field-length": 8,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page2-korpus_number",
                        "field-length": 8,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page2-flat_type",
                        "field-length": 8,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "page2-flat_number",
                        "field-length": 8,
                        "text-align": "left",
                    },
                    {
                        "name": "page2-doc_type",
                        "field-length": 2,
                        "text-align": "left",
                        # "case" : "upper"
                    },
                    {
                        "name": "page2-doc_number",
                        "field-length": 25,
                        "text-align": "left",
                        # "case" : "upper"
                    },
                    {
                        "name": "page2-issue_date__day",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    },
                    {
                        "name": "page2-issue_date__month",
                        "field-length": 2,
                        "text-align": "right",
                        "space-filler": u"0",
                    },
                    {
                        "name": "page2-issue_date__year",
                        "field-length": 4,
                        "text-align": "right",
                        "space-filler": u"0",
                    },
                    {
                        "name": "page2-subdivision_code__left",
                        "field-length": 3,
                        "text-align": "left",
                    },
                    {
                        "name": "page2-subdivision_code__right",
                        "field-length": 3,
                        "text-align": "right",
                    },
                ],
                "array_fields": [
                    {
                        "name": "page2-nas_punkt_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    },
                    {
                        "name": "page2-street_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    },
                    {
                        "name": "page2-district_name__line{{item}}",
                        "count": 2,
                        "field-length": [28, 40],
                        "case": "upper"
                    },
                    {
                        "name": "page2-issuer__line{{item}}",
                        "count": 3,
                        "field-length": [34, 40, 40],
                        "case": "upper"
                    },
                    {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }
                ]
            },
            # {
            #     "page_file": get_test_resource_name(config, "21001/pg_0003.pdf"),
            #     "fields": [
            #         {
            #             "name": "page3-document_number",
            #             "field-length": 25,
            #             "text-align": "left",
            #         },
            #         {
            #             "name": "page3-issued_by_line_1",
            #             "field-length": 34,
            #             "text-align": "left",
            #         },
            #         {
            #             "name": "page3-issued_by_line_2",
            #             "field-length": 40,
            #             "text-align": "left",
            #         },
            #         {
            #             "name": "page3-issued_by_line_3",
            #             "field-length": 40,
            #             "text-align": "left",
            #         },
            #         {
            #             "name": "page3-residential_permit",
            #             "field-length": 1,
            #             "text-align": "left",
            #         },
            #         {
            #             "name": "page3-issue_date__day",
            #             "field-length": 2,
            #             "text-align": "right",
            #             "space-filler": u"0",
            #         },
            #         {
            #             "name": "page3-issue_date__month",
            #             "field-length": 2,
            #             "text-align": "right",
            #             "space-filler": u"0",
            #         },
            #         {
            #             "name": "page3-issue_date__year",
            #             "field-length": 4,
            #             "text-align": "right",
            #             "space-filler": u"0",
            #         },
            #         {
            #             "name": "page3-validity_period__day",
            #             "field-length": 2,
            #             "text-align": "right",
            #             "space-filler": u"0",
            #         },
            #         {
            #             "name": "page3-validity_period__month",
            #             "field-length": 2,
            #             "text-align": "right",
            #             "space-filler": u"0",
            #         },
            #         {
            #             "name": "page3-validity_period__year",
            #             "field-length": 4,
            #             "text-align": "right",
            #             "space-filler": u"0",
            #         },
            #         {
            #             "name": "$page",
            #             "field-length": 3,
            #             "text-align": "right",
            #             "space-filler": u"0",
            #         }
            #     ],
            #     "array_fields": []
            # },
            #
            {
                "page_file": get_test_resource_name(config, "21001/pg_0004.pdf"),
    
                "fields": [
                    {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    },
                    {
                        "name": "page4-main_job_code__part1",
                        "text-align": "left",
                        "field-length": 2,
                    },
                    {
                        "name": "page4-main_job_code__part2",
                        "text-align": "center",
                        "field-length": 2,
                    },
                    {
                        "name": "page4-main_job_code__part3",
                        "text-align": "right",
                        "field-length": 2,
                    },
                ],
                "array_fields": [
                    {
                        "name": "page4-job_code#{{item}}__part1",
                        "count": 56,
                        "field-length": 2,
                        "text-align": "left",
                    },
                    {
                        "name": "page4-job_code#{{item}}__part2",
                        "count": 56,
                        "field-length": 2,
                        "text-align": "center",
                    },
                    {
                        "name": "page4-job_code#{{item}}__part3",
                        "count": 56,
                        "field-length": 2,
                        "text-align": "right",
                    }
                ],
            },
            {
                "page_file": get_test_resource_name(config, "21001/pg_0005.pdf"),
                "fields": [
                    {
                        "name": "page5-document_delivery_type",
                        "field-length": 1,
                        "text-align": "left",
                    },
                    {
                        "name": "page5-zaveritel_type",
                        "field-length": 1,
                        "text-align": "left",
                    },
                    {
                        "name": "page5-phone_number",
                        "field-length": 20,
                        "text-align": "left",
                    },
                    {
                        "name": "page5-inn",
                        "field-length": 12,
                        "text-align": "left",
                    },
                    {
                        "name": "page5-email",
                        "field-length": 35,
                        "text-align": "left",
                        "case": "upper"
                    },
                    {
                        "name": "$page",
                        "field-length": 3,
                        "text-align": "right",
                        "space-filler": u"0",
                    }
                ],
                "array_fields": []
            },
        ]
    }
    

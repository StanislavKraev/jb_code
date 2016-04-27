# -*- coding: utf-8 -*-

from decimal import Decimal

from fw.documents.fields.complex_doc_fields import ObjectRefField, DocArrayField
from fw.documents.fields.general_doc_fields import general_doc_field, GeneralField, DocCurrencyField, \
    DocNumericPartField
from fw.documents.fields.simple_doc_fields import DocEnumField, DocDecimalField, DocIntField, DocTextField, \
    DocDateTimeField, DocBoolField
from services.llc_reg.documents.enums import InitialCapitalDepositTypeEnum, FounderTypeEnum


@general_doc_field
class NecessaryVotesForGeneralMeeting(GeneralField):
    company_strategy = DocEnumField(enum_cls="NecessaryVotesEnum")
    articles_change = DocEnumField(enum_cls="NecessaryVotesEnum")
    executives_formation = DocEnumField(enum_cls="NecessaryVotesEnum")
    auditor_election = DocEnumField(enum_cls="NecessaryVotesEnum")
    annual_reports_approval = DocEnumField(enum_cls="NecessaryVotesEnum")
    profit_distribution = DocEnumField(enum_cls="NecessaryVotesEnum")
    internal_documents_approval = DocEnumField(enum_cls="NecessaryVotesEnum")
    obligations_emission = DocEnumField(enum_cls="NecessaryVotesEnum")
    audit_assignment = DocEnumField(enum_cls="NecessaryVotesEnum")
    large_deals_approval = DocEnumField(enum_cls="NecessaryVotesEnum")
    concern_deals_approval = DocEnumField(enum_cls="NecessaryVotesEnum")
    reorganization_or_liquidation = DocEnumField(enum_cls="NecessaryVotesEnum")
    liquidation_committee_assignment = DocEnumField(enum_cls="NecessaryVotesEnum")
    branch_establishment = DocEnumField(enum_cls="NecessaryVotesEnum")
    other_issues = DocEnumField(enum_cls="NecessaryVotesEnum")


@general_doc_field
class DocPersonPropertyField(GeneralField):
    name = DocTextField()
    price = DocCurrencyField()
    count = DocIntField(min_val=1)

    def __unicode__(self):
        return self.name

@general_doc_field
class FarmObjectField(GeneralField):
    person = ObjectRefField(cls="PrivatePerson")
    ogrnip = DocTextField(max_length=15, required=False)


@general_doc_field
class HolderShareField(GeneralField):
    holder_type = DocEnumField(enum_cls="JSCMemberTypeEnum", required=False)
    company = ObjectRefField(cls="CompanyObject", required=False)

@general_doc_field
class FounderObject(GeneralField):
    caption = DocTextField(required=False)
    founder_type = DocEnumField(enum_cls="FounderTypeEnum")

    company = ObjectRefField(cls="CompanyObject", required=False,
                             override_fields_kwargs={"address": {"required": True}})
    person = ObjectRefField(cls="PrivatePerson", required=False, override_fields_kwargs={"address": {"required": True}})
    name = DocTextField(max_length=160, required=False)

    management_company = ObjectRefField(cls="CompanyObject", required=False)

    gov_founder_type = DocEnumField(enum_cls="GovernmentFounderTypeEnum", required=False)
    region = DocEnumField(enum_cls="RFRegionsEnum", required=False)

    documents_recipient_type = DocEnumField(enum_cls="DocumentDeliveryTypeEnum", required=False)

    nominal_capital = DocCurrencyField(required=True)
    share = DocNumericPartField(required=True)

    properties = DocArrayField(cls='DocPersonPropertyField', required=False)

    duplicate_fio = DocBoolField(required=False, is_service=True)
    is_starter_capital_dividable = DocBoolField(required=False, is_service=True)

    @property
    def deposit_type(self):
        if self.fully_initialized:
            if self.properties.initialized and self.properties.api_value():
                sum = 0
                for i in self.properties.api_value():
                    sum += Decimal(i['price']['value']) * i['count']
                if Decimal(sum) == Decimal(self.nominal_capital.api_value()['value']):
                    return InitialCapitalDepositTypeEnum.ICD_PROPERTY
                return InitialCapitalDepositTypeEnum.ICD_MONEY_PARTIAL

        return InitialCapitalDepositTypeEnum.ICD_MONEY_FULL

    @property
    def property_total_amount(self):
        if not self.fully_initialized:
            return 0
        if self.nominal_capital.initialized:
            if self.properties.initialized and self.properties.api_value():
                sum = 0
                for i in self.properties.api_value():
                    sum += Decimal(i['price']['value']) * i['count']
                return Decimal(sum)

        return 0

    @property
    def fully_initialized(self):
        return self.initialized and self.nominal_capital.initialized and self.share.initialized

    @property
    def property_total_percents(self):
        if not self.fully_initialized:
            return 0
        return float(self.property_total_amount) / float(self.nominal_capital.value) * 100.0 * self.share.normal_value

    @property
    def money_total_percents(self):
        if not self.fully_initialized:
            return 0
        return float(self.money_total_amount) / float(self.nominal_capital.value) * 100.0 * self.share.normal_value

    @property
    def money_total_amount(self):
        if not self.fully_initialized:
            return 0
        return self.nominal_capital.value - self.property_total_amount

    @property
    def full_name(self):
        if not self.initialized or (not self.person.initialized and not self.company.initialized):
            return u""
        if self.founder_type == FounderTypeEnum.FT_PERSON:
            return self.person.full_name
        if self.founder_type == FounderTypeEnum.FT_COMPANY:
            return u"%s %s %s" % (self.company.general_manager_caption, self.company.qualified_short_name,
                                  self.company.general_manager.full_name)
        return u""

    @property
    def short_name(self):
        if not self.initialized:
            return u""
        if self.founder_type == FounderTypeEnum.FT_PERSON:
            if not self.person.initialized:
                return u""
            return self.person.short_name
        if self.founder_type == FounderTypeEnum.FT_COMPANY:
            if not self.company.initialized:
                return u""
            return u"%s %s %s" % (self.company.general_manager_caption, self.company.qualified_short_name,
                                  self.company.general_manager.short_name)
        return u""

@general_doc_field
class FounderUIObject(GeneralField):
    founder = ObjectRefField(required=True)
    nominal_capital = DocCurrencyField(required=True)
    share = DocDecimalField(required=True)


@general_doc_field
class ManagementCompanyField(GeneralField):
    company = ObjectRefField(cls="CompanyObject")

    foreign_company = ObjectRefField(cls="CompanyObject", required=False)
    russian_branch_or_agency = ObjectRefField(cls="CompanyObject", required=False)
    russian_agent = ObjectRefField(cls="PrivatePerson", required=False)


@general_doc_field
class DocWitnessField(GeneralField):
    inn = DocTextField(min_length=1)
    type = DocEnumField(enum_cls='WitnessTypeEnum')

    def __unicode__(self):
        return u""


@general_doc_field
class CompanyStarterCapitalField(GeneralField):
    capital_type = DocEnumField(enum_cls='CompanyStarterCapitalTypeEnum')
    value = DocCurrencyField()


@general_doc_field
class CharterCapitalPartField(GeneralField):
    person = ObjectRefField(cls='PrivatePerson')
    company = ObjectRefField(cls='CompanyObject')
    share_percents = DocIntField(min_val=1, max_val=100)
    share_value = DocCurrencyField()
    deposit_type = DocEnumField(enum_cls='InitialCapitalDepositTypeEnum')
    properties = DocArrayField(cls='DocPersonPropertyField')
    property_examinator = DocTextField()
    real_estate = DocTextField()

    def __unicode__(self):
        return u""


@general_doc_field
class DocAdditionalRightsField(GeneralField):
    rights = DocArrayField(cls='DocTextField', required=False, subfield_kwargs={'min_length': 1})
    responsibility = DocArrayField(cls='DocTextField', required=False, subfield_kwargs={'min_length': 1})
    duties = DocArrayField(cls='DocTextField', required=False, subfield_kwargs={'min_length': 1})


@general_doc_field
class IfnsRegInfoField(GeneralField):
    # full_name = DocTextField(required=False)
    ogrn = DocTextField(min_length=13, max_length=13, required=False)
    status = DocEnumField(enum_cls='IfnsRegStatusEnum', required=True)
    reg_date = DocDateTimeField(required=False)

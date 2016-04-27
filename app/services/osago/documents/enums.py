# -*- coding: utf-8 -*-


class CrashSubjectEnum(object):
    CS_VICTIM = "victim"
    CS_GUILTY = "guilty"
    CS_BOTH = "both"

    _NAMES = {
        CS_VICTIM: u"жертва",
        CS_GUILTY: u"виновник",
        CS_BOTH: u"и то и другое"
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return CrashSubjectEnum._NAMES.get(value, u"неизвестно")


class OsagoReasonEnum(object):
    OR_REFUSAL = "refusal"
    OR_UNDERPAY = "underpay"

    _NAMES = {
        OR_REFUSAL: u"отказ",
        OR_UNDERPAY: u"недоплата",
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return OsagoReasonEnum._NAMES.get(value, u"неизвестно")


class OsagoRefusalReasonEnum(object):
    ORR_REPAIRED = "repaired"
    ORR_NOT_SHOWN = "not_shown"
    ORR_DELAY = "delay"
    ORR_WRONG_DOCS = "wrong_docs"
    ORR_INCOMPLETE_DOCS = "incomplete_docs"

    _NAMES = {
        ORR_REPAIRED: u"отремонтирована",
        ORR_NOT_SHOWN: u"не осмотрена",
        ORR_DELAY: u"задержка",
        ORR_WRONG_DOCS: u"ошибки в документах",
        ORR_INCOMPLETE_DOCS: u"неполные документы"
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return OsagoRefusalReasonEnum._NAMES.get(value, u"неизвестно")

class _SimpleEnum(object):

    @classmethod
    def validate(cls, value):
        return value in cls._ALL

    @staticmethod
    def get_name(value):
        return ""

class OsagoDocTypeEnum(_SimpleEnum):
    ODT_INQUIRE_CRASH = "inquire_crash"
    ODT_NOTICE_CRASH = "notice_crash"
    ODT_ACT_INSURANCE_CASE = "act_insurance_case"
    ODT_INSURANCE_DENIAL = "insurance_denial"
    ODT_POLICE_STATEMENT = "police_statement"
    ODT_POLICE_PROTOCOL = "police_protocol"
    ODT_CASE_INITIATION_REFUSAL = "case_init_refusal"
    ODT_EXPERTISE_REPORT = "expertise_report"
    ODT_EXPERTISE_CONTRACT = "expertise_contract"
    ODT_PRETENSION_ANSWER_COPY = "pretension_answer"
    ODT_NOTARY_PAY_ACT = "notary_pay_act"
    ODT_POLICY_OSAGO = "policy_osago"
    ODT_BANK_STATEMENT = "bank_statement"

    _ALL = {
        ODT_INQUIRE_CRASH: u"cправка о ДТП",
        ODT_NOTICE_CRASH: u"извещение о ДТП",
        ODT_ACT_INSURANCE_CASE: u"акт о страховом случае",
        ODT_INSURANCE_DENIAL: u"отказ в выплате страховой компании",
        ODT_POLICE_STATEMENT: u"постановление по делу об административном нарушении",
        ODT_POLICE_PROTOCOL: u"протокол об административном нарушении",
        ODT_CASE_INITIATION_REFUSAL: u"определение об отказе в возбуждении дела об административном правонарушении",
        ODT_EXPERTISE_REPORT: u"отчет независимой экспертизы",
        ODT_EXPERTISE_CONTRACT: u"договор о проведении независимой экспертизы",
        ODT_PRETENSION_ANSWER_COPY: u"копия ответа на претензию",
        ODT_NOTARY_PAY_ACT: u"документы об оплате нотариальных услуг",
        ODT_POLICY_OSAGO: u"полис ОСАГО",
        ODT_BANK_STATEMENT: u"банковские документы, подтверждающие оплату страхового возмещения"
    }

    @staticmethod
    def get_name(value):

        return OsagoDocTypeEnum._ALL.get(value, u"")

class ApplicationTypeEnum(_SimpleEnum):
    AT_ONESELF = "oneself"
    AT_RESPONSIBLE_PERSON = "responsible_person"
    AT_MAIL = "mail"

    _ALL = {
        AT_ONESELF,
        AT_RESPONSIBLE_PERSON,
        AT_MAIL
    }

class ObtainAddressEnum(_SimpleEnum):
    OA_OWNER_ADDRESS = "owner_address"
    OA_RESPONSIBLE_PERSON_ADDRESS = "responsible_person_address"
    OA_OTHER_ADDRESS = "other_address"

    _ALL = {
        OA_OWNER_ADDRESS,
        OA_RESPONSIBLE_PERSON_ADDRESS,
        OA_OTHER_ADDRESS
    }

class OsagoBatchStatusEnum(_SimpleEnum):
    OBS_NEW = "new"
    OBS_PRETENSION = "pretension"
    OBS_CLAIM = "claim"
    OBS_CLAIM_PRESENTATION = "claim_presentation"

    _ALL = {
        OBS_NEW,
        OBS_PRETENSION,
        OBS_CLAIM,
        OBS_CLAIM_PRESENTATION
    }

class PretensionResultEnum(_SimpleEnum):
    PR_SUCCESS = "success"
    PR_REFUSE = "refuse"
    PR_PARTIAL_SUCCESS = "partial_success"
    PR_UNKNOWN = "unknown"

    _ALL = {
        PR_SUCCESS,
        PR_REFUSE,
        PR_PARTIAL_SUCCESS,
        PR_UNKNOWN
    }

class CourtAttendanceEnum(_SimpleEnum):
    CA_ONESELF = "oneself"
    CA_NOBODY = "nobody"
    CA_RESPONSIBLE_PERSON = "responsible_person"

    _ALL = {
        CA_ONESELF,
        CA_NOBODY,
        CA_RESPONSIBLE_PERSON
    }

class ActObtainWayEnum(_SimpleEnum):
    ABW_ONESELF = "oneself"
    ABW_MAIL = "mail"
    ABW_RESPONSIBLE_PERSON = "responsible_person"
    ABW_NO_OBTAIN = "no_obtain"

    _ALL = {
        ABW_ONESELF,
        ABW_MAIL,
        ABW_RESPONSIBLE_PERSON,
        ABW_NO_OBTAIN
    }

class InsuranceLawsuitEnum(_SimpleEnum):
    ILS_UNDERPAY = "insurance_underpay_lawsuit"
    ILS_PENALTY = "insurance_penalty_lawsuit"
    ILS_EXPERTISE_COST = "insurance_expertise_cost_lawsuit"
    ILS_FINE = "insurance_fine_lawsuit"

    _ALL = {
        ILS_UNDERPAY,
        ILS_PENALTY,
        ILS_EXPERTISE_COST,
        ILS_FINE
    }

class CourtLawsuitDocEnum(_SimpleEnum):
    CLD_LAWSUIT = u"lawsuit"
    CLD_CLAIM_COURT_ABSENT = u"claim_court_absent"
    CLD_INQUIRE_CRASH = u"inquire_crash"
    CLD_POLICE_PROTOCOL = u"police_protocol"
    CLD_POLICE_STATEMENT = u"police_statement"
    CLD_CASE_INIT_REFUSAL = u"case_init_refusal"
    CLD_NOTICE_CRASH = u"notice_crash"
    CLD_INSURANCE_DENIAL = u"insurance_denial"
    CLD_ACT_INSURANCE_CASE = u"act_insurance_case"
    CLD_EXPERTISE_REPORT = u"expertise_report"
    CLD_EXPERTISE_CONTRACT = u"expertise_contract"
    CLD_EXPERTISE_RECEIPT = u"expertise_receipt"
    CLD_PRETENSION_MAIL_RECEIPT = u"pretension_mail_receipt"
    CLD_PRETENSION_MAIL_LIST = u"pretension_mail_list"
    CLD_PRETENSION_MAIL_NOTIFY = u"pretension_mail_notify"
    CLD_PRETENSION = u"pretension"
    CLD_PRETENSION_INSURANCE_NOTE = u"pretension_insurance_note"
    CLD_DOCUMENTS_CLAIM = u"documents_claim"
    CLD_DOCUMENTS_CLAIM_INSURANCE_NOTE = u"documents_claim_insurance_note"
    CLD_PRETENSION_ANSWER_COPY = u"pretension_answer"
    CLD_POLICY_OSAGO_COPY = u"policy_osago_copy"
    CLD_CAR_CERTIFICATE = u"car_certificate"
    CLD_CAR_PASSPORT = u"car_passport"
    CLD_LEGAL_FEE_RECEIPT = u"legal_fee_receipt"
    CLD_TRUST_COURT_REPRESENTATION = u"trust_court_representation"
    CLD_TRUST_SUBMISION_OBTAIN_DOCS = u"trust_submision_obtain_docs"
    CLD_TRUST_INSURANCE_COURT = u"trust_insurance_court"
    CLD_MAIL_DOCS_LIST = u"mail_docs_list"
    CLD_BANK_STATEMENT = u"bank_statement"
    CLD_NOTARY_PAY_ACT = u"notary_pay_act"
    CLD_VICTIM_OWNER_PASSPORT_COPY = u"victim_owner_passport_copy"

    _ALL = {
        CLD_LAWSUIT,
        CLD_CLAIM_COURT_ABSENT,
        CLD_INQUIRE_CRASH,
        CLD_POLICE_PROTOCOL,
        CLD_POLICE_STATEMENT,
        CLD_CASE_INIT_REFUSAL,
        CLD_NOTICE_CRASH,
        CLD_INSURANCE_DENIAL,
        CLD_ACT_INSURANCE_CASE,
        CLD_EXPERTISE_REPORT,
        CLD_EXPERTISE_CONTRACT,
        CLD_EXPERTISE_RECEIPT,
        CLD_PRETENSION_MAIL_RECEIPT,
        CLD_PRETENSION_MAIL_LIST,
        CLD_PRETENSION_MAIL_NOTIFY,
        CLD_PRETENSION,
        CLD_PRETENSION_INSURANCE_NOTE,
        CLD_DOCUMENTS_CLAIM,
        CLD_DOCUMENTS_CLAIM_INSURANCE_NOTE,
        CLD_PRETENSION_ANSWER_COPY,
        CLD_POLICY_OSAGO_COPY,
        CLD_CAR_CERTIFICATE,
        CLD_CAR_PASSPORT,
        CLD_LEGAL_FEE_RECEIPT,
        CLD_TRUST_COURT_REPRESENTATION,
        CLD_TRUST_SUBMISION_OBTAIN_DOCS,
        CLD_TRUST_INSURANCE_COURT,
        CLD_MAIL_DOCS_LIST,
        CLD_BANK_STATEMENT,
        CLD_NOTARY_PAY_ACT,
        CLD_VICTIM_OWNER_PASSPORT_COPY
    }

# -*- coding: utf-8 -*-


class StarterCompanyCapitalTypeEnum(object):
    TYPE_CLS = int

    SCT_USTAVNOY_CAPITAL = 1
    SCT_SKLADOCHNY_CAPITAL = 2
    SCT_USTAVNOY_FOND = 3
    SCT_PAEVOY_FOND = 4

    _NAMES = {
        SCT_USTAVNOY_CAPITAL: u"уставной капитал",
        SCT_SKLADOCHNY_CAPITAL: u"складочный капитал",
        SCT_USTAVNOY_FOND: u"уставной фонд",
        SCT_PAEVOY_FOND: u"паевой фонд"
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES


    @staticmethod
    def get_name(value):
        return StarterCompanyCapitalTypeEnum._NAMES.get(value, u"неизвестно")


class JSCMemberTypeEnum(object):
    TYPE_CLS = int
    JSCMT_NEW_JSC = 1
    JSCMT_REGISTRATOR = 2

    _NAMES = {
        JSCMT_NEW_JSC: u"акционерное общество",
        JSCMT_REGISTRATOR: u"регистратор"
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return JSCMemberTypeEnum._NAMES.get(value, u"неизвестно")


class InitialCapitalDepositTypeEnum(object):
    TYPE_CLS = int

    ICD_MONEY_FULL = 1
    ICD_MONEY_PARTIAL = 2
    ICD_PROPERTY = 3
    ICD_REAL_ESTATES = 4
    ICD_PROPERTY_WITH_EXAMINATION = 5

    _NAMES = {
        ICD_MONEY_FULL: u"полностью оплатить",
        ICD_MONEY_PARTIAL: u"частично оплатить",
        ICD_PROPERTY: u"вещевой вклад",
        ICD_REAL_ESTATES: u"оплатить недвижимостью",
        ICD_PROPERTY_WITH_EXAMINATION: u"вещевой вклад с экспертизой"
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return InitialCapitalDepositTypeEnum._NAMES.get(value, u"неизвестно")


class DocumentDeliveryTypeEnum(object):
    TYPE_CLS = int

    DDT_ISSUE_TO_THE_APPLICANT = 1
    DDT_ISSUE_TO_THE_APPLICANT_OR_AGENT = 2
    DDT_SEND_BY_MAIL = 3

    _NAMES = {
        DDT_ISSUE_TO_THE_APPLICANT: u"выдать заявителю",
        DDT_ISSUE_TO_THE_APPLICANT_OR_AGENT: u"выдать заявителю или лицу, действующему на основании доверенности",
        DDT_SEND_BY_MAIL: u"направить по почте"
    }

    @classmethod
    def validate(cls, value):
        return value in DocumentDeliveryTypeEnum._NAMES

    @staticmethod
    def get_name(value):
        return DocumentDeliveryTypeEnum._NAMES.get(value, u"неизвестно")


class WitnessTypeEnum(object):
    TYPE_CLS = int

    WT_NOTARY = 1
    WT_NOTARY_TEMPORARY_SUBSTITUTE = 2
    WT_NOTARIAL_ACT_AUTHORIZED_PERSON = 3

    _NAMES = {
        WT_NOTARY: u"нотариус",
        WT_NOTARY_TEMPORARY_SUBSTITUTE: u"лицо, замещающее временно отсутствующего нотариуса",
        WT_NOTARIAL_ACT_AUTHORIZED_PERSON: u"должностное лицо, уполномоченное на совершение нотариального действия"
    }

    @classmethod
    def validate(cls, value):
        return value in WitnessTypeEnum._NAMES

    @staticmethod
    def get_name(value):
        return WitnessTypeEnum._NAMES.get(value, u"неизвестно")


class CompanyStarterCapitalTypeEnum(object):
    TYPE_CLS = int

    CSC_USTAVNOY_CAPITAL = 1
    CSC_SKLADOCHNY_CAPITAL = 2
    CSC_USTAVNOY_FOND = 3
    CSC_PAEVOY_FOND = 4

    _NAMES = {
        CSC_USTAVNOY_CAPITAL: u"уставной капитал",
        CSC_SKLADOCHNY_CAPITAL: u"складочный капитал",
        CSC_USTAVNOY_FOND: u"уставной фонд",
        CSC_PAEVOY_FOND: u"паевой фонд"
    }

    @classmethod
    def validate(cls, value):
        return value in CompanyStarterCapitalTypeEnum._NAMES

    @staticmethod
    def get_name(value):
        return unicode(value)

    @staticmethod
    def get_description(value):
        return CompanyStarterCapitalTypeEnum._NAMES.get(value, u"неизвестно")


class GovernmentFounderTypeEnum(object):
    TYPE_CLS = int

    GF_RUSSIA = 1
    GF_REGION = 2
    GF_MUNICIPALITY = 3

    _NAMES = {
        GF_RUSSIA: u'Российская Федерация',
        GF_REGION: u"субъект Российской Федерации",
        GF_MUNICIPALITY: u"муниципальное образование"
    }

    @classmethod
    def validate(cls, value):
        return value in GovernmentFounderTypeEnum._NAMES

    @staticmethod
    def get_name(value):
        return GovernmentFounderTypeEnum._NAMES.get(value, u"")


class FounderTypeEnum(object):
    TYPE_CLS = int

    FT_PERSON = 1
    FT_COMPANY = 2

    _NAMES = {
        FT_PERSON: u"учредитель юридического лица — физическое лицо",
        FT_COMPANY: u"учредитель юридического лица — российское юридическое лицо"
    }

    @classmethod
    def validate(cls, value):
        return value in FounderTypeEnum._NAMES

    @staticmethod
    def get_name(value):
        return FounderTypeEnum._NAMES.get(value, u"")


class FounderStrTypeEnum(object):
    FST_PERSON = "person"
    FST_COMPANY = "company"

    _NAMES = {
        FST_PERSON: u"учредитель юридического лица — физическое лицо",
        FST_COMPANY: u"учредитель юридического лица — российское юридическое лицо"
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return FounderStrTypeEnum._NAMES.get(value, u"")


class AlienationRightEnum(object):
    TYPE_CLS = int

    AR_PROHIBITED = 1
    AR_SOGLASIE_DRUGIH_UCHASTNIKOV_NE_TREBUETSYA = 2
    AR_SOGLASIE_DRUGIH_UCHASTNIKOV_TREBUETSYA = 3
    AR_THIRD_TREB_UCH_NE_TREB = 4
    AR_THIRD_PROHIB_UCH_NE_TREB = 5

    _NAMES = {
        AR_PROHIBITED: u"Продажа доли или части доли в уставном капитале Обществу третьим лицам запрещена, согласие на продажу или отчуждение в пользу учредителей требуется.",
        AR_SOGLASIE_DRUGIH_UCHASTNIKOV_NE_TREBUETSYA: u"Согласие других участников общества на продажу или отчуждение в пользу третьих лиц или участников не требуется.",
        AR_SOGLASIE_DRUGIH_UCHASTNIKOV_TREBUETSYA: u"Согласие других участников общества на продажу или отчуждение в пользу третьих лиц или участников требуется.",
        AR_THIRD_TREB_UCH_NE_TREB: u"Согласие других участников общества на продажу или отчуждение в пользу третьих лиц или участников требуется, участников — не требуется.",
        AR_THIRD_PROHIB_UCH_NE_TREB: u"Продажа доли или части доли в уставном капитале Обществу третьим лицам запрещена, согласие на продажу или отчуждение в пользу учредителей не требуется."
    }

    @classmethod
    def validate(cls, value):
        return value in AlienationRightEnum._NAMES

    @staticmethod
    def get_name(value):
        return AlienationRightEnum._NAMES.get(value, u"")


class BoardOfDirectorsAuthority(object):
    TYPE_CLS = int

    BDA_BONDS = 1
    BDA_BUSINESS_PLAN = 2
    BDA_BUDGET = 3
    BDA_ASSOCIATIONS = 4
    BDA_COMPANY_PROPERTY_BIG_DEALS = 5
    BDA_REAL_ESTATE_DEALS = 6
    BDA_INTELLECTUAL_PROPERTY_DEALS = 7
    BDA_PLEDGE_DECISIONMAKING = 8
    BDA_DEALS_CHANGES_DECISIONMAKING = 9
    BDA_OBLIGATION_DEALS_DECISIONMAKING = 10
    BDA_AUDIT_APPOINTMENT = 11
    BDA_CHANGE_GENERAL_MANAGER = 12
    BDA_CHANGE_BANK_ACCOUNTS_CREDENTIALS = 13
    BDA_INTERNAL_SHARE_PLEDGE_DECISIONMAKING = 14
    BDA_FUNDS_SPENDING_REPORTS_APPROVAL = 15
    BDA_GENERAL_MANAGER_CONTRACT_APPROVAL = 16
    BDA_CHANGE_COMPANY_REGULATIONS = 17
    BDA_FINANCE_DIRECTOR_APPROVAL = 18
    BDA_KEY_PERSONS_CONTRACTS_APPROVAL = 19
    BDA_ASSETS_MANAGEMENT_DEALS_APPROVAL = 20
    BDA_CREDITS_USAGE_DEALS_DECISIONMAKING = 21
    BDA_CONSULTATIONS_DEALS_APPROVAL = 22
    BDA_STAFF_LIST_APPROVAL = 23
    BDA_BILL_DEAL_APPROVAL = 24
    BDA_TAKING_PART_IN_COMERCIAL_COMPANIES = 25
    BDA_MANAGE_EXECUTIVES = 26
    BDA_MANAGE_EXECUTIVE_CONTRACTS = 27
    BDA_SHARES_RIGHTS_MANAGEMENT = 28

    _NAMES = {
        BDA_BONDS: u"принятие решения о размещении Обществом облигаций и иных эмиссионных ценных бумаг",
        BDA_BUSINESS_PLAN: u"утверждение и изменение Бизнес-плана Общества",
        BDA_BUDGET: u"утверждение и изменение Бюджетов Общества",
        BDA_ASSOCIATIONS: u"принятие решения об участии Общества в ассоциациях и других объединениях коммерческих организаций",
        BDA_COMPANY_PROPERTY_BIG_DEALS: u"принятие решений о совершении крупных сделок, связанных с приобретением, отчуждением или возможностью отчуждения Обществом прямо либо косвенно имущества, стоимость которого составляет от двадцати пяти до пятидесяти процентов стоимости имущества Общества, определенной на основании данных бухгалтерской отчетности за последний отчетный период, предшествующий дню принятия решения о совершении таких сделок, если уставом общества не предусмотрен более высокий размер крупной сделки",
        BDA_REAL_ESTATE_DEALS: u"принятие решений о совершении сделок с недвижимым имуществом или правами на недвижимое имущество",
        BDA_INTELLECTUAL_PROPERTY_DEALS: u"принятие решений о совершении сделок с приобретением, отчуждением  и обременением исключительных прав на объекты интеллектуальной собственности и или средства индивидуализации (кроме случаев приобретения прав на использование программ для электронных вычислительных машин и/или баз данных)",
        BDA_PLEDGE_DECISIONMAKING: u"принятие решений о предоставлении имущества Общества в залог (или иные обременения), заключение Обществом иных договоров, направленных на обеспечение исполнения обязательств Общества или третьих лиц, изменение или прекращение таких договоров",
        BDA_DEALS_CHANGES_DECISIONMAKING: u"принятие решений о заключении или изменении сделки Общества в совершении которой имеется заинтересованность",
        BDA_OBLIGATION_DEALS_DECISIONMAKING: u"принятие решений о заключении, изменении или прекращении любого соглашения, не входящего в обычную сферу деятельности Общества или которое направлено на создание обязательств у Общества сроком более чем на 12 месяцев",
        BDA_AUDIT_APPOINTMENT: u"назначение аудиторской проверки, утверждение аудитора и установление размера оплаты его услуг как для Общества. принятие решения о порядке голосования на общих собраниях Участников/акционеров дочерних и зависимых Обществ в части утверждения аудитора и установления размера оплаты его услуг",
        BDA_CHANGE_GENERAL_MANAGER: u"избрание Генерального директора Общества и досрочное прекращение его полномочий, определение и изменение объёма его полномочий, а также принятие решения о передаче полномочий Генерального директора Общества коммерческой организации или индивидуальному предпринимателю (далее - управляющий), утверждение такого управляющего и условий договора с ним",
        BDA_CHANGE_BANK_ACCOUNTS_CREDENTIALS: u"утверждение полномочий и прекращение полномочий на распоряжение (включая право подписи) банковскими счетами Общества",
        BDA_INTERNAL_SHARE_PLEDGE_DECISIONMAKING: u"принятие решения об одобрении залога (или обременения иным образом) доли в уставном капитале Общества любым из Участников Общества в пользу другого Участника Общества",
        BDA_FUNDS_SPENDING_REPORTS_APPROVAL: u"утверждение отчетов Генерального директора и документов, подтверждающих  целевое расходование денежных средств в рамках финансового плана  (бюджета) Общества",
        BDA_GENERAL_MANAGER_CONTRACT_APPROVAL: u"утверждений условий трудового договора, установление размера вознаграждения и денежных компенсаций Генеральному директору Общества",
        BDA_CHANGE_COMPANY_REGULATIONS: u"утверждение, принятие или изменение документов, регулирующих организацию деятельности Общества (внутренних документов Общества), за исключением внутренних документов, утверждение которых отнесено к компетенции общего собрания участников Общества",
        BDA_FINANCE_DIRECTOR_APPROVAL: u"принятие решения об одобрении кандидатуры на должность финансового директора Общества, определение и изменение объёма его полномочий, утверждение условий договора с ним, включая размер вознаграждения и денежных компенсаций",
        BDA_KEY_PERSONS_CONTRACTS_APPROVAL: u"утверждение условий трудовых договоров и изменений к ним с  ключевыми работниками Общества, включая размер вознаграждения и денежных компенсаций",
        BDA_ASSETS_MANAGEMENT_DEALS_APPROVAL: u"принятие решений об одобрении сделок по приобретению или продаже активов (включая движимое и недвижимое имущество) Общества, иных капиталовложениях Общества, включая сделки в рамках текущей хозяйственной деятельности Общества и сделки во исполнение Бизнес-плана Общества, в форме одной сделки или нескольких взаимосвязанных сделок, превышающих в сумме 500000 (пятьсот тысяч) рублей, но не превышающих 3000000 (три миллиона рублей)",
        BDA_CREDITS_USAGE_DEALS_DECISIONMAKING: u"принятие решений об одобрении сделок о предоставлении/получении Обществом любых займов, кредитов",
        BDA_CONSULTATIONS_DEALS_APPROVAL: u"одобрение сделок Общества на оказании консультационных, маркетинговых и иных услуг в форме одной сделки или нескольких взаимосвязанных сделок, превышающих в сумме 500000 (пятьсот тысяч)  рублей, но не превышающих 3000000 (три миллиона рублей)",
        BDA_STAFF_LIST_APPROVAL: u"утверждение штатного расписания Общества",
        BDA_BILL_DEAL_APPROVAL: u"одобрение вексельной сделки, в том числе по выдаче Обществом векселей, производстве по ним передаточных надписей, авалей, платежей независимо от суммы",
        BDA_TAKING_PART_IN_COMERCIAL_COMPANIES: u"принятие решений об учреждении, участии и прекращении участия в коммерческих организациях, а также о совершении сделок, связанных с приобретением, отчуждением и возможностью отчуждения акций (паев, долей в уставном или складочном капитале) других коммерческих организаций",
        BDA_MANAGE_EXECUTIVES: u"образование исполнительных органов общества и досрочное прекращение их полномочий, а также принятие решения о передаче полномочий единоличного исполнительного органа общества",
        BDA_MANAGE_EXECUTIVE_CONTRACTS: u"установление размера вознаграждения и денежных компенсаций единоличному исполнительному органу общества, членам коллегиального исполнительного органа общества, управляющему",
        BDA_SHARES_RIGHTS_MANAGEMENT: u"принятие решения об использовании прав, предоставляемых принадлежащими Обществу акциями (паями, долями в уставном или складочном капитале) других коммерческих организаций"
    }

    @classmethod
    def validate(cls, value):
        return value in BoardOfDirectorsAuthority._NAMES

    @staticmethod
    def get_name(value):
        return BoardOfDirectorsAuthority._NAMES.get(value, u"")


class NecessaryVotesEnum(object):
    TYPE_CLS = int

    NV_ALL = 1
    NV_2_3 = 2
    NV_3_4 = 3

    _NAMES = {
        NV_ALL: u"единогласно",
        NV_2_3: u"простым большинством (2/3 голосов)",
        NV_3_4: u"квалифицированным большинством (3/4 голосов)"
    }

    @classmethod
    def validate(cls, value):
        return value in NecessaryVotesEnum._NAMES

    @staticmethod
    def get_name(value):
        return NecessaryVotesEnum._NAMES.get(value, u"")


class IfnsServiceEnum(object):
    TYPE_CLS = int

    IS_REG_COMPANY = 1
    IS_RECEIVE_REG_DOCS = 2
    IS_REG_IP = 3

    _NAMES = {
        IS_REG_COMPANY: u"регистрация юр. лица",
        IS_RECEIVE_REG_DOCS: u"получение документов юр. лица по создании",
        IS_REG_IP: u"регистрация ИП",
    }

    @classmethod
    def validate(cls, value):
        return value in IfnsServiceEnum._NAMES

    @staticmethod
    def get_name(value):
        return IfnsServiceEnum._NAMES.get(value, u"")


class UsnTaxType(object):
    TYPE_CLS = int

    UT_INCOME = 1
    UT_INCOME_MINUS_EXPENSE = 2

    _NAMES = {
        UT_INCOME: u"доходы",
        UT_INCOME_MINUS_EXPENSE: u"доходы, уменьшенные на сумму расходов"
    }

    @classmethod
    def validate(cls, value):
        return value in UsnTaxType._NAMES

    @staticmethod
    def get_name(value):
        return UsnTaxType._NAMES.get(value, u"")


class RegistrationWay(object):
    RW_ALL_FOUNDERS = "all_founders"
    RW_SOME_FOUNDERS = "some_founders"
    RW_RESPONSIBLE_PERSON = "responsible_person"
    RW_NOTARY = "notary"

    _NAMES = {
        RW_ALL_FOUNDERS: u"все учредители",
        RW_SOME_FOUNDERS: u"некоторые учредители",
        RW_RESPONSIBLE_PERSON: u"ответственное лицо",
        RW_NOTARY: u"нотариус"
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return RegistrationWay._NAMES.get(value, u"")


class DocumentDeliveryTypeStrEnum(object):
    DDT_ISSUE_TO_THE_APPLICANT = "founder"
    DDT_ISSUE_TO_THE_APPLICANT_OR_AGENT = "responsible_person"
    DDT_SEND_BY_MAIL = "mail"

    _NAMES = {
        DDT_ISSUE_TO_THE_APPLICANT: u"выдать заявителю",
        DDT_ISSUE_TO_THE_APPLICANT_OR_AGENT: u"выдать заявителю или лицу, действующему на основании доверенности",
        DDT_SEND_BY_MAIL: u"направить по почте"
    }

    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return DocumentDeliveryTypeStrEnum._NAMES.get(value, u"неизвестно")


class AddressType(object):
    AT_GENERAL_MANAGER_REGISTRATION_ADDRESS = "general_manager_registration_address"
    AT_FOUNDER_REGISTRATION_ADDRESS = "founder_registration_address"
    AT_REAL_ESTATE_ADDRESS = "real_estate_address"
    AT_OFFICE_ADDRESS = "office_address"

    _NAMES = {
        AT_GENERAL_MANAGER_REGISTRATION_ADDRESS: "x",
        AT_FOUNDER_REGISTRATION_ADDRESS: "y",
        AT_REAL_ESTATE_ADDRESS: "z",
        AT_OFFICE_ADDRESS: "."
    }


    @classmethod
    def validate(cls, value):
        return value in cls._NAMES

    @staticmethod
    def get_name(value):
        return AddressType._NAMES.get(value, u"неизвестно")



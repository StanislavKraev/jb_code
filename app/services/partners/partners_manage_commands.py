# -*- coding: utf-8 -*-

from datetime import datetime
from fw.db.sql_base import db as sqldb
from fw.documents.address_enums import RFRegionsEnum
from fw.documents.common_schema_fields import ADDRESS_FIELD
from manage_commands import BaseManageCommand
from services.partners.models import (
    AccountantPartnersObject,
    BankPartnersObject,
    BankPartnersServiceObject,
    StampPartnersObject,
    BankPartnerRequestObject)

_BANK_PARTNER_SCHEMA = [{
    "name": "contact_phone",
    "type": "calculated",
    "field_type": "DocPhoneNumberField",
    "required": True,
    "suppress_validation_errors": True,
    "value": {
        "#cases": {
            "list": [{
                "conditions": {
                    "bank_contact_phone_general_manager": True
                },
                "value": {
                    "#field": "general_manager->phone"
                }
            }],
            "default": {
                "value": {
                    "#field": "bank_contact_phone"
                }
            }
        }
    }
}, {
    "name": "short_name",
    "type": "DocTextField",
    "required": False,
    "suppress_validation_errors": {
        "send_private_data": False
    }
}, {
    "name": "ogrn",
    "type": "calculated",
    "field_type": "DocTextField",
    "value": {
        "#field": "<batch>->result_fields->ifns_reg_info->ogrn"
    }
}, {
    "name": "inn",
    "type": "DocTextField",
    "required": False,
    "suppress_validation_errors": {
        "send_private_data": False
    }
}, ADDRESS_FIELD, {
    "name": "general_manager_caption",
    "type": "DocTextField",
    "required": False,
    "suppress_validation_errors": {
        "send_private_data": False
    }
}, {
    "name": "general_manager",
    "type": "db_object",
    "cls": "PrivatePerson",
    "required": False,
    "override_fields_kwargs": {
        "phone": {
            "required": True
        },
        "address": {
            "required": True
        }
    },
    "suppress_validation_errors": {
        "send_private_data": False
    }
}, {
    "name": "bank_title",
    "type": "DocTextField",
    "required": True,
    "suppress_validation_errors": True
}, {
    "name": "schema",
    "type": "calculated",
    "field_type": "DocTextField",
    "required": True,
    "value": {
        "#field": "<config>->WEB_SCHEMA"
    }
}, {
    "name": "domain",
    "type": "calculated",
    "field_type": "DocTextField",
    "required": True,
    "value": {
        "#field": "<config>->DOMAIN"
    }
}]

#################################################################################################

_BANK_PARTNER_SCHEMA2 = [
    {
        "name": "contact_phone",
        "type": "calculated",
        "field_type": "DocPhoneNumberField",
        "required": True,
        "suppress_validation_errors": True,
        "value": {
            "#cases": {
                "list": [{
                    "conditions": {
                        "bank_contact_phone_general_manager": True
                    },
                    "value": {
                        "#field": "general_manager->phone"
                    }
                }],
                "default": {
                    "value": {
                        "#field": "bank_contact_phone"
                    }
                }
            }
        }
    },
    ADDRESS_FIELD,
    {
        "name": "general_manager",
        "type": "db_object",
        "cls": "PrivatePerson",
        "required": False,
        "override_fields_kwargs": {
            "phone": {
                "required": True
            },
            "address": {
                "required": True
            }
        },
        "suppress_validation_errors": {
            "send_private_data": False
        }
    }
]


class ReinitPartnersCommand(BaseManageCommand):
    NAME = "reinit_partners"

    def run(self):
        schema = self.config['WEB_SCHEMA']
        domain = self.config['DOMAIN']

        make_link = lambda x: '%s://%s/res/%s' % (schema, domain, x)

        BankPartnerRequestObject.query.delete()
        BankPartnersServiceObject.query.delete()
        BankPartnersObject.query.delete()
        sqldb.session.commit()

        new_item = BankPartnersObject(
            id="553faf59bdffb5220faca395",
            region=[RFRegionsEnum.RFR_SPB,
                    RFRegionsEnum.RFR_MOSCOW,
                    RFRegionsEnum.RFR_SVERDLOVSKAYA_REGION,
                    RFRegionsEnum.RFR_CHELYABINSKAYA_REGION,
                    RFRegionsEnum.RFR_TATARSTAN,
                    RFRegionsEnum.RFR_NOVOSIBIRSKAYA_REGION,
                    RFRegionsEnum.RFR_KRASNOYARSKIY_KRAY],
            city=[RFRegionsEnum.RFR_SPB,
                  RFRegionsEnum.RFR_MOSCOW,
                  u"Екатеринбург",
                  u"Челябинск",
                  u"Казань",
                  u"Новосибирск",
                  u"Красноярск"],
            enabled=True,
            sort_index=1,
            link='',
            banner=make_link('b1.png'),
            title=u'«Открытие»',
            created=datetime.utcnow(),
            conditions=[u"Открытие расчетного счета — бесплатно"]
        )
        sqldb.session.add(new_item)
        sqldb.session.commit()

        new_item = BankPartnersObject(
            id="55c9afab543ed837fea53db2",
            region=[
                RFRegionsEnum.RFR_IRKUTSKAYA_REGION,
                RFRegionsEnum.RFR_ALTAYSKIY_KRAI,
                RFRegionsEnum.RFR_BELGORODSKAYA_REGION,
                RFRegionsEnum.RFR_PRIMORSKIY_KRAI,
                RFRegionsEnum.RFR_VOLGOGRADSKAYA_REGION,
                RFRegionsEnum.RFR_VORONEZHSKAYA_REGION,
                RFRegionsEnum.RFR_SVERDLOVSKAYA_REGION,
                RFRegionsEnum.RFR_UDMURTIYA,
                RFRegionsEnum.RFR_IRKUTSKAYA_REGION,
                RFRegionsEnum.RFR_TATARSTAN,
                RFRegionsEnum.RFR_KALININGRADSKAYA_REGION,
                RFRegionsEnum.RFR_KALUZHSKAYA_REGION,
                RFRegionsEnum.RFR_KEMEROVSKAYA_REGION,
                RFRegionsEnum.RFR_KRASNODARSKIY_KRAI,
                RFRegionsEnum.RFR_KRASNOYARSKIY_KRAY,
                RFRegionsEnum.RFR_LIPETSKAYA_REGION,
                RFRegionsEnum.RFR_CHELYABINSKAYA_REGION,
                RFRegionsEnum.RFR_MOSCOW,
                RFRegionsEnum.RFR_MURMANSKAYA_REGION,
                RFRegionsEnum.RFR_UGRA,
                RFRegionsEnum.RFR_NIZHEGORODSKAYA_REGION,
                RFRegionsEnum.RFR_NOVOSIBIRSKAYA_REGION,
                RFRegionsEnum.RFR_OMSKAYA_REGION,
                RFRegionsEnum.RFR_ORENBURGSKAYA_REGION,
                RFRegionsEnum.RFR_PENZENSKAYA_REGION,
                RFRegionsEnum.RFR_PERMSKIY_KRAI,
                RFRegionsEnum.RFR_ROSTOVSKAYA_REGION,
                RFRegionsEnum.RFR_RYAZANSKAYA_REGION,
                RFRegionsEnum.RFR_SAMARSKAYA_REGION,
                RFRegionsEnum.RFR_SPB,
                RFRegionsEnum.RFR_SARATOVSKAYA_REGION,
                RFRegionsEnum.RFR_STAVROPOLSKY_KRAI,
                RFRegionsEnum.RFR_TVERSKAYA_REGION,
                RFRegionsEnum.RFR_TOMSKAYA_REGION,
                RFRegionsEnum.RFR_TULSKAYA_REGION,
                RFRegionsEnum.RFR_TUMENSKAYA_REGION,
                RFRegionsEnum.RFR_ULYANOVSKAYA_REGION,
                RFRegionsEnum.RFR_BASHKARTOSTAN,
                RFRegionsEnum.RFR_HABAROVSKY_KRAI,
                RFRegionsEnum.RFR_CHUVASHIYA,
                RFRegionsEnum.RFR_YAROSLAVSKAYA_REGION
            ],
            city=[
                u"Ангарск"
                u"Барнаул",
                u"Белгород",
                u"Владивосток",
                u"Волгоград",
                u"Волжский",
                u"Воронеж",
                u"Екатеринбург",
                u"Ижевск",
                u"Иркутск",
                u"Казань",
                u"Калининград",
                u"Калуга",
                u"Кемерово",
                u"Краснодар",
                u"Красноярск",
                u"Липецк",
                u"Магнитогорск",
                u"Москва",
                u"Мурманск",
                u"Набережные Челны",
                u"Нижневартовск",
                u"Нижний Новгород",
                u"Новокузнецк",
                u"Новосибирск",
                u"Омск",
                u"Оренбург",
                u"Орск",
                u"Пенза",
                u"Пермь",
                u"Ростов-на-Дону",
                u"Рязань",
                u"Самара",
                u"Санкт-Петербург",
                u"Саратов",
                u"Сочи",
                u"Ставрополь",
                u"Сургут",
                u"Тверь",
                u"Томск",
                u"Тула",
                u"Тюмень",
                u"Ульяновск",
                u"Уфа",
                u"Хабаровск",
                u"Чебоксары",
                u"Челябинск",
                u"Ярославль"],
            enabled=True,
            sort_index=2,
            link='',
            banner=make_link('b2.png'),
            title=u'«Альфа-банк»',
            created=datetime.utcnow(),
            conditions=[
                u"бесплатный выезд менеджера в офис",
                u"открытие расчетного счета за 2‒3 дня",
                u"3 месяца бесплатно при оплате сразу 9 месяцев",
                u"до 3000 рублей на поиск профессионалов на HH.ru",
                u"до 9000 рублей на Яндекс.Директ после открытия счета в подарок"
            ]
        )
        sqldb.session.add(new_item)
        sqldb.session.commit()

        new_item = BankPartnersServiceObject(
            id="553faff4bdffb5220faca396",
            type='email',
            email='grigoryan@bank24.ru',
            fields=_BANK_PARTNER_SCHEMA,
            template_name='account_creation_consultation_request',
            bank_partner_id="553faf59bdffb5220faca395"
        )
        sqldb.session.add(new_item)
        sqldb.session.commit()

        is_prod = not self.config['STAGING'] and not self.config['DEBUG']
        new_item = BankPartnersServiceObject(
            id="55c9eab75f7105f302fbfadc",
            type='web',
            config={
                'method': 'post',
                'url': 'https://alfabank.ru/sme/invitation/' if is_prod
                       else 'http://ifns.staging.legalcloud.ru/send_bank_request/',
            },
            fields=_BANK_PARTNER_SCHEMA2,
            template_name='alpha_bank_web_request',
            bank_partner_id="55c9afab543ed837fea53db2"
        )
        sqldb.session.add(new_item)
        sqldb.session.commit()

        if self.config['STAGING'] or self.config['DEBUG']:
            new_item = BankPartnersObject(
                id="554b5d3fd045c98560aa9352",
                region=[RFRegionsEnum.RFR_SPB,
                        RFRegionsEnum.RFR_MOSCOW],
                city=[RFRegionsEnum.RFR_SPB,
                      RFRegionsEnum.RFR_MOSCOW],
                enabled=True,
                sort_index=1,
                link='',
                banner=make_link('b1.png'),
                title=u'«Закрытие»',
                created=datetime.utcnow(),
                conditions=[u"condition1", u"ждфыловаджо фывалджо фыджво"]
            )
            sqldb.session.add(new_item)
            sqldb.session.commit()

            new_item = BankPartnersServiceObject(
                id="554b5d4dd045c98560aa9353",
                type='email',
                email='sas@tochka2.com',
                fields=_BANK_PARTNER_SCHEMA,
                template_name='account_creation_consultation_request',
                bank_partner_id="554b5d3fd045c98560aa9352"
            )
            sqldb.session.add(new_item)
            sqldb.session.commit()

        # accounts
        AccountantPartnersObject.query.delete()
        sqldb.session.commit()

        new_partner = AccountantPartnersObject(
            id="55424ad532dba9d4e53c990a",
            region=None,
            enabled=True,
            sort_index=1,
            link='https://www.moedelo.org/Referal/Lead/12568?targetUrl=www.moedelo.org/Prices',
            banner=make_link('a1.png'),
            title=u'«Моё.Дело»',
            created=datetime.utcnow(),
            type='online'
        )
        sqldb.session.add(new_partner)

        new_partner = AccountantPartnersObject(
            id="554a408d8d807ba959e548a8",
            region=None,
            enabled=True,
            sort_index=1,
            link='http://www.b-kontur.ru/?p=3020',
            banner=make_link('a2.png'),
            title=u'«Контур.Бухгалтерия»',
            created=datetime.utcnow(),
            type='online'
        )
        sqldb.session.add(new_partner)
        sqldb.session.commit()

        if self.config['STAGING'] or self.config['DEBUG']:
            new_partner = AccountantPartnersObject(
                id="554b5d11d045c98560aa9351",
                region=[RFRegionsEnum.RFR_SPB, RFRegionsEnum.RFR_MOSCOW],
                enabled=True,
                sort_index=100,
                link='http://www.b-kontur.ru/?p=3020',
                banner=make_link('a2.png'),
                title=u'«Бухгалтерия.Контур»',
                created=datetime.utcnow(),
                type='offline'
            )
            sqldb.session.add(new_partner)
            sqldb.session.commit()

        StampPartnersObject.query.delete()
        sqldb.session.commit()

        if self.config['STAGING'] or self.config['DEBUG']:
            new_item = StampPartnersObject(
                id="55424a8432dba9d4e53c9909",
                region=[RFRegionsEnum.RFR_SPB, RFRegionsEnum.RFR_MOSCOW, RFRegionsEnum.RFR_SVERDLOVSKAYA_REGION,
                        RFRegionsEnum.RFR_CHELYABINSKAYA_REGION, RFRegionsEnum.RFR_TATARSTAN,
                        RFRegionsEnum.RFR_NOVOSIBIRSKAYA_REGION, RFRegionsEnum.RFR_KRASNOYARSKIY_KRAY],
                enabled=True,
                sort_index=1,
                link='http://google.ru',
                banner='http://yastatic.net/morda-logo/i/logo.svg',
                title=u'«Закрытие»',
                created=datetime.utcnow()
            )
            sqldb.session.add(new_item)
            sqldb.session.commit()

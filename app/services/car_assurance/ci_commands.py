# -*- coding: utf-8 -*-
from fw.documents.address_enums import RFRegionsEnum
from manage_commands import BaseManageCommand
from fw.db.sql_base import db as sqldb
from services.car_assurance.db_models import CarAssurance, CarAssuranceBranch


class InitCarInsurancesCommand(BaseManageCommand):
    NAME = "create_car_insurances"

    def run(self):
        self.logger.info(u'=' * 50)

        CarAssuranceBranch.query.filter().delete()
        sqldb.session.commit()
        CarAssurance.query.filter().delete()
        sqldb.session.commit()

        a_data = (
            (u'559a9b984056d47aa5c57c5b', u'РЕСО-Гарантия'),
            (u'559a9b984056d47aa5c57c5c', u'ООО "СФ "Адонис"'),
            (u'559a9b994056d47aa5c57c5d', u'ООО "СК АЛРОСА"'),
            (u'559a9b994056d47aa5c57c5e', u'ОАО "АльфаСтрахование"'),
            (u'559a9b994056d47aa5c57c5f', u'ОАО СК "Альянс"'),
            (u'559a9b994056d47aa5c57c60', u'ООО "Страховая компания "Ангара"'),
            (u'559a9b9a4056d47aa5c57c61', u'ООО "Антал-Страхование"'),
            (u'559a9b9a4056d47aa5c57c62', u'ООО "СГ "АСКО"'),
            (u'559a9b9a4056d47aa5c57c63', u'ООО СК "ВТБ Страхование"'),
            (u'559a9b9a4056d47aa5c57c64', u'ООО Страховая Компания "Гелиос"')
        )

        for id_val, name in a_data:
            c = CarAssurance(id=id_val, full_name=name, short_name=name)
            sqldb.session.add(c)
            sqldb.session.commit()

        b_data = (
            (u'559a9b984056d47aa5c57c5b', u'РЕСО-Гарантия филиал 1', u'730-30-00; доб.1682 (факс)', u'Нагорный проезд д.6, г.Москва, 117105', RFRegionsEnum.RFR_MOSCOW, u'559a9cf64056d47aa5c57c69'),
            (u'559a9b984056d47aa5c57c5b', u'РЕСО-Гарантия филиал 2', u'730-30-00; доб.1682 (факс)', u'Нагорный проезд д.6, г.Москва, 117105', RFRegionsEnum.RFR_MOSCOW, u'559a9cf64056d47aa5c57c6a'),
            (u'559a9b984056d47aa5c57c5b', u'РЕСО-Гарантия филиал 3', u'730-30-00; доб.1682 (факс)', u'Нагорный проезд д.6, г.Москва, 117105', RFRegionsEnum.RFR_MOSCOW, u'559a9cf64056d47aa5c57c6b'),

            (u'559a9b984056d47aa5c57c5c', u'ООО "СФ "Адонис" филиал 1', u"(342) 241-02-87", u'ул. Братьев Игнатовых, д. 3, оф.710, г. Пермь', RFRegionsEnum.RFR_PERMSKIY_KRAI, u'559a9e0964f10cabe6678653'),
            (u'559a9b984056d47aa5c57c5c', u'ООО "СФ "Адонис" филиал 2', u"(342) 241-02-87", u'ул. Братьев Игнатовых, д. 3, оф.710, г. Пермь', RFRegionsEnum.RFR_PERMSKIY_KRAI, u'559a9e0a64f10cabe6678654'),
            (u'559a9b984056d47aa5c57c5c', u'ООО "СФ "Адонис" филиал 3', u"(342) 241-02-87", u'ул. Братьев Игнатовых, д. 3, оф.710, г. Пермь', RFRegionsEnum.RFR_PERMSKIY_KRAI, u'559a9e0b64f10cabe6678655'),

            (u'559a9b994056d47aa5c57c5d', u'ООО "СК АЛРОСА" филиал 1', u"(495) 664-28-81 (тел/факс)", u"Мукомольный пр-д, д.2, стр.1, г.Москва, 123290", RFRegionsEnum.RFR_MOSCOW, u"559a9e9c64f10cabe6678658"),
            (u'559a9b994056d47aa5c57c5d', u'ООО "СК АЛРОСА" филиал 2', u"(495) 664-28-81 (тел/факс)", u"Мукомольный пр-д, д.2, стр.1, г.Москва, 123290", RFRegionsEnum.RFR_MOSCOW, u"559a9e9c64f10cabe6678657"),
            (u'559a9b994056d47aa5c57c5d', u'ООО "СК АЛРОСА" филиал 3', u"(495) 664-28-81 (тел/факс)", u"Мукомольный пр-д, д.2, стр.1, г.Москва, 123290", RFRegionsEnum.RFR_MOSCOW, u"559a9e9c64f10cabe6678656"),

            (u'559a9b994056d47aa5c57c5e', u'ОАО "АльфаСтрахование" филиал 1', u"788-09-99; 785-08-88 (факс)", u"Ул. Шаболовка, д. 31, строение \"Б\", г.Москва, 115162", RFRegionsEnum.RFR_MOSCOW, u"559a9ee564f10cabe6678659"),
            (u'559a9b994056d47aa5c57c5e', u'ОАО "АльфаСтрахование" филиал 2', u"788-09-99; 785-08-88 (факс)", u"Ул. Шаболовка, д. 31, строение \"Б\", г.Москва, 115162", RFRegionsEnum.RFR_MOSCOW, u"559a9ee564f10cabe667865a"),
            (u'559a9b994056d47aa5c57c5e', u'ОАО "АльфаСтрахование" филиал 3', u"788-09-99; 785-08-88 (факс)", u"Ул. Шаболовка, д. 31, строение \"Б\", г.Москва, 115162", RFRegionsEnum.RFR_MOSCOW, u"559a9ee664f10cabe667865b"),

            (u'559a9b994056d47aa5c57c5f', u'ОАО СК "Альянс" филиал 1', u"956-21-05", u"Озерковская набережная, д. 30, г.Москва, 115184", RFRegionsEnum.RFR_MOSCOW, u"559a9f3364f10cabe667865c"),
            (u'559a9b994056d47aa5c57c5f', u'ОАО СК "Альянс" филиал 2', u"956-21-05", u"Озерковская набережная, д. 30, г.Москва, 115184", RFRegionsEnum.RFR_MOSCOW, u"559a9f3364f10cabe667865d"),
            (u'559a9b994056d47aa5c57c5f', u'ОАО СК "Альянс" филиал 3', u"956-21-05", u"Озерковская набережная, д. 30, г.Москва, 115184", RFRegionsEnum.RFR_MOSCOW, u"559a9f3364f10cabe667865e"),

            (u'559a9b994056d47aa5c57c60', u'ООО "Страховая компания "Ангара" филиал 1', u"(3953) 41-15-15 (тел/факс)", u"ул.Южная, д.23, г.Братск, Иркутская обл., 665717", RFRegionsEnum.RFR_IRKUTSKAYA_REGION, u"559a9f8764f10cabe667865f"),
            (u'559a9b994056d47aa5c57c60', u'ООО "Страховая компания "Ангара" филиал 2', u"(3953) 41-15-15 (тел/факс)", u"ул.Южная, д.23, г.Братск, Иркутская обл., 665717", RFRegionsEnum.RFR_IRKUTSKAYA_REGION, u"559a9f8764f10cabe6678660"),
            (u'559a9b994056d47aa5c57c60', u'ООО "Страховая компания "Ангара" филиал 3', u"(3953) 41-15-15 (тел/факс)", u"ул.Южная, д.23, г.Братск, Иркутская обл., 665717", RFRegionsEnum.RFR_IRKUTSKAYA_REGION, u"559a9f8864f10cabe6678661"),

            (u'559a9b9a4056d47aa5c57c61', u'ООО "Антал-Страхование" филиал 1', u"8-800-333-18-22", u"Петровский пер., д.10, строение 2, г. Москва, 107031", RFRegionsEnum.RFR_MOSCOW, u"559a9fd164f10cabe6678662"),
            (u'559a9b9a4056d47aa5c57c61', u'ООО "Антал-Страхование" филиал 2', u"8-800-333-18-22", u"Петровский пер., д.10, строение 2, г. Москва, 107031", RFRegionsEnum.RFR_MOSCOW, u"559a9fd164f10cabe6678663"),
            (u'559a9b9a4056d47aa5c57c61', u'ООО "Антал-Страхование" филиал 3', u"8-800-333-18-22", u"Петровский пер., д.10, строение 2, г. Москва, 107031", RFRegionsEnum.RFR_MOSCOW, u"559a9fd264f10cabe6678664"),

            (u'559a9b9a4056d47aa5c57c62', u'ООО "СГ "АСКО" филиал 1', u"(8552) 39-23-9", u"Проспект Вахитова, дом 24, а/я 27, г.Набережные Челны, Республика Татарстан, 423815", RFRegionsEnum.RFR_TATARSTAN, u"559aa01364f10cabe6678665"),
            (u'559a9b9a4056d47aa5c57c62', u'ООО "СГ "АСКО" филиал 2', u"(8552) 39-23-9", u"Проспект Вахитова, дом 24, а/я 27, г.Набережные Челны, Республика Татарстан, 423815", RFRegionsEnum.RFR_TATARSTAN, u"559aa01364f10cabe6678666"),
            (u'559a9b9a4056d47aa5c57c62', u'ООО "СГ "АСКО" филиал 3', u"(8552) 39-23-9", u"Проспект Вахитова, дом 24, а/я 27, г.Набережные Челны, Республика Татарстан, 423815", RFRegionsEnum.RFR_TATARSTAN, u"559aa01364f10cabe6678667"),

            (u'559a9b9a4056d47aa5c57c63', u'ООО СК "ВТБ Страхование" филиал 1', u"(495) 644-44-40", u"Чистопрудный бульвар, д. 8, стр. 1, г. Москва", RFRegionsEnum.RFR_MOSCOW, u"559aa08e64f10cabe6678668"),
            (u'559a9b9a4056d47aa5c57c63', u'ООО СК "ВТБ Страхование" филиал 2', u"(495) 644-44-40", u"Чистопрудный бульвар, д. 8, стр. 1, г. Москва", RFRegionsEnum.RFR_MOSCOW, u"559aa08e64f10cabe6678669"),
            (u'559a9b9a4056d47aa5c57c63', u'ООО СК "ВТБ Страхование" филиал 3', u"(495) 644-44-40", u"Чистопрудный бульвар, д. 8, стр. 1, г. Москва", RFRegionsEnum.RFR_MOSCOW, u"559aa08f64f10cabe667866a"),

            (u'559a9b9a4056d47aa5c57c64', u'ООО Страховая Компания "Гелиос" филиал 1', u"(495)981-96-33", u"Бульвар Энтузиастов, д. 2, г. Москва, 109544", RFRegionsEnum.RFR_MOSCOW, u"559aa0bf64f10cabe667866b"),
            (u'559a9b9a4056d47aa5c57c64', u'ООО Страховая Компания "Гелиос" филиал 2', u"(495)981-96-33", u"Бульвар Энтузиастов, д. 2, г. Москва, 109544", RFRegionsEnum.RFR_MOSCOW, u"559aa0bf64f10cabe667866c"),
            (u'559a9b9a4056d47aa5c57c64', u'ООО Страховая Компания "Гелиос" филиал 3', u"(495)981-96-33", u"Бульвар Энтузиастов, д. 2, г. Москва, 109544", RFRegionsEnum.RFR_MOSCOW, u"559aa0c064f10cabe667866d")
        )

        for ca_id, title, phone, address, region, id_val in b_data:
            cb = CarAssuranceBranch(
                car_assurance_id=ca_id,
                id=id_val,
                title=title,
                address=address,
                phone=phone,
                region=region
            )
            sqldb.session.add(cb)
            sqldb.session.commit()

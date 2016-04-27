# -*- coding: utf-8 -*-
import json
import requests
from flask import current_app
from fw.catalogs.models import GeoCities, GeoRanges
from fw.documents.address_enums import RFRegionsEnum


class GeoIpLocator(object):
    REGION_NAME_MAP = {
        u"Республика Адыгея": RFRegionsEnum.RFR_ADYGEYA,
        u"Кировская область": RFRegionsEnum.RFR_KIROVSKAYA_REGION,
        u"Республика Башкортостан": RFRegionsEnum.RFR_BASHKARTOSTAN,
        u"Костромская область": RFRegionsEnum.RFR_KOSTROMSKAYA_REGION,
        u"Республика Бурятия": RFRegionsEnum.RFR_BURYATIYA,
        u"Курганская область": RFRegionsEnum.RFR_KURGANSKAYA_REGION,
        u"Алтайский край": RFRegionsEnum.RFR_ALTAY,
        u"Курская область": RFRegionsEnum.RFR_KURSKAYA_REGION,
        u"Республика Дагестан": RFRegionsEnum.RFR_DAGESTAN,
        u"Ленинградская область": RFRegionsEnum.RFR_LENINGRADSKAYA_REGION,
        u"Республика Ингушетия": RFRegionsEnum.RFR_INGUSHETIYA,
        u"Липецкая область": RFRegionsEnum.RFR_LIPETSKAYA_REGION,
        u"Республика Кабардино-Балкария": RFRegionsEnum.RFR_KABARDINO_BALKARIYA,
        u"Магаданская область": RFRegionsEnum.RFR_MAGADANSKAYA_REGION,
        u"Республика Калмыкия": RFRegionsEnum.RFR_KALMYKIYA,
        u"Московская область": RFRegionsEnum.RFR_MOSCOVSKAYA_REGION,
        u"Республика Карачаево-Черкессия": RFRegionsEnum.RFR_KARACHAEVO_CHERKESIYA,
        u"Мурманская область": RFRegionsEnum.RFR_MURMANSKAYA_REGION,
        u"Республика Карелия": RFRegionsEnum.RFR_KARELIYA,
        u"Нижегородская область": RFRegionsEnum.RFR_NIZHEGORODSKAYA_REGION,
        u"Республика Коми": RFRegionsEnum.RFR_KOMI,
        u"Новгородская область": RFRegionsEnum.RFR_NOVGORODSKAYA_REGION,
        u"Республика Марий Эл": RFRegionsEnum.RFR_MARIY_EL,
        u"Новосибирская область": RFRegionsEnum.RFR_NOVOSIBIRSKAYA_REGION,
        u"Республика Мордовия": RFRegionsEnum.RFR_MORDOVIYA,
        u"Омская область": RFRegionsEnum.RFR_OMSKAYA_REGION,
        u"Республика Саха (Якутия)": RFRegionsEnum.RFR_SAHA_YAKUTIYA,
        u"Оренбургская область": RFRegionsEnum.RFR_ORENBURGSKAYA_REGION,
        u"Республика Северная Осетия (Алания)": RFRegionsEnum.RFR_SEVERNAYA_OSETIYA,
        u"Орловская область": RFRegionsEnum.RFR_ORLOVSKAYA_REGION,
        u"Республика Татарстан": RFRegionsEnum.RFR_TATARSTAN,
        u"Пензенская область": RFRegionsEnum.RFR_PENZENSKAYA_REGION,
        u"Республика Тыва (Тува)": RFRegionsEnum.RFR_TYVA,
        u"Пермский край": RFRegionsEnum.RFR_PERMSKIY_KRAI,
        u"Республика Удмуртия": RFRegionsEnum.RFR_UDMURTIYA,
        u"Псковская область": RFRegionsEnum.RFR_PSKOVSKAYA_REGION,
        u"Республика Хакасия": RFRegionsEnum.RFR_HAKASIYA,
        u"Ростовская область": RFRegionsEnum.RFR_ROSTOVSKAYA_REGION,
        u"Республика Чечня": RFRegionsEnum.RFR_CHECHNYA,
        u"Рязанская область": RFRegionsEnum.RFR_RYAZANSKAYA_REGION,
        u"Республика Чувашия": RFRegionsEnum.RFR_CHUVASHIYA,
        u"Самарская область": RFRegionsEnum.RFR_SAMARSKAYA_REGION,
        u"Саратовская область": RFRegionsEnum.RFR_SARATOVSKAYA_REGION,
        u"Краснодарский край": RFRegionsEnum.RFR_KRASNODARSKIY_KRAI,
        u"Сахалинская область": RFRegionsEnum.RFR_SAHALINSKAYA_REGION,
        u"Красноярский край": RFRegionsEnum.RFR_KRASNOYARSKIY_KRAY,
        u"Свердловская область": RFRegionsEnum.RFR_SVERDLOVSKAYA_REGION,
        u"Приморский край": RFRegionsEnum.RFR_PRIMORSKIY_KRAI,
        u"Смоленская область": RFRegionsEnum.RFR_SMOLENSKAYA_REGION,
        u"Ставропольский край": RFRegionsEnum.RFR_STAVROPOLSKY_KRAI,
        u"Тамбовская область": RFRegionsEnum.RFR_TAMBOVSKAYA_REGION,
        u"Хабаровский край": RFRegionsEnum.RFR_HABAROVSKY_KRAI,
        u"Тверская область": RFRegionsEnum.RFR_TVERSKAYA_REGION,
        u"Амурская область": RFRegionsEnum.RFR_AMURSKAYA_REGION,
        u"Томская область": RFRegionsEnum.RFR_TOMSKAYA_REGION,
        u"Архангельская область": RFRegionsEnum.RFR_ARCHANGELSKAYA_REGION,
        u"Тульская область": RFRegionsEnum.RFR_TULSKAYA_REGION,
        u"Астраханская область": RFRegionsEnum.RFR_ASTRAHANSKAYA_REGION,
        u"Тюменская область": RFRegionsEnum.RFR_TUMENSKAYA_REGION,
        u"Белгородская область": RFRegionsEnum.RFR_BELGORODSKAYA_REGION,
        u"Ульяновская область": RFRegionsEnum.RFR_ULYANOVSKAYA_REGION,
        u"Брянская область": RFRegionsEnum.RFR_BRYANSKAYA_REGION,
        u"Челябинская область": RFRegionsEnum.RFR_CHELYABINSKAYA_REGION,
        u"Владимирская область": RFRegionsEnum.RFR_VLADIMIRSKAYA_REGION,
        u"Забайкальский край": RFRegionsEnum.RFR_ZABAIKALSKY_KRAI,
        u"Волгоградская область": RFRegionsEnum.RFR_VOLGOGRADSKAYA_REGION,
        u"Вологодская область": RFRegionsEnum.RFR_VOLOGODSKAYA_REGION,
        u"Воронежская область": RFRegionsEnum.RFR_VORONEZHSKAYA_REGION,
        u"Ярославская область": RFRegionsEnum.RFR_YAROSLAVSKAYA_REGION,
        u"Ивановская область": RFRegionsEnum.RFR_IVANOVSKAYA_REGION,
        u"Москва": RFRegionsEnum.RFR_MOSCOW,
        u"Иркутская область": RFRegionsEnum.RFR_IRKUTSKAYA_REGION,
        u"Санкт-Петербург": RFRegionsEnum.RFR_SPB,
        u"Еврейская автономная область": RFRegionsEnum.RFR_EVREISKAYA_AO,
        u"Калининградская область": RFRegionsEnum.RFR_KALININGRADSKAYA_REGION,
        u"Ненецкий автономный округ": RFRegionsEnum.RFR_NENETSKY_AO,
        u"Калужская область": RFRegionsEnum.RFR_KALUZHSKAYA_REGION,
        u"Ханты-Мансийский автономный округ": RFRegionsEnum.RFR_UGRA,
        u"Камчатский край": RFRegionsEnum.RFR_KAMCHATSKY_KRAI,
        u"Чукотский автономный округ": RFRegionsEnum.RFR_CHUKOTSKY_AO,
        u"Кемеровская область": RFRegionsEnum.RFR_KEMEROVSKAYA_REGION,
        u"Ямало-Ненецкий автономный округ": RFRegionsEnum.RFR_YAMALO_NENETSKY_AO,
        u"Крым": RFRegionsEnum.RFR_KRYM,
        u"Севастополь": RFRegionsEnum.RFR_SEVASTOPOL,
    }

    def __init__(self):
        pass

    @classmethod
    def get_location(cls, ip):
        logger = current_app.logger

        try:
            ip_parts = ip.split('.')
            ip_val = int(ip_parts[0]) * 256 * 256 * 256 + int(ip_parts[1]) * 256 * 256 + int(ip_parts[2]) * 256 + int(
                ip_parts[0])
            obj = GeoRanges.query.filter(GeoRanges.start.__le__(ip_val), GeoRanges.end.__ge__(ip_val)).scalar()
            if not obj:
                logger.info(u"get location e1")
                raise Exception()
            cid = obj.cid
            city = GeoCities.query.filter_by(cid=cid).scalar()
            if not city:
                logger.info(u"get location e2")
                raise Exception()
            return {
                'region': cls.REGION_NAME_MAP.get(city.region, city.region)
            }

        except Exception:
            logger.info(u"get location EE")
            # return {'region' : None}
            pass  # fall back to ipgeobase request

        try:
            response = requests.get('http://ipgeobase.ru:7020/geo?ip=%s&json=1' % ip, timeout=3)
        except Exception:
            return

        if response.status_code != 200:
            raise Exception("Failed to get geo info by ip. Response code: %s" % unicode(response.status_code))
        try:
            data = json.loads(response.text)
            if ip in data:
                data = data[ip]
            if 'region' in data:
                data['region'] = cls.REGION_NAME_MAP.get(data['region'], data['region'])
            return data
        except Exception, ex:
            raise Exception("Failed to get geo info by ip. %s" % unicode(ex))

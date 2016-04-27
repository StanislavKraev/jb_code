# -*- coding: utf-8 -*-

from fw.api import dadata_proxy
from flask import current_app

from fw.cache.cache_wrapper import CacheWrapper

cache = CacheWrapper()


def dadata_suggest(method, data):
    return dadata_proxy.dadata_suggest(method, data)


def dadata_clean(method, data):
    return dadata_proxy.dadata_clean(method, data)


def get_detailed_address(address):
    from fw.utils.address_utils import get_detailed_address as _get_detailed_address

    return _get_detailed_address(address)


def dadata_standardize_address(address):
    from fw.utils.address_utils import dadata_standardize_address as _dadata_standardize_address

    return _dadata_standardize_address(address)


def get_ifns_by_address(address, service_nalog_ru_url):
    from services.ifns.ifns_manager import get_ifns_by_address as _get_ifns_by_address

    return _get_ifns_by_address(address, service_nalog_ru_url)


def get_ifns_by_code(tax_office, service_nalog_ru_url):
    from services.ifns.ifns_manager import get_ifns_by_code as _get_ifns_by_code

    return _get_ifns_by_code(tax_office, service_nalog_ru_url)


def get_nalog_ru_time_slots(person_data, company_data, internal_ifns_number, internal_ifns_service, logger):
    from services.ifns.ifns_manager import get_nalog_ru_time_slots as _get_nalog_ru_time_slots

    return _get_nalog_ru_time_slots(person_data, company_data, internal_ifns_number, internal_ifns_service, logger)


def book_ifns(person_data, company_data, internal_ifns_number, internal_ifns_service, dt, logger):
    from services.ifns.ifns_manager import book_ifns as _book_ifns

    return _book_ifns(person_data, company_data, internal_ifns_number, internal_ifns_service, dt, logger)


def get_registration_ifns(service_nalog_ru_url, address_ifns=None):
    from services.ifns.ifns_manager import get_registration_ifns as _get_registration_ifns

    return _get_registration_ifns(service_nalog_ru_url, address_ifns=address_ifns)


def get_ifns_registrations(name, company_type='ooo', date_from=None, date_to=None,
                           service=None, ifns=None, service_nalog_ru_url=None, logger=None):
    from services.ifns.ifns_manager import get_ifns_registrations as _get_ifns_registrations

    return _get_ifns_registrations(name, company_type=company_type, date_from=date_from, date_to=date_to,
                                   service=service, ifns=ifns, service_nalog_ru_url=service_nalog_ru_url, logger=logger)

def check_car_policy(policy_series, policy_number, timeout=20.0):
    from services.car_assurance.integration import check_car_policy as _check_car_policy
    return _check_car_policy(policy_series, policy_number, timeout=timeout)



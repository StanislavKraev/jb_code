# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import json
import requests
from data.get_all_ifns import ALL_IFNS_NUMBERS
from fw.db.sql_base import db as sqldb
from fw.documents.fields.general_doc_fields import DocAddressField
from fw.utils.address_utils import dadata_standardize_address
from manage_commands import BaseManageCommand
from common_utils import int_to_ifns
from services.ifns.data_model.models import IfnsCatalogObject


class UpdateIfnsCatalogInitCommand(BaseManageCommand):
    NAME = "update_ifns_catalog_init"

    def run(self):
        """
            Should be started once.
        """

        updated = datetime.now() - timedelta(days=365)
        for ifns in ALL_IFNS_NUMBERS:
            res = IfnsCatalogObject.query.filter_by(code=ifns).first()
            if not res:
                new_item = IfnsCatalogObject(code=ifns, updated=updated)
                sqldb.session.add(new_item)
                sqldb.session.commit()


def get_phone_list(phone_str, logger):
    phone_list_str = phone_str.split(',')
    city_code = None
    phones = []
    phones_without_city_code = []
    for phone_item in phone_list_str:
        try:
            phone_item = phone_item.strip()
            phone_item = filter(lambda x: x.isdigit() or x in ('(', ')'), phone_item)
            if '(' in phone_item and ')' in phone_item:
                bracket_split_parts = phone_item.split('(')

                country_code, remaining = phone_item.split('(')
                if country_code not in ('', '8', '+7', '+38'):
                    raise ValueError()
                if not remaining:
                    raise ValueError()
                city_code, number = remaining.split(')')
                if not city_code or not number:
                    raise ValueError()
                phones.append(u"+7(%s)%s" % (city_code, number))
            else:
                if len(phone_item) == 7:
                    phones_without_city_code.append(phone_item)
                elif len(phone_item) == 11 and phone_item[0] == 8:
                    city_code = phone_item[1:4]
                    number = phone_item[4:]
                    phones.append(u"+7(%s)%s" % (city_code, number))
                elif len(phone_item) == 12 and phone_item[0:2] == "+7":
                    city_code = phone_item[2:5]
                    number = phone_item[5:]
                    phones.append(u"+7(%s)%s" % (city_code, number))
                elif len(phone_item) == 10:
                    city_code = phone_item[0:3]
                    number = phone_item[3:]
                    phones.append(u"+7(%s)%s" % (city_code, number))

        except Exception:
            logger.exception(u"Failed to parse number %s" % phone_item)

    if city_code and phones_without_city_code:
        for phone in phones_without_city_code:
            phones.append(u"+7(%s)%s" % (city_code, phone))
    return phones


def str_address_to_struct(address):
    source_address = address
    address_json = dadata_standardize_address(address)
    if not address_json:
        return
    address_field = DocAddressField()
    address_json['address_string'] = address
    fields_map = {
        "okato": "okato",
        "tax_office": "ifns",
        "qc_complete": "qc_complete",
        "region": "region",
        "postal_code": "index",
        "city_type": "city_type",
        "city": "city",
        "area": "district",
        "area_type": "district_type",
        "flat": "flat",
        "flat_type": "flat_type",
        "house": "house",
        "house_type": "house_type",
        "settlement": "village",
        "settlement_type": "village_type",
        "street": "street",
        "street_type": "street_type",
        "result": "address_string",
        "geo_lat": "coord_lat",
        "geo_lon": "coord_long",
        "block": "building",
        "block_type": "building_type",
        "qc": "qc"
    }
    result_address = {}
    for field_name in fields_map:
        if field_name in address_json:
            val = address_json[field_name]
            if val is not None:
                result_address[fields_map[field_name]] = val

    address_field.parse_raw_value(result_address)
    address = address_field.db_value()
    address['source_address'] = source_address
    return address


class UpdateIfnsCatalogCommand(BaseManageCommand):
    NAME = "update_ifns_catalog"

    def run(self):
        """
            Should be started every minute.
        """

        result = IfnsCatalogObject.query.filter(
            IfnsCatalogObject.updated.__ne__(None)
        ).order_by(IfnsCatalogObject.updated.asc()).first()

        if not result:
            self.logger.error(u"Failed to find ifns to update")
            return

        ifns_item = result
        ifns = ifns_item.code

        self.logger.info(u"Updating ifns %s" % unicode(ifns))

        ifns_item.updated = datetime.utcnow()
        sqldb.session.commit()

        s = requests.Session()
        s.get('https://service.nalog.ru/addrno.do', timeout=5)
        result = s.get('https://service.nalog.ru/addrno.do?l=6&g=%s' % int_to_ifns(ifns), timeout=5)
        if result.status_code != 200:
            self.logger.error(u"Failed to get data for ifns %s" % ifns)
            return

        data = {}
        try:
            data = result.json()
            res = data['res']

            required_fields = ('naimk', 'adres')
            if any([field not in res for field in required_fields]):
                if not ifns_item.naimk:
                    sqldb.session.delete(ifns_item)
                    sqldb.session.commit()
                raise Exception(u"Empty data")
            name = res['naimk']
            address = res['adres']
            old_address = ifns_item.address

            old_address_str = old_address['address_string'] if (
                isinstance(old_address, dict) and 'address_string' in old_address) else old_address

            # if address != old_address_str or isinstance(old_address_str, basestring):
            #                address = str_address_to_struct(address)

            tel = get_phone_list(res['tel'], self.logger) if 'tel' in res else None
            comment = res.get('coment', '')

            plat_src = res.get('plat', None)
            plat = {}
            if plat_src:
                plat['recipient_name'] = plat_src['naimpol']
                plat['recipient_kpp'] = plat_src['kpppol']
                plat['recipient_inn'] = plat_src['innpol']

                if plat_src['found']:
                    plat['bik'] = plat_src['bik']
                    plat['bank_name'] = plat_src['naimbank']
                    plat['recipient_account'] = plat_src['schetpol']

            rou = {}
            rou_src = res.get('rou', None)

            if rou_src:
                rou['name'] = rou_src['naimk']
                rou['code'] = rou_src['code']
                if 'tel' in rou_src:
                    rou['tel'] = get_phone_list(rou_src['tel'], self.logger)
                rou_addr = rou_src['adres']
                rou['address_str'] = rou_addr
                old_rou_addr_str = (ifns_item.rou or {}).get('address_str', "")
                if rou_addr != old_rou_addr_str:
                    rou['address'] = str_address_to_struct(rou_addr)
                else:
                    rou['address'] = (ifns_item.rou or {}).get('address', {})

            rof = {}
            rof_src = res.get('rof', None)

            if rof_src:
                rof['name'] = rof_src['naimk']
                rof['code'] = rof_src['code']
                if 'tel' in rof_src:
                    rof['tel'] = get_phone_list(rof_src['tel'], self.logger)
                rof['address'] = rof_src['adres']

            new_fields = {
                'name': name,
                'address': address,
                'comment': comment
            }
            unset_fields = {}
            if tel:
                new_fields['tel'] = tel
            else:
                unset_fields['tel'] = ""

            if plat:
                new_fields['plat'] = plat
            else:
                unset_fields['plat'] = ""

            if rou:
                new_fields['rou'] = rou
            else:
                unset_fields['rou'] = ""

            if rof:
                new_fields['rof'] = rof
            else:
                unset_fields['rof'] = ""

            # TODO:
            # if not unset_fields:
            #     col.update({'code': ifns}, {'$set': new_fields})
            # else:
            #     col.update({'code': ifns}, {'$set': new_fields, '$unset': unset_fields})
            # self.logger.info(u"ifns %s updated" % str(ifns))
        except Exception:
            self.logger.exception(u"Invalid data returned for ifns %s: \r\n %s" %
                                  (ifns, json.dumps(data, default=lambda x: unicode(x),
                                                    indent=1, ensure_ascii=False)))
            return


# class ReloadBankInfo(BaseManageCommand):
#     NAME = "reload_bank_info"
#
#     def run(self):
#         # TODO:
#         file_path = get_single(u'csv file path: ')
#         if not os.path.exists(file_path):
#             self.logger.error(u"File %s not found" % file_path)
#             return False
#
#         col = self.db['bik_catalog']
#
#         col.remove({})
#
#         with open(file_path, 'r') as f:
#             content = f.read()
#
#         data = json.loads(content)
#         for item in data:
#             if 'NAMEP' not in item or 'NEWNUM' not in item:
#                 continue
#
#             name = item['NAMEP']
#             bik = item['NEWNUM']
#
#             if not name or not bik:
#                 continue
#
#             item_data = {
#                 'name': name,
#                 'bik': bik
#             }
#
#             if 'ADR' in item and item['ADR']:
#                 item_data['address'] = item['ADR']
#
#             if 'TELEF' in item and item['TELEF']:
#                 item_data['phone'] = item['TELEF']
#
#             if 'OKPO' in item and item['OKPO']:
#                 item_data['okpo'] = item['OKPO']
#
#             if 'KSNP' in item and item['KSNP']:
#                 item_data['kor_account'] = item['KSNP']
#
#             col.insert(item_data)
#
#         self.logger.info("%d items added" % col.find({}).count())
#
#
# class UpdateIfnsCatalogCommandAddresses(BaseManageCommand):
#     NAME = "update_ifns_addresses"
#
#     def run(self):
#         """
#             Should be started every minute.
#         """
#         assert False
#
#         # TODO:
#         col = self.db['ifns_catalog']
#
#         addr_set = set()
#         result = col.find()
#         for r in result:
#             if 'address' in r and r['address']:
#                 addr_set.add(r['address'])
#             if 'rou' in r and 'address' in r['rou'] and r['rou']['address'] and isinstance(r['rou']['address'],
#                                                                                            basestring):
#                 addr_set.add(r['rou']['address'])
#             if 'rof' in r and 'address' in r['rof'] and r['rof']['address'] and isinstance(r['rof']['address'],
#                                                                                            basestring):
#                 addr_set.add(r['rof']['address'])
#
#         addr_map = {}
#
#         for addr in addr_set:
#             self.logger.info(addr)
#             try:
#                 norm_addr = str_address_to_struct(addr)
#                 addr_map[addr] = norm_addr
#                 self.logger.info(json.dumps(norm_addr, indent=1, ensure_ascii=False))
#                 col.update({'address': addr}, {'$set': {'address': norm_addr}}, multi=True)
#                 col.update({'rou.address': addr}, {'$set': {'rou.address': norm_addr}}, multi=True)
#                 col.update({'rof.address': addr}, {'$set': {'rof.address': norm_addr}}, multi=True)
#             except Exception:
#                 self.logger.exception(u"Failed to clean address %s " % addr)
#                 continue
#

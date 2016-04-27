# -*- coding: utf-8 -*-
import shlex
import subprocess
import os
import codecs
import re
from fw.catalogs.models import GeoCities
from fw.catalogs.models import GeoRanges
from fw.db.sql_base import db as sqldb
from manage_commands import BaseManageCommand, get_single


class UpdateGeoDbFromFileCommand(BaseManageCommand):
    NAME = "update_geo"

    class FilenameSimpleValidator(object):
        def validate(self, val):
            if not os.path.exists(val):
                return False
            return True

        def get_value(self, value):
            return value

    def run(self):

        file_name = get_single(u'File name: ', validator=UpdateGeoDbFromFileCommand.FilenameSimpleValidator(),
                               error_hint=u"File not found")

        tmp_dir = '/tmp/geo_files'
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)

        subprocess.call(shlex.split('tar -xzvf %s -C %s' % (file_name, tmp_dir)))

        cities_file_name = os.path.join(tmp_dir, "cities.txt")
        data_file_name = os.path.join(tmp_dir, "cidr_optim.txt")

        if not os.path.exists(cities_file_name) or not os.path.exists(data_file_name):
            self.logger.error("missing required file(s)")
            return

        cities_file = codecs.open(cities_file_name, 'r', 'cp1251')
        cities = cities_file.read()
        cities_file.close()

        data_file = codecs.open(data_file_name, 'r', 'cp1251')
        data = data_file.read()
        data_file.close()

        os.unlink(cities_file_name)
        os.unlink(data_file_name)

        self.logger.info('processing')

        cities_objects = []

        for line in cities.split('\n'):
            line = line.strip()
            if not line:
                continue
            match = re.search(ur'(\d+)\t(.+)\t(.+)\t(.+)\t(.+)\t(.+)', line)
            if not match:
                self.logger.warn(u"Failed to process: %s" % line)
                continue

            cid = int(match.groups(0)[0])
            city_name = match.groups(0)[1]
            region = match.groups(0)[2]
            # district = match.groups(0)[3]
            lat = match.groups(0)[4]
            lng = match.groups(0)[5]
            cities_objects.append({
                'cid': cid,
                'name': city_name,
                'region': region,
                'lat': lat,
                'lng': lng
            })

        geo_ranges = []
        for line in data.split('\n'):
            line = line.strip()
            if not line:
                continue
            match = re.search(
                ur'(\d+)\t(\d+)\t(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3} - \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\t(.+)\t(.+)',
                line)
            if not match:
                self.logger.warn(u"Failed to process: %s" % line)
                continue
            cid = match.groups(0)[4]
            if not cid.isdigit():
                continue
            geo_ranges.append({
                'start': int(match.groups(0)[0]),
                'end': int(match.groups(0)[1]),
                'cid': int(cid)
            })

        for g in GeoCities.query.filter():
            g.delete()
        sqldb.session.commit()
        for g in GeoRanges.query.filter():
            g.delete()
        sqldb.session.commit()

        for city in cities_objects:
            new_gc = GeoCities(
                name=city['name'],
                cid=city['cid'],
                region=city['region'],
                lat=city['lat'],
                lng=city['lng']
            )
            sqldb.session.add(new_gc)
        sqldb.session.commit()

        for geo in geo_ranges:
            new_gr = GeoRanges(
                cid=geo['cid'],
                start=geo['start'],
                end=geo['end']
            )
            sqldb.session.add(new_gr)
        sqldb.session.commit()

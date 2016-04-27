# -*- coding: utf-8 -*-
import os
os.environ['CELERY_CONFIG_MODULE'] = 'dev_celeryconfig'

from base_test_case import BaseTestCase
from test_pack.test_api import authorized

class RosstatApiTestCase(BaseTestCase):

    @authorized()
    def test_get_stat_codes_moscow(self):
        pass
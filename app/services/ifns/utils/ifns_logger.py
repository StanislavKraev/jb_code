# -*- coding: utf-8 -*-

import logging

IFNS_LOGGER = logging.getLogger("IFNS")
IFNS_LOGGER.setLevel(logging.DEBUG)

try:
    _fh = logging.FileHandler('/var/log/jb/ifns.log')
    _fh.setLevel(logging.DEBUG)
    _formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    _fh.setFormatter(_formatter)
    IFNS_LOGGER.addHandler(_fh)
except Exception:
    pass





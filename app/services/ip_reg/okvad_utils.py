# -*- coding: utf-8 -*-

def is_restricted_for_ip_okvad(okvad):
    if not okvad or not isinstance(okvad, basestring):
        return False

    exact_match = ('15.91', '15.96', '51.17.22', '51.34', '51.34.2', '52.25', '52.25.1', '29.60',
                   '24.61', '28.75.3', '24.61', '51.12.36', '51.55.33', '31.62.1', '74.20.53',
                   '74.60', '66.02', '51.56.4', '67.13.51')
    if okvad in exact_match:
        return True

    groups = ('35.30.', '75.', '24.4.', '62.', '65.')
    for item in groups:
        if okvad == item[:-1]:
            return True
        if okvad[:len(item)] == item:
            return True

    return False
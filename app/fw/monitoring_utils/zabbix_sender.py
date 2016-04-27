# -*- coding: utf-8 -*-
import shlex
import subprocess

def send(key, val):
    try:
        cmd = 'zabbix_sender -c /etc/zabbix/zabbix_agentd.conf -k %s -o %s' % (unicode(key),unicode(val))
        p = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, err = p.communicate()
        rc = p.returncode
    except Exception:
        return
    if rc != 0:
        raise Exception(err or output)

    return output

def zabbixed(key, val):
    def wrapper(f):
        def deco(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except:
                if isinstance(val, list) or isinstance(val, tuple):
                    for v in val:
                        send(key, val)
                else:
                    send(key, val)
        return deco
    return wrapper


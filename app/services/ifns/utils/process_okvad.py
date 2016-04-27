# -*- coding: utf-8 -*-
import json
import os
from time import time
from bson.objectid import ObjectId
from fw.db.sql_base import db as sqldb
from fw.catalogs.models import OkvadObject


def process_okvad():
    with open(os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/okvad.json'))), 'r') as f:
        okvad_data = json.loads(f.read())

    with open(os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/okvad_nalog_eshn.txt'))),
              'r') as f:
        eshn_okvads = filter(lambda x: x, [i.strip() for i in f.read().strip().split('\n')])

    with open(os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../data/okvad_nalog_general.txt'))),
              'r') as f:
        gen_okvads = filter(lambda x: x, [i.strip() for i in f.read().strip().split('\n')])

    print("a")
    OkvadObject.query.delete()
    sqldb.session.commit()
    print("b")

    PARENTS = {}
    for s in okvad_data:
        okved = s["okved"]
        caption = s["name"]
        parent = s.get("parent_okved", None)
        if okved in eshn_okvads:
            nalog = 'eshn'
        elif okved in gen_okvads:
            nalog = 'general'
        else:
            nalog = 'usn'

        t = time()
        new_ok = OkvadObject(
            id=str(ObjectId()),
            okved=okved,
            caption=caption,
            nalog=nalog,
            parent=parent
        )
        sqldb.session.add(new_ok)
        sqldb.session.commit()
        print(time() - t)
        item_id = new_ok.id
        PARENTS[okved] = item_id
    print("c")

    for obj in OkvadObject.query.filter():
        if obj.parent and len(obj.parent) > 15:
            continue
        if obj.parent:
            obj_parent = obj.parent
            if (len(obj_parent) > 1) and (len(obj_parent) < 9) and len(
                    filter(lambda c: c == '.' or c.isdigit(), obj_parent)) == len(obj_parent) and obj_parent[0].isdigit() and obj_parent[-1].isdigit():
                obj_parent = obj_parent[:2]

            obj.parent = PARENTS[obj_parent]
            sqldb.session.commit()
    print("d")

    for okvad in eshn_okvads:
        if not OkvadObject.query.filter_by(okved=okvad).scalar():
            print(u"Invalid okved in eshn okvads: %s" % okvad)

    for okvad in gen_okvads:
        if not OkvadObject.query.filter_by(okved=okvad).scalar():
            print(u"Invalid okved in general okvads: %s" % okvad)


if __name__ == "__main__":
    process_okvad()

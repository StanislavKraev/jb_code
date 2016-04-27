# -*- coding: utf-8 -*-

from datetime import datetime
import calendar
# noinspection PyUnresolvedReferences
from flask.ext.sqlalchemy import SQLAlchemy
import json
from bson import ObjectId
from sqlalchemy import func

CUSTOM_SERIALIZERS = {
    datetime: lambda dt: {"custom_type": "datetime", "val": calendar.timegm(dt.timetuple())},
    ObjectId: lambda oid: unicode(oid)
}

def raiser(val):
    raise TypeError(val)


def custom_json_serializer(data, **kwargs):
    return json.dumps(data, default=lambda x: CUSTOM_SERIALIZERS.get(type(x), raiser)(x), **kwargs)


def custom_obj_parser(obj):
    if 'custom_type' in obj and 'val' in obj and obj['custom_type'] == 'datetime':
        return datetime.utcfromtimestamp(obj['val'])
    return obj


def custom_json_deserializer(data):
    return json.loads(data, object_hook=custom_obj_parser)


class CustomSQLAlchemy(SQLAlchemy):

    def apply_driver_hacks(self, app, info, options):
        super(CustomSQLAlchemy, self).apply_driver_hacks(app, info, options)

        options['json_serializer'] = custom_json_serializer
        options['json_deserializer'] = custom_json_deserializer

db = CustomSQLAlchemy()

# -*- coding: utf-8 -*-


class BaseMongoModel(object):
    def __init__(self, **kwargs):
        self.__data = kwargs or {}

    def __getattr__(self, item):
        if item == '_BaseMongoModel__data':
            return object.__getattribute__(self, '__data')
        return self.__data.get(item, None)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            object.__setattr__(self, key, value)
            return
        self.__data[key] = value

    def __getitem__(self, item):
        return self.__data[item]

    def __setitem__(self, item, value):
        self.__data[item] = value

    def get(self, item, default_value=None):
        return self.__data.get(item, default_value)

    def insert(self, db, prepared_data=None, **kwargs):
        prepared_data = prepared_data or self.__data

        result_data = {}
        for c in prepared_data:
            val = prepared_data[c]
            if isinstance(val, BaseMongoModel):
                result_data[c] = val.as_dict()
            elif isinstance(val, list):
                tmp_list = []
                for i in val:
                    if isinstance(i, BaseMongoModel):
                        tmp_list.append(i.as_dict())
                    else:
                        tmp_list.append(i)
                result_data[c] = tmp_list
            else:
                result_data[c] = prepared_data[c]

        _id = self.get_collection(db).insert(result_data, **kwargs)
        self.__data['_id'] = _id
        return _id

    def __cmp__(self, other):
        if '_id' not in self.__data and '_id' not in other.__data:
            return 0 if self.__data == other.__data else -1
        if ('_id' not in self.__data and '_id' in other.__data) or '_id' in self.__data and '_id' not in other.__data:
            return -1
        return 0 if self.__data['_id'] == other.__data['_id'] else -1

    @classmethod
    def get_collection(cls, db):
        return db[cls.COLLECTION_NAME]

    @classmethod
    def find_one(cls, db, *args, **kwargs):
        col = cls.get_collection(db)
        result = col.find_one(*args, **kwargs)
        if not result:
            return
        new_obj = cls(**result)
        return new_obj

    @classmethod
    def find(cls, db, *args, **kwargs):
        col = cls.get_collection(db)
        return col.find(*args, **kwargs)

    def as_dict(self):
        return self.__data

    def update_attr(self, key, val):
        self.__data[key] = val

    @classmethod
    def update(cls, db, spec, document, upsert=False, manipulate=False, safe=None, multi=False, check_keys=True,
               **kwargs):
        col = cls.get_collection(db)
        return col.update(spec, document, upsert, manipulate, safe, multi, check_keys, **kwargs)

    def save(self, db):
        if '_id' not in self.__data:
            raise Exception("Can't save new model. Use insert method instead")
        self.get_collection(db).update({"_id": self.__data["_id"]}, self.__data)

    @classmethod
    def remove(cls, db, query):
        col = cls.get_collection(db)
        return col.remove(query)

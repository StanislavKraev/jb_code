# -*- coding: utf-8 -*-
from datetime import datetime
import shutil
import os
from custom_exceptions import FileNotFound
import urllib
from fw.documents.pdf_tools import get_pdf_doc_paget_count
from fw.storage.models import FileObject
from fw.db.sql_base import db as sqldb


class FileStorage(object):
    @staticmethod
    def add_file_from_disk(file_path, config, owner_id=None, file_name=None):
        assert file_name
        assert file_path

        if not os.path.exists(file_path):
            return

        new_file_path = datetime.utcnow().strftime('%Y-%m-%d')
        new_file_obj = FileObject(file_path=new_file_path, file_name=file_name)

        if owner_id:
            new_file_obj._owner_id = owner_id

        sqldb.session.add(new_file_obj)
        sqldb.session.commit()

        obj_id = new_file_obj.id

        new_file_location = os.path.join(
            config['DOCUMENT_STORAGE'],
            new_file_path,
            unicode(obj_id) + (os.path.splitext(file_path)[1] if (len(os.path.splitext(file_path)) == 2) else u""))

        try:
            os.makedirs(os.path.dirname(new_file_location), mode=0755)
        except Exception:
            pass
        shutil.copyfile(file_path, new_file_location)
        return new_file_obj

    @staticmethod
    def get_url(file_obj, config, absolute=False):
        if not file_obj:
            return
        prefix = u"" if not absolute else config['WEB_SCHEMA'] + '://' + config['DOMAIN']
        return prefix + config['STORAGE_URL'] + urllib.quote((unicode(file_obj.id) + '/' + file_obj.file_name).encode('utf8'))

    @staticmethod
    def get_path(file_obj, config):
        #file_ext = file_obj.file_ext if 'file_ext' in file_obj.as_dict() else os.path.splitext(file_obj.file_name)[1]

        file_ext = os.path.splitext(file_obj.file_name)[1]

        if file_obj._owner:
            return config['PRIVATE_STORAGE'] + file_obj.file_path + u'/' + unicode(file_obj.id) + file_ext

        return config['DOCUMENT_STORAGE'] + file_obj.file_path + u'/' + unicode(file_obj.id) + file_ext

    @staticmethod
    def remove_file(file_id, config):
        file_obj = FileObject.query.filter_by(id=file_id).first()
        if not file_obj:
            raise FileNotFound()

        try:
            os.unlink(FileStorage.get_path(file_obj, config))
        except Exception:
            raise FileNotFound()
        FileObject.query.filter_by(id=file_id).delete(synchronize_session='fetch')
        sqldb.session.commit()

    @staticmethod
    def get_file(file_id):
        return FileObject.query.filter_by(id=file_id).first()

    @staticmethod
    def get_shared_link(original_file_id, config, absolute=False):
        file_obj = FileObject.query.filter_by(id=original_file_id).first()
        if not file_obj:
            raise FileNotFound()
        if not file_obj._owner:
            return FileStorage.get_url(file_obj, config, absolute=absolute)

        shared_file_obj = FileObject.query.filter_by(_original_file=original_file_id, _owner=None).first()
        if shared_file_obj:
            return FileStorage.get_url(shared_file_obj, config, absolute=absolute)

        shared_file_obj = FileObject(
            file_name=file_obj.file_name,
            file_path=file_obj.file_path,
            _original_file=original_file_id
        )
        sqldb.session.add(shared_file_obj)
        sqldb.session.commit()
        return FileStorage.get_url(shared_file_obj, config, absolute=absolute)

    @staticmethod
    def get_pdf_file_page_count(file_id, config):
        file_obj = FileObject.query.filter_by(id=file_id).first()
        if not file_obj:
            return 0
        path = FileStorage.get_path(file_obj, config)
        ext = os.path.splitext(path)[1]
        if not ext or ext.lower() != '.pdf':
            return 0
        if not os.path.exists(path):
            return 0
        return get_pdf_doc_paget_count(path)

# -*- coding: utf-8 -*-
from datetime import datetime

from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject
from fw.storage.file_storage import FileStorage
from services.yurist.data_model.models import YuristBatchCheckObject, YuristCheckFilesObject


def forward(config, logger):
    logger.debug(u"Migrate yurist models")

    yurist_col = db['yurist_batch_check']
    YuristCheckFilesObject.query.delete()
    YuristBatchCheckObject.query.delete()
    sqldb.session.commit()
    for old_yc in yurist_col.find():
        batch_id = str(old_yc['batch_id'])
        batch = DocumentBatchDbObject.query.filter_by(id=batch_id).first()
        if not batch:
            continue

        new_yc = YuristBatchCheckObject(
            id=str(old_yc['_id']),
            batch_id=batch_id,
            status=old_yc['status'],
            create_date=old_yc.get('create_date', datetime.utcnow()),
            typos_correction=old_yc.get('typos_correction', False)
        )
        sqldb.session.add(new_yc)
        for file_descr in (old_yc.get('attached_files') or []):
            file_obj = FileStorage.get_file(str(file_descr['id']))
            if file_obj:
                attach = YuristCheckFilesObject()
                attach.files_id = file_obj.id
                new_yc.attached_files.append(attach)
    sqldb.session.commit()

def rollback(config, logger):
    pass

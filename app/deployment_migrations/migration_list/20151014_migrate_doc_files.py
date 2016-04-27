# -*- coding: utf-8 -*-

from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import BatchDocumentDbObject, DocumentFilesObject


def forward(config, logger):
    logger.debug(u"Migrate document files")

    for doc in BatchDocumentDbObject.query.filter(BatchDocumentDbObject.file_id != None):
        existing_mapping = DocumentFilesObject.query.filter_by(doc_id=doc.id, files_id=doc.file_id).first()
        if existing_mapping:
            continue
        new_mapping = DocumentFilesObject(doc_id=doc.id, files_id=doc.file_id)
        sqldb.session.add(new_mapping)
        sqldb.session.commit()

def rollback(config, logger):
    pass

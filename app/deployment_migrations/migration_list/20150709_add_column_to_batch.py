# -*- coding: utf-8 -*-
from datetime import datetime
import logging
from tempfile import TemporaryFile, NamedTemporaryFile
from bson import ObjectId
import requests
from fw.auth.models import AuthUser
from fw.db.sql_base import db as sqldb
from fw.documents.db_fields import DocumentBatchDbObject, BatchDocumentDbObject, CompanyDbObject, PrivatePersonDbObject
from fw.documents.enums import PersonTypeEnum, IncorporationFormEnum, CompanyTypeEnum
from fw.storage.models import FileObject


def forward(config, logger):
    logger.debug(u"Add column sent_mails to table doc_batch")

    sqldb.session.close()
    sqldb.engine.execute("ALTER TABLE doc_batch ADD COLUMN sent_mails VARCHAR[] DEFAULT NULL;")

def rollback(config, logger):
    sqldb.session.close()
    sqldb.engine.execute("ALTER TABLE doc_batch DROP COLUMN sent_mails;")

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
    logger.debug(u"Add column tried_to_render to table batch_docs")

    sqldb.session.close()
    sqldb.engine.execute("ALTER TABLE batch_docs ADD COLUMN tried_to_render BOOLEAN NOT NULL DEFAULT FALSE;")

def rollback(config, logger):
    pass

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
    logger.debug(u"Modify car assurances tables")

    sqldb.session.close()
    sqldb.engine.execute("ALTER TABLE car_assurance ADD COLUMN address VARCHAR NOT NULL DEFAULT '';")

    sqldb.engine.execute("ALTER TABLE car_assurance_branch ALTER COLUMN title DROP NOT NULL;")
    sqldb.engine.execute("ALTER TABLE car_assurance_branch ALTER COLUMN phone DROP NOT NULL;")
    sqldb.engine.execute("ALTER TABLE car_assurance_branch ALTER COLUMN address DROP NOT NULL;")
    sqldb.engine.execute("ALTER TABLE car_assurance_branch ALTER COLUMN address SET DEFAULT '';")

def rollback(config, logger):
    pass
